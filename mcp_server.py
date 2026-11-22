"""Servidor MCP local via stdio. Sem acesso remoto e sem comandos arbitrários."""
from mcp.server.fastmcp import FastMCP
from bridge import diagnostic, drives, list_folder, folder_sizes, ollama_models

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


if __name__ == "__main__":
    mcp.run(transport="stdio")
