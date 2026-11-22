"""WMK MCP dedicado ao ChatGPT/assistentes: SOMENTE pasta autorizada.

Uso: configure WMK_WORKSPACE e execute com cliente MCP stdio.
Compatível com clientes locais e com OpenAI Secure MCP Tunnel (se disponível).
Não oferece shell, Blender, diagnósticos do Windows nem exclusão.
"""
from mcp.server.fastmcp import FastMCP
from workspace import workspace_root, workspace_status, list_workspace, read_workspace
from mcp_approvals import propose_write, proposal_status

# Falhar ANTES de anunciar ferramentas, se a pasta não estiver autorizada.
workspace_root()
mcp = FastMCP("WMK Workspace Seguro")


@mcp.tool()
def wmk_workspace_status() -> dict:
    """Ver pasta autorizada e estado do workspace local."""
    return workspace_status()


@mcp.tool()
def wmk_workspace_list(subdir: str = "", limit: int = 100) -> dict:
    """Listar somente pasta autorizada, sem arquivos sensíveis."""
    return list_workspace(subdir, limit)


@mcp.tool()
def wmk_workspace_read(relative: str) -> dict:
    """Ler texto de arquivo interno da pasta autorizada, até 256 KiB."""
    return read_workspace(relative)


@mcp.tool()
def wmk_workspace_propose_write(relative: str, content: str, description: str = "") -> dict:
    """Propor criação ou edição UTF-8 na pasta autorizada.
    NÃO grava arquivo. O usuário aprova depois no painel local /approvals.
    """
    return propose_write(relative, content, description)


@mcp.tool()
def wmk_workspace_proposal_status(proposal_id: str) -> dict:
    """Consultar estado de proposta pendente/aprovada/recusada."""
    return proposal_status(proposal_id)


if __name__ == "__main__":
    mcp.run(transport="stdio")
