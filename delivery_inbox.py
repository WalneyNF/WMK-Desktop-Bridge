"""Caixa de Entregas WMK — recebe versões públicas do GitHub sob aprovação.

Não expõe portas remotas, não instala dependências, não executa arquivos,
não substitui e não exclui projetos. NÃO é um upload direto do ChatGPT.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile

from workspace import _path, workspace_root, DENIED_DIRS, DENIED_NAMES, DENIED_SUFFIXES

MAX_DOWNLOAD = 24 * 1024 * 1024
MAX_UNPACKED = 60 * 1024 * 1024
MAX_FILES = 800
MAX_ONE_FILE = 12 * 1024 * 1024
TTL = 300
EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".html", ".htm", ".css",
    ".json", ".md", ".txt", ".xml", ".yml", ".yaml", ".toml", ".ini",
    ".php", ".sql", ".rs", ".go", ".java", ".c", ".h", ".cpp", ".hpp",
    ".cs", ".gd", ".sh", ".bat", ".ps1", ".vue", ".svelte", ".svg",
    ".png", ".jpg", ".jpeg", ".webp", ".obj", ".gltf", ".glb", ".blend",
}
PENDING: dict[str, dict] = {}
LOCK = threading.RLock()


def _slug(value: str, field: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,90}", value):
        raise ValueError(field + " inválido")
    if value.startswith(".") or value.endswith("."):
        raise ValueError(field + " inválido")
    return value


def _owner() -> str:
    return _slug(os.getenv("WMK_DELIVERY_OWNER", "WalneyNF"), "Proprietário")


def _request(url: str, limit: int) -> bytes:
    request = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "WMK-Desktop-Bridge-Entrega/0.7",
    })
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            if urllib.parse.urlparse(response.geturl()).hostname not in ("api.github.com", "codeload.github.com"):
                raise PermissionError("Redirecionamento externo recusado")
            data = response.read(limit + 1)
    except urllib.error.HTTPError as exc:
        raise ValueError("GitHub HTTP " + str(exc.code) + " — repositório público indisponível") from None
    except urllib.error.URLError as exc:
        raise ValueError("GitHub indisponível: " + str(exc.reason)) from None
    if len(data) > limit:
        raise ValueError("Entrega excede o limite de download")
    return data


def _archive(repo: str) -> tuple[dict, bytes]:
    owner = _owner()
    repo = _slug(repo, "Repositório")
    meta_url = "https://api.github.com/repos/" + owner + "/" + repo
    metadata = json.loads(_request(meta_url, 1024 * 200).decode("utf-8"))
    if metadata.get("private") or metadata.get("owner", {}).get("login", "").lower() != owner.lower():
        raise PermissionError("Somente repositórios públicos do proprietário autorizado")
    branch = metadata.get("default_branch")
    if not isinstance(branch, str) or not re.fullmatch(r"[A-Za-z0-9_./-]{1,100}", branch) or ".." in branch:
        raise ValueError("Branch não autorizada")
    url = "https://codeload.github.com/" + owner + "/" + repo + "/zip/refs/heads/" + urllib.parse.quote(branch, safe="/")
    return {"repositorio": owner + "/" + repo, "branch": branch,
            "url_repositorio": metadata.get("html_url", meta_url)}, _request(url, MAX_DOWNLOAD)


def _members(data: bytes) -> tuple[list[tuple[str, bytes]], int]:
    result = []
    skipped = 0
    total = 0
    names = set()
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        infos = archive.infolist()
        if len(infos) > MAX_FILES + 100:
            raise ValueError("Pacote tem entradas demais")
        for info in infos:
            raw = info.filename.replace("\\", "/")
            parts = PurePosixPath(raw).parts
            if info.is_dir():
                continue
            if len(parts) < 2 or raw.startswith("/") or any(p in (".", "..") for p in parts) or ":" in parts[0]:
                raise PermissionError("Caminho inseguro no ZIP")
            relative = PurePosixPath(*parts[1:])
            subparts = tuple(p.lower() for p in relative.parts)
            mode = info.external_attr >> 16
            if stat.S_ISLNK(mode):
                raise PermissionError("Link simbólico no ZIP")
            suffix = relative.suffix.lower()
            if (not relative.parts or any(part in DENIED_DIRS for part in subparts)
                    or relative.name.lower() in DENIED_NAMES
                    or relative.name.lower().startswith(".env.")
                    or suffix in DENIED_SUFFIXES
                    or suffix not in EXTENSIONS):
                skipped += 1
                continue
            key = str(relative).lower()
            if key in names:
                raise ValueError("Arquivos duplicados no ZIP (Windows)")
            names.add(key)
            if info.file_size > MAX_ONE_FILE:
                raise ValueError("Arquivo excede 12 MiB: " + str(relative))
            total += info.file_size
            if total > MAX_UNPACKED or len(result) >= MAX_FILES:
                raise ValueError("Limites de arquivos da entrega excedidos")
            content = archive.read(info)
            if len(content) != info.file_size:
                raise ValueError("Tamanho inválido: " + str(relative))
            result.append((str(relative), content))
    if not result:
        raise ValueError("Entrega sem arquivos permitidos")
    return result, skipped


def prepare(repo: str) -> dict:
    workspace_root()  # obriga modo de pasta única
    meta, downloaded = _archive(repo)
    files, skipped = _members(downloaded)
    digest = hashlib.sha256(downloaded).hexdigest()
    import secrets
    token = secrets.token_urlsafe(24)
    with LOCK:
        now = time.monotonic()
        for key in list(PENDING):
            if PENDING[key]["expires"] < now:
                del PENDING[key]
        # Limite de prévias em memória
        if len(PENDING) >= 3:
            raise ValueError("Já existem três entregas pendentes. Aguarde expirar ou confirme uma.")
        PENDING[token] = {
            "files": files, "meta": meta, "workspace": str(workspace_root()),
            "expires": now + TTL, "digest": digest,
        }
    return {**meta, "proposta": token, "expira_segundos": TTL,
            "sha256_arquivo": digest, "arquivos": len(files),
            "bytes_descompactados": sum(len(content) for _, content in files),
            "ignorados": skipped,
            "amostra": [name for name, _ in files[:30]],
            "observacao": "Prévia somente; nenhum arquivo gravado. Destino deve ser pasta nova."}


def receive(token: str, destination: str) -> dict:
    if not isinstance(token, str) or len(token) > 80:
        raise ValueError("Identificador de entrega inválido")
    if not isinstance(destination, str) or not re.fullmatch(r"[A-Za-z0-9_-]{2,70}", destination):
        raise ValueError("Destino deve ser nome de subpasta nova (letras, números, - ou _)")
    with LOCK:
        item = PENDING.pop(token, None)
    if not item or item["expires"] < time.monotonic():
        raise PermissionError("Entrega expirada ou já utilizada")
    if str(workspace_root()) != item["workspace"]:
        raise PermissionError("Pasta autorizada mudou desde a prévia")
    root = workspace_root()
    target = _path(destination)
    if target.exists():
        raise FileExistsError("Pasta destino já existe. A entrega nunca sobrescreve projetos.")
    target.mkdir(mode=0o700)
    # Nunca executar códigos: salvar apenas arquivos permitidos dentro da nova subpasta.
    written = []
    try:
        for relative, data in item["files"]:
            file = _path(destination + "/" + relative.replace("\\", "/"))
            file.parent.mkdir(parents=True, exist_ok=True)
            file = _path(destination + "/" + relative.replace("\\", "/"))
            if file.exists():
                raise FileExistsError("Arquivo já existe durante a entrega")
            with file.open("xb") as output:
                output.write(data)
            written.append(str(file))
    except Exception:
        # Segurança: não remover nada automaticamente após erro; arquivos parciais
        # ficam na pasta NOVA, para inspeção humana.
        raise
    return {"recebido": True, "pasta": str(target), "arquivos": len(written),
            "origem": item["meta"]["repositorio"], "sha256_arquivo": item["digest"],
            "aviso": "Não execute scripts de projetos desconhecidos. Não houve exclusão ou sobrescrita."}
