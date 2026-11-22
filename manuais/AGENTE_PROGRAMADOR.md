# WMK Coding Agent v0.7.4 — programando com IA como Codex/Claude Code

**Walney Moreira Klein — walneyk@hotmail.com**

## Objetivo

O WMK agora oferece um agente de programação iterativo, separado do chat explicativo: é possível selecionar um agente com acesso a **uma pasta autorizada**, descrever a tarefa e deixar a IA listar diretórios, ler vários arquivos e preparar até quatro propostas de criação/edição para revisão humana.

**Importante:** este protótipo ainda **não tem** execução automática de testes, builds, comandos shell, Git nem autonomia completa de ferramentas como Codex e Claude Code. Não faz substituição em massa sem aprovação. Esta limitação é intencional enquanto o executor Windows não tiver sandbox de sistema operacional e autenticação centralizada.

## Testar no Windows

Abra PowerShell sem privilégios de administrador:

```powershell
cd D:\Ferramentas\WMK-Desktop-Bridge
git pull
$env:WMK_WORKSPACE='D:\Ferramentas\MeuProjetoDeTeste'
py web_server.py
```

A pasta `D:\Ferramentas\MeuProjetoDeTeste` deve existir. Se for a primeira vez, crie-a antes:

```powershell
New-Item -ItemType Directory -Path 'D:\Ferramentas\MeuProjetoDeTeste' -Force
```

Abra `http://127.0.0.1:8767/agents`. Use o agente de exemplo **Revisor de projeto**, que possui a capacidade `workspace_read`, ou cadastre outro com essa capacidade.

No painel **Agente programador de projetos**, escreva:

> Leia os arquivos Python deste projeto, identifique um problema pequeno e proponha a correção em um arquivo, sem apagar nada. Explique o que mudou.

Marque o consentimento para envio de conteúdos ao provedor do agente e clique em **Iniciar tarefa de programação**. Aguarde a resposta da requisição, sem fechar o navegador.

Depois abra `http://127.0.0.1:8767/approvals` para revisar as propostas. A IA não salva arquivos ao planejar. Somente sua aprovação cria ou altera o arquivo. O WMK verifica versão SHA-256 e cria backup quando necessário.

## Como o agente toma ações

```text
Pedido de programação
  -> modelo IA escolhe {acao: list|read|propose_write|finish}
  -> WMK valida a ação
  -> leitura/proposta dentro de WMK_WORKSPACE
  -> resultado volta ao modelo
  -> até 8 passos / até 4 propostas
  -> você revisa diffs em /approvals
  -> gravação manual com backup
```

O modelo **não recebe** acesso a PowerShell, `cmd`, processos, rede arbitrária, exclusão ou execução de testes nessa rota. As propostas não são comandos e o texto de arquivos não é tratado como autorização.

## Provedores

O agente cadastrado pode usar Ollama, Groq, OpenAI API ou Gemini API, respeitando configurações da `Central de Agentes`. O código utiliza a interface de respostas JSON do provedor escolhido. Alguns modelos locais pequenos não conseguem seguir consistentemente o formato de ferramentas; se aparecer erro de JSON ou planos ruins, utilize um modelo mais capaz ou reduza a tarefa.

### Exemplo local com Ollama

```powershell
ollama list
Invoke-RestMethod http://127.0.0.1:11434/api/tags
```

No cadastro de agente selecione `ollama` e um modelo instalado com memória suficiente. O consumo de RAM/VRAM dependerá do modelo. Se estiver lento, peça mudanças em um único arquivo.

### Para contas de provedores

Configure chaves externas com `configurar-chaves.ps1`, ou apenas na sessão PowerShell. Consulte `manuais/AGENTES_MCP_BLENDER.md` para configurar Groq, OpenAI e Gemini. Ao consentir com uma tarefa em provedor externo, textos lidos podem sair do seu computador. Evite bases de clientes, chaves e dados pessoais.

## O que ainda falta para se aproximar de Codex

1. Executor de comandos em **sandbox real** (Windows Sandbox, VM ou usuário Windows com ACLs restritas), não apenas verificação de caminho em Python.
2. Comandos de teste aprovados, com limites de CPU, tempo e memória, logs e botão cancelar.
3. Leitura de erros de testes e ciclo de autocorreção.
4. Modificações multi-arquivo com revisão conjunta e restauração atômica.
5. Histórico de tarefas, checkpoints e controle de versões Git.
6. Chat de acompanhamento com streaming, intervenção humana e continuação de tarefas.
7. Contexto inteligente para projetos grandes (indexação, busca semântica e RAG local).
8. Autenticação forte da interface e isolamento das sessões MCP.
9. Auditoria e filtros de segredos mais robustos.
10. Testes reais em Windows, especialmente contra junções NTFS e ataques de condição de corrida.

## Alternativa pronta para autonomia completa

Se você precisa de um agente que já consiga rodar testes e modificar projetos **hoje**, pode instalar o **Codex CLI** diretamente no computador, com suas opções de sandbox e aprovações, em vez de esperar o WMK reproduzir esse mecanismo. Consulte a documentação atual:

- https://learn.chatgpt.com/docs/cli/reference
- https://learn.chatgpt.com/docs/non-interactive-mode
- https://github.com/openai/codex

**Nunca use flags que desligam a sandbox ou pulam aprovações** em código de origem desconhecida. Em Windows, valide as garantias de isolamento específicas da versão instalada.

## Segurança e limites

O sistema é protótipo e não foi validado no seu Windows nesta publicação. `WMK_WORKSPACE` restringe o acesso das ferramentas deste agente, mas não é isolamento do usuário Windows. A aprovação da página local é uma decisão humana dentro do navegador e **não protege contra processos maliciosos rodando na mesma conta**. Faça testes em uma pasta de demonstração e salve cópia externa de seus projetos importantes.
