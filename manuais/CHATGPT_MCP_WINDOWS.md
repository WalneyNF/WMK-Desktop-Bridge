# Conectar WMK Desktop Bridge ao ChatGPT como Desktop Commander

**WMK Workspace Seguro v0.7.3 — Walney Moreira Klein — walneyk@hotmail.com**

## Objetivo

Permitir que assistentes de IA usem ferramentas de arquivos do **seu Windows**, dentro de **uma única pasta** explicitamente autorizada, sem envio de ZIPs pelo chat a cada alteração.

### Como o Desktop Commander Remote funciona

O serviço usa um servidor MCP remoto, autenticação e um agente de dispositivo no computador. O ChatGPT chama o servidor remoto, que encaminha a tarefa ao agente local. **O ChatGPT não acessa `C:\` ou `D:\` diretamente.**

Nosso WMK agora tem o executor seguro MCP e a fila de aprovação, mas **a conexão do WMK como plugin nesta conversa ainda não foi configurada**. Não confundir servidor MCP local com plugin ChatGPT já instalado.

## Arquitetura WMK

```text
ChatGPT / outro cliente MCP
         |
         | Servidor MCP remoto autenticado OU Secure MCP Tunnel
         v
mcp_workspace_safe.py (stdio, Windows)
         |
         +-- wmk_workspace_status
         +-- wmk_workspace_list
         +-- wmk_workspace_read
         +-- wmk_workspace_propose_write
         +-- wmk_workspace_proposal_status
                            |
                            v
               config/mcp_proposals.sqlite3
                            |
                   painel local /approvals
                            |
                 aprovação humana + diff + SHA
                            |
                      editor_backend.py
                            |
                      WMK_WORKSPACE
```

**Nenhuma ferramenta desse servidor executa PowerShell, shell, comandos de instalação, exclusão, scripts ou gerenciamento externo de hardware.** O cliente MCP comum `mcp_server.py` tem recursos extras; **use exclusivamente `mcp_workspace_safe.py` para conectar uma IA remota**.

## Preparação local no Windows

1. Crie sua pasta de trabalho (por exemplo `D:\Ferramentas\ProjetoAutorizado`).
2. Abra um PowerShell sem elevação.
3. Instale a dependência MCP no ambiente virtual:

```powershell
cd D:\Ferramentas\WMK-Desktop-Bridge
git pull
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:WMK_WORKSPACE = 'D:\Ferramentas\ProjetoAutorizado'
py web_server.py
```

O painel de aprovação estará em `http://127.0.0.1:8767/approvals`.

O servidor MCP usa **stdio**, portanto é iniciado automaticamente por clientes locais compatíveis. Uma configuração ilustrativa para cliente MCP local:

```json
{
  "mcpServers": {
    "wmk-workspace-seguro": {
      "command": "D:\\Ferramentas\\WMK-Desktop-Bridge\\.venv\\Scripts\\python.exe",
      "args": ["D:\\Ferramentas\\WMK-Desktop-Bridge\\mcp_workspace_safe.py"],
      "env": {
        "WMK_WORKSPACE": "D:\\Ferramentas\\ProjetoAutorizado"
      }
    }
  }
}
```

Não cole chaves de API, tokens, senhas ou credenciais nesse JSON.

## ChatGPT web: duas opções

A documentação oficial do ChatGPT informa que **não conecta diretamente a MCP stdio local**. Existe a opção **Secure MCP Tunnel**, que permite conectar um processo MCP privado sem abrir portas para a internet. Porém a criação/uso do túnel exige recursos e permissões da organização OpenAI Platform e do workspace ChatGPT. Verifique a disponibilidade na sua conta.

Fontes:
- https://help.openai.com/en/articles/12584461-connecting-custom-mcp-servers-in-chatgpt
- https://developers.openai.com/api/docs/guides/secure-mcp-tunnels
- https://developers.openai.com/plugins/deploy/connect-chatgpt

### Opção A: Secure MCP Tunnel (quando a conta permitir)

1. Crie um `tunnel_id` nas configurações de túneis da OpenAI Platform e configure uma credencial **com permissões mínimas**.
2. Instale o cliente oficial `openai/tunnel-client` no PC e consulte a ajuda de sua versão (`tunnel-client help quickstart`).
3. Configure um perfil stdio cujo **MCP command** seja o Python que executa `mcp_workspace_safe.py`, garantindo `WMK_WORKSPACE` definido no processo/ambiente do cliente.
4. Execute `tunnel-client doctor --profile <perfil> --explain` e depois `tunnel-client run --profile <perfil>`.
5. No ChatGPT web, abra **Plugins → + → Add custom MCP server**, escolha **Tunnel**, selecione seu `tunnel_id`, configure a autenticação e revise as ferramentas.
6. Instale o plugin aprovado e teste `wmk_workspace_status` e `wmk_workspace_list`.

**Não execute o túnel antes de configurar a pasta autorizada**. O servidor falha ao iniciar sem `WMK_WORKSPACE`.

### Opção B: servidor MCP remoto próprio

Para publicar uma integração para muitas pessoas, será necessário um **gateway HTTPS remoto com OAuth** e autenticação/pareamento de dispositivos. Um agente local inicia uma conexão de saída autenticada para receber chamadas MCP específicas de cada usuário. Isso é um produto adicional, **ainda não implementado** no WMK. Não publique diretamente `127.0.0.1:8767` por túnel genérico desprotegido nem disponibilize as chaves no GitHub.

### Observação sobre planos

As capacidades de usar MCP personalizado e ferramentas de escrita dependem do plano/conta e das permissões. Um servidor com `propose_write` pode não ser permitido como ação de escrita em todas as modalidades do ChatGPT. Confira a documentação atual e o resultado do cadastro da sua conexão; **a disponibilidade não é garantida**.

## Teste: IA criar um arquivo

Depois da conexão MCP estar ativa, peça ao agente:

> Use `wmk_workspace_status`. Liste a pasta autorizada. Proponha um arquivo `teste_wmk.py` que imprima "Olá WMK". Não execute nada. Retorne o ID da proposta.

A IA deverá usar `wmk_workspace_propose_write`. Em seguida:

1. Abra `http://127.0.0.1:8767/approvals` no navegador do seu Windows.
2. Clique na proposta pendente e revise o **diff completo**.
3. Clique em **Aprovar e salvar arquivo**, confirme.
4. O servidor grava o arquivo somente dentro de `WMK_WORKSPACE`.
5. Peça à IA para consultar `wmk_workspace_proposal_status` e ler o arquivo criado.

Para editar arquivo existente, o WMK guarda a versão SHA-256 original, recusa alterações feitas por outro programa desde a proposta, registra o resultado e cria backup. Para remover uma proposta, clique **Recusar**; isso não exclui nenhum arquivo.

## Limitações de segurança

- A restrição é lógica, feita no Python; **não é isolamento do sistema operacional**.
- Não exponha o servidor web ou um MCP local por porta pública sem autenticação adequada.
- O painel local exige origem do próprio host para POST, mas **não possui autenticação forte de sessão**: outro software executando sob a mesma conta Windows pode representar risco.
- O SQLite contém propostas de código que podem incluir informação confidencial. Guarde a pasta `config/` com ACLs apropriadas.
- O agente pode propor conteúdo inadequado; confira o diff, não execute scripts de projetos desconhecidos.
- Não há apagamento de arquivos por ferramentas MCP. Recusar proposta apenas altera seu status no banco.
- Textos contendo segredos não devem ser enviados a provedores remotos. O WMK não oferece detector infalível.
- Falhas de energia, symlinks, junções ou processos hostis concorrentes exigem testes específicos e isolamento de baixo privilégio.
- Teste a integração em um projeto de demonstração, nunca inicialmente em códigos de clientes.
- Em qualquer momento, desconecte o túnel/cliente MCP para interromper novas chamadas.

## Roadmap

- Gateway multiusuário e dispositivo pareado com OAuth 2.1.
- Cliente local com chave de sessão e reconexão de saída.
- Centro de permissões por conexão, logs e revogação.
- Autenticação forte da interface e proteção contra solicitações cruzadas.
- Testes de segurança de links/junções NTFS, TOCTOU e escrita atômica.
- Permissões de sistema operacional (ACL) e agente Windows de baixo privilégio.
- Suporte a transferência de arquivos binários após auditoria, mantendo bloqueio de exclusões.
