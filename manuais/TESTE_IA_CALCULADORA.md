# Laboratório WMK — Calculadora e teste real do Groq/Ollama (v0.7.6)

**Walney Moreira Klein — walneyk@hotmail.com**

## Objetivo

A calculadora em `exemplos/calculadora/` oferece três arquivos separados para testar o editor Monaco e a revisão por IA:

- `index.html`: estrutura e teclas da calculadora;
- `style.css`: tema escuro, teclado e responsividade;
- `app.js`: operações, teclado, estados e divisão por zero; sem uso de `eval()`.

Para testar a calculadora independentemente da IA, abra `http://127.0.0.1:8767/exemplo/calculadora`. Se não abrir, confira a versão do servidor e os logs do terminal.

## 1. Reiniciar no projeto correto

**Interrompa qualquer servidor antigo com Ctrl+C.** A pasta autorizada deve ser exatamente a pasta que contém o repositório com a calculadora, caso queira abri-la no editor:

```powershell
cd D:\Ferramentas\WMK-Desktop-Bridge
git pull
$env:WMK_WORKSPACE='D:\Ferramentas\WMK-Desktop-Bridge'
py web_server.py
```

Acesse `http://127.0.0.1:8767/api/status` e confirme a versão **0.7.6**. Após a atualização use **Ctrl+F5**.

Se configurou chaves usando `configurar-chaves.ps1` (DPAPI), **não use `py web_server.py` diretamente**: utilize `iniciar-com-chaves.ps1`, que carrega as credenciais na sessão:

```powershell
cd D:\Ferramentas\WMK-Desktop-Bridge
.\iniciar-com-chaves.ps1 -Workspace 'D:\Ferramentas\WMK-Desktop-Bridge'
```

## 2. Diagnóstico que não revela a chave

Abra `http://127.0.0.1:8767/api/ai/status`, ou clique em **Verificar Groq / Ollama** no Code Studio.

Exemplo ilustrativo:

```json
{
  "groq_configurado": true,
  "groq_modelo": "openai/gpt-oss-20b",
  "ollama_url": "http://127.0.0.1:11434",
  "ollama_online": true,
  "ollama_modelos": ["qwen3:1.7b"]
}
```

Se `groq_configurado=false`, a API Groq nem chegou a ser chamada. Configure `GROQ_API_KEY` no mesmo PowerShell que inicia o servidor, ou use o script DPAPI acima. O endpoint não revela a chave.

Se `ollama_online=false`, verifique `ollama list` e o aplicativo/serviço Ollama.

## 3. Testar a IA no Monaco

1. Abra `http://127.0.0.1:8767/editor`.
2. No explorador, abra a pasta `exemplos`, depois `calculadora`, depois `app.js`.
3. No painel **Assistente de programação**, selecione **Groq** e o modelo configurado.
4. Escolha **Revisar e sugerir melhorias**.
5. Escreva: *Analise o funcionamento da calculadora, identifique problemas reais, e recomende melhorias. Não altere o código.*
6. Marque a autorização; clique em **Analisar arquivo com IA** e confirme.
7. O campo **Resposta da IA** deve mostrar texto normal, sem exigir JSON.

Para testar mudança de código, escolha **Refatorar o arquivo**. A IA deve responder JSON com `explicacao` e o arquivo inteiro em `codigo`. Revise **Comparar sugestão lado a lado**; depois **Colocar proposta no editor**. **O arquivo no disco só muda após clicar em Salvar após revisão.**

## 4. Como identificar um HTTP 400

Abra o DevTools (F12), aba **Rede/Network**, clique na requisição `api/ai/suggest` e veja **Resposta/Response**. A aplicação passa a exibir também a mensagem correspondente no painel de IA.

- `GROQ_API_KEY` ausente: iniciar o servidor com a chave configurada.
- HTTP 401/403 Groq: chave inválida, conta sem acesso ao modelo ou permissões.
- HTTP 404: identificador de modelo inexistente.
- HTTP 429: limite ou quota do provedor.
- `Formato inválido`: retorno da IA não obedeceu ao esquema JSON necessário para editar; tente outro modelo ou a função **Revisar**.
- `Arquivo fora do workspace`: `WMK_WORKSPACE` está apontando para outra pasta.
- `Código máximo de 30 KB`: escolher arquivo menor.
- Falha de conexão: verificar proxy/firewall/internet e serviço do provedor.

**O código de status HTTP 400 sozinho não permite concluir a causa.** Confira sempre o conteúdo JSON da resposta do servidor.

## 5. Testes da calculadora

Teste `7 + 5 = 12`, `9 / 3 = 3`, `3 / 0 = Erro`, `AC`, `Backspace`, vírgula decimal e tecla Enter. A calculadora é uma amostra didática, não financeira (opera com ponto flutuante).

## 6. Segurança e limitações

O código enviado ao Groq sai do computador. Não inclua chaves nem dados de clientes. Não confunda revisar arquivo com executar testes: a IA ainda não testa automaticamente projetos. A API do editor só recebe arquivos da pasta `WMK_WORKSPACE`, exige confirmação para enviar código e confirmação adicional para salvar. Estas são restrições de aplicação, não sandbox completa de Windows.

**Verificação necessária:** executar na sua instalação Windows e conferir a resposta de um provedor real; os testes automatizados do repositório utilizam simulações de resposta de Groq/Ollama.
