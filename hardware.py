"""Inventário de hardware Windows usando CIM. Consulta local, sem alterações."""
from __future__ import annotations

import base64
import json
import os
import platform
import subprocess
import time

_CACHE = None
_CACHE_AT = 0.0

# Script estático: não recebe trechos de código, caminhos ou parâmetros do usuário.
_PS = r"""
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
function Consultar([string]$classe, [string[]]$campos) {
    try {
        $result = @(Get-CimInstance -ClassName $classe -ErrorAction Stop |
            Select-Object -Property $campos)
        return @{ dados = $result; erro = $null }
    } catch {
        return @{ dados = @(); erro = $_.Exception.Message }
    }
}
$inventario = [ordered]@{
    processador = Consultar 'Win32_Processor' @('Name','Manufacturer','NumberOfCores','NumberOfLogicalProcessors','MaxClockSpeed','LoadPercentage')
    memoria = Consultar 'Win32_OperatingSystem' @('TotalVisibleMemorySize','FreePhysicalMemory','Caption','Version','OSArchitecture')
    modulos_ram = Consultar 'Win32_PhysicalMemory' @('Manufacturer','Capacity','Speed','ConfiguredClockSpeed','PartNumber','DeviceLocator')
    video = Consultar 'Win32_VideoController' @('Name','AdapterRAM','DriverVersion','VideoProcessor','CurrentHorizontalResolution','CurrentVerticalResolution')
    rede = Consultar 'Win32_NetworkAdapter' @('Name','NetConnectionStatus','Speed','MACAddress','PhysicalAdapter','NetEnabled','NetConnectionID')
    placa_mae = Consultar 'Win32_BaseBoard' @('Manufacturer','Product','Version')
    discos_fisicos = Consultar 'Win32_DiskDrive' @('Model','Size','InterfaceType','MediaType')
}
$inventario | ConvertTo-Json -Depth 7 -Compress
"""


def _ps_inventory() -> dict:
    if os.name != "nt":
        return {"status": "nao_suportado", "erro": "Inventário CIM disponível apenas no Windows"}
    command = [
        "powershell.exe", "-NoLogo", "-NoProfile", "-NonInteractive",
        "-EncodedCommand", base64.b64encode(_PS.encode("utf-16le")).decode("ascii")
    ]
    try:
        result = subprocess.run(
            command, capture_output=True, encoding="utf-8", errors="replace",
            timeout=35, shell=False, stdin=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if result.returncode:
            return {"status": "erro", "erro": result.stderr.strip()[:1000] or "Falha no PowerShell"}
        # PowerShell 5.1 pode codificar a saída na página de códigos local;
        # para os nomes, substituições são preferíveis a travar toda a interface.
        data = json.loads(result.stdout.lstrip("\ufeff").strip())
        return {"status": "ok", "sistema": platform.platform(), "categorias": data}
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "erro": "Consulta CIM ultrapassou 35 segundos"}
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {"status": "erro", "erro": str(exc)}


def hardware_info() -> dict:
    """Consulta cacheada por 30 segundos. Não exibe números de série nem IP."""
    global _CACHE, _CACHE_AT
    now = time.monotonic()
    if _CACHE is not None and now - _CACHE_AT < 30:
        return _CACHE
    data = _ps_inventory()
    _CACHE, _CACHE_AT = data, now
    return data
