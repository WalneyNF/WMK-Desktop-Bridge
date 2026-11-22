# WMK Skills Manager v0.7.0 — Manual em português

**Walney Moreira Klein — walneyk@hotmail.com**

## Conceitos básicos

- **Modelo:** mecanismo de IA (por exemplo, modelo Ollama).
- **Agente:** combinação de modelo, instruções, skills e permissões.
- **Skill:** documento de procedimentos que orienta o agente. Não executa código, não recebe senha e não dá acesso a arquivos.
- **Ferramenta / MCP:** capacidade oferecida por software, normalmente através de interface padronizada. O conector Blender do WMK usa HTTP local e o WMK expõe ferramentas consultivas via MCP.
- **Provedor:** API ou serviço que hospeda o modelo.

## Começar

```powershell
cd D:\Ferramentas\WMK-Desktop-Bridge
git pull
$env:WMK_WORKSPACE = 'D:\Ferramentas\WMK-Desktop-Bridge'
py web_server.py
```

Abra `http://127.0.0.1:8767/agents`. Na seção **WMK Skills Manager**, escolha um dos cinco exemplos, edite o texto e salve. Para nova skill, clique em **Nova skill**, preencha nome, descrição e instruções.

## Exemplos fornecidos

- Revisor Python — examinar manutenção, desempenho e segurança.
- Modelador Blender — planejar objetos, materiais e dimensões.
- Análise de imagem — observar referências visuais e limitações.
- Inspeção de malhas 3D — diferenciar metadados e geometria real.
- Professor WMK — ensinar programação de modo progressivo.

## Associar ao agente

No painel **Cadastrar novo agente**, escolha um modelo, marque capacidades permitidas e selecione até **cinco skills** (Ctrl+clique na lista). Clique em **Cadastrar agente**. Os agentes de exemplo já estão vinculados a uma skill apropriada. Um agente criado nesta versão tem suas skills registradas no cadastro local `config/agents.json`.

**Atenção:** skills mudam orientações, não privilégios. O agente modelador continua restrito a operações predefinidas do Blender. O agente revisor continua limitado a ler arquivos permitidos. A IA pode falhar em seguir as instruções.

## Onde são armazenadas

- Templates de origem: `skills_manager.py`, versionados no repositório.
- Personalizações locais: `config/skills.json`.
- Agentes locais: `config/agents.json`.

Cadastros em `config/` são ignorados no Git, e a interface os salva como JSON. Não cole senhas ou dados pessoais em skills.

## Formato compatível com Agent Skills

O sistema de skills deste protótipo possui campos `nome`, `descricao`, `instrucoes` e `ativo` em JSON. **Ainda não importa pastas de skills com SKILL.md, scripts executáveis ou dependências externas.** A compatibilidade plena com convenções externas de Agent Skills fica no roadmap, com importação controlada e sem execução automática de scripts.

## Exercício prático

Crie uma skill **Revisor JavaScript**:
- Nome: Revisor JavaScript.
- Descrição: arquitetura, segurança e desempenho de JavaScript.
- Instruções: *Revisar o arquivo selecionado, identificar riscos, sugerir melhorias localizadas e justificar cada mudança. Não alterar arquivos nem executar comandos.*

Crie um agente com capacidade `workspace_read`, associe a skill, selecione o agente e analise `web/index.html` (quando estiver dentro da pasta WMK_WORKSPACE).

## Segurança

- Nenhuma skill executa Python, PowerShell, shell ou código no Blender.
- Skills podem conter prompt injection: trate texto de terceiros como não confiável.
- Acesso à pasta depende exclusivamente do backend e das capacidades do agente, nunca de texto da skill.
- A leitura de arquivos enviada a APIs externas exige consentimento e pode expor conteúdo privado.
- Não exponha o servidor web na rede.
