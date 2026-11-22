# WMK Desktop Bridge

**Ponte gratuita e de código aberto entre assistentes de IA e seu computador Windows.**

> Versão: **0.8.1 (agente de projeto lê múltiplos arquivos e prepara modificações reais)** · Interface em português do Brasil.

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
| Servidor MCP mínimo para acessar uma pasta e propor alterações | ✅ Protótipo |
| Fila de alterações com diff, SHA e aprovação pelo painel | ✅ Protótipo, testes de campo pendentes |
| Agente programador iterativo: ler projeto e propor várias edições | ✅ Protótipo (sem execução de testes) |
| Plugin ChatGPT conectado ao Windows | ❌ Ainda exige conexão/túnel e permissão da conta |
| Pasta única autorizada para agentes (somente leitura) | ✅ |
| Monaco Code Studio, diff, hash e backup para edição manual | ✅ Protótipo |
| IA integrada ao Monaco com Groq/Ollama e propostas lado a lado | ✅ Protótipo, sujeito a testes Windows |
| Central de Agentes: cadastro de agentes/provedores/permissões | ✅ Protótipo |
| Blender Safe Bridge: consulta/criação de primitivas com aprovação | ✅ Protótipo |
| Cliente MCP genérico para servidores externos | ❌ Ainda não implementado |
| Painel HTML local com painéis móveis, redimensionáveis e layout persistente | ✅ |
| Executar diagnósticos PowerShell fixos por IA (Groq/MCP) | ✅ Com restrições |
| Executar PowerShell arbitrário pela IA | ❌ Não permitido |
| Excluir arquivos pela IA | 🔒 Bloqueado: nenhuma ferramenta de exclusão |
| Controle remoto pelo ChatGPT web | ❌ Não implementado |

## Conectar o ChatGPT ao WMK Desktop Bridge

**O servidor MCP local não se instala automaticamente nesta conversa.** Para usar o WMK como o Desktop Commander, é preciso adicionar uma conexão MCP ao ChatGPT, normalmente por **Secure MCP Tunnel** ou por um gateway HTTPS autenticado. O ChatGPT web não chama processos Python locais diretamente.

O projeto possui `mcp_workspace_safe.py`, um MCP mínimo que expõe somente listagem, leitura e **propostas de alteração** dentro de `WMK_WORKSPACE`. Uma IA pode propor criar/editar um arquivo sem gravar imediatamente. O usuário confere o diff e aprova no painel `http://127.0.0.1:8767/approvals`. Não existem ferramentas de exclusão, shell ou PowerShell livre neste servidor.

**Guia completo de conexão, passos e limitações:** [manuais/CHATGPT_MCP_WINDOWS.md](manuais/CHATGPT_MCP_WINDOWS.md).

Enquanto o ChatGPT não estiver ligado ao WMK via MCP, ainda podemos atualizar projetos via repositório GitHub conectado. Não afirme que os arquivos locais foram modificados antes de uma chamada MCP bem-sucedida.

## Agente programador de projetos — v0.7.4

No painel `http://127.0.0.1:8767/agents` foi incluída a seção **Agente programador de projetos**, inspirada no fluxo de ferramentas de agentes como Codex e Claude Code. Selecione um agente com capacidade `workspace_read` e indique uma tarefa. O agente pode listar diretórios, ler arquivos de texto e gerar até quatro propostas de criação/edição em no máximo oito passos, **sem executar scripts ou salvar arquivos diretamente**.

O resultado aparece em `/approvals`, onde o usuário lê o diff, aprova ou rejeita. Os arquivos são gravados apenas com aprovação humana e backup. É obrigatório configurar `WMK_WORKSPACE` para uma única pasta.

**Não é ainda um substituto funcional completo para Codex/Claude Code**: não inclui shell, execução de testes/build, busca semântica, Git ou sandbox forte do Windows. Tarefas longas e projetos extensos exigem versões posteriores. O uso de APIs externas pode transmitir conteúdo dos arquivos para o provedor após consentimento.

**Manual:** [manuais/AGENTE_PROGRAMADOR.md](manuais/AGENTE_PROGRAMADOR.md).

## Correção do erro /api/status 400 — v0.7.5

Se o servidor iniciar com `WMK_WORKSPACE` apontando para uma pasta inexistente, a versão anterior lançava exceção e retornava HTTP 400. **Agora /api/status responde com a situação da pasta e um aviso**, enquanto as ferramentas de arquivos continuam bloqueadas até que o usuário configure uma pasta válida. Não é necessário desligar as proteções para visualizar o painel.

No PowerShell, após `git pull`, crie uma pasta de teste explícita e inicie o servidor:

```powershell
cd D:\Ferramentas\WMK-Desktop-Bridge
git pull
New-Item -ItemType Directory -Force 'D:\Ferramentas\WMK-Teste-IA' | Out-Null
$env:WMK_WORKSPACE = 'D:\Ferramentas\WMK-Teste-IA'
py web_server.py
```

**Pare a instância antiga com Ctrl+C antes de reiniciar** e atualize o navegador com Ctrl+F5. Teste:

```powershell
Invoke-RestMethod 'http://127.0.0.1:8767/api/status' | ConvertTo-Json -Depth 6
Invoke-RestMethod 'http://127.0.0.1:8767/api/workspace/status' | ConvertTo-Json
```

O primeiro resultado precisa informar `versao: 0.7.5`; se ainda mostrar a versão antiga, o processo anterior provavelmente continua ativo. Veja também `tests/test_status_workspace.py`.

## Teste real do Groq/Ollama — v0.7.6

A versão 0.7.6 corrige a exigência de JSON para operações **Explicar** e **Revisar** no Code Studio. Respostas dessas operações agora são aceitas como texto normal. Para **Corrigir**, **Refatorar** e **Gerar**, o JSON estruturado continua necessário para comparar arquivos completos.

O Code Studio possui os botões **Verificar configuração** (informa chave Groq presente e modelos Ollama locais) e **Testar resposta do provedor (sem arquivo)**, que realiza uma chamada mínima ao serviço escolhido sem enviar código-fonte. Quando a consulta falhar, a interface exibe a mensagem do backend em vez de apenas o status HTTP 400.

Foi adicionado um projeto de exemplo **Calculadora WMK** em `exemplos/calculadora/`, com `index.html`, `style.css` e `app.js`. Acesse `http://127.0.0.1:8767/exemplo/calculadora` para testar a calculadora, ou abra os arquivos no Monaco para pedir uma revisão à IA. Configure `WMK_WORKSPACE` com o caminho do próprio repositório para encontrá-los no explorador.

**Manual de configuração e diagnóstico:** [manuais/TESTE_IA_CALCULADORA.md](manuais/TESTE_IA_CALCULADORA.md).

As integrações com provedores reais ainda requerem validação no Windows do usuário. Os novos testes automatizados utilizam respostas simuladas, não consomem a API Groq nem comprovam conectividade externa.

## Correções v0.7.7 — Groq 403/1010 e calculadora sem CSS

A calculadora servida por `/exemplo/calculadora` estava sendo aberta sem barra final: os caminhos relativos `style.css` e `app.js` eram resolvidos fora da pasta. A página agora usa URLs absolutas e a rota sem barra final redireciona para `/exemplo/calculadora/`. O CSS recebeu visual dark neon revisado.

O Groq pode devolver **403 com `error code: 1010`** devido à regra Cloudflare de assinatura do cliente HTTP. O Python `urllib.request` usa por padrão um User-Agent genérico. O WMK passou a identificar-se com um User-Agent próprio tanto no Code Studio quanto na Central de Agentes. O erro 1010 agora recebe mensagem específica, diferente de chave inválida ou modelo inexistente. **A correção é uma hipótese técnica fundamentada, não uma confirmação de que sua conexão particular foi liberada.** Se a Cloudflare persistir bloqueando, entre em contato com o suporte do Groq; não tente desativar o filtro.

Teste após reiniciar o servidor:

```powershell
cd D:\Ferramentas\WMK-Desktop-Bridge
git pull
.\iniciar-com-chaves.ps1 -Workspace 'D:\Ferramentas\WMK-Desktop-Bridge'
```

Abra `http://127.0.0.1:8767/exemplo/calculadora/` e no Code Studio clique em **Testar resposta do provedor (sem arquivo)**. Confirme a versão `0.7.7` em `/api/status`.

Documentação Cloudflare: https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-1xxx-errors/error-1010/

## Groq não encontra a chave? Correção v0.7.8

O Code Studio antes consultava apenas `GROQ_API_KEY` no ambiente do processo Python, mesmo quando a chave tinha sido cadastrada em outra sessão/PowerShell. Agora existe um **cofre de credenciais local no Windows**, com criptografia DPAPI vinculada ao usuário atual e um botão na própria interface.

1. Interrompa o servidor antigo com Ctrl+C e execute `git pull`.
2. Inicie o WMK com `$env:WMK_WORKSPACE='D:\\Ferramentas\\WMK-Desktop-Bridge'; py web_server.py`.
3. Abra `http://127.0.0.1:8767/editor`.
4. Selecione Groq → clique **Configurar chave Groq no Windows** → cole a sua chave no campo protegido → clique **Salvar chave protegida**.
5. Clique **Verificar configuração** e depois **Testar resposta do provedor (sem arquivo)**.
6. Se a resposta for OK, abra a calculadora e peça para o Groq revisar `exemplos/calculadora/app.js`.

**Não é necessário reiniciar após salvar uma chave pelo painel.** O Code Studio, o teste de conexão e os agentes consultam o mesmo cofre. A chave não é gravada no repositório nem exibida nas respostas da API. Arquivos protegidos ficam em `%LOCALAPPDATA%\\WMKDesktopBridge\\secrets` com sufixo `.wmk`. O antigo script PowerShell gravava segredos em um formato `.dpapi` diferente: quem utilizou esse script deverá cadastrar novamente **uma única vez** no painel. Não coloque credenciais em chats, issues ou arquivos do projeto.

**Segurança:** DPAPI protege a chave em repouso para o usuário Windows, mas não impede outro programa malicioso executado com essa mesma conta de recuperar credenciais. A interface HTTP local ainda não possui autenticação forte por sessão; não exponha a porta 8767 à rede. O código precisa de validação prática em Windows.

Se o teste retornar **HTTP 403/1010** depois de cadastrar a chave, é um problema distinto: o provedor/Cloudflare está recusando a conexão. Não significa que a chave está ausente, e não há garantia de que o WMK possa contornar o bloqueio.

## Code Studio v0.7.9 — resposta da IA ao lado do Monaco

O painel direito do Code Studio agora é dedicado à **resposta da IA**, com área de leitura ampla e rolável, seleção e cópia do texto integral, identificação do arquivo/provedor/modelo, estado de análise e botão Limpar. A configuração de Groq/Ollama fica recolhível; ao receber a análise, o painel fecha automaticamente as configurações para mostrar a resposta completa, e reabre em caso de erro.

Em telas maiores que 1050px, arraste a divisória à esquerda da resposta para ajustar a largura do painel; o valor fica salvo no navegador. Em telas menores, o editor passa a ter organização adaptativa. A revisão e a comparação de códigos permanecem disponíveis, e nenhuma resposta salva o arquivo sem confirmação.

**Teste:** atualize com `git pull`, reinicie o Python, entre em `http://127.0.0.1:8767/editor`, faça `Ctrl+F5`, abra `exemplos/calculadora/app.js`, clique em **Configurar IA** e escolha **Revisar**. Após receber a resposta, a área à direita exibirá a análise completa, sem misturar o texto com mensagens de status.

## Code Studio v0.8.0 — resposta Markdown formatada

A análise Groq/Ollama não é mais mostrada com asteriscos, tabelas e marcações Markdown literais. No painel ao lado do Monaco, o visualizador local `web/markdown_renderer.js` reconhece:

- Títulos `#`, `##`, `###` e níveis seguintes.
- **Negrito**, *itálico*, links `https://`, código em linha.
- Listas numeradas ou com marcadores; citações; separadores.
- Tabelas Markdown com cabeçalhos e rolagem horizontal.
- Blocos de código cercados por três crases, com botão **Copiar código**.
- Botões **Copiar Markdown** e **Salvar .md** para preservar a resposta original do modelo.

**Segurança:** o renderizador constrói os elementos com APIs DOM e `textContent`. Não interpreta nem executa HTML recebido da IA; URLs só são abertas como links para endereços HTTP(S), em nova aba com `noopener noreferrer`. Não depende de biblioteca de Markdown externa.

Para testar no Windows, atualize via `git pull`, **pare e reinicie** `web_server.py`, abra `http://127.0.0.1:8767/editor`, pressione `Ctrl+F5` e faça a revisão de `exemplos/calculadora/index.html` ou `app.js`. A resposta anterior não é restaurada após atualizar; solicite uma análise nova.

O parser é intencionalmente limitado ao Markdown mais comum. HTML embutido, extensões específicas como Mermaid, matemática LaTeX e tabelas malformadas continuam como texto normal. As formatações só funcionam se o modelo retornar Markdown minimamente válido.

## Novo: trabalhar nos arquivos do projeto pelo Code Studio (v0.8.1)

**Há dois modos diferentes**: o botão `Analisar arquivo com IA` apenas revisa o código que estiver aberto; ele NÃO grava alterações. Para o agente efetivamente consultar outros arquivos e editar o projeto, abra `/editor` e clique **🛠 Trabalhar no projeto**.

O agente lê automaticamente o arquivo aberto e até quatro arquivos relacionados da mesma pasta (por exemplo `index.html`, `style.css`, `app.js`), enviados ao provedor selecionado apenas após consentimento. Ele produz patches exatos ou novas versões de arquivos. O WMK valida se cada trecho original existe, prepara uma proposta e exibe o diff. Clique **Revisar e aplicar** e então **Aprovar e gravar este arquivo** para modificar os arquivos no disco com backup. **Nenhum arquivo é modificado apenas pela resposta da IA.**

As propostas podem ser verificadas em `/approvals`. Um relatório que diga "corrigimos" sem patches é mostrado como **zero alterações**. O aplicativo não executa builds, testes, shell ou comandos do projeto; não se deve compará-lo ainda à autonomia completa de Codex.

**Manual e procedimento de teste:** [manuais/AGENTE_PROJETO_MONACO.md](manuais/AGENTE_PROJETO_MONACO.md).

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

## IA no Code Studio — v0.5.2

O editor Monaco agora possui um painel de assistência com **Groq** (API com `GROQ_API_KEY`) e **Ollama** local (`127.0.0.1:11434`). Depois de abrir um arquivo autorizado, é possível pedir: **Explicar**, **Revisar**, **Corrigir**, **Refatorar** e **Gerar** código. A interface requer consentimento para cada consulta.

Nas ações com código proposto, o usuário pode **comparar original e sugestão lado a lado**, enviar a sugestão para a memória do editor e, separadamente, clicar em **Salvar após revisão**. O modelo **não possui ferramentas para gravar ou excluir arquivos**. O backend valida os caminhos, os limites de tamanho e nomes sensíveis, e aplica detecção básica de credenciais — que não é infalível.

**O código enviado à Groq pode sair do computador**; somente use arquivos para os quais possui autorização. A configuração da chave deve ser feita no ambiente do servidor Python, nunca dentro do HTML ou no repositório. O modo protegido exige `WMK_WORKSPACE`.

Para os passos completos e problemas conhecidos: **[Manual do Assistente de Código](manuais/ASSISTENTE_CODIGO_IA.md)**.

## Central de Agentes e Blender — v0.6.0

Acesse **http://127.0.0.1:8767/agents** para cadastrar agentes com nome, provedor, modelo, instruções e capacidades. Os provedores disponíveis no cadastro são **Ollama**, **Groq**, **OpenAI API** e **Gemini API**; disponibilidade prática depende das chaves, modelos e suporte a respostas JSON dos provedores.

A integração Blender desta versão utiliza **um add-on HTTP local próprio com token**, incluindo consulta de objetos, criação de cubos/esferas/cilindros e alteração de cores. **Não é um cliente MCP genérico**: o Bridge expõe ferramentas Blender de leitura ao MCP local, mas não conecta automaticamente qualquer MCP externo. A IA deve gerar uma proposta que o usuário aprova individualmente no painel antes de qualquer modificação da cena.

**Configurar chaves no Windows:** `configurar-chaves.ps1` utiliza DPAPI; `iniciar-com-chaves.ps1` carrega os segredos protegidos do usuário e inicia o servidor. Para OpenAI, Groq e Gemini também podem ser usadas variáveis de ambiente temporárias, sem armazená-las no código.

**Manual completo em português:** [Central de Agentes, MCP e Blender](manuais/AGENTES_MCP_BLENDER.md).

**Segurança:** o painel web ainda não possui autenticação forte por sessão. A aprovação pelo navegador protege contra ações acidentais da IA, mas **não oferece isolamento robusto contra outros processos locais**. Não exponha portas do WMK/Blender à internet. A integração do Blender não inclui Python arbitrário nem exclusão. Os testes Windows/Blender permanecem pendentes.

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
├── code_ai.py               # adaptadores Groq/Ollama sem escrita
├── agent_hub.py             # cadastro de agentes e propostas
├── blender_client.py        # cliente HTTP seguro do Blender
├── blender_addon/           # add-on Blender sem Python remoto
├── agente_groq.py            # agente experimental Groq com tool calling
├── powershell_tools.py       # executor de diagnósticos PowerShell permitidos
├── hardware.py              # inventário de hardware via CIM
├── mcp_server.py            # oito ferramentas MCP via stdio
├── web_server.py            # API/painel local HTTP
├── web/index.html           # painel com janelas móveis
├── web/editor.html          # Monaco Code Studio
├── web/editor_ai.js         # interface das sugestões e comparação
├── web/agents.html          # central de agentes e Blender
├── configurar-chaves.ps1    # salva credenciais cifradas por DPAPI
├── iniciar-com-chaves.ps1   # inicia servidor usando DPAPI
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
- **v0.5.2:** assistente Groq/Ollama no Monaco, propostas e comparação lado a lado (testes de campo ainda necessários).
- **v0.6.0:** cadastro de agentes, provedores, Blender Safe Bridge e manuais. Necessita testes Windows/Blender.
- **v0.7:** cliente MCP genérico com catálogo de ferramentas, permissões por agente, testes e autenticação de sessão.
- **futuro:** agente remoto autenticado com TLS, transporte seguro e integração ao ChatGPT web.

## Contribuições

Pull requests e relatos de problemas são bem-vindos. Descreva o Windows, versão do Python, passos para reproduzir e mensagem de erro. **Não publique tokens, caminhos pessoais sensíveis ou arquivos privados nos issues.**

## Licença

**Licença MIT**, arquivo [LICENSE](LICENSE). Reprodução do aviso de copyright e texto da licença obrigatória em cópias substanciais.

---
**WMK — Walney Moreira Klein** · **walneyk@hotmail.com**
