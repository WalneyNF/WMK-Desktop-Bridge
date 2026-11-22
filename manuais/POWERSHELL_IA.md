# PowerShell controlado por IA — WMK Desktop Bridge v0.4.0

**Autor:** Walney Moreira Klein — walneyk@hotmail.com  
**Licença:** MIT (consulte `LICENSE`)

## Objetivo
Permitir que agentes MCP e o exemplo Groq solicitem diagnósticos do Windows sem receber acesso a um terminal PowerShell irrestrito.

## O que funciona agora
- Painel móvel **PowerShell (diagnóstico)** no navegador local.
- Catálogo de **seis ações fixas** (`powershell_tools.py`).
- Cada execução iniciada pelo painel exige confirmação do usuário.
- No agente Groq, a execução de diagnóstico exige resposta `s` ou `sim` no terminal.
- No MCP, duas ferramentas: `wmk_powershell_catalog` e `wmk_powershell_diagnose`.
- Timeout de 20 segundos e registros locais em `logs/powershell-audit.jsonl`.

## Catálogo
| Identificador | Descrição |
| --- | --- |
| `versao_powershell` | Consulta versão do PowerShell |
| `processos` | Mostra até 15 processos com maior uso de RAM |
| `servicos_parados` | Mostra até 25 serviços parados |
| `unidades` | Consulta capacidade e espaço livre em discos |
| `rede` | Mostra interfaces conectadas sem IP ou MAC |
| `tempo_atividade` | Última inicialização do Windows |

## Atualizar
```powershell
cd D:\Ferramentas\WMK-Desktop-Bridge
git pull
py web_server.py
```

Abra `http://127.0.0.1:8767/`, pressione `Ctrl+F5`, selecione uma ação no painel **PowerShell (diagnóstico)** e confirme.

## Teste com Groq
```powershell
$env:GROQ_API_KEY = 'SUA_CHAVE'
$env:GROQ_MODEL = 'openai/gpt-oss-20b'
py agente_groq.py
```
Pergunte: **Quais são os 15 processos que mais consomem memória RAM?**. O agente poderá escolher `wmk_powershell_diagnose` e deverá solicitar confirmação no terminal.

**Privacidade:** perguntas e resultados das ferramentas podem ser enviados ao Groq. Não use em computadores ou dados de terceiros sem autorização.

## Limitações de segurança
- Os scripts são pré-definidos; o modelo não pode inserir código PowerShell na ação.
- Não há exclusão de arquivos, alteração de serviços, instalação de programas ou execução arbitrária.
- Clientes **MCP externos podem chamar diretamente** as ferramentas; eles não passam pela confirmação do painel nem do agente Groq. Configure apenas clientes confiáveis.
- O agente local não é um sandbox contra programas maliciosos no mesmo usuário.
- Não execute como administrador sem necessidade; não exponha portas locais à internet.
- Logs registram ações e resultados, não a saída completa. Consulte-os localmente.

## Roadmap técnico proposto
1. Aprovações centralizadas no agente local, inclusive para chamadas MCP, com tokens de uso único.
2. Perfis de permissão (`somente leitura`, `diagnósticos`, `manutenção assistida`) por cliente/agente.
3. Explorador de processos, serviços, tarefas agendadas e inicialização do Windows.
4. Análise de disco e cache com pré-visualização de espaço a recuperar.
5. Operações de escrita transacionais com simulação, backup e recuperação.
6. Conexão remota autenticada (TLS, autorização e auditoria), jamais túnel aberto com PowerShell irrestrito.
7. Testes de integração no Windows e automatizados para políticas de segurança.

**Situação:** código publicado, mas os testes executados diretamente no Windows de usuários ainda são necessários.
