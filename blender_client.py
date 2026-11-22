"""Cliente Blender integrado ao WMK. Apenas operações constantes e autenticadas."""
from __future__ import annotations
import json
import os
import urllib.error
import urllib.request

from agent_hub import _validate_action, consume_approval

URL = "http://127.0.0.1:8768"

def status() -> dict:
    try:
        with urllib.request.urlopen(URL + "/status", timeout=3) as response:
            result = json.load(response)
        return {"conectado": True, **result, "token_configurado": bool(os.getenv("WMK_BLENDER_TOKEN"))}
    except (OSError, ValueError) as exc:
        return {"conectado": False, "erro": str(exc), "token_configurado": bool(os.getenv("WMK_BLENDER_TOKEN"))}


def _call(data: dict) -> dict:
    data = _validate_action(data)
    token = os.getenv("WMK_BLENDER_TOKEN", "").strip()
    if len(token) < 16:
        raise PermissionError("Configure WMK_BLENDER_TOKEN com pelo menos 16 caracteres")
    request = urllib.request.Request(
        URL + "/action", data=json.dumps(data, allow_nan=False).encode("utf-8"),
        headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
        method="POST")
    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        raise ValueError(f"Blender recusou ação (HTTP {exc.code}): " +
                         exc.read(400).decode("utf-8", "replace")) from None


def execute_approved(nonce: str) -> dict:
    # A proposta é consumida uma única vez, mesmo se a execução falhar.
    actions = consume_approval(nonce)
    results = []
    for action in actions:
        try:
            results.append({"acao": action, "resultado": _call(action)})
        except (OSError, ValueError, PermissionError) as exc:
            return {"status": "parcial", "executadas": results, "erro": str(exc),
                    "aviso": "Nenhum desfazer automático; utilize Ctrl+Z no Blender se necessário."}
    return {"status": "concluido", "executadas": results}


def list_objects() -> dict:
    return _call({"type": "list_objects"})
