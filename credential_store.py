"""Segredos WMK com DPAPI nativa do Windows, sem dependências adicionais.

Nunca grava credenciais no repositório, logs, JSON, cookies ou navegador.
A proteção DPAPI é vinculada ao usuário Windows; não isola outros processos
maliciosos que executem sob a MESMA conta. Desative em sistemas não Windows.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import re
import sys
import tempfile

ALLOWED = frozenset(("GROQ_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY", "WMK_BLENDER_TOKEN"))
_FOLDER = "WMKDesktopBridge"
_PREFIX = "wmk-dpapi-v1"


def _directory() -> Path:
    if os.name != "nt":
        raise RuntimeError("Cadastro protegido no painel disponível apenas no Windows")
    base = os.environ.get("LOCALAPPDATA", "").strip()
    if not base:
        raise RuntimeError("LOCALAPPDATA não definido na sessão Windows")
    root = Path(base) / _FOLDER / "secrets"
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    return root


def _name(name: str) -> str:
    if name not in ALLOWED:
        raise ValueError("Nome de credencial não autorizado")
    return name


def _path(name: str) -> Path:
    return _directory() / (_name(name) + ".wmk")


class DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]


def _blob(data: bytes) -> tuple[DATA_BLOB, object]:
    buf = ctypes.create_string_buffer(data, len(data))
    return DATA_BLOB(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_ubyte))), buf


def _crypt(data: bytes, protect: bool) -> bytes:
    if sys.platform != "win32":
        raise RuntimeError("DPAPI requer Windows")
    input_blob, reference = _blob(data)
    output_blob = DATA_BLOB()
    crypt = ctypes.windll.crypt32
    func = crypt.CryptProtectData if protect else crypt.CryptUnprotectData
    func.restype = wintypes.BOOL
    # CRYPTPROTECT_UI_FORBIDDEN = 0x01
    if protect:
        ok = func(ctypes.byref(input_blob), None, None, None, None, 1,
                  ctypes.byref(output_blob))
    else:
        ok = func(ctypes.byref(input_blob), None, None, None, None, 1,
                  ctypes.byref(output_blob))
    if not ok:
        raise OSError("DPAPI recusou a operação (usuário Windows ou perfil diferente)")
    try:
        return ctypes.string_at(output_blob.pbData, output_blob.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(output_blob.pbData)


def save(name: str, value: str) -> dict:
    name = _name(name)
    if not isinstance(value, str) or not 16 <= len(value.strip()) <= 512:
        raise ValueError("Chave inválida: informe 16 a 512 caracteres")
    if any(ord(c) < 33 or ord(c) > 126 for c in value.strip()):
        raise ValueError("A chave não pode ter espaços nem caracteres de controle")
    path = _path(name)
    encrypted = _crypt((_PREFIX + "\n" + value.strip()).encode("utf-8"), True)
    fd, tmp = tempfile.mkstemp(prefix=".wmk-secret-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as out:
            out.write(encrypted)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    return {"credencial": name, "salva": True, "armazenamento": "DPAPI Windows",
            "aviso": "Chave não retornada pela API. Reiniciar servidor não é necessário."}


def get(name: str) -> str:
    name = _name(name)
    current = os.getenv(name, "").strip()
    if current:
        return current
    if os.name != "nt":
        return ""
    path = _path(name)
    if not path.is_file():
        return ""
    try:
        data = _crypt(path.read_bytes(), False).decode("utf-8")
        prefix = _PREFIX + "\n"
        if not data.startswith(prefix):
            raise ValueError("Formato de credencial inválido")
        return data[len(prefix):]
    except (OSError, UnicodeError, ValueError) as exc:
        raise RuntimeError("Credencial armazenada indisponível. Cadastre novamente no painel.") from exc


def status(name: str) -> dict:
    name = _name(name)
    env = bool(os.getenv(name, "").strip())
    stored = os.name == "nt" and _path(name).is_file()
    return {"configurada": bool(env or stored),
            "origem": "ambiente" if env else ("DPAPI Windows" if stored else "ausente")}
