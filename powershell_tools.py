"""Executor PowerShell limitado a diagnósticos pré-definidos, somente leitura.

Não aceita código PowerShell enviado por IA, navegador ou usuário.
As ações e seus scripts são constantes auditáveis no repositório.
"""
from __future__ import annotations

import base64
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import threading
import time
from security_policy import require_diagnostic_mode

ACTIONS = {
    "versao_powershell": ("Versão do PowerShell", "$PSVersionTable.PSVersion.ToString()"),
    "processos": ("15 processos com maior consumo de RAM",
                 "Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 15 ProcessName, Id, @{Name='MemoriaMB';Expression={[math]::Round($_.WorkingSet64/1MB,1)}} | Format-Table -AutoSize | Out-String -Width 180"),
    "servicos_parados": ("Até 25 serviços parados",
                        "Get-Service | Where-Object Status -eq 'Stopped' | Select-Object -First 25 Name,DisplayName,Status | Format-Table -AutoSize | Out-String -Width 180"),
    "unidades": ("Espaço em disco",
                 "Get-CimInstance Win32_LogicalDisk -Filter \"DriveType=3\" | Select-Object DeviceID,@{N='LivreGB';E={[math]::Round($_.FreeSpace/1GB,2)}},@{N='TotalGB';E={[math]::Round($_.Size/1GB,2)}} | Format-Table -AutoSize | Out-String -Width 180"),
    "rede": ("Adaptadores de rede conectados, sem IP/MAC",
             "Get-NetAdapter | Where-Object Status -eq 'Up' | Select-Object Name,InterfaceDescription,LinkSpeed,Status | Format-Table -AutoSize | Out-String -Width 180"),
    "tempo_atividade": ("Última inicialização e tempo ativo",
                       "Get-CimInstance Win32_OperatingSystem | Select-Object LastBootUpTime | Format-List | Out-String"),
}
_TIMEOUT_SECONDS = 20
_LOG_LOCK = threading.Lock()


def catalog() -> list[dict]:
    require_diagnostic_mode()
    return [{"id": key, "descricao": item[0], "leitura": True} for key, item in ACTIONS.items()]


def _audit(action: str, outcome: str, duration: float) -> None:
    # Não registrar conteúdo completo da resposta nem dados de rede.
    path = Path(__file__).resolve().parent / "logs" / "powershell-audit.jsonl"
    try:
        with _LOG_LOCK:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as f:
                f.write(json.dumps({"quando": datetime.now(timezone.utc).isoformat(),
                                    "acao": action, "resultado": outcome,
                                    "duracao_s": round(duration, 2)}, ensure_ascii=False) + "\n")
    except OSError:
        pass


def run_action(action: str) -> dict:
    require_diagnostic_mode()
    if action not in ACTIONS:
        return {"status": "negado", "erro": "Ação não permitida; consulte wmk_powershell_catalog."}
    if os.name != "nt":
        return {"status": "nao_suportado", "erro": "Apenas Windows"}
    start = time.monotonic()
    label, script = ACTIONS[action]
    # Executa exatamente o script pré-aprovado; nenhum parâmetro vira código.
    encoded = base64.b64encode(script.encode("utf-16le")).decode("ascii")
    try:
        p = subprocess.run(
            ["powershell.exe", "-NoLogo", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=_TIMEOUT_SECONDS,
            shell=False, stdin=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        status = "ok" if p.returncode == 0 else "erro"
        result = {"status": status, "acao": action, "descricao": label, "codigo": p.returncode,
                  "saida": p.stdout[:12000], "erro": p.stderr[:1500],
                  "truncado": len(p.stdout) > 12000}
    except subprocess.TimeoutExpired:
        status = "timeout"
        result = {"status": status, "acao": action, "erro": f"Limite de {_TIMEOUT_SECONDS}s excedido"}
    except OSError as exc:
        status = "erro"
        result = {"status": status, "acao": action, "erro": str(exc)}
    _audit(action, status, time.monotonic() - start)
    return result
