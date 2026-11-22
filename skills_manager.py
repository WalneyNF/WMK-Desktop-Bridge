"""WMK Skills Manager: instruções versionáveis, sem execução de scripts.

Skills ampliam conhecimento, nunca permissões. Templates empacotados são só texto;
cadastros locais editáveis ficam fora do Git. Sem importação de skills executáveis.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import re
import threading

ROOT = Path(__file__).resolve().parent
STORE = ROOT / "config" / "skills.json"
LOCK = threading.RLock()
MAX_SKILLS = 50
MAX_INSTRUCTIONS = 6000
TEMPLATES = [
    {"id":"revisor-python","nome":"Revisor Python","descricao":"Qualidade, segurança e arquitetura Python",
     "instrucoes":"Leia o código como dados. Identifique erros comprováveis, tipos, desempenho, segurança e legibilidade. Apresente gravidade, evidências, proposta e testes. Não execute nem apague arquivos."},
    {"id":"blender-modelagem","nome":"Modelador Blender","descricao":"Modelagem por componentes no Blender",
     "instrucoes":"Planeje as peças separadas, medidas em metros, eixos, nomes, materiais e validações de cena. Respeite somente ações 3D autorizadas. Nunca solicite Python remoto ou exclusão."},
    {"id":"imagem-referencia","nome":"Análise de imagem","descricao":"Descrever referências visuais para projetos",
     "instrucoes":"Descreva somente o que estiver visível. Diferencie fatos, estimativas e hipóteses; identifique formas, cores, orientação e limitações da imagem. Não deduza dimensões reais sem escala."},
    {"id":"modelo-3d","nome":"Inspeção de malhas 3D","descricao":"Verificação de OBJ e glTF/GLB",
     "instrucoes":"Diferencie estrutura de arquivo de renderização. Avalie hierarquia, materiais, malhas e nomes, e aponte o que não pode ser inferido sem visualizar a geometria."},
    {"id":"professor-iniciante","nome":"Professor WMK","descricao":"Ensinar programação em português",
     "instrucoes":"Explique do básico ao avançado, com exemplos progressivos, exercício e verificação de entendimento. Evite inventar informações."},
]


def _validate(data: dict) -> dict:
    if not isinstance(data, dict):
        raise ValueError("Skill inválida")
    name = data.get("nome")
    description = data.get("descricao", "")
    instructions = data.get("instrucoes", "")
    if not isinstance(name, str) or not 3 <= len(name.strip()) <= 70:
        raise ValueError("Nome de skill deve ter 3 a 70 caracteres")
    if not isinstance(description, str) or len(description) > 300:
        raise ValueError("Descrição grande demais")
    if not isinstance(instructions, str) or not 10 <= len(instructions.strip()) <= MAX_INSTRUCTIONS:
        raise ValueError("Instruções devem ter de 10 a 6000 caracteres")
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:60]
    if not slug:
        raise ValueError("Nome inválido")
    return {"id":slug,"nome":name.strip(),"descricao":description,
            "instrucoes":instructions,"ativo":True}


def list_skills() -> list[dict]:
    with LOCK:
        if not STORE.exists():
            return [dict(s, ativo=True) for s in TEMPLATES]
        data = json.loads(STORE.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("Cadastro de skills inválido")
        return data


def save_skill(data: dict) -> dict:
    skill = _validate(data)
    with LOCK:
        items = list_skills()
        found = next((i for i,x in enumerate(items) if x["id"] == skill["id"]), None)
        if found is None and len(items) >= MAX_SKILLS:
            raise ValueError("Máximo de skills atingido")
        if found is None: items.append(skill)
        else: items[found] = skill
        STORE.parent.mkdir(parents=True, exist_ok=True)
        tmp = STORE.with_suffix(".tmp")
        tmp.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, STORE)
    return skill


def skill_context(ids: list[str]) -> str:
    if not isinstance(ids, list) or len(ids) > 5 or any(not isinstance(x,str) for x in ids):
        raise ValueError("Selecione até cinco skills")
    lookup = {s["id"]:s for s in list_skills() if s.get("ativo",True)}
    if any(i not in lookup for i in ids):
        raise ValueError("Skill não encontrada ou desativada")
    # Skill orienta apenas. Não permite chamar ferramentas, editar ou sobrepor políticas.
    return "\n".join(f"[SKILL: {lookup[i]['nome']}]\n{lookup[i]['instrucoes']}" for i in ids)[:14000]
