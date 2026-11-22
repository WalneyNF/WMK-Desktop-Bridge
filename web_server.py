"""Painel local na porta 8767. Não oferece terminal nem exclusão."""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from bridge import diagnostic, drives, folder_sizes, list_folder, ollama_models
from hardware import hardware_info
from powershell_tools import catalog, run_action

HOST, PORT = "127.0.0.1", 8767
DASHBOARD = Path(__file__).parent / "web" / "index.html"


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
            if route == "/":
                data = DASHBOARD.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'self'; object-src 'none'; frame-ancestors 'none'")
                self.end_headers()
                self.wfile.write(data)
                return
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
        except (OSError, ValueError, PermissionError) as exc:
            return self.reply({"erro": str(exc)}, 400)

    def do_POST(self):
        host = self.headers.get("Host", "")
        origin = self.headers.get("Origin", "")
        allowed = (f"http://127.0.0.1:{PORT}", f"http://localhost:{PORT}")
        if host not in (f"127.0.0.1:{PORT}", f"localhost:{PORT}") or origin not in allowed:
            return self.reply({"erro": "Origem não autorizada"}, 403)
        if urlparse(self.path).path != "/api/powershell/diagnose":
            return self.reply({"erro": "Rota desconhecida"}, 404)
        if self.headers.get("Content-Type", "").split(";")[0].strip() != "application/json":
            return self.reply({"erro": "Content-Type deve ser application/json"}, 415)
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 1 <= size <= 1024:
                return self.reply({"erro": "Requisição muito grande"}, 413)
            data = json.loads(self.rfile.read(size))
            if not isinstance(data, dict) or type(data.get("action")) is not str:
                return self.reply({"erro": "Ação inválida"}, 400)
            return self.reply(run_action(data["action"]))
        except (ValueError, OSError, json.JSONDecodeError) as exc:
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
