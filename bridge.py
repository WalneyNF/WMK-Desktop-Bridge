"""WMK Desktop Bridge — ferramentas locais de diagnóstico, somente leitura."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

VERSION = "0.2.0"
GIB = 1024 ** 3


def allowed_roots() -> list[Path]:
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
    try:
        process = subprocess.run(["ollama", "list"], capture_output=True, text=True,
                                 timeout=15, shell=False, stdin=subprocess.DEVNULL)
        return {"codigo": process.returncode, "saida": process.stdout[:12000],
                "erro": process.stderr[:2000]}
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as exc:
        return {"erro": str(exc)}


def diagnostic() -> dict:
    return {"aplicativo": "WMK Desktop Bridge", "versao": VERSION,
            "modo": "somente leitura", "sistema": sys.platform,
            "raizes_autorizadas": [str(p) for p in allowed_roots()], "unidades": drives()}


if __name__ == "__main__":
    print(json.dumps(diagnostic(), ensure_ascii=False, indent=2))
