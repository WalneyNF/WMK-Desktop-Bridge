"""Propostas de edição via MCP, aprovadas no painel do WMK.

MCP pode enviar proposta, mas não recebe ferramenta de gravação. O painel local
confere SHA-256 e diff antes de aplicar. Banco SQLite é compartilhado entre
processos stdio MCP e servidor HTTP. Controle lógico, NÃO sandbox Windows.
"""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import secrets
import sqlite3
import threading
from editor_backend import _check_file, proposal, save_file
from workspace import workspace_root

DB = Path(__file__).resolve().parent / "config" / "mcp_proposals.sqlite3"
MAX_PENDING = 30
MAX_NEW_BYTES = 256 * 1024
LOCK = threading.RLock()

def _conn():
    DB.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB, timeout=6, isolation_level=None)
    conn.execute("PRAGMA busy_timeout=6000")
    conn.execute("""CREATE TABLE IF NOT EXISTS proposals(
        id TEXT PRIMARY KEY,
        root TEXT NOT NULL,
        relative TEXT NOT NULL,
        content TEXT NOT NULL,
        old_sha TEXT,
        new_sha TEXT NOT NULL,
        description TEXT NOT NULL,
        state TEXT NOT NULL DEFAULT 'pendente',
        created TEXT NOT NULL,
        result TEXT
    )""")
    return conn

def _check_path(relative: str) -> str:
    if not isinstance(relative, str):
        raise ValueError("Informe um caminho relativo")
    file = _check_file(relative)
    return str(file.relative_to(workspace_root())).replace("\\", "/")

def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()

def propose_write(relative: str, content: str, description: str = "") -> dict:
    """IA só propõe; NUNCA escreve no workspace."""
    relative = _check_path(relative)
    if not isinstance(content, str) or len(content.encode("utf-8")) > MAX_NEW_BYTES:
        raise ValueError("Limite: 256 KiB de texto UTF-8")
    if not isinstance(description, str) or len(description) > 500:
        raise ValueError("Descrição muito longa")
    file = _check_file(relative)
    old_sha = _sha_bytes(file.read_bytes()) if file.exists() else None
    result = proposal(relative, content, old_sha)
    if result["diff_truncado"]:
        raise ValueError("Diff excede 16 KB; envie uma alteração menor")
    if not result["mudou"]:
        return {"status": "sem_alteracao", "arquivo":relative}
    token = secrets.token_urlsafe(22)
    with LOCK, _conn() as conn:
        conn.execute("BEGIN IMMEDIATE")
        num = conn.execute("SELECT count(*) FROM proposals WHERE state='pendente'").fetchone()[0]
        if num >= MAX_PENDING:
            conn.execute("ROLLBACK")
            raise ValueError("Limite de propostas pendentes atingido")
        conn.execute("""INSERT INTO proposals
            (id,root,relative,content,old_sha,new_sha,description,state,created)
            VALUES (?,?,?,?,?,?,?,'pendente',?)""",
            (token,str(workspace_root()),relative,content,old_sha,
             _sha_bytes(content.encode("utf-8")),description,
             datetime.now(timezone.utc).isoformat()))
        conn.commit()
    return {"id":token,"status":"aguardando_aprovacao","arquivo":relative,
            "descricao":description,"novo_sha256":_sha_bytes(content.encode("utf-8")),
            "instrucoes":"Peça ao usuário para abrir /approvals e revisar. Não há execução automática."}

def list_pending() -> list[dict]:
    root = str(workspace_root())
    with _conn() as conn:
        rows=conn.execute("""SELECT id,relative,description,created,new_sha FROM proposals
                             WHERE state='pendente' AND root=? ORDER BY created DESC LIMIT 30""",(root,)).fetchall()
    return [{"id":a,"arquivo":b,"descricao":c,"criado":d,"sha256":e} for a,b,c,d,e in rows]

def get_proposal(token: str) -> dict:
    if not isinstance(token,str) or len(token)>100:
        raise ValueError("ID de proposta inválido")
    with _conn() as conn:
        row=conn.execute("""SELECT relative,content,old_sha,new_sha,description,state,root,created
                             FROM proposals WHERE id=?""",(token,)).fetchone()
    if not row or row[6] != str(workspace_root()):
        raise ValueError("Proposta não encontrada para esta pasta")
    relative,content,old_sha,new_sha,description,state,_,created=row
    if state!="pendente":
        raise ValueError("Proposta não está pendente")
    preview = proposal(relative,content,old_sha)   # falha se arquivo mudou
    return {"id":token,"arquivo":relative,"descricao":description,"criado":created,
            "sha256":new_sha,"diff":preview["diff"],"bytes":preview["bytes_novos"],
            "status":state}

def approve(token: str, expected_hash: str) -> dict:
    """Chame apenas após aprovação humana explícita na interface local."""
    if not isinstance(token,str) or len(token)>100 or not isinstance(expected_hash,str):
        raise ValueError("Proposta ou hash inválido")
    with LOCK, _conn() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row=conn.execute("""SELECT relative,content,old_sha,new_sha,root,state FROM proposals WHERE id=?""",(token,)).fetchone()
        if not row or row[4]!=str(workspace_root()) or row[5]!="pendente":
            conn.execute("ROLLBACK")
            raise ValueError("Proposta não encontrada ou já processada")
        relative,content,old_sha,new_sha,_,_=row
        if expected_hash != new_sha:
            conn.execute("ROLLBACK")
            raise ValueError("Hash da proposta diverge da versão revisada")
        # Não fazemos marcação antecipada 'aprovado': em erro, fica pendente para reabrir.
        result = save_file(relative, content, old_sha)
        conn.execute("UPDATE proposals SET state='aprovada',result=? WHERE id=?",
                     (json.dumps(result,ensure_ascii=False),token))
        conn.commit()
    return {"status":"aprovada","arquivo":relative,**result}

def reject(token: str) -> dict:
    if not isinstance(token,str) or len(token)>100:
        raise ValueError("Proposta inválida")
    with LOCK,_conn() as conn:
        changed=conn.execute("""UPDATE proposals SET state='recusada'
                                WHERE id=? AND root=? AND state='pendente'""",
                             (token,str(workspace_root()))).rowcount
    if not changed:
        raise ValueError("Proposta indisponível")
    return {"status":"recusada","id":token,"arquivos_excluidos":0}

def proposal_status(token: str) -> dict:
    if not isinstance(token,str) or len(token)>100:
        raise ValueError("ID inválido")
    with _conn() as conn:
        row=conn.execute("SELECT state,relative,root FROM proposals WHERE id=?",(token,)).fetchone()
    if not row or row[2]!=str(workspace_root()):
        raise ValueError("Proposta não encontrada")
    return {"status":row[0],"arquivo":row[1],"id":token}
