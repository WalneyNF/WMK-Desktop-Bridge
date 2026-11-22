# WMK Desktop Bridge — Central de Agentes e Blender v0.6.0

**Autor:** Walney Moreira Klein — walneyk@hotmail.com  
**Licença:** MIT.

## O que está implementado

- Painel `http://127.0.0.1:8767/agents` para cadastrar agentes com nome, modelo, provedor, instruções e capacidades.
- Cadastro local em `config/agents.json`, que deve ser tratado como configuração privada e não enviado ao Git.
- Provedores configuráveis: **Ollama local, Groq, OpenAI API e Gemini API (endpoint compatível com OpenAI)**; suporte prático depende do modelo escolhido aceitar JSON e dos limites de cada API.
- Agente Blender: IA propõe de **1 a 3 ações permitidas**, o usuário vê a proposta e precisa clicar em **Aprovar e executar**.
- Add-on `blender_addon/wmk_blender_bridge.py` com API local autenticada em `127.0.0.1:8768`, sem aceitar código Python remoto.
- Operações Blender fixas: listar objetos, criar cubo/esfera/cilindro e aplicar cor RGBA em malha existente.
- Agente revisor de código: analisa **um único arquivo** autorizado por vez, com consentimento, sem alteração do disco.
- MCP local (stdio): ferramentas Blender **somente leitura**, além das ferramentas já existentes.

**O que ainda não existe:** cliente MCP genérico capaz de conectar qualquer servidor externo, manipulação avançada de malhas, execução de scripts livres e integração remota ChatGPT web. O Blender desta versão utiliza um **conector HTTP local próprio**, não o protocolo MCP para a conexão entre o Blender e o Bridge. O Bridge, por sua vez, expõe ferramentas de consulta do Blender via MCP a clientes compatíveis.

## 1 — Preparar o ambiente

Requisitos: Windows 10/11, Python 3.10+, Blender compatível com a API `bpy` usada pelo add-on, e acesso local ao Blender. O painel principal usa biblioteca padrão do Python.

```powershell
cd D:\Ferramentas\WMK-Desktop-Bridge
git pull
```

Para habilitar servidores MCP locais opcionais:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Modo de execução

**Projeto protegido** — permite acesso ao projeto configurado e bloqueia diagnósticos gerais do sistema:

```powershell
$env:WMK_WORKSPACE='D:\Ferramentas\WMK-Desktop-Bridge'
py web_server.py
```

**Manutenção** — remove o workspace somente para essa sessão antes de iniciar:

```powershell
Remove-Item Env:WMK_WORKSPACE -ErrorAction SilentlyContinue
py web_server.py
```

O painel de agentes é acessível nos dois modos. O revisor de código necessita do modo protegido e de um arquivo dentro do workspace.

## 2 — Configurar provedores e chaves

Ollama é local; geralmente não precisa chave. Instale e inicie Ollama, depois:

```powershell
ollama pull qwen3:1.7b
ollama list
Invoke-RestMethod http://127.0.0.1:11434/api/tags
```

As chaves dos serviços externos são obtidas nos respectivos painéis oficiais, dependendo do plano e de disponibilidade:

- Groq: https://console.groq.com/keys — variável `GROQ_API_KEY`.
- OpenAI API: https://platform.openai.com/api-keys — variável `OPENAI_API_KEY`.
- Google Gemini API: https://aistudio.google.com/apikey — variável `GEMINI_API_KEY`.

**Não confunda assinatura ChatGPT com créditos da API OpenAI.** Uso das APIs pode ter quotas e cobrança. Não publique chaves nem as inclua em arquivos do projeto.

### Opção rápida: variáveis temporárias

```powershell
$env:GROQ_API_KEY='SUA_CHAVE'
$env:OPENAI_API_KEY='SUA_CHAVE'
$env:GEMINI_API_KEY='SUA_CHAVE'
$env:GROQ_MODEL='openai/gpt-oss-20b'
py web_server.py
```

Configure apenas provedores que de fato pretende utilizar. As variáveis são do processo iniciado naquele terminal.

### Opção recomendada no Windows: DPAPI

```powershell
cd D:\Ferramentas\WMK-Desktop-Bridge
.\configurar-chaves.ps1
```

Escolha o provedor e informe a chave no campo oculto. O script grava o valor **cifrado pelo DPAPI para o usuário atual** em `%LOCALAPPDATA%\WMKDesktopBridge\secrets`, fora do Git.

Para iniciar com credenciais recuperadas:

```powershell
.\iniciar-com-chaves.ps1 -Workspace 'D:\Ferramentas\WMK-Desktop-Bridge'
```

Se sua política do PowerShell impedir executar scripts, não desative proteções globalmente. Prefira autorizar o script local após inspecionar seu conteúdo ou usar variáveis de sessão. DPAPI protege o arquivo em repouso, mas **não impede que programas maliciosos rodando com a mesma conta Windows recuperem as credenciais**.

## 3 — Instalar o Blender Safe Bridge

1. Abra o Blender.
2. Vá às preferências de add-ons/extensões e use **Install from Disk / Instalar do disco** para carregar `blender_addon/wmk_blender_bridge.py`. O caminho exato da opção depende da versão do Blender.
3. Ative o add-on **WMK Blender Safe Bridge**.
4. Abra uma área 3D e pressione `N` para exibir a barra lateral. Procure a aba **WMK**.
5. Digite uma senha/token aleatório de **pelo menos 16 caracteres**, preferencialmente 32 ou mais. Use um gerador criptograficamente seguro.
6. Clique em **Iniciar ponte local**.
7. Configure a **mesma** sequência no WMK, por exemplo, com `./configurar-chaves.ps1` e escolhendo `WMK_BLENDER_TOKEN`.

O add-on deve apresentar serviço local em `127.0.0.1:8768`. Para testar a disponibilidade (não altera a cena):

```powershell
Invoke-RestMethod http://127.0.0.1:8768/status
```

Se o Blender estiver fechado, desconectado ou o token for diferente, ações falharão. A cena não é salva automaticamente; use o Blender para salvar o arquivo `.blend` depois de validar as mudanças.

## 4 — Executar um teste com IA

Com Blender aberto e ponte iniciada, execute no terminal:

```powershell
cd D:\Ferramentas\WMK-Desktop-Bridge
.\iniciar-com-chaves.ps1 -Workspace 'D:\Ferramentas\WMK-Desktop-Bridge'
```

Abra `http://127.0.0.1:8767/agents`.

1. Selecione **Especialista Blender** (agente de exemplo) ou cadastre um novo.
2. Escolha provedor e modelo; configure capacidade `blender_list` e, quando necessário, `blender_create`.
3. Clique em **Testar conexão Blender**.
4. Peça: **Crie um cubo de tamanho 2 na posição [0,0,1]**.
5. Clique em **Gerar proposta com IA**. Isso ainda **não executa** ações.
6. Revise cada comando no quadro de aprovação. Clique em **Aprovar e executar** para enviar as ações ao Blender.
7. Verifique os objetos na cena.

O modelo pode fornecer JSON inválido ou propor ações não permitidas; nesse caso, o sistema recusa o plano. Propostas expiram em 120 segundos e são consumidas ao executar. Se uma sequência falhar no meio, operações anteriores podem permanecer na cena; desfazer manualmente no Blender.

## 5 — Agentes de revisão de código

No modo de projeto protegido, abra `/agents`, escolha o agente de revisão, indique por exemplo `bridge.py`, escreva a pergunta e marque a autorização de envio. O conteúdo do arquivo autorizado pode ser enviado ao provedor selecionado. O agente não recebe ferramenta de escrita.

Para alterar código com propostas lado a lado, use o **Code Studio** em `/editor`.

## 6 — Privacidade e segurança

- Não execute o Bridge como administrador.
- O serviço web fica em `127.0.0.1:8767` e o add-on em `127.0.0.1:8768`. **Nunca exponha essas portas à internet**.
- O token Blender protege o endpoint Blender, mas o painel WMK ainda não implementa autenticação forte por sessão. Outros programas locais no mesmo usuário podem tentar fazer solicitações.
- Agentes não recebem função de exclusão, PowerShell arbitrário ou execução de Python no Blender.
- Os controles de pasta são **restrições de aplicação**, não uma sandbox do sistema operacional. Não execute ZIPs, builds e scripts não confiáveis.
- Arquivos potencialmente sensíveis não devem ser disponibilizados a serviços remotos. O scanner de segredos é básico e não detecta tudo.
- A criação de objetos Blender é uma **alteração de cena** e só ocorre após aprovação explícita no painel, não por simples solicitação do modelo.
- O uso genérico de servidores MCP de terceiros permanece planejado: deve vir acompanhado de inspeção de ferramentas, permissões e isolamento.

## 7 — Problemas conhecidos e próximos passos

- **Blender offline:** confira add-on ativo, porta 8768 e painel `WMK` no Blender.
- **401 do Blender:** token no add-on diferente de `WMK_BLENDER_TOKEN`.
- **Modelo inexistente:** confira o nome no provedor e se suporta saída JSON.
- **Groq/Google/OpenAI 401:** confira chave e permissões da conta.
- **Sem acesso ao arquivo:** configure `WMK_WORKSPACE`, abra um caminho relativo e evite arquivos bloqueados.
- **Sem o botão Agentes:** execute `git pull`, reinicie Python e pressione `Ctrl+F5`.

**Esta versão é protótipo.** Integração no Windows/Blender, testes adversariais, autenticação local, aprovação resistente a falsificação e revisão independente ainda são necessários antes de uso em computadores de terceiros.
