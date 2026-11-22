/* WMK Code Studio — Assistente Groq/Ollama v0.7.6.
   Não grava arquivo. Propostas precisam de revisão e salvamento manual. */
(function () {
  const $ = id => document.getElementById(id);
  const aside = document.querySelector('main > aside:last-child');
  if (!aside) return;
  const top = document.createElement('section');
  top.style.cssText = 'padding:9px;display:grid;gap:7px;border-bottom:1px solid #36516a';
  top.innerHTML = `
    <strong>🤖 Assistente de programação</strong>
    <label for="ai-provider">Provedor</label>
    <select id="ai-provider"><option value="ollama">Ollama local</option><option value="groq">Groq (API)</option></select>
    <label for="ai-model">Modelo</label>
    <input id="ai-model" value="qwen3:1.7b" maxlength="90" autocomplete="off">
    <label for="ai-action">O que a IA deve fazer?</label>
    <select id="ai-action">
      <option value="explicar">Explicar o código</option>
      <option value="revisar">Revisar e sugerir melhorias</option>
      <option value="corrigir">Corrigir problemas</option>
      <option value="refatorar">Refatorar o arquivo</option>
      <option value="gerar">Gerar código a partir da descrição</option>
    </select>
    <textarea id="ai-instruction" rows="3" placeholder="Ex.: melhore os erros de validação e explique as mudanças"></textarea>
    <label style="font-size:12px"><input type="checkbox" id="ai-consent"> Autorizo enviar o texto do editor ao provedor escolhido nesta consulta.</label>
    <button type="button" id="ai-ask">Analisar arquivo com IA</button>
    <button type="button" id="ai-compare" disabled>Comparar sugestão lado a lado</button>
    <button type="button" id="ai-check">Verificar Groq / Ollama</button>
    <div id="ai-provider-state" class="muted">Clique em Verificar antes de testar uma análise.</div>
    <div id="ai-state" class="muted" role="status">A IA só recebe o conteúdo do editor; não recebe ferramentas de exclusão.</div>`;
  const title = aside.querySelector('.panel-title');
  title.insertAdjacentElement('afterend', top);
  const style = document.createElement('style');
  style.textContent = `
  #ai-provider,#ai-model,#ai-action,#ai-instruction{background:#0c1b2a;color:#e6f6fd;border:1px solid #355b75;border-radius:5px;padding:7px;max-width:100%;width:100%}
  #ai-instruction{resize:vertical;min-height:66px}#ai-state{overflow-wrap:anywhere}
  #ai-compare{background:#1b535c}
  #ai-diff-view{display:none;position:absolute;inset:0;background:#101d2a;z-index:5;flex-direction:column}
  #ai-diff-head{padding:8px;background:#1b3348;display:flex;gap:7px;align-items:center;flex-wrap:wrap}
  #ai-diff-editor{flex:1;min-height:0}
  #ai-diff-fallback{display:none;flex:1;overflow:auto;padding:12px;white-space:pre-wrap;font:12px Consolas,monospace}
  .editor-pane{position:relative}
  `;
  document.head.append(style);
  const overlay = document.createElement('div');
  overlay.id = 'ai-diff-view';
  overlay.innerHTML = '<div id="ai-diff-head"><b>Comparar: original ↔ proposta IA</b><button id="ai-apply">Colocar proposta no editor</button><button id="ai-back">Voltar sem aplicar</button></div><div id="ai-diff-editor"></div><pre id="ai-diff-fallback"></pre>';
  document.querySelector('.editor-pane').append(overlay);
  const oldTitle = aside.querySelectorAll('.panel-title')[1];
  if (oldTitle) oldTitle.textContent = '💡 Resposta da IA (sem salvar)';
  $('suggestion').placeholder = 'A resposta do Groq/Ollama aparecerá aqui. O código proposto poderá ser comparado antes de entrar no editor.';
  let proposal = null, comparison = null, diffModelA = null, diffModelB = null;
  const setState = value => { $('ai-state').textContent = value; };
  async function checkProvider(){
    $('ai-provider-state').textContent = 'Verificando configurações do servidor...';
    try{
      const response = await fetch('/api/ai/status',{cache:'no-store'});
      const result = await response.json();
      if(!response.ok)throw Error(result.erro || 'HTTP '+response.status);
      const groq = result.groq_configurado ? 'Chave configurada no servidor' : 'SEM CHAVE no servidor Python';
      const ollama = result.ollama_online ? 'Online' : 'Offline';
      const models = (result.ollama_modelos||[]).slice(0,12).join(', ');
      $('ai-provider-state').textContent = 'Groq: '+groq+' | Ollama: '+ollama+
        (models?' | Modelos: '+models:'');
      if($('ai-provider').value==='groq'&&!result.groq_configurado)
        setState('Groq não está configurado. Defina GROQ_API_KEY e reinicie web_server.py (ou use iniciar-com-chaves.ps1).');
      if($('ai-provider').value==='ollama'&&!result.ollama_online)
        setState('Ollama offline. Execute ollama serve ou abra o aplicativo Ollama.');
    }catch(e){$('ai-provider-state').textContent = 'Falha no diagnóstico: '+e.message;}
  }
  $('ai-provider').addEventListener('change', () => {
    $('ai-model').value = $('ai-provider').value === 'groq' ? 'openai/gpt-oss-20b' : 'qwen3:1.7b';
    $('ai-consent').checked = false;
    checkProvider();
  });
  async function ask() {
    if (!currentPath) return setState('Abra um arquivo ou prepare um novo arquivo primeiro.');
    if (!$('ai-consent').checked) return setState('Marque a autorização para esta consulta.');
    const provider = $('ai-provider').value, model = $('ai-model').value.trim();
    const action = $('ai-action').value, instruction = $('ai-instruction').value.trim();
    const code = getText(), path = currentPath, sha = expectedSha;
    if (!model) return setState('Informe o modelo.');
    if (provider === 'groq' && !window.confirm('O código do arquivo será enviado à API Groq. Confirma o envio desta consulta?')) return;
    if (provider === 'ollama' && !window.confirm('O código será enviado ao Ollama em 127.0.0.1:11434. Continuar?')) return;
    $('ai-ask').disabled = true;
    $('ai-compare').disabled = true;
    proposal = null;
    setState('Consultando ' + provider + ' / ' + model + ' ...');
    try {
      const response = await fetch('/api/ai/suggest', {
        method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({provider,model,action,instruction,code,path,consent:true})
      });
      const answer = await response.json();
      if (!response.ok) throw Error(answer.erro || 'HTTP ' + response.status);
      $('suggestion').value = answer.explicacao || '(Sem explicação do modelo.)';
      if (typeof answer.codigo === 'string' && ['corrigir','refatorar','gerar'].includes(action)) {
        proposal = {path,sha,code,proposed:answer.codigo};
        $('ai-compare').disabled = false;
        setState('Sugestão recebida. Compare com seu código antes de aplicar.');
      } else {
        setState('Análise recebida. Nenhuma alteração foi proposta.');
      }
    } catch (err) {
      $('suggestion').value = 'Falha na consulta '+provider+' / '+model+': '+err.message;
      setState('ERRO AO ANALISAR: '+err.message+' | Use Verificar Groq / Ollama para diagnosticar.');
    } finally {
      $('ai-consent').checked = false;
      $('ai-ask').disabled = false;
    }
  }
  function closeCompare() {
    overlay.style.display = 'none';
    if (comparison) {
      comparison.dispose();
      comparison = null;
      if (diffModelA) diffModelA.dispose();
      if (diffModelB) diffModelB.dispose();
      diffModelA = diffModelB = null;
    }
  }
  function compare() {
    if (!proposal) return setState('Nenhuma sugestão disponível.');
    if (currentPath !== proposal.path || expectedSha !== proposal.sha || getText() !== proposal.code) {
      return setState('O arquivo mudou desde a análise. Peça uma nova sugestão.');
    }
    overlay.style.display = 'flex';
    if (window.monaco && monaco.editor && monacoEditor) {
      const lang = monacoEditor.getModel().getLanguageId();
      diffModelA = monaco.editor.createModel(proposal.code,lang);
      diffModelB = monaco.editor.createModel(proposal.proposed,lang);
      comparison = monaco.editor.createDiffEditor($('ai-diff-editor'), {
        theme:'vs-dark',readOnly:true,originalEditable:false,automaticLayout:true,
        renderSideBySide:true,enableSplitViewResizing:true,minimap:{enabled:false}
      });
      comparison.setModel({original:diffModelA,modified:diffModelB});
    } else {
      $('ai-diff-fallback').style.display='block';
      $('ai-diff-fallback').textContent='ORIGINAL:\n'+proposal.code+'\n\nPROPOSTA:\n'+proposal.proposed;
    }
  }
  function apply() {
    if (!proposal || currentPath!==proposal.path || expectedSha!==proposal.sha || getText()!==proposal.code) {
      closeCompare();
      return setState('Conteúdo mudou: proposta antiga recusada.');
    }
    const text = proposal.proposed;
    closeCompare();
    setText(text, currentPath);
    $('state').textContent = currentPath + ' ●';
    setState('Proposta colocada no editor, NÃO SALVA. Clique em Comparar e Salvar após revisão quando concordar.');
    feedback('IA não salvou o arquivo. Revise o diff e confirme manualmente.');
    proposal = null; $('ai-compare').disabled = true;
  }
  $('ai-ask').onclick = ask;
  $('ai-check').onclick = checkProvider;
  checkProvider();
  $('ai-compare').onclick = compare;
  $('ai-back').onclick = closeCompare;
  $('ai-apply').onclick = apply;
})();
