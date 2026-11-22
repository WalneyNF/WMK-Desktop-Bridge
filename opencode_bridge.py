"""Inicia a interface WEB REAL do OpenCode em uma pasta WMK autorizada.

Não contém LLM nem sistema de patches substituto: os agentes/edições pertencem
ao OpenCode. Regras de aplicação não substituem sandbox/ACL de Windows.
"""
from __future__ import annotations
import atexit
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import threading
import time
import urllib.error
import urllib.request

from workspace import workspace_root

PORT = 4097
URL = f"http://127.0.0.1:{PORT}"
LOCK = threading.RLock()
PROCESS = None
PASSWORD = None
PROJECT = None
LOG = None
CONFIG = Path(__file__).resolve().parent / "config" / "wmk-opencode-policy.json"


def _command() -> str:
    cmd = shutil.which("opencode")
    if not cmd:
        raise RuntimeError(
            "OpenCode não encontrado no PATH deste Python. Instale/configure "
            "o OpenCode e confirme 'opencode --version' no mesmo terminal."
        )
    return cmd


def _policy() -> Path:
    """Cria configuração dedicada sem editar configuração de projeto/usuário."""
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    rules = {
        "$schema": "https://opencode.ai/config.json",
        "permissions": [
            {"action": "external_directory", "resource": "*", "effect": "deny"},
            {"action": "shell", "resource": "*", "effect": "deny"},
            {"action": "edit", "resource": "*", "effect": "ask"},
            {"action": "read", "resource": "*.env", "effect": "deny"},
            {"action": "read", "resource": "*.env.*", "effect": "deny"},
            {"action": "edit", "resource": "*.env", "effect": "deny"},
            {"action": "edit", "resource": "*.env.*", "effect": "deny"}
        ],
        "policies": [
            {"action": "tool.use", "resource": "shell:*", "effect": "deny"},
            {"action": "tool.use", "resource": "external_directory:*", "effect": "deny"}
        ]
    }
    CONFIG.write_text(json.dumps(rules, ensure_ascii=False, indent=2), encoding="utf-8")
    return CONFIG


def _healthy(password: str) -> bool:
    # O OpenCode Web é protegido por senha e escuta exclusivamente localhost.
    import base64
    token = base64.b64encode(("opencode:" + password).encode()).decode()
    request = urllib.request.Request(
        URL + "/global/health", headers={"Authorization": "Basic " + token}
    )
    try:
        with urllib.request.urlopen(request, timeout=1.3) as result:
            payload = json.load(result)
            return bool(payload.get("healthy"))
    except (OSError, ValueError):
        return False


def state() -> dict:
    root = str(workspace_root())
    with LOCK:
        running = PROCESS is not None and PROCESS.poll() is None
        return {
            "instalado": bool(shutil.which("opencode")),
            "ativo": bool(running),
            "url": URL if running else None,
            "pasta": PROJECT if running else root,
            "pasta_atual_corresponde": not running or PROJECT == root,
            "modo": "OpenCode real (interface web própria)",
            "restricoes": "shell negado; diretórios externos negados; edições exigem autorização",
            "isolamento_windows": False,
        }


def start() -> dict:
    global PROCESS, PASSWORD, PROJECT, LOG
    root = workspace_root()
    with LOCK:
        if PROCESS is not None and PROCESS.poll() is None:
            if PROJECT != str(root):
                raise RuntimeError(
                    "OpenCode já trabalha em outra pasta WMK. Encerre a sessão primeiro."
                )
            # A senha é devolvida apenas no evento de início/reabertura local.
            return {"ativo": True, "url": URL, "senha": PASSWORD,
                    "pasta": PROJECT, "reutilizado": True}
        exe = _command()
        config = _policy()
        password = secrets.token_urlsafe(32)
        env = os.environ.copy()
        env["OPENCODE_PASSWORD"] = password
        env["OPENCODE_SERVER_PASSWORD"] = password
        env["OPENCODE_CONFIG"] = str(config)
        env["OPENCODE_CONFIG_CONTENT"] = json.dumps({
            "permissions": [
                {"action": "external_directory", "resource": "*", "effect": "deny"},
                {"action": "shell", "resource": "*", "effect": "deny"},
                {"action": "edit", "resource": "*", "effect": "ask"}
            ],
            "policies": [
                {"action": "tool.use", "resource": "shell:*", "effect": "deny"},
                {"action": "tool.use", "resource": "external_directory:*", "effect": "deny"}
            ]
        })
        logs = config.parent / "wmk-opencode-runtime.log"
        LOG = logs.open("ab", buffering=0)
        command = [exe, "serve", "--hostname", "127.0.0.1", "--port", str(PORT)]
        # NPM no Windows pode publicar 'opencode.cmd'; Python não o executa
        # diretamente como um .exe. Somente o caminho já resolvido pelo PATH
        # é passado ao cmd.exe. Nenhum texto do usuário vira comando.
        if os.name == "nt" and Path(exe).suffix.lower() in (".cmd", ".bat"):
            command = [os.environ.get("ComSpec", r"C:\\Windows\\System32\\cmd.exe"),
                       "/d", "/s", "/c", subprocess.list2cmdline(command)]
        try:
            PROCESS = subprocess.Popen(
                command,
                cwd=str(root), env=env, stdin=subprocess.DEVNULL,
                stdout=LOG, stderr=subprocess.STDOUT,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except (OSError, ValueError) as exc:
            LOG.close()
            LOG = None
            PROCESS = None
            raise RuntimeError("Não foi possível iniciar OpenCode: " + str(exc)) from exc
        PASSWORD = password
        PROJECT = str(root)
        pid = PROCESS.pid

    # Espera finita somente por inicialização local, nunca pelo trabalho da IA.
    for _ in range(22):
        if PROCESS.poll() is not None:
            raise RuntimeError(
                "OpenCode encerrou ao iniciar. Consulte config/wmk-opencode-runtime.log "
                "e execute 'opencode serve --help'."
            )
        if _healthy(password):
            return {"ativo": True, "url": URL, "senha": password, "pasta": str(root),
                    "pid": pid, "reutilizado": False}
        time.sleep(0.35)
    raise RuntimeError(
        "OpenCode ainda não respondeu no localhost:4097. Confira a versão instalada "
        "e config/wmk-opencode-runtime.log. Nenhuma tarefa foi enviada à IA."
    )


def stop() -> dict:
    global PROCESS, PASSWORD, PROJECT, LOG
    with LOCK:
        process = PROCESS
        if process is None or process.poll() is not None:
            PROCESS = None
            PASSWORD = None
            PROJECT = None
            return {"ativo": False, "mensagem": "Nenhuma sessão WMK ativa"}
        process.terminate()
        try:
            process.wait(timeout=4)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=4)
        PROCESS = None
        PASSWORD = None
        PROJECT = None
        if LOG:
            LOG.close()
            LOG = None
        return {"ativo": False, "mensagem": "Servidor OpenCode iniciado pelo WMK encerrado"}


atexit.register(stop)
