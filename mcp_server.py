"""Servidor MCP local via stdio. Sem acesso remoto e sem comandos arbitrários."""
from mcp.server.fastmcp import FastMCP
from bridge import diagnostic, drives, list_folder, folder_sizes, ollama_models
from hardware import hardware_info
from powershell_tools import catalog, run_action
from workspace import workspace_status, list_workspace, read_workspace
from blender_client import status as blender_status, list_objects as blender_list_objects
from mcp_approvals import propose_write, proposal_status

mcp = FastMCP("WMK Desktop Bridge")


@mcp.tool()
def wmk_status() -> dict:
    """Diagnóstico e permissões atuais do WMK Desktop Bridge."""
    return diagnostic()


@mcp.tool()
def wmk_drives() -> list[dict]:
    """Consultar espaço disponível nas unidades de disco."""
    return drives()


@mcp.tool()
def wmk_list_folder(path: str, limit: int = 100) -> list[dict]:
    """Listar arquivos dentro de uma raiz autorizada, sem modificar arquivos."""
    return list_folder(path, limit)


@mcp.tool()
def wmk_folder_sizes(path: str, limit: int = 20) -> dict:
    """Medir as maiores subpastas; retorna aviso quando a análise é parcial."""
    return folder_sizes(path, limit)


@mcp.tool()
def wmk_ollama_models() -> dict:
    """Consultar os modelos do Ollama sem instalar nem remover modelos."""
    return ollama_models()


@mcp.tool()
def wmk_hardware() -> dict:
    """Inventário de CPU, RAM, vídeo, rede, placa-mãe e discos físicos (somente leitura)."""
    return hardware_info()


@mcp.tool()
def wmk_powershell_catalog() -> list[dict]:
    """Listar diagnósticos PowerShell permitidos; scripts são fixos, somente leitura."""
    return catalog()


@mcp.tool()
def wmk_powershell_diagnose(action: str) -> dict:
    """Executar uma ação pré-definida pelo ID; não recebe código PowerShell livre."""
    return run_action(action)

@mcp.tool()
def wmk_workspace_status() -> dict:
    """Informar qual pasta foi autorizada como workspace da IA."""
    return workspace_status()


@mcp.tool()
def wmk_workspace_list(subdir: str = "", limit: int = 100) -> dict:
    """Listar somente arquivos dentro de WMK_WORKSPACE, ocultando arquivos sensíveis."""
    return list_workspace(subdir, limit)


@mcp.tool()
def wmk_workspace_read(relative: str) -> dict:
    """Ler arquivo texto UTF-8 de até 256 KiB, dentro da pasta autorizada."""
    return read_workspace(relative)

@mcp.tool()
def wmk_blender_status() -> dict:
    """Verificar conexão com o add-on WMK Blender local (sem modificar cena)."""
    return blender_status()


@mcp.tool()
def wmk_blender_list() -> dict:
    """Listar objetos da cena Blender local, exige token e não altera objetos."""
    return blender_list_objects()

@mcp.tool()
def wmk_workspace_propose_write(relative: str, content: str, description: str = "") -> dict:
    """PROPOR criação/edição de um arquivo relativo da pasta autorizada.
    Não grava no projeto: o usuário precisa revisar diff e aprovar no painel /approvals.
    Nenhuma exclusão nem execução de programas é disponibilizada.
    """
    return propose_write(relative, content, description)


@mcp.tool()
def wmk_workspace_proposal_status(proposal_id: str) -> dict:
    """Consultar se a proposta de código aguarda aprovação, foi aprovada ou recusada."""
    return proposal_status(proposal_id)


if __name__ == "__main__":
    mcp.run(transport="stdio")
