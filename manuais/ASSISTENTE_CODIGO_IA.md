# WMK Code Studio — Assistente de IA v0.5.2

**Autor:** Walney Moreira Klein — walneyk@hotmail.com  
**Licença:** MIT

## Funcionalidade

Esta versão integra ao **Monaco Code Studio** um assistente de programação que consulta **Ollama local** ou **Groq**. O assistente recebe **somente o caminho relativo, o texto do editor, a operação e a instrução informada**, sem autorização para executar comandos de sistema, excluir ou salvar arquivos.

Operações disponíveis:
- **Explicar:** descreve o código em português.
- **Revisar:** sugere melhorias de arquitetura, clareza e manutenção.
- **Corrigir:** solicita uma versão completa corrigida do arquivo.
- **Refatorar:** solicita uma versão melhorada do arquivo.
- **Gerar:** solicita um arquivo completo a partir da descrição.

## Como iniciar o modo protegido

Pare o servidor anterior e inicie um novo PowerShell:

```powershell
cd D:\Ferramentas\WMK-Desktop-Bridge
git pull
$env:WMK_WORKSPACE = 'D:\Ferramentas\WMK-Desktop-Bridge'
py web_server.py
```

Abra `http://127.0.0.1:8767/editor` e pressione `Ctrl + F5`.

## Teste com Ollama

Instale um modelo pequeno (exemplo):

```powershell
ollama pull qwen3:1.7b
ollama list
```

O Ollama precisa estar ativo em `127.0.0.1:11434`. No editor:
1. Abra um arquivo, como `bridge.py`.
2. Selecione **Ollama local**.
3. Informe o modelo, por exemplo `qwen3:1.7b`.
4. Escolha **Explicar o código** ou **Corrigir problemas**.
5. Marque a autorização e clique em **Analisar arquivo com IA**.

Modelos que não atendam ao formato JSON solicitado podem gerar erro: tente outro modelo. Alguns modelos pequenos podem produzir alterações incompletas ou incorretas. Sempre revise.

## Teste com Groq

**Não grave a chave de API no repositório.** Configure-a apenas no PowerShell que iniciará o servidor:

```powershell
$env:WMK_WORKSPACE = 'D:\Ferramentas\WMK-Desktop-Bridge'
$env:GROQ_API_KEY = 'SUA_CHAVE'
$env:GROQ_MODEL = 'openai/gpt-oss-20b'
py web_server.py
```

No editor, escolha **Groq (API)** e o modelo disponível em sua conta. O texto do arquivo será enviado ao provedor **após você consentir para cada solicitação**. Confira preços, cotas e políticas do Groq. Não inclua segredos ou código de clientes sem autorização.

## Comparar proposta e salvar

Para ações **Corrigir**, **Refatorar** ou **Gerar**, se o modelo devolver `codigo`, a interface habilita **Comparar sugestão lado a lado**.

1. O editor mostra **original × proposta** com o Monaco Diff Editor.
2. Clique em **Voltar sem aplicar** para rejeitar.
3. Clique em **Colocar proposta no editor** para alterar apenas o conteúdo da memória do editor.
4. Clique em **Comparar** novamente para revisar as diferenças contra o arquivo no disco.
5. Por último, clique em **Salvar após revisão** e confirme a gravação.

**A IA nunca executa o botão Salvar.** O backend mantém validação do caminho, lista de extensões, verificação SHA-256 do arquivo anterior, limite de 256 KiB para edição e backup ao sobrescrever arquivos.

## Limites e segurança

- A API de IA só funciona com `WMK_WORKSPACE` configurado.
- O cliente não envia o código de outros arquivos automaticamente.
- Arquivos de segredos conhecidos (`.env`, `*.pem`, etc.) são bloqueados pelo workspace.
- Há um detector básico de credenciais no texto antes de enviar aos provedores, mas **não substitui revisão humana nem ferramentas dedicadas de DLP**.
- O código-fonte enviado à IA é limitado a **30 KB** por requisição.
- Respostas são limitadas; resultados muito grandes são recusados.
- Não há função de escrita, deleção ou shell à disposição da IA nesta integração.
- A autenticação de chamadas locais ainda não isola outros processos rodando sob o mesmo usuário Windows. Não exponha o servidor à internet.
- Conteúdo de projetos pode conter *prompt injection*. É dado não confiável, e a IA pode se confundir apesar das instruções do sistema.
- Mudar o arquivo enquanto a IA responde invalida a sugestão antiga.
- Não há chat persistente/histórico entre sessões nem edição de múltiplos arquivos nesta versão.
- A conexão externa não foi executada/testada no seu Windows durante o desenvolvimento remoto.

## Solução de problemas

| Sintoma | Verificar |
|---|---|
| Falha ao conectar Ollama | Ollama ativo em `http://127.0.0.1:11434` |
| Groq sem chave | `GROQ_API_KEY` configurada **antes** de iniciar `web_server.py` |
| Modelo não encontrado | Nome correto no Ollama ou Groq |
| JSON inválido | Escolher outro modelo ou solicitação mais simples |
| Sugestão não comparável | Use a ação Corrigir, Refatorar ou Gerar; o modelo deve fornecer `codigo` |
| Erro ao salvar | Reabrir o arquivo, conferir hash/conflito e permissões do Windows |
| Ferramenta não aparece | Reiniciar Python, `git pull` e `Ctrl + F5` |

## Roadmap

- Chat com histórico de contexto autorizado, tokenização e orçamento.
- Indexação opt-in do projeto, com exclusões de dados sensíveis.
- Testes automatizados para os adaptadores Groq e Ollama.
- Central de permissões com aprovação centralizada e autenticação de sessão.
- Monaco integrado offline via assets locais, sem CDN.
