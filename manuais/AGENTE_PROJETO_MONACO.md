# WMK Project Agent v0.8.1 — IA lendo e corrigindo o projeto

**Walney Moreira Klein — walneyk@hotmail.com**

## A diferença entre o revisor e o agente

O botão **Analisar arquivo com IA** do Code Studio envia somente o texto do editor e recebe uma revisão. **Não modifica o projeto e não lê outros arquivos.** Uma resposta como *"Corrigimos a acessibilidade"* não prova que alguma coisa foi gravada.

O botão **Trabalhar no projeto** abre uma nova tarefa: o backend lê efetivamente o arquivo aberto no workspace e até **quatro arquivos relacionados da mesma pasta**, obedecendo os limites de tamanho e bloqueios de segredos; envia essas fontes com consentimento à IA; recebe substituições exatas ou arquivos completos; cria propostas de alteração com SHA; e exibe diferenças no painel direito. Você clica **Aprovar e gravar este arquivo**, confirma e só então os bytes são escritos no Windows, com backup de versões anteriores.

Isso é um **primeiro agente de edição de projeto**, mas não um substituto integral do Codex: ainda não possui shell, execução de testes, indexação de um repositório inteiro, execução de ferramentas MCP arbitrárias, tarefas em segundo plano ou sandbox do Windows. Não deve alegar que compilou/testou.

## Instalação e primeiro teste

No PowerShell:

```powershell
cd D:\Ferramentas\WMK-Desktop-Bridge
git pull
$env:WMK_WORKSPACE='D:\Ferramentas\WMK-Desktop-Bridge'
py web_server.py
```

Pare o servidor antigo com `Ctrl+C`, atualize o navegador com `Ctrl+F5` e confirme `versao: 0.8.1` em `http://127.0.0.1:8767/api/status`.

1. Abra `http://127.0.0.1:8767/editor`.
2. No explorador, abra `exemplos/calculadora/index.html`.
3. No painel direito clique em **Configurar IA**, selecione Groq e o modelo `openai/gpt-oss-20b` (ou Ollama local compatível).
4. Clique em **🛠 Trabalhar no projeto**.
5. Em **Tarefa a executar**, escreva: *Leia os arquivos da calculadora, melhore a acessibilidade dos botões, mas preserve os caminhos de recursos que já funcionam. Corrija os problemas concretos de código; não apenas descreva as correções.*
6. Marque a autorização de leitura e envio dos arquivos relacionados; clique **Analisar arquivos e preparar alterações**.
7. Veja os **Arquivos realmente lidos**. Para a calculadora, espera-se `index.html`, `app.js`, `style.css`, sujeitos aos limites de tamanho e ao filtro de possíveis segredos.
8. Na lista de propostas, clique **Revisar e aplicar: index.html**. O painel direito exibe um diff real.
9. Leia as linhas removidas e adicionadas e clique **Aprovar e gravar este arquivo**. Confirme na janela seguinte.
10. O sistema grava no workspace, faz backup, e recarrega o arquivo no Monaco **se não houver alterações humanas não salvas**.

Para verificar no disco, reabra `exemplos/calculadora/index.html`. A mudança deve estar presente. Se nenhuma alteração for gerada, a interface avisa **0 arquivos gravados** e não diz que houve correção.

## Funcionamento

```text
Tarefa no Monaco
  -> backend valida WMK_WORKSPACE
  -> lê arquivo aberto + arquivos relacionados na mesma pasta
  -> filtro de tamanho e credenciais
  -> envia conteúdo autorizado ao modelo
  -> modelo devolve JSON com substituicoes (antes/depois) ou codigo inteiro
  -> WMK valida nomes e conteúdo
  -> salva propostas no banco SQLite de aprovação
  -> mostra diff por arquivo
  -> você aprova individualmente
  -> arquivo efetivamente escrito com verificação SHA e backup
```

As mudanças são preparadas **sem executar shell ou programas**. O modelo não pode solicitar arquivos fora da lista fornecida nesta tarefa, nem escrever em diretórios protegidos. Não há exclusão de arquivos neste fluxo.

## Limites reais

- Lê no máximo **5 arquivos**, até **12 KB cada**, e até **24 KB no total**.
- Arquivos relacionados precisam estar **na mesma pasta** do arquivo aberto e possuir extensões reconhecidas.
- No máximo **4 arquivos alterados por tarefa**.
- Cada arquivo usa até **12 substituições textuais exatas** (ou código integral).
- Um trecho `antes` deve ocorrer **uma única vez**. Caso contrário, o patch é recusado.
- Propostas cujo diff exceda os limites de revisão são recusadas; divida a tarefa.
- Não importa automaticamente mudanças em arquivos que o usuário esteja editando no Monaco sem salvar.
- Se a IA mencionar uma correção, mas não fornecer conteúdo modificado, o sistema deve mostrar **sem alterações**.
- Groq depende de internet e chave válida; Ollama precisa estar ligado com modelo de texto instalado. Pequenos modelos podem falhar em produzir JSON de código correto.
- Os arquivos lidos são enviados ao provedor escolhido após consentimento. Não use com código que contenha dados sensíveis.

## Segurança

A restrição de caminhos Python não equivale a sandbox de sistema operacional. Não conecte o servidor local à internet sem autenticação forte. Valide o funcionamento em uma cópia do projeto, e não na única versão do cliente.

## Evoluções necessárias para se aproximar do Codex

1. Agente com ferramentas de busca por projeto inteiro, leitura seletiva e loop multi-etapa.
2. Executor de testes/build em ambiente isolado com aprovação e logs.
3. Ciclo de correção baseado nos erros de testes.
4. Revisão e aprovação em lote, transações e checkpoints Git.
5. Continuação da tarefa e gerenciamento de contexto/tokens.
6. Comunicação MCP autenticada para aplicações autorizadas.
