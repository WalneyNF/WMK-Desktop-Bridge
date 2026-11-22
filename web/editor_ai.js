/* WMK Code Studio — Assistente Groq/Ollama v0.7.9.
   Não grava arquivo. Propostas precisam de revisão e salvamento manual. */
(function () {
  const $ = id => document.getElementById(id);
  const aside = document.getElementById('ai-sidebar');
  if (!aside) return;
  const top = document.createElement('section');
  top.style.cssText = 'display:grid;gap:7px';
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
    <button type="button" id="ai-config-key">🔑 Configurar chave Groq no Windows</button>
    <div id="ai-key-box" style="display:none;border:1px solid #39657b;padding:8px;border-radius:6px">
      <label for="ai-key-value">Cole sua chave Groq (será salva criptografada por DPAPI)</label>
      <input id="ai-key-value" type="password" autocomplete="off" spellcheck="false" placeholder="gsk_...">
      <button type="button" id="ai-key-save">Salvar chave protegida</button>
      <small>Somente no seu computador. Nunca incluída no projeto, no GitHub ou no histórico do chat.</small>
    </div>
    <button type="button" id="ai-check">Verificar configuração</button>
    <button type="button" id="ai-ping">Testar resposta do provedor (sem arquivo)</button>
`;
  $('ai-settings-content').appendChild(top);
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
  let responseText = '';
  const output = $('ai-output');
  function showResponse(text, state='done', title='Resposta recebida'){
    responseText = text || '';
    output.textContent = responseText || '(O modelo não retornou texto.)';
    output.dataset.state = state;
    $('ai-output-title').textContent = title;
  }
  $('ai-copy-output').onclick = async ()=>{
    if(!responseText)return setState('Nenhuma resposta para copiar.');
    try{await navigator.clipboard.writeText(responseText);setState('Resposta copiada.')}
    catch(e){setState('Falha ao copiar: '+e.message)}
  };
  $('ai-clear-output').onclick = ()=>{
    responseText='';
    showResponse('Abra um arquivo, configure uma IA e solicite a análise.', 'empty','Sem análise');
    $('ai-meta').textContent = 'Nenhuma análise recebida';
  };
  $('ai-open-settings').onclick = ()=>{
    $('ai-settings').open = !$('ai-settings').open;
    if($('ai-settings').open)$('ai-settings').scrollIntoView({block:'nearest'});
  };
  // O divisor só ajusta a coluna da resposta, sem deslocar o código Monaco.
  const root = document.querySelector('main');
  const handle = $('ai-resize-handle');
  const storageKey = 'wmk-code-studio-ai-width-v1';
  const stored = Number(localStorage.getItem(storageKey));
  if(Number.isFinite(stored) && stored>=320 && stored<=900)
    root.style.setProperty('--wmk-ai-width', stored+'px');
  handle.addEventListener('pointerdown', e=>{
    if(e.button!==0 || window.matchMedia('(max-width:1050px)').matches)return;
    e.preventDefault();
    handle.setPointerCapture(e.pointerId);
    const initial=e.clientX;
    const initialWidth=aside.getBoundingClientRect().width;
    const onMove=ev=>{
      const max=Math.max(320,root.clientWidth-520);
      const width=Math.round(Math.max(320,Math.min(max,initialWidth+initial-ev.clientX)));
      root.style.setProperty('--wmk-ai-width',width+'px');
    };
    const onEnd=()=>{
      handle.removeEventListener('pointermove',onMove);
      handle.removeEventListener('pointerup',onEnd);
      const width=Math.round(aside.getBoundingClientRect().width);
      localStorage.setItem(storageKey,String(width));
    };
    handle.addEventListener('pointermove',onMove);
    handle.addEventListener('pointerup',onEnd,{once:true});
  });
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
    showResponse('Consultando o modelo. A resposta será exibida neste painel.', 'loading', 'Analisando...');
    $('ai-meta').textContent = path+' · '+provider+' / '+model+' · '+action;
    try {
      const response = await fetch('/api/ai/suggest', {
        method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({provider,model,action,instruction,code,path,consent:true})
      });
      const answer = await response.json();
      if (!response.ok) throw Error(answer.erro || 'HTTP ' + response.status);
      showResponse(answer.explicacao || '(Sem explicação do modelo.)', 'done', 'Análise concluída');
      $('ai-meta').textContent = path+' · '+provider+' / '+model+' · '+action;
      if (typeof answer.codigo === 'string' && ['corrigir','refatorar','gerar'].includes(action)) {
        proposal = {path,sha,code,proposed:answer.codigo};
        $('ai-compare').disabled = false;
        setState('Código proposto. Clique em Comparar sugestão lado a lado, nas configurações.');
      } else {
        setState('Análise recebida. O texto completo está ao lado do Monaco.');
      }
    } catch (err) {
      showResponse('Falha na consulta '+provider+' / '+model+': '+err.message, 'error','Falha na análise');
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
  async function pingProvider(){
    const provider=$('ai-provider').value, model=$('ai-model').value.trim();
    if(!model)return setState('Informe o nome do modelo.');
    if(!confirm('Enviar apenas a frase de teste ao '+provider+' / '+model+'? Nenhum arquivo será enviado.'))return;
    $('ai-ping').disabled=true;
    setState('Testando resposta do '+provider+' ...');
    try{
      const response=await fetch('/api/ai/test',{
        method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({provider,model,consent:true})
      });
      const data=await response.json();
      if(!response.ok)throw Error(data.erro || 'HTTP '+response.status);
      setState('Conexão FUNCIONOU: '+data.provedor+' / '+data.modelo+' respondeu: '+data.resposta);
    }catch(e){
      setState('Teste falhou: '+e.message);
    }finally{$('ai-ping').disabled=false;}
  }
  $('ai-config-key').onclick=()=>{
    const box=$('ai-key-box');
    box.style.display = box.style.display==='none' ? 'grid' : 'none';
  };
  $('ai-key-save').onclick=async()=>{
    const value=$('ai-key-value').value.trim();
    if(value.length<16)return setState('Informe sua chave Groq completa no campo protegido.');
    $('ai-key-save').disabled=true;
    try{
      const response=await fetch('/api/credentials/save',{
        method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({name:'GROQ_API_KEY',value})
      });
      const data=await response.json();
      if(!response.ok)throw Error(data.erro||('HTTP '+response.status));
      $('ai-key-value').value='';
      $('ai-key-box').style.display='none';
      setState('Chave Groq protegida no Windows. Agora use Testar resposta do provedor.');
      await checkProvider();
    }catch(e){setState('Não foi possível configurar Groq: '+e.message)}
    finally{$('ai-key-save').disabled=false}
  };
  $('ai-ask').onclick = ask;
  $('ai-ping').onclick = pingProvider;
  $('ai-check').onclick = checkProvider;
  checkProvider();
  $('ai-settings').open = true;
  $('ai-compare').onclick = compare;
  $('ai-back').onclick = closeCompare;
  $('ai-apply').onclick = apply;
})();
