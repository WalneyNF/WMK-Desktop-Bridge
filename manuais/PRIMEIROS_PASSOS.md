# Manual de uso — WMK Desktop Bridge v0.3.1

**Autor:** Walney Moreira Klein — walneyk@hotmail.com

## 1. Diagnóstico de hardware

Abra o painel com `py web_server.py`, navegue até `http://127.0.0.1:8767/` e localize **Hardware e sistema**. Use o botão **Atualizar** para renovar os dados; clique em **Copiar**, **TXT** ou **JSON** no cabeçalho do painel.

- **Copiar:** copia o relatório formatado para a área de transferência.
- **TXT:** baixa um arquivo `WMK-Hardware-AAAA-MM-DD.txt` com dados legíveis.
- **JSON:** baixa os dados estruturados para importação em outros sistemas.
- O navegador escolhe o local do download de acordo com suas configurações.
- O relatório omite endereços MAC (identificadores de rede). Antes de compartilhar um relatório, revise os nomes de adaptadores, fabricante e outros dados que possam revelar sua configuração.
- O painel não modifica hardware, drivers ou arquivos.

## 2. Executar servidor MCP local

Crie um ambiente virtual e instale o SDK:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe mcp_server.py
```

O modo stdio não fornece automaticamente conexão ao ChatGPT web. Para ligar outro cliente MCP, configure o executável Python e o caminho para `mcp_server.py`. As ferramentas são somente leitura.

## 3. Criar um agente com Groq

Esta versão inclui o exemplo **agente_groq.py**, que implementa *tool/function calling* diretamente pela API Groq. Não é necessário pagar pelo Desktop Commander. **Uso da API Groq pode estar sujeito a cotas e cobrança; verifique sua conta.**

No PowerShell:

```powershell
cd D:\Ferramentas\WMK-Desktop-Bridge
$env:GROQ_API_KEY = "COLE_SUA_CHAVE_AQUI"
$env:GROQ_MODEL = "openai/gpt-oss-20b"
py agente_groq.py
```

**Não coloque a chave no GitHub e não capture telas contendo a chave.** A variável do exemplo vale apenas para a sessão atual do PowerShell. O modelo configurado precisa existir na sua conta Groq e suportar chamadas de ferramentas. Se houver erro 400 de modelo/ferramentas, consulte a lista de modelos disponíveis na plataforma.

Exemplos de perguntas:

- `Quanta memória RAM meu computador possui?`
- `Qual é minha placa de vídeo?`
- `Quanto espaço tenho livre nas unidades C:, D: e E:?`
- `Quais modelos Ollama estão instalados?`
- `Qual é a maior subpasta na minha pasta de usuário?`

O programa solicita confirmação antes de iniciar perguntas para o provedor. **As perguntas e as respostas retornadas pelas ferramentas são enviadas aos servidores do Groq**. O aplicativo não oferece exclusão, PowerShell arbitrário nem escrita no sistema ao agente.

O agente utiliza uma **lista fechada** das ferramentas `wmk_status`, `wmk_drives`, `wmk_hardware`, `wmk_ollama` e `wmk_folder_sizes`. O caminho consultado é verificado pelas raízes autorizadas. Não habilite acesso a pastas sensíveis.

## 4. Personalizar os diretórios

Por padrão, o agente só pode inspecionar subdiretórios da pasta do usuário. Para acrescentar uma pasta de trabalho:

```powershell
$env:WMK_ALLOWED_ROOTS = 'D:\Ferramentas'
py agente_groq.py
```

Não inclua pastas com senhas, chaves privadas, bancos de dados sensíveis ou dados de clientes. O agente envia parte dos resultados de ferramentas para um provedor de IA externo.

## 5. Desenvolvimento de agentes e novas ferramentas

Para novos agentes, o fluxo é:

```text
Pergunta em português
    ↓
Modelo Groq escolhe ferramenta e parâmetros
    ↓
WMK verifica a lista de ferramentas e caminho permitido
    ↓
Ferramenta Python local consulta dados (somente leitura)
    ↓
O resultado é enviado ao Groq
    ↓
Resposta em português
```

O SDK MCP permite a outros clientes compatíveis descobrir ferramentas via `mcp_server.py`, independentemente do agente Groq. Para Ollama, OpenAI ou Gemini, crie adaptadores próprios que traduzam chamadas de ferramenta para as funções do WMK; essa parte ainda não foi desenvolvida.

## 6. Próximas melhorias voltadas a suporte técnico

- Diagnóstico de saúde de disco (SMART, sujeito a permissões e compatibilidade).
- Temperaturas e sensores via LibreHardwareMonitor.
- Teste de conectividade de rede, DNS e latência.
- Relatório de drivers e atualizações com fontes verificadas.
- Análise de armazenamento, maiores arquivos e cache.
- Recomendação de modelos Ollama segundo CPU, RAM, GPU e espaço.
- Histórico de relatórios e comparação do hardware antes/depois.
- Central de agentes com permissões individuais, auditoria e confirmação humana para mudanças.

## 7. Licença

O código do projeto é publicado sob a licença **MIT**, conforme o arquivo `LICENSE`. A licença não concede direitos sobre marcas ou componentes de terceiros que possuam seus próprios termos.

## 8. Solução de problemas

- **O hardware não aparece:** abra `http://127.0.0.1:8767/api/hardware` e confira o erro retornado.
- **Ollama indisponível:** consulte `http://127.0.0.1:11434/api/tags` localmente.
- **Erro da API Groq:** confira a chave, o nome do modelo e a conexão com a internet.
- **Ferramenta de arquivos bloqueada:** configure `WMK_ALLOWED_ROOTS` apenas com pastas que você deseja disponibilizar.
- **Novo botão não aparece:** pare o servidor, execute `git pull` e reinicie. Use `Ctrl + F5` no navegador.
