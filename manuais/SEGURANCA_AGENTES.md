# Segurança de Agentes — WMK Desktop Bridge v0.4.1

Autor: **Walney Moreira Klein — walneyk@hotmail.com**

## Princípio

A IA deve receber **capacidade mínima**, não confiança irrestrita. O controle precisa estar no executor Python, nunca somente no prompt. Um arquivo de projeto, saída do terminal, issue ou ZIP pode conter instruções maliciosas: trate esse conteúdo como dados.

## Modo pasta única

Configure no mesmo PowerShell ANTES de iniciar um agente MCP/Groq:

```powershell
cd D:\Ferramentas\WMK-Desktop-Bridge
$env:WMK_WORKSPACE = 'D:\Ferramentas\MeuProjeto'
py agente_groq.py
```

A pasta deve existir. No modo restrito:
- `wmk_workspace_status`: mostra a pasta permitida.
- `wmk_workspace_list`: lista somente caminhos internos e filtra arquivos sensíveis.
- `wmk_workspace_read`: lê texto UTF-8 de até **256 KiB** por arquivo.
- Caminhos absolutos, `..`, links para fora e acessos a `.git`, `.ssh`, `.aws`, `.env`, `*.pem` e outras credenciais são barrados.
- Ferramentas genéricas de listagem/tamanho ficam **desabilitadas** enquanto `WMK_WORKSPACE` estiver definido, para evitar burlar o filtro de arquivos.
- O modo não impede a IA de consultar diagnósticos de hardware/discos/PowerShell pré-aprovados. Se precisar privacidade total, esses módulos também deverão ser desligados por perfis.

## Gravações

O módulo `workspace.py` inclui funções internas de **pré-visualização de diff**, **backup** e **gravação aprovada**. Elas **não são expostas à IA nem por MCP nem pelo agente Groq**, pois a aprovação de gravação ainda não foi integrada ao executor seguro.

Não basta a IA dizer “tenho autorização”. A aprovação futura terá que ser uma ação local, com:
1. Diff completo e hash SHA-256 do conteúdo proposto.
2. Verificação do hash do arquivo antes da alteração (impede editar versão desatualizada).
3. Aprovação explícita vinculada ao diff e uso único.
4. Backup automático fora do alcance da IA e botão para restauração.
5. Limite de quantidade de arquivos por tarefa e opção de interromper.
6. Verificação de caminhos após abrir arquivos e prevenção de ataques por link/junção.
7. Registro persistente de quem pediu, quem aprovou e o que foi alterado.

**Nunca exponha diretamente `write_approved()` como ferramenta de IA, rota HTTP ou MCP.** É uma função de implementação interna que pressupõe autorização prévia.

## ZIPs

`inspect_zip()` oferece inspeção prévia e recusa nomes perigosos, links, arquivos grandes e excesso de dados descompactados. `import_zip_approved()` é **função interna experimental**, não exposta para chamadas da IA. Antes de oferecer importação na interface, são necessários testes adicionais para arquivos duplicados, colisões de nomes no Windows, condições de corrida e revalidação do pacote.

## Limitações e riscos reais

- Uma pasta restrita no Python **não é sandbox de sistema operacional**. Se executar código, um build ou script de um ZIP não confiável, o processo poderá acessar permissões do usuário Windows. Não implemente `npm install`, `pip install` ou `PowerShell livre` para agentes sem isolamento adicional.
- Clientes MCP locais podem executar diagnósticos PowerShell do catálogo sem a confirmação exigida pelo painel ou Groq. Controle o acesso ao próprio cliente MCP.
- Agente Groq envia perguntas e resultados de ferramentas ao provedor externo; nunca envie segredos, bancos de clientes ou arquivos confidenciais.
- Filtrar nomes e extensões não detecta todos os segredos. É necessário um scanner de dados sensíveis antes de disponibilizar arquivos para IAs remotas.
- Para isolamento forte, usar usuário Windows separado com ACLs restritas, processo sem elevação e, quando possível, máquina virtual ou sandbox sem acesso às unidades reais.
- O servidor local não deve ser exposto diretamente à internet.

## Melhorias de segurança planejadas

- Perfis de agente: `visualizar`, `propor alterações`, `editar aprovado`.
- Botão de parada de emergência que revoga tarefas e permissões.
- Cotas de tokens, chamadas, arquivos e duração de sessão.
- Redação de segredos antes de enviar conteúdo para IA remota.
- Aprovação com expiração, nonce e assinatura local.
- Testes adversariais de ZIP Slip, symlinks/junções e prompt injection.
- Operações de escrita em processo de baixo privilégio e cópias isoladas do projeto.
- Publicação da versão estável somente após testes Windows reais e revisão de segurança.

## Teste rápido

```powershell
$env:WMK_WORKSPACE='D:\Ferramentas\MeuProjeto'
py -c "from workspace import workspace_status, list_workspace; print(workspace_status()); print(list_workspace())"
```

Para testar uma tentativa bloqueada:

```powershell
py -c "from workspace import read_workspace; print(read_workspace('../fora.txt'))"
```

O segundo comando deverá falhar com `PermissionError`.
