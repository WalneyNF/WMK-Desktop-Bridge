"""Operações do editor WMK: interface humana, sem exposição a agentes IA.

Proteção por workspace, versões SHA-256 e backup anterior à gravação.
A autorização da interface não constitui sandbox do Windows.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

from workspace import _path, list_workspace, read_workspace, preview_write, write_approved, workspace_status

MAX_EDITOR_BYTES = 256 * 1024
EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx", ".html", ".css", ".json",
              ".md", ".txt", ".xml", ".yml", ".yaml", ".toml", ".ini",
              ".php", ".sql", ".rs", ".go", ".java", ".c", ".h", ".cpp",
              ".hpp", ".cs", ".gd", ".sh", ".bat", ".ps1", ".vue", ".svelte"}


def _check_file(path: str) -> Path:
    p = _path(path)
    if p.suffix.lower() not in EXTENSIONS:
        raise PermissionError("Tipo de arquivo não autorizado no editor")
    if p.is_symlink():
        raise PermissionError("Links não são editáveis")
    if p.exists() and not p.is_file():
        raise ValueError("Destino não é arquivo")
    return p


def _hash(text: bytes) -> str:
    return hashlib.sha256(text).hexdigest()


def list_files(subdir: str = "") -> dict:
    return list_workspace(subdir, 200)


def open_file(relative: str) -> dict:
    file = _check_file(relative)
    data = read_workspace(relative)
    raw = file.read_bytes()
    data["sha256"] = _hash(raw)
    return data


def proposal(relative: str, content: str, expected_sha256: str | None) -> dict:
    """Revalida arquivo original. Usa hash para evitar sobrescrever mudanças externas."""
    file = _check_file(relative)
    if not isinstance(content, str) or len(content.encode("utf-8")) > MAX_EDITOR_BYTES:
        raise ValueError("Conteúdo excede 256 KiB")
    if file.exists():
        original = file.read_bytes()
        if len(original) > MAX_EDITOR_BYTES:
            raise ValueError("Arquivo atual excede 256 KiB")
        if expected_sha256 != _hash(original):
            raise RuntimeError("Conflito: arquivo foi alterado fora do editor. Reabra antes de salvar.")
    elif expected_sha256 is not None:
        raise RuntimeError("Conflito: o arquivo foi removido; reabra o projeto.")
    return preview_write(relative, content)


def save_file(relative: str, content: str, expected_sha256: str | None) -> dict:
    """Somente após clique humano explícito, pelo endpoint local da interface."""
    diff = proposal(relative, content, expected_sha256)
    if diff["diff_truncado"]:
        raise ValueError("Diff excede o limite de revisão; divida a edição")
    if not diff["mudou"]:
        return {"alterado": False, "sha256": expected_sha256, "backup": None}
    # O backend revalida imediatamente antes de gravar. Não protege contra
    # processos hostis concorrentes; usar ACLs/isolamento para segurança forte.
    result = write_approved(relative, content)
    result["sha256"] = _hash(content.encode("utf-8"))
    return result
