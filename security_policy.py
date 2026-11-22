"""Política fail-closed do modo projeto: nenhuma consulta genérica fora da pasta."""
from __future__ import annotations
import os

def project_mode() -> bool:
    return bool(os.environ.get("WMK_WORKSPACE", "").strip())

def require_diagnostic_mode() -> None:
    if project_mode():
        raise PermissionError("Modo pasta única ativo: diagnósticos de sistema, discos, processos e Ollama estão bloqueados. Pare o servidor e remova WMK_WORKSPACE para habilitar o modo manutenção.")

def policy_status() -> dict:
    return {
        "modo": "projeto_restrito" if project_mode() else "manutencao_diagnostico",
        "edicao_por_ia": False,
        "exclusao_por_ia": False,
        "powershell_livre": False,
        "observacao": "Permissões lógicas não substituem isolamento por usuário Windows/ACL ou máquina virtual."
    }
