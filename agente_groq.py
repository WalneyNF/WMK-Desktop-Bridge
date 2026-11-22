"""Agente Groq experimental: perguntas em português + ferramentas locais somente leitura.

Necessário GROQ_API_KEY configurado no ambiente.
As respostas das ferramentas solicitadas pelo modelo são enviadas à API Groq.
Somente diagnósticos PowerShell fixos, com confirmação individual; sem código arbitrário, escrita ou exclusão.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

from bridge import diagnostic, drives, folder_sizes, ollama_models
from hardware import hardware_info
from powershell_tools import catalog, run_action, ACTIONS

BASE_URL = "https://api.groq.com/openai/v1/chat/completions"
TOOLS = {
    "wmk_powershell_catalog": (catalog, "Listar diagnósticos PowerShell autorizados, como processos, serviços, rede e discos.", {}),
    "wmk_powershell_diagnose": (run_action, "Executar apenas diagnóstico PowerShell pré-definido. IDs possíveis: versao_powershell, processos, servicos_parados, unidades, rede, tempo_atividade. Nunca executa código livre.", {
        "action": {"type": "string", "enum": list(ACTIONS.keys()), "description": "ID de diagnóstico pré-definido"}
    }),
    "wmk_status": (diagnostic, "Verificar estado e informações do WMK Desktop Bridge.", {}),
    "wmk_drives": (drives, "Consultar espaço livre e usado dos discos.", {}),
    "wmk_hardware": (hardware_info, "Consultar inventário de CPU, memória, GPU e placa-mãe.", {}),
    "wmk_ollama": (ollama_models, "Consultar modelos Ollama instalados.", {}),
    "wmk_folder_sizes": (folder_sizes, "Calcular tamanho de subpastas autorizadas.", {
        "path": {"type": "string", "description": "Caminho absoluto de pasta autorizada"},
        "limit": {"type": "integer", "description": "Número de pastas, até 20"},
    }),
}


def groq_request(messages: list[dict], definitions: list[dict], key: str, model: str) -> dict:
    request = urllib.request.Request(
        BASE_URL,
        data=json.dumps({"model": model, "messages": messages,
                         "tools": definitions, "tool_choice": "auto", "temperature": 0.2}).encode("utf-8"),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
        method="POST")
    with urllib.request.urlopen(request, timeout=70) as response:
        data = json.load(response)
    return data["choices"][0]["message"]


def tool_specs() -> list[dict]:
    result = []
    for name, (_, description, properties) in TOOLS.items():
        required = ["path"] if name == "wmk_folder_sizes" else (["action"] if name == "wmk_powershell_diagnose" else [])
        result.append({"type": "function", "function": {
            "name": name, "description": description,
            "parameters": {"type": "object", "properties": properties,
                           "required": required, "additionalProperties": False}}})
    return result


def run_question(question: str) -> str:
    key = os.getenv("GROQ_API_KEY", "").strip()
    if not key:
        raise RuntimeError("Configure a variável GROQ_API_KEY no PowerShell antes de executar.")
    model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b").strip()
    messages = [
        {"role": "system", "content": (
            "Você é o assistente WMK. Responda em português do Brasil. "
            "Use somente as ferramentas autorizadas e nunca invente resultados. "
            "Você pode solicitar apenas diagnósticos PowerShell pré-definidos, mediante confirmação do usuário. Nunca pode executar código livre, apagar arquivos nem alterar o computador. "
            "Dados enviados pela máquina podem conter informações privadas; não solicite "
            "informações sensíveis desnecessárias. "
            "Se a resposta de uma ferramenta estiver incompleta, avise."
        )},
        {"role": "user", "content": question},
    ]
    specs = tool_specs()
    for _ in range(3):
        message = groq_request(messages, specs, key, model)
        calls = message.get("tool_calls") or []
        if not calls:
            return message.get("content") or "(O modelo não retornou texto.)"
        messages.append({"role": "assistant", "content": message.get("content"), "tool_calls": calls})
        for call in calls[:4]:
            fn = call.get("function") or {}
            name = fn.get("name", "")
            try:
                args = json.loads(fn.get("arguments") or "{}")
                if name not in TOOLS:
                    raise ValueError("Ferramenta não autorizada")
                if not isinstance(args, dict):
                    raise ValueError("Parâmetros inválidos")
                function = TOOLS[name][0]
                if name == "wmk_powershell_diagnose":
                    args = {"action": str(args.get("action", ""))}
                    requested = args["action"]
                    print("\\n[AGENTE] Solicitação PowerShell: " + requested)
                    if input("Autorizar esta consulta local? [s/N] ").strip().lower() not in ("s", "sim"):
                        raise PermissionError("Usuário negou a consulta PowerShell")
                if name == "wmk_folder_sizes":
                    args = {"path": str(args.get("path", "")),
                            "limit": max(1, min(int(args.get("limit", 10)), 20))}
                else:
                    args = {}
                output = function(**args)
                # O inventário pode conter identificadores de rede.
                # Não enviar endereços MAC para o provedor.
                if name == "wmk_hardware":
                    for group in output.get("categorias", {}).values():
                        for item in group.get("dados", []):
                            item.pop("MACAddress", None)
                payload = json.dumps(output, ensure_ascii=False, default=str)[:24000]
            except (ValueError, TypeError, PermissionError, OSError, EOFError) as exc:
                payload = json.dumps({"erro": str(exc)}, ensure_ascii=False)
            messages.append({"role": "tool", "tool_call_id": call.get("id", ""), "content": payload})
    # Limite intencional de chamadas para evitar custo e loops.
    return "Limite de etapas do agente atingido. Tente uma pergunta mais específica."


def main() -> int:
    print("WMK Agente Groq (somente leitura). Digite sair para encerrar.")
    print("AVISO: perguntas e resultados de diagnóstico poderão ser enviados à API Groq.")
    if input("Você autoriza esta transmissão? [s/N] ").strip().lower() not in ("s", "sim"):
        print("Cancelado.")
        return 0
    while True:
        try:
            question = input("\nPergunta> ").strip()
            if question.lower() in ("sair", "exit", "quit"):
                return 0
            if not question:
                continue
            print("\n" + run_question(question))
        except (KeyboardInterrupt, EOFError):
            return 0
        except urllib.error.HTTPError as exc:
            body = exc.read(800).decode("utf-8", errors="replace")
            print(f"Erro HTTP Groq {exc.code}: {body}")
        except (urllib.error.URLError, RuntimeError, OSError, KeyError) as exc:
            print(f"Erro: {exc}")


if __name__ == "__main__":
    sys.exit(main())
