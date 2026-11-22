"""Workspace da IA: leitura restrita, gravação com backup e importação ZIP local.

ATENÇÃO: restrição lógica de caminhos, não é sandbox de sistema operacional.
Não execute código de projeto não confiável. Não exponha este módulo à internet.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
import difflib
import os
import shutil
import stat
import tempfile
import zipfile

MAX_READ = 256 * 1024
MAX_WRITE = 256 * 1024
MAX_ZIP_FILES = 2000
MAX_ZIP_TOTAL = 100 * 1024 * 1024
MAX_ZIP_ITEM = 20 * 1024 * 1024
BACKUPS = ".wmk-backups"


def workspace_root() -> Path:
    value = os.environ.get("WMK_WORKSPACE", "").strip()
    if not value:
        raise RuntimeError("Configure WMK_WORKSPACE para uma pasta específica antes de usar o agente.")
    root = Path(value).expanduser().resolve(strict=True)
    if not root.is_dir():
        raise ValueError("WMK_WORKSPACE não é uma pasta")
    if root.parent == root or (os.name == "nt" and root == Path(root.anchor)):
        raise PermissionError("A raiz de uma unidade não pode ser o espaço de trabalho.")
    return root


def _path(relative: str, *, existing: bool = False) -> Path:
    root = workspace_root()
    if not isinstance(relative, str) or not relative.strip():
        raise ValueError("Informe um caminho relativo dentro do workspace")
    rel = Path(relative)
    if rel.is_absolute() or rel.drive or any(p in ("..", ".wmk-backups") for p in rel.parts):
        raise PermissionError("Caminho absoluto, pai ou backup não permitido")
    candidate = root / rel
    # Resolve cada componente para impedir fugas por links/junções (incluindo Windows).
    canonical = candidate.resolve(strict=existing)
    if root not in canonical.parents and canonical != root:
        raise PermissionError("Caminho fora da pasta autorizada")
    if canonical == root:
        raise PermissionError("Selecione um arquivo ou subpasta, não a raiz")
    return canonical


def workspace_status() -> dict:
    try:
        return {"configurado": True, "pasta": str(workspace_root()),
                "modo": "edição com confirmação no agente CLI; MCP leitura"}
    except (OSError, ValueError, RuntimeError) as exc:
        return {"configurado": False, "erro": str(exc)}


def list_workspace(subdir: str = "", limit: int = 100) -> dict:
    base = workspace_root() if not subdir else _path(subdir, existing=True)
    if not base.is_dir():
        raise ValueError("Diretório não encontrado")
    limit = max(1, min(int(limit), 200))
    rows = []
    for item in sorted(base.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
        if item.name == BACKUPS or item.is_symlink():
            continue
        try:
            # Resolve também junctions no Windows.
            safe = item.resolve(strict=True)
            if workspace_root() not in safe.parents and safe != workspace_root():
                continue
            if len(rows) >= limit:
                break
            rows.append({"nome": item.name, "tipo": "pasta" if item.is_dir() else "arquivo",
                         "caminho_relativo": str(safe.relative_to(workspace_root())).replace("\\", "/"),
                         "bytes": item.stat().st_size if item.is_file() else None})
        except (OSError, ValueError):
            continue
    return {"pasta": str(base), "itens": rows, "limite": limit}


def read_workspace(relative: str) -> dict:
    file = _path(relative, existing=True)
    if not file.is_file() or file.is_symlink():
        raise ValueError("Não é arquivo regular")
    if file.stat().st_size > MAX_READ:
        raise ValueError("Arquivo maior que 256 KiB; leitura integral bloqueada")
    content = file.read_text(encoding="utf-8")
    if "\0" in content:
        raise ValueError("Arquivo binário não permitido")
    return {"arquivo": relative, "conteudo": content, "bytes": file.stat().st_size}


def preview_write(relative: str, content: str) -> dict:
    file = _path(relative)
    if not isinstance(content, str) or len(content.encode("utf-8")) > MAX_WRITE:
        raise ValueError("Conteúdo precisa ser texto UTF-8 com até 256 KiB")
    if file.exists() and (not file.is_file() or file.is_symlink()):
        raise ValueError("Destino não é arquivo regular")
    if file.exists() and file.stat().st_size > MAX_READ:
        raise ValueError("Arquivo existente maior que limite de edição")
    previous = file.read_text(encoding="utf-8") if file.exists() else ""
    diff = "".join(difflib.unified_diff(previous.splitlines(keepends=True),
                                        content.splitlines(keepends=True),
                                        fromfile=relative+" (antes)", tofile=relative+" (depois)"))
    return {"arquivo": relative, "existia": file.exists(), "mudou": previous != content,
            "diff": diff[:16000], "diff_truncado": len(diff) > 16000,
            "bytes_novos": len(content.encode("utf-8"))}


def write_approved(relative: str, content: str) -> dict:
    """Somente chamável por fluxo confiável após aprovação humana fora desta função."""
    preview = preview_write(relative, content)
    file = _path(relative)
    root = workspace_root()
    file.parent.mkdir(parents=True, exist_ok=True)
    # Verifica novamente após criar diretórios.
    file = _path(relative)
    backup = None
    if file.exists():
        backups = root / BACKUPS / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        destination = backups / Path(relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file, destination, follow_symlinks=False)
        backup = str(destination)
    fd, staging = tempfile.mkstemp(prefix=".wmk-stage-", dir=str(file.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as out:
            out.write(content)
        os.replace(staging, file)
    finally:
        if os.path.exists(staging):
            os.unlink(staging)
    return {"salvo": str(file), "backup": backup, "alterado": preview["mudou"]}


def inspect_zip(archive: str) -> dict:
    """Pré-visualização e validação; não extrai nada."""
    path = Path(archive).expanduser().resolve(strict=True)
    if not path.is_file() or not zipfile.is_zipfile(path):
        raise ValueError("Selecione um ZIP válido")
    members = []
    total = 0
    with zipfile.ZipFile(path) as zf:
        infos = zf.infolist()
        if len(infos) > MAX_ZIP_FILES:
            raise ValueError("ZIP contém arquivos demais")
        for info in infos:
            name = info.filename.replace("\\", "/")
            rel = PurePosixPath(name)
            if name.startswith("/") or not name or any(part in (".", "..", BACKUPS) for part in rel.parts):
                raise PermissionError("ZIP contém caminho inseguro")
            if ":" in rel.parts[0] or "\0" in name:
                raise PermissionError("ZIP contém caminho inválido")
            mode = info.external_attr >> 16
            if stat.S_ISLNK(mode):
                raise PermissionError("ZIP contém link simbólico")
            if info.file_size > MAX_ZIP_ITEM:
                raise ValueError("Arquivo ZIP individual excede 20 MiB")
            total += info.file_size
            if total > MAX_ZIP_TOTAL:
                raise ValueError("ZIP excede 100 MiB descompactados")
            if not info.is_dir():
                members.append({"arquivo": name, "bytes": info.file_size})
    return {"zip": str(path), "arquivos": members[:40],
            "quantidade": len(members), "total_mb": round(total / (1024*1024), 2)}


def import_zip_approved(archive: str, target_subfolder: str) -> dict:
    """Importação após confirmação humana na CLI. Destino deve ser subpasta nova."""
    report = inspect_zip(archive)
    destination = _path(target_subfolder)
    if destination.exists():
        raise FileExistsError("Destino já existe. Escolha uma subpasta NOVA para não sobrescrever arquivos.")
    archive_path = Path(archive).expanduser().resolve(strict=True)
    destination.mkdir(parents=True, exist_ok=False)
    try:
        with zipfile.ZipFile(archive_path) as zf:
            for info in zf.infolist():
                name = info.filename.replace("\\", "/")
                rel = PurePosixPath(name)
                target = _path(str(PurePosixPath(target_subfolder) / rel))
                if info.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                target = _path(str(PurePosixPath(target_subfolder) / rel))
                if target.exists():
                    raise FileExistsError("Arquivo duplicado no ZIP: " + name)
                with zf.open(info) as source, target.open("xb") as dest:
                    remaining = MAX_ZIP_ITEM + 1
                    while remaining > 0:
                        chunk = source.read(min(65536, remaining))
                        if not chunk:
                            break
                        dest.write(chunk)
                        remaining -= len(chunk)
                    if source.read(1):
                        raise ValueError("ZIP excedeu o tamanho permitido durante a extração")
        return {"importado": str(destination), "quantidade": report["quantidade"]}
    except Exception:
        shutil.rmtree(destination, ignore_errors=True)
        raise
