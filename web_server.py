"""Painel local na porta 8767. Editor humano restrito, sem exclusão ou shell livre."""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from bridge import diagnostic, drives, folder_sizes, list_folder, ollama_models
from hardware import hardware_info
from powershell_tools import catalog, run_action
from workspace import workspace_status
from editor_backend import list_files, open_file, proposal, save_file
from code_ai import ai_status, suggest_code
from agent_hub import list_agents, register_agent, providers_status, propose
from blender_client import status as blender_status, list_objects as blender_objects, execute_approved

HOST, PORT = "127.0.0.1", 8767
DASHBOARD = Path(__file__).parent / "web" / "index.html"
EDITOR = Path(__file__).parent / "web" / "editor.html"
EDITOR_AI = Path(__file__).parent / "web" / "editor_ai.js"
AGENTS_HTML = Path(__file__).parent / "web" / "agents.html"


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Proteção adicional contra requisições vindas de páginas externas.
        host = self.headers.get("Host", "")
        origin = self.headers.get("Origin", "")
        if host not in (f"127.0.0.1:{PORT}", f"localhost:{PORT}") or (
                origin and origin not in (f"http://127.0.0.1:{PORT}", f"http://localhost:{PORT}")):
            return self.reply({"erro": "Origem não autorizada"}, 403)
        route = urlparse(self.path).path
        try:
            if route == "/editor_ai.js":
                data = EDITOR_AI.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "application/javascript; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            if route in ("/", "/editor", "/agents"):
                is_editor = route == "/editor"
                data = (EDITOR if is_editor else (AGENTS_HTML if route == "/agents" else DASHBOARD)).read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
                if is_editor:
                    self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; font-src 'self' data: https://cdn.jsdelivr.net; worker-src 'self' blob:; connect-src 'self' https://cdn.jsdelivr.net; object-src 'none'; frame-ancestors 'none'")
                else:
                    self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'self'; object-src 'none'; frame-ancestors 'none'")
                self.end_headers()
                self.wfile.write(data)
                return
            if route == "/api/agents":
                return self.reply(list_agents())
            if route == "/api/providers":
                return self.reply(providers_status())
            if route == "/api/blender/status":
                return self.reply(blender_status())
            if route == "/api/blender/objects":
                return self.reply(blender_objects())
            if route == "/api/ai/status":
                return self.reply(ai_status())
            if route == "/api/workspace/status":
                return self.reply(workspace_status())
            if route == "/api/editor/list":
                args = parse_qs(urlparse(self.path).query)
                return self.reply(list_files(args.get("subdir", [""])[0]))
            if route == "/api/editor/open":
                args = parse_qs(urlparse(self.path).query)
                return self.reply(open_file(args.get("path", [""])[0]))
            if route == "/api/powershell/catalog":
                return self.reply(catalog())
            if route == "/api/status":
                return self.reply(diagnostic())
            if route == "/api/drives":
                return self.reply(drives())
            if route == "/api/ollama":
                return self.reply(ollama_models())
            if route == "/api/hardware":
                return self.reply(hardware_info())
            if route == "/api/home":
                return self.reply(list_folder(str(Path.home()), 80))
            if route == "/api/size-home":
                return self.reply(folder_sizes(str(Path.home()), 15))
            return self.reply({"erro": "Rota desconhecida"}, 404)
        except (OSError, ValueError, PermissionError, RuntimeError, UnicodeError) as exc:
            return self.reply({"erro": str(exc)}, 400)

    def do_POST(self):
        host = self.headers.get("Host", "")
        origin = self.headers.get("Origin", "")
        allowed = (f"http://127.0.0.1:{PORT}", f"http://localhost:{PORT}")
        if host not in (f"127.0.0.1:{PORT}", f"localhost:{PORT}") or origin not in allowed:
            return self.reply({"erro": "Origem não autorizada"}, 403)
        route = urlparse(self.path).path
        if route not in ("/api/powershell/diagnose", "/api/editor/preview", "/api/editor/save", "/api/ai/suggest", "/api/agents/register", "/api/agents/propose", "/api/blender/approve"):
            return self.reply({"erro": "Rota desconhecida"}, 404)
        if self.headers.get("Content-Type", "").split(";")[0].strip() != "application/json":
            return self.reply({"erro": "Content-Type deve ser application/json"}, 415)
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 1 <= size <= (110000 if route == "/api/ai/suggest" else (550000 if route.startswith("/api/editor/") else 12000)):
                return self.reply({"erro": "Requisição muito grande"}, 413)
            data = json.loads(self.rfile.read(size))
            if not isinstance(data, dict):
                return self.reply({"erro": "JSON inválido"}, 400)
            if route == "/api/agents/register":
                return self.reply(register_agent(data))
            if route == "/api/agents/propose":
                return self.reply(propose(data.get("agent_id"), data.get("task")))
            if route == "/api/blender/approve":
                if not isinstance(data.get("proposta"), str):
                    return self.reply({"erro": "Identificador de proposta inválido"}, 400)
                return self.reply(execute_approved(data["proposta"]))
            if route == "/api/ai/suggest":
                return self.reply(suggest_code(data))
            if route == "/api/powershell/diagnose":
                if type(data.get("action")) is not str:
                    return self.reply({"erro": "Ação inválida"}, 400)
                return self.reply(run_action(data["action"]))
            if type(data.get("path")) is not str or type(data.get("content")) is not str:
                return self.reply({"erro": "Informe path e content"}, 400)
            sha = data.get("sha256")
            if sha is not None and (type(sha) is not str or len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha)):
                return self.reply({"erro": "Hash de versão inválido"}, 400)
            if route == "/api/editor/preview":
                return self.reply(proposal(data["path"], data["content"], sha))
            return self.reply(save_file(data["path"], data["content"], sha))
        except (ValueError, OSError, PermissionError, RuntimeError, UnicodeError, KeyError) as exc:
            return self.reply({"erro": str(exc)}, 400)

    def reply(self, obj, status=200):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):
        print("WMK WEB:", fmt % args)


if __name__ == "__main__":
    print(f"WMK Desktop Bridge — painel local http://{HOST}:{PORT}")
    print("Somente leitura; pressione Ctrl+C para encerrar.")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
