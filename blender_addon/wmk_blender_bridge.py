bl_info = {
    "name": "WMK Blender Safe Bridge",
    "author": "Walney Moreira Klein",
    "version": (0, 6, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > WMK",
    "description": "Ponte local com comandos 3D fixos, sem execução Python arbitrária",
    "category": "3D View",
}

import bpy
from bpy.props import StringProperty
from bpy.types import Operator, Panel
import json
import math
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread, Event
from queue import Queue, Empty

PORT = 8768
jobs = Queue(maxsize=12)
server = None
thread = None
timer_active = False
VALID_TYPES = {"list_objects", "create_cube", "create_uv_sphere", "create_cylinder", "set_color"}


def do_action(data):
    kind = data.get("type")
    if kind == "list_objects":
        return {"objects": [
            {"name": obj.name, "type": obj.type,
             "location": [round(float(x), 3) for x in obj.location]}
            for obj in list(bpy.context.scene.objects)[:200]
        ]}
    name = data["name"]
    if kind == "set_color":
        obj = bpy.data.objects.get(name)
        if obj is None or obj.type != "MESH":
            raise ValueError("Objeto não encontrado ou não é uma malha")
        rgba = data["color"]
        mat = bpy.data.materials.new(name="WMK_Cor_" + name[:36])
        mat.diffuse_color = tuple(rgba)
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)
        return {"object": obj.name, "material": mat.name}
    if kind == "create_cube":
        bpy.ops.mesh.primitive_cube_add(size=data["size"], location=data["location"])
    elif kind == "create_uv_sphere":
        bpy.ops.mesh.primitive_uv_sphere_add(radius=data["size"] / 2, location=data["location"])
    elif kind == "create_cylinder":
        bpy.ops.mesh.primitive_cylinder_add(radius=data["size"] / 2, depth=data["size"], location=data["location"])
    else:
        raise ValueError("Ação desconhecida")
    obj = bpy.context.object
    obj.name = name
    return {"object": obj.name, "type": kind}


def process_jobs():
    global timer_active
    if not timer_active:
        return None
    for _ in range(4):
        try:
            data, result_box, complete = jobs.get_nowait()
        except Empty:
            break
        try:
            result_box["result"] = do_action(data)
        except Exception as exc:
            result_box["error"] = str(exc)[:400]
        finally:
            complete.set()
    return 0.08


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/status":
            return self.send_json(404, {"error": "Not found"})
        return self.send_json(200, {"online": True, "addon": "WMK Blender Safe Bridge", "version": "0.6.0"})

    def do_POST(self):
        if self.path != "/action":
            return self.send_json(404, {"error": "Not found"})
        token = bpy.context.scene.wmk_bridge_token if bpy.context.scene else ""
        # O servidor sempre exige token; consulte propriedades no Blender.
        import hmac
        if not token or not hmac.compare_digest(self.headers.get("Authorization", ""), "Bearer " + token):
            return self.send_json(401, {"error": "Token inválido ou não configurado"})
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 1 <= size <= 4096:
                return self.send_json(413, {"error": "Requisição muito grande"})
            payload = json.loads(self.rfile.read(size))
            if not isinstance(payload, dict) or payload.get("type") not in VALID_TYPES:
                return self.send_json(400, {"error": "Ação não permitida"})
            # Não recebemos código nem scripts do cliente. Apenas tipos fixos.
            from math import isfinite
            kind = payload["type"]
            if kind != "list_objects":
                name = payload.get("name")
                if not isinstance(name, str) or not 1 <= len(name) <= 50:
                    return self.send_json(400, {"error": "Nome inválido"})
                if kind == "set_color":
                    c = payload.get("color")
                    if not isinstance(c, list) or len(c) != 4 or any(type(v) not in (float, int) or not isfinite(v) or not 0 <= v <= 1 for v in c):
                        return self.send_json(400, {"error": "Cor inválida"})
                else:
                    loc = payload.get("location")
                    size_value = payload.get("size")
                    if (not isinstance(loc, list) or len(loc) != 3 or
                        any(type(v) not in (float, int) or not isfinite(v) or abs(v) > 100 for v in loc) or
                        type(size_value) not in (int, float) or not isfinite(size_value) or not 0.05 <= size_value <= 20):
                        return self.send_json(400, {"error": "Posição/tamanho inválidos"})
            complete, holder = Event(), {}
            jobs.put_nowait((payload, holder, complete))
            if not complete.wait(timeout=8):
                return self.send_json(503, {"error": "Blender não processou o comando; verifique o add-on"})
            if "error" in holder:
                return self.send_json(400, {"error": holder["error"]})
            return self.send_json(200, holder["result"])
        except Exception as exc:
            return self.send_json(400, {"error": str(exc)[:300]})

    def send_json(self, code, payload):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


class WMK_OT_start(Operator):
    bl_idname = "wmk_bridge.start"
    bl_label = "Iniciar ponte local"

    def execute(self, context):
        global server, thread, timer_active
        if server:
            self.report({"INFO"}, "WMK Bridge já está ativo")
            return {"FINISHED"}
        if len(context.scene.wmk_bridge_token) < 16:
            self.report({"ERROR"}, "Configure token de pelo menos 16 caracteres")
            return {"CANCELLED"}
        try:
            server = HTTPServer(("127.0.0.1", PORT), Handler)
            thread = Thread(target=server.serve_forever, daemon=True)
            timer_active = True
            thread.start()
            bpy.app.timers.register(process_jobs, first_interval=0.1)
            self.report({"INFO"}, "WMK Bridge ativo na porta 8768 (somente localhost)")
        except Exception as exc:
            server = None
            timer_active = False
            self.report({"ERROR"}, str(exc)[:200])
            return {"CANCELLED"}
        return {"FINISHED"}


class WMK_OT_stop(Operator):
    bl_idname = "wmk_bridge.stop"
    bl_label = "Parar ponte"

    def execute(self, context):
        global server, timer_active
        timer_active = False
        if server:
            server.shutdown()
            server.server_close()
            server = None
        self.report({"INFO"}, "WMK Bridge parado")
        return {"FINISHED"}


class WMK_PT_panel(Panel):
    bl_label = "WMK Blender Bridge"
    bl_idname = "WMK_PT_safe_bridge"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "WMK"

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene, "wmk_bridge_token", text="Token")
        layout.operator("wmk_bridge.start", icon="PLAY")
        layout.operator("wmk_bridge.stop", icon="CANCEL")
        layout.label(text="Local: 127.0.0.1:8768")
        layout.label(text="Sem exclusão ou Python remoto")


classes = (WMK_OT_start, WMK_OT_stop, WMK_PT_panel)


def register():
    bpy.types.Scene.wmk_bridge_token = StringProperty(name="Token WMK", subtype="PASSWORD", default="")
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    global server, timer_active
    timer_active = False
    if server:
        server.shutdown()
        server.server_close()
        server = None
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.wmk_bridge_token


if __name__ == "__main__":
    register()
