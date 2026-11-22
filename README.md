# WMK Desktop Bridge

**Ponte gratuita e de código aberto entre assistentes de IA e seu computador Windows.**

> Versão: **0.5.1 (protótipo local, com editor manual protegido)** · Interface em português do Brasil.

**Autor:** Walney Moreira Klein — walneyk@hotmail.com

## Objetivo

Criar uma alternativa independente para diagnósticos locais de disco e arquivos, compatível com o protocolo **MCP (Model Context Protocol)**. O projeto não depende de assinatura do Desktop Commander. A integração específica com o ChatGPT pelo navegador **ainda não está disponível** nesta versão: para isso será necessário um endpoint HTTPS remoto autenticado e compatibilidade com o modo de conexão da conta.

## Funcionalidades implementadas

| Recurso | Estado |
|---|---|
| Consultar espaço livre/usado em unidades | ✅ |
| Listar arquivos e subpastas autorizadas | ✅ |
| Calcular tamanho de subpastas (limite de varredura) | ✅ |
| Consultar modelos do Ollama (API local, fallback CLI) | ✅ |
| Inventário Windows de CPU, RAM, GPU, rede, placa-mãe e discos físicos via CIM | ✅ |
| Copiar inventário e exportar relatórios TXT/JSON | ✅ |
| Agente experimental Groq com ferramentas de leitura permitidas | ✅ |
| Servidor MCP local via stdio | ✅ |
| Pasta única autorizada para agentes (somente leitura) | ✅ |
| Monaco Code Studio, diff, hash e backup para edição manual | ✅ Protótipo |
| Painel HTML local com painéis móveis, redimensionáveis e layout persistente | ✅ |
| Executar diagnósticos PowerShell fixos por IA (Groq/MCP) | ✅ Com restrições |
| Executar PowerShell arbitrário pela IA | ❌ Não permitido |
| Excluir arquivos pela IA | 🔒 Bloqueado: nenhuma ferramenta de exclusão |
| Controle remoto pelo ChatGPT web | ❌ Não implementado |

## Instalação no Windows 10/11

Requisitos: Python 3.10+ instalado. O programa de diagnóstico e o painel web usam somente a biblioteca padrão do Python.

1. Clone ou baixe este repositório:

   ```powershell
   git clone https://github.com/WalneyNF/WMK-Desktop-Bridge.git
   cd WMK-Desktop-Bridge
   ```

2. Teste o diagnóstico:

   ```powershell
   py bridge.py
   ```

3. Abra o painel local:

   ```powershell
   py web_server.py
   ```

4. Acesse **http://127.0.0.1:8767/** no navegador. Você também pode executar `iniciar-painel.bat`.

### Servidor MCP local

Instale a dependência numa virtualenv (recomendado):

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe mcp_server.py
```

O servidor utiliza **stdio** e foi feito para clientes MCP locais que iniciem esse processo. A execução direta pode não produzir saída aparente até que um cliente se conecte.

Exemplo de configuração conceitual para um cliente MCP que aceita servidores stdio (ajuste caminhos):

```json
{
  "mcpServers": {
    "wmk-desktop": {
      "command": "C:\\caminho\\WMK-Desktop-Bridge\\.venv\\Scripts\\python.exe",
      "args": ["C:\\caminho\\WMK-Desktop-Bridge\\mcp_server.py"]
    }
  }
}
```

### Limitar as pastas disponíveis à IA

Por padrão, somente a **pasta do usuário atual** pode ser explorada nas ferramentas de arquivo. Para acrescentar outro diretório, configure `WMK_ALLOWED_ROOTS` antes de iniciar:

```powershell
$env:WMK_ALLOWED_ROOTS = 'D:\\Ferramentas;D:\\IA-Local'
py mcp_server.py
```

No Windows, o delimitador entre diretórios é `;`. A variável adiciona raízes permitidas; não substitui a pasta do usuário.

> **Cuidado:** autorizar a raiz de uma unidade expõe toda essa unidade para leitura ao cliente MCP. Configure apenas os diretórios necessários. Não conecte o agente a um cliente de IA não confiável.

## Ollama: tempo limite e diagnóstico

A versão 0.2.1 consulta primeiro `http://127.0.0.1:11434/api/tags` (tempo limite de 5 segundos). Quando a API não responde, tenta `ollama list` com **60 segundos** de tempo limite, em vez dos 15 segundos anteriores.

Para mudar o limite do executável, antes de iniciar o painel:

```powershell
$env:WMK_OLLAMA_TIMEOUT = '120'
py web_server.py
```

O intervalo aceito é de 5 a 180 segundos. Se a API estiver disponível, a consulta é realizada por HTTP e não precisa esperar o processo CLI. Para conferir manualmente:

```powershell
Invoke-RestMethod http://127.0.0.1:11434/api/tags
```

Ollama indisponível, comando ausente no PATH e tempo esgotado são apresentados como situações distintas. Uma falha de conexão **não comprova** que os modelos foram removidos.

## Inventário de hardware (v0.3.0)

Um painel **Hardware e sistema** foi acrescentado ao dashboard, com arraste e redimensionamento. Os dados vêm do WMI/CIM local por meio de um comando PowerShell **fixo**, sem entrada de código arbitrário. A consulta possui timeout de 35 segundos e cache de 30 segundos.

- Rota local: `GET http://127.0.0.1:8767/api/hardware`
- Ferramenta MCP: `wmk_hardware`
- CPU: identificação, núcleos, threads e clock informado pelo sistema.
- RAM: total e livre, módulos, velocidade e slots quando disponíveis.
- Vídeo: adaptadores, resolução e driver. **O campo AdapterRAM pode apresentar VRAM imprecisa**, sobretudo em placas modernas ou integradas.
- Rede: adaptadores e estado. O relatório pode exibir **endereços MAC**, considerados informações sensíveis: não compartilhe a saída completa publicamente.
- Placa-mãe, discos físicos e versão do Windows.

Os dados dependem dos drivers e do acesso CIM; campos ausentes ou incorretos devem ser tratados como indisponíveis, não estimados. Não inclui monitoramento de sensores ou temperatura nesta versão.

## Exportação do hardware e licença MIT

Na versão **0.3.1**, o painel **Hardware e sistema** contém botões **Copiar**, **TXT** e **JSON**. Eles utilizam recursos do próprio navegador, sem escrever arquivos diretamente pelo servidor Python. Os dados exportados omitem **endereços MAC**. Revise o restante do relatório antes de compartilhá-lo.

Este projeto está sob a **licença MIT**: consulte [LICENSE](LICENSE). São permitidos uso, modificação e distribuição, inclusive comercial, desde que respeitadas as condições de aviso de direitos autorais e licença.

## Agentes de IA e Groq

**Sim, outras IAs podem utilizar as ferramentas.** O MCP usa protocolo interoperável para clientes compatíveis; o exemplo `agente_groq.py` emprega chamadas de ferramentas (**function calling**) diretamente pela API Groq, com uma lista restrita de funções disponíveis. Isso **não configura automaticamente um plugin no ChatGPT web**.

```powershell
$env:GROQ_API_KEY = "SUA_CHAVE"
$env:GROQ_MODEL = "openai/gpt-oss-20b"
py agente_groq.py
```

O modelo precisa estar disponível na sua conta e suportar tool calling. Evite inserir sua chave em arquivos versionados. O agente pede consentimento no terminal, envia as perguntas e resultados de ferramentas à API Groq e não pode executar PowerShell livre, apagar arquivos ou modificar projetos. Quotas e cobrança dependem do provedor.

**Manual completo:** [manuais/PRIMEIROS_PASSOS.md](manuais/PRIMEIROS_PASSOS.md).

## PowerShell controlado por IA — v0.4.0

O módulo [powershell_tools.py](powershell_tools.py) implementa **ações de diagnóstico fixas**. Uma IA pode selecionar um identificador de ação, mas **não pode enviar comandos PowerShell próprios** ao executor.

| ID | O que consulta |
|---|---|
| `versao_powershell` | Versão do PowerShell |
| `processos` | 15 processos com maior consumo de RAM |
| `servicos_parados` | Lista resumida de serviços parados |
| `unidades` | Espaço dos discos |
| `rede` | Interfaces de rede ativas (sem IP/MAC) |
| `tempo_atividade` | Última inicialização do Windows |

A interface possui painel **PowerShell (diagnóstico)** com seleção e confirmação para cada execução; o agente Groq também exige confirmação individual no terminal. O servidor MCP local expõe `wmk_powershell_catalog` e `wmk_powershell_diagnose`; **clientes MCP externos podem invocar esses diagnósticos diretamente, sem passar pela confirmação do navegador ou Groq**. Por isso, configure somente clientes de confiança.

Os scripts são constantes versionadas no código, usam PowerShell sem perfil, timeout de 20 segundos, saída limitada e logs locais `logs/powershell-audit.jsonl` (sem armazenar a saída). A proteção é uma lista fechada de scripts, não um analisador genérico de comandos. O projeto não deve ser executado como administrador sem necessidade.

Rotas locais: `GET /api/powershell/catalog` e `POST /api/powershell/diagnose` com corpo JSON `{"action":"processos"}`. A rota POST exige Origin local e ação previamente cadastrada. Não expose a porta 8767 na internet.

## Editor Monaco e modo pasta protegida — v0.5.0

O projeto agora oferece **WMK Code Studio** em `http://127.0.0.1:8767/editor`, com explorador da pasta autorizada, editor Monaco (carregado de CDN), criação manual de arquivos de código, comparação de alterações (diff), detecção de conflitos por hash SHA-256 e backups ao salvar.

Para ativar a pasta única, **pare o servidor atual** e reinicie com:

```powershell
cd D:\Ferramentas\WMK-Desktop-Bridge
$env:WMK_WORKSPACE = 'D:\Ferramentas\MeuProjeto'
py web_server.py
```

No modo restrito, as ferramentas Groq de arquivos enxergam apenas a pasta autorizada. Ferramentas de diagnóstico genérico de sistema, processos, hardware, discos, Ollama e PowerShell ficam bloqueadas neste modo. **A IA não recebe ferramentas de gravação ou exclusão.** O botão de salvar é operação humana no editor web e não deve ser confundido com isolamento de sistema operacional.

Para entender as restrições, riscos e testes: [manuais/FERRAMENTAS_SEGURAS.md](manuais/FERRAMENTAS_SEGURAS.md) e [manuais/SEGURANCA_AGENTES.md](manuais/SEGURANCA_AGENTES.md).

**Atenção:** a interface do Monaco depende da CDN do jsDelivr e portanto necessita internet para carregar esse editor. Quando indisponível, há um campo de texto alternativo. O programa ainda não passou por auditoria de segurança ou testes completos em Windows de terceiros. Evite abrir projetos que contenham segredos e não exponha a porta 8767 na rede.

## Dois modos da interface (v0.5.1)

No **modo Projeto Protegido**, quando `WMK_WORKSPACE` está configurado, o painel principal exibe apenas a pasta autorizada, os arquivos visíveis e a situação de segurança. As janelas de discos, hardware, Ollama e PowerShell ficam ocultas em vez de apresentar mensagens de erro. O botão **Code Studio** abre o editor Monaco.

No **modo Manutenção**, sem `WMK_WORKSPACE`, o painel mostra normalmente discos, hardware, Ollama e PowerShell de diagnóstico. Para mudar de modo, pare o servidor e inicie novamente com ou sem a variável; alternar somente o navegador não altera as permissões.

No PowerShell:
```powershell
# Projeto protegido:
$env:WMK_WORKSPACE = 'D:\Ferramentas\WMK-Desktop-Bridge'
py web_server.py

# Para voltar à manutenção (em uma nova execução após Ctrl+C):
Remove-Item Env:WMK_WORKSPACE -ErrorAction SilentlyContinue
py web_server.py
```

**Não há botão de alternância em tempo real:** mudar o ambiente do servidor requer reinicialização, para evitar reconfiguração acidental das permissões.

## Segurança

- Todas as ferramentas são **somente leitura**.
- Não há endpoint para executar comandos arbitrários nem para apagar arquivos.
- A interface web escuta apenas em `127.0.0.1:8767` e valida o cabeçalho Host/Origin.
- Os caminhos de arquivos são validados após resolução para bloquear saídas das raízes permitidas por links simbólicos.
- Limites em listagens e varreduras evitam consultas sem fim.
- Não abra portas do servidor na internet nem exponha o MCP por túnel sem autenticação, autorização e auditoria.
- Uma aplicação local pode ser acessada por outros programas executados no mesmo usuário; não é uma fronteira de segurança contra malware local.

## Estrutura

```text
WMK-Desktop-Bridge/
├── bridge.py                # núcleo de leitura e diagnóstico
├── security_policy.py       # perfis de segurança
├── workspace.py             # isolamento lógico de arquivos de projetos
├── editor_backend.py        # leitura, diff, hash e gravação humana
├── agente_groq.py            # agente experimental Groq com tool calling
├── powershell_tools.py       # executor de diagnósticos PowerShell permitidos
├── hardware.py              # inventário de hardware via CIM
├── mcp_server.py            # oito ferramentas MCP via stdio
├── web_server.py            # API/painel local HTTP
├── web/index.html           # painel com janelas móveis
├── web/editor.html          # Monaco Code Studio
├── iniciar-painel.bat
├── iniciar-mcp.bat
├── requirements.txt
├── .gitignore
├── LICENSE                   # licença MIT
├── manuais/PRIMEIROS_PASSOS.md
└── README.md
```

## Roadmap

- **v0.3.1:** inventário e exportação TXT/JSON implementados, exemplo de agente Groq incluído; análise de caches e testes automatizados ainda pendentes.
- **v0.4.0:** diagnósticos PowerShell com lista fechada, confirmações no painel e Groq, logs e timeout; operações de escrita continuam pendentes.
- **v0.5.0:** Monaco Code Studio e pasta única implementados como protótipo; aprovação centralizada segura para agentes e testes em Windows ainda pendentes.
- **v0.6:** agente remoto autenticado, transporte seguro e integração documentada com clientes compatíveis.

## Contribuições

Pull requests e relatos de problemas são bem-vindos. Descreva o Windows, versão do Python, passos para reproduzir e mensagem de erro. **Não publique tokens, caminhos pessoais sensíveis ou arquivos privados nos issues.**

## Licença

**Licença MIT**, arquivo [LICENSE](LICENSE). Reprodução do aviso de copyright e texto da licença obrigatória em cópias substanciais.

---
**WMK — Walney Moreira Klein** · **walneyk@hotmail.com**
