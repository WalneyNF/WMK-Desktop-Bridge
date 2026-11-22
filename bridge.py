"""WMK Desktop Bridge — ferramentas locais de diagnóstico, somente leitura."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from security_policy import require_diagnostic_mode, policy_status

VERSION = "0.8.1"
GIB = 1024 ** 3


def allowed_roots() -> list[Path]:
    # Se WMK_WORKSPACE estiver definido, TODAS as ferramentas genéricas de arquivos
    # ficam limitadas à pasta do projeto. Isso prevalece sobre WMK_ALLOWED_ROOTS.
    workspace = os.getenv("WMK_WORKSPACE", "").strip()
    if workspace:
        root = Path(workspace).expanduser().resolve(strict=True)
        if not root.is_dir() or root.parent == root or root == Path(root.anchor):
            raise PermissionError("WMK_WORKSPACE deve ser uma subpasta válida, não uma unidade inteira")
        return [root]
    roots = [Path.home()]
    configured = os.getenv("WMK_ALLOWED_ROOTS", "")
    if configured:
        roots.extend(Path(part.strip()) for part in configured.split(os.pathsep) if part.strip())
    return [root.expanduser().resolve() for root in roots]


def safe_path(value: str) -> Path:
    if not value or not value.strip():
        raise ValueError("Informe um caminho")
    path = Path(value).expanduser().resolve(strict=False)
    if not any(path == root or root in path.parents for root in allowed_roots()):
        raise PermissionError("Acesso negado: caminho fora de WMK_ALLOWED_ROOTS")
    return path


def drives() -> list[dict]:
    require_diagnostic_mode()
    candidates = [f"{letter}:\\" for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"] if os.name == "nt" else ["/"]
    result = []
    for drive in candidates:
        if not Path(drive).exists():
            continue
        try:
            usage = shutil.disk_usage(drive)
            result.append({"unidade": drive, "total_gb": round(usage.total/GIB, 2),
                           "usado_gb": round(usage.used/GIB, 2), "livre_gb": round(usage.free/GIB, 2)})
        except OSError:
            pass
    return result


def list_folder(path: str, limit: int = 100) -> list[dict]:
    if os.getenv("WMK_WORKSPACE", "").strip():
        raise PermissionError("Modo pasta única ativo: use wmk_workspace_list para filtrar arquivos sensíveis.")
    base = safe_path(path)
    if not base.is_dir():
        raise ValueError("A pasta não existe")
    rows = []
    for item in base.iterdir():
        if len(rows) >= max(1, min(int(limit), 200)):
            break
        try:
            info = item.lstat()
            rows.append({"nome": item.name, "caminho": str(item),
                         "tipo": "link" if item.is_symlink() else ("pasta" if item.is_dir() else "arquivo"),
                         "bytes": info.st_size if item.is_file() and not item.is_symlink() else None})
        except OSError:
            continue
    return rows


def folder_sizes(path: str, limit: int = 20, max_files: int = 200000) -> dict:
    if os.getenv("WMK_WORKSPACE", "").strip():
        raise PermissionError("Modo pasta única ativo: análise genérica desabilitada para proteger arquivos sensíveis.")
    base = safe_path(path)
    if not base.is_dir():
        raise ValueError("A pasta não existe")
    max_files = max(1000, min(int(max_files), 200000))
    rows, scanned, incomplete = [], 0, False
    for child in base.iterdir():
        if scanned >= max_files:
            incomplete = True
            break
        if not child.is_dir() or child.is_symlink():
            continue
        size = 0
        for root, dirs, files in os.walk(child, followlinks=False, onerror=lambda _: None):
            dirs[:] = [d for d in dirs if not Path(root, d).is_symlink()]
            for filename in files:
                if scanned >= max_files:
                    incomplete = True
                    break
                scanned += 1
                try:
                    size += (Path(root) / filename).lstat().st_size
                except OSError:
                    pass
            if incomplete:
                break
        rows.append({"pasta": str(child), "gb": round(size/GIB, 3)})
    rows.sort(key=lambda r: r["gb"], reverse=True)
    return {"pastas": rows[:max(1, min(int(limit), 100))],
            "arquivos_analisados": scanned, "parcial": incomplete,
            "observacao": "Estimativa; links e arquivos inacessíveis não entram no cálculo."}


def ollama_models() -> dict:
    require_diagnostic_mode()
    """Preferir API HTTP local do Ollama; CLI apenas como alternativa.

    A API normalmente responde sem precisar aguardar o executável 'ollama list'.
    Se o Ollama estiver offline, informar a causa em vez de aguardar indefinidamente.
    """
    url = os.getenv("WMK_OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
    # Não permitir URLs externas: este diagnóstico é exclusivamente local.
    if not (url.startswith("http://127.0.0.1:") or url.startswith("http://localhost:")):
        return {"status": "configuracao_invalida", "erro": "WMK_OLLAMA_URL deve apontar para localhost"}
    try:
        request = urllib.request.Request(url + "/api/tags", headers={"Accept": "application/json"})
        with urllib.request.urlopen(request, timeout=5) as response:
            data = json.load(response)
        models = data.get("models", [])
        if not isinstance(models, list):
            raise ValueError("Resposta inválida da API: models não é uma lista")
        return {
            "status": "online", "origem": "api", "url": url,
            "modelos": [{"nome": m.get("name", ""), "tamanho_gb": round(m.get("size", 0)/GIB, 2),
                         "modificado": m.get("modified_at", "")} for m in models if isinstance(m, dict)],
            "quantidade": len(models)
        }
    except (urllib.error.URLError, TimeoutError, ValueError, OSError, json.JSONDecodeError) as api_error:
        api_message = str(api_error)
    timeout = max(5, min(int(os.getenv("WMK_OLLAMA_TIMEOUT", "60")), 180))
    try:
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        process = subprocess.run(
            ["ollama", "list"], capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=timeout, shell=False, stdin=subprocess.DEVNULL, creationflags=flags)
        return {
            "status": "online" if process.returncode == 0 else "erro_cli",
            "origem": "cli", "codigo": process.returncode,
            "saida": process.stdout[:12000], "erro": process.stderr[:2000],
            "aviso_api": api_message
        }
    except FileNotFoundError:
        return {"status": "indisponivel",
                "erro": "API local indisponível e executável ollama não encontrado no PATH.",
                "detalhe_api": api_message}
    except subprocess.TimeoutExpired:
        return {"status": "timeout",
                "erro": f"Comando ollama list não respondeu em {timeout} segundos.",
                "detalhe_api": api_message,
                "sugestao": "Verifique se o Ollama está iniciado e teste http://127.0.0.1:11434/api/tags"}
    except OSError as exc:
        return {"status": "erro", "erro": str(exc), "detalhe_api": api_message}


def diagnostic() -> dict:
    """Status sempre consultável, mesmo se WMK_WORKSPACE estiver inválido.

    Não altera a política de acesso: as ferramentas de projeto continuam
    rejeitando pastas inexistentes, links ou diretórios não autorizados.
    """
    from workspace import workspace_status
    politica = policy_status()
    result = {
        "aplicativo": "WMK Desktop Bridge",
        "versao": VERSION,
        "politica": politica,
        "sistema": sys.platform,
        "raizes_autorizadas": [],
        "unidades": [],
        "workspace": workspace_status(),
    }
    if politica["modo"] == "projeto_restrito":
        if result["workspace"]["configurado"]:
            result["raizes_autorizadas"] = [result["workspace"]["pasta"]]
        else:
            result["aviso"] = "Pasta autorizada inválida: " + result["workspace"]["erro"]
        return result
    try:
        result["raizes_autorizadas"] = [str(p) for p in allowed_roots()]
        result["unidades"] = drives()
    except (OSError, ValueError, PermissionError, RuntimeError) as exc:
        result["aviso"] = "Diagnóstico parcialmente indisponível: " + str(exc)
    return result


if __name__ == "__main__":
    print(json.dumps(diagnostic(), ensure_ascii=False, indent=2))
