# WMK Coding Studio v0.9.0 — integração com OpenCode real

**Walney Moreira Klein — walneyk@hotmail.com**

## O que foi entregue

O WMK deixou de tentar emular Codex apenas com respostas JSON. A nova rota **/coder** inicia a **interface WEB própria do OpenCode** usando o executável já instalado no Windows. Este é um motor de agentes real, com sessões, leitura e edição de arquivos e suporte a modelos/provedores configurados no OpenCode.

**Isto não é uma implementação nova de Codex, nem um agente próprio independente**. A tela WMK é um lançador e controla início/parada do servidor; a edição efetiva acontece no OpenCode, em uma nova aba do navegador, por suas próprias ferramentas.

## Instalação no Windows

No PowerShell, verifique:

```powershell
opencode --version
```

Se o comando não existir, consulte o projeto oficial para instruções de instalação: https://opencode.ai/docs/ . Não confunda a extensão WMK IA Assistente com o executável CLI do OpenCode.

Interrompa o WMK anterior com Ctrl+C, depois:

```powershell
cd D:\Ferramentas\WMK-Desktop-Bridge
git pull
$env:WMK_WORKSPACE = 'D:\Ferramentas\WMK-Desktop-Bridge'
py web_server.py
```

Abra `http://127.0.0.1:8767/coder`. Clique **Iniciar OpenCode para esta pasta**, depois **Abrir interface de programação**. A interface oficial será aberta em `http://127.0.0.1:4097`.

Se a página pedir autenticação, use usuário `opencode` e a senha temporária gerada e exibida pela página WMK. Essa senha é diferente de sua chave Groq. O OpenCode poderá solicitar que você selecione o projeto ou confirme a conexão inicial; escolha exclusivamente a pasta autorizada mostrada no WMK.

## Exemplo: corrigir a calculadora sem ficar copiando código

No OpenCode, configure seu provedor (Groq ou Ollama) e um modelo que suporte efetivamente chamadas de ferramentas. Abra/crie uma sessão para a pasta `WMK_WORKSPACE` e peça:

> Abra os arquivos exemplos/calculadora/index.html, exemplos/calculadora/style.css e exemplos/calculadora/app.js. Melhore a acessibilidade dos botões da calculadora e preserve o funcionamento. Mostre quais arquivos alterou. Não execute comandos de terminal.

O OpenCode usa suas ferramentas `read`, `edit` e `write`; o WMK não obriga respostas de edição em JSON e não depende do endpoint antigo `/api/coding/project`.

Após aprovar as solicitações de edição, confira o arquivo atualizado no Monaco. Se o OpenCode pedir permissão para editar, leia o destino antes de autorizar.

## Configuração de IA

O OpenCode usa seu próprio catálogo e credenciais. A chave Groq cadastrada no painel DPAPI do WMK não é compartilhada automaticamente, porque isso exigiria transferir a credencial para um processo externo sem sua autorização. No OpenCode, configure o provedor em seus controles oficiais. Para Ollama local, use a integração documentada pelo OpenCode.

O modelo `qwen3:1.7b` pode ter dificuldade com ferramentas e projetos grandes. Se uma edição não acontecer, verifique o histórico de ferramentas e o modelo selecionado no OpenCode.

## Segurança — fundamental

- O WMK inicia o OpenCode apenas com `--hostname 127.0.0.1` e porta `4097`.
- Gera senha aleatória por sessão e exige autenticação do servidor.
- Fornece configuração dedicada de permissões `external_directory: deny`, `shell: deny`, `edit: ask` e bloqueio adicional de shell/external_directory por políticas do OpenCode.
- O WMK **não libera shell** nesse modo; testes/build por terminal ficam indisponíveis enquanto essa restrição estiver ligada.
- O processo OpenCode é executado **com as permissões da sua conta Windows**. Essas configurações são controles de aplicação, **não uma sandbox forte**. Plugins/MCPs e versões distintas podem ter comportamentos diferentes. Não confie nisso como bloqueio absoluto contra código malicioso.
- Execute inicialmente em uma pasta de teste, sem documentos pessoais, credenciais e códigos de clientes; mantenha backup.
- Se o diretório autorizado estiver dentro de um repositório Git cujo worktree abranja diretórios externos à pasta, as permissões de worktree do OpenCode podem alcançar esses diretórios; evite essa organização ou use uma conta Windows com ACLs restritas.
- Não use Opencode em modo auto-aprovação ou sem permissões na primeira execução. Não exponha a porta 4097 na rede ou via túnel.

O projeto WMK não instalou um driver/sandbox de Windows. Não é possível garantir isolamento total só usando a variável `WMK_WORKSPACE`.

## Troubleshooting

- **OpenCode não encontrado**: execute `opencode --version` no mesmo terminal e confira o PATH. Reinicie o WMK após atualizar PATH.
- **Servidor não respondeu**: consulte `config/wmk-opencode-runtime.log`; pode haver outra aplicação na porta 4097.
- **Não consegue editar**: confira se a solicitação de permissão do OpenCode foi aprovada e se a pasta correta está aberta.
- **Provedor não reconhecido**: configure a API pelo próprio OpenCode e selecione o modelo disponível.
- **O modelo diz que corrigiu mas não edita**: confira as operações `edit/write` no histórico; é possível que o modelo escolhido não suporte ferramentas.
- **A interface 4097 pede senha**: ela aparece na tela `/coder`, no campo de credencial temporária.

### Referências oficiais

- https://opencode.ai/docs/cli/web/
- https://opencode.ai/docs/cli/commands/
- https://opencode.ai/docs/permissions/
- https://opencode.ai/docs/tools/
