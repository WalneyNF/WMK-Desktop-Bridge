# WMK Desktop Bridge

**Ponte gratuita e de código aberto entre assistentes de IA e seu computador Windows.**

> Versão: **0.2.1 (protótipo local, somente leitura)** · Interface em português do Brasil.

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
| Servidor MCP local via stdio | ✅ |
| Painel HTML local com painéis móveis, redimensionáveis e layout persistente | ✅ |
| Executar PowerShell pela IA | ❌ Não implementado |
| Excluir arquivos pela IA | ❌ Não implementado |
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
├── mcp_server.py            # cinco ferramentas MCP via stdio
├── web_server.py            # API/painel local HTTP
├── web/index.html           # painel com janelas móveis
├── iniciar-painel.bat
├── iniciar-mcp.bat
├── requirements.txt
├── .gitignore
└── README.md
```

## Roadmap

- **v0.3:** análise de caches, relatórios JSON e HTML e testes automatizados.
- **v0.4:** fila de operações de escrita com revisão humana, cópia de segurança e permissões por ferramenta.
- **v0.5:** executor PowerShell com política restritiva, tempo limite e logs; nunca acesso irrestrito por padrão.
- **v0.6:** agente remoto autenticado, transporte seguro e integração documentada com clientes compatíveis.

## Contribuições

Pull requests e relatos de problemas são bem-vindos. Descreva o Windows, versão do Python, passos para reproduzir e mensagem de erro. **Não publique tokens, caminhos pessoais sensíveis ou arquivos privados nos issues.**

## Licença

**Ainda não foi selecionada uma licença.** O repositório é público para consulta; para permitir reutilização, distribuição e alterações com condições claras, o mantenedor deve adicionar uma licença (por exemplo, MIT).

---
**WMK — Walney Moreira Klein** · **walneyk@hotmail.com**
