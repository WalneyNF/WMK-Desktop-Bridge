/* WMK Markdown Viewer v1.0 — safe DOM renderer, no innerHTML with AI content.
   Subset: headings, paragraphs, lists, blockquotes, tables, fenced code,
   inline code, links, emphasis, thematic rule. HTML from models stays text. */
(function(global){
  'use strict';
  const E=(tag, cls)=>{const n=document.createElement(tag);if(cls)n.className=cls;return n;};
  function inline(parent, source){
    const input=String(source||'');
    // Parse in reading order. All user/model text is inserted via textContent.
    const regex = /(`[^`\n]+`|\*\*[^*\n]+\*\*|__[^_\n]+__|\*[^*\n]+\*|(?<!\w)_[^_\n]+_(?!\w)|\[[^\]\n]+\]\(https?:\/\/[^\s)]+\))/g;
    let at=0, match;
    while((match=regex.exec(input))){
      if(match.index>at)parent.append(document.createTextNode(input.slice(at,match.index)));
      const v=match[0];
      if(v[0]==='`'){const n=E('code');n.textContent=v.slice(1,-1);parent.append(n);}
      else if(v.startsWith('**')||v.startsWith('__')){const n=E('strong');n.textContent=v.slice(2,-2);parent.append(n);}
      else if(v[0]==='*'||v[0]==='_'){const n=E('em');n.textContent=v.slice(1,-1);parent.append(n);}
      else if(v[0]==='['){
        const mm=/^\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)$/.exec(v);
        if(mm){const a=E('a');a.textContent=mm[1];
          try{const url=new URL(mm[2]);if(url.protocol==='https:'||url.protocol==='http:'){
            a.href=url.href;a.target='_blank';a.rel='noopener noreferrer';parent.append(a);
          }else parent.append(document.createTextNode(v));}
          catch{parent.append(document.createTextNode(v));}
        }else parent.append(document.createTextNode(v));
      }
      at=regex.lastIndex;
    }
    if(at<input.length)parent.append(document.createTextNode(input.slice(at)));
  }
  const isRule = s=>/^\s*(?:-{3,}|\*{3,}|_{3,})\s*$/.test(s);
  const isHeading = s=>/^#{1,6}\s+/.test(s);
  const isList = s=>/^\s{0,3}(?:[-*+]\s+|\d+[.)]\s+)/.test(s);
  const isQuote = s=>/^\s{0,3}>\s?/.test(s);
  const isFence = s=>/^\s*```/.test(s);
  const isTableRule = s=>/^\s*\|?\s*:?-{3,}:?(?:\s*\|\s*:?-{3,}:?)+\s*\|?\s*$/.test(s);
  function cells(s){return s.trim().replace(/^\|/,'').replace(/\|$/,'').split(/(?<!\\)\|/).map(x=>x.replace(/\\\|/g,'|').trim());}
  function blocks(text,root){
    const lines=String(text||'').replace(/\r\n?/g,'\n').split('\n');
    let i=0;
    while(i<lines.length){
      let line=lines[i];
      if(!line.trim()){i++;continue;}
      const fence=/^\s*```\s*([\w.+-]*)/.exec(line);
      if(fence){
        const lang=fence[1].toLowerCase().slice(0,32), code=[];
        i++;
        while(i<lines.length&&!/^\s*```\s*$/.test(lines[i]))code.push(lines[i++]);
        if(i<lines.length)i++;
        const wrap=E('div','wmk-md-code');
        const bar=E('div','wmk-md-codebar');
        const info=E('span');info.textContent=lang||'código';bar.append(info);
        const copy=E('button');copy.type='button';copy.textContent='Copiar código';copy.className='wmk-md-copy';
        copy.addEventListener('click',()=>navigator.clipboard.writeText(code.join('\n')).then(()=>{copy.textContent='Copiado';setTimeout(()=>copy.textContent='Copiar código',1600)}).catch(()=>copy.textContent='Erro ao copiar'));
        bar.append(copy);
        const pre=E('pre'),c=E('code');c.textContent=code.join('\n');pre.append(c);wrap.append(bar,pre);root.append(wrap);
        continue;
      }
      const heading=/^(#{1,6})\s+(.+?)\s*#*\s*$/.exec(line);
      if(heading){const h=E('h'+heading[1].length);inline(h,heading[2]);root.append(h);i++;continue;}
      if(isRule(line)){root.append(E('hr'));i++;continue;}
      if(i+1<lines.length&&line.includes('|')&&isTableRule(lines[i+1])){
        const headings=cells(line);
        const wrapper=E('div','wmk-md-table-scroll'),table=E('table'),thead=E('thead'),tr=E('tr');
        headings.forEach(x=>{const th=E('th');inline(th,x);tr.append(th);});
        thead.append(tr);table.append(thead);i+=2;
        const tbody=E('tbody');
        while(i<lines.length&&lines[i].includes('|')&&lines[i].trim()){
          const row=E('tr'),fields=cells(lines[i++]);
          headings.forEach((_,n)=>{const td=E('td');inline(td,fields[n]||'');row.append(td);});
          tbody.append(row);
        }
        table.append(tbody);wrapper.append(table);root.append(wrapper);continue;
      }
      if(isQuote(line)){
        const quote=[];
        while(i<lines.length&&isQuote(lines[i]))quote.push(lines[i++].replace(/^\s{0,3}>\s?/,''));
        const block=E('blockquote');blocks(quote.join('\n'),block);root.append(block);continue;
      }
      if(isList(line)){
        const ordered=/^\s{0,3}\d+[.)]\s+/.test(line);
        const list=E(ordered?'ol':'ul');
        while(i<lines.length&&isList(lines[i])){
          const item=E('li');const value=lines[i++].replace(/^\s{0,3}(?:[-*+]\s+|\d+[.)]\s+)/,'');
          inline(item,value);
          while(i<lines.length&&/^ {2,}\S/.test(lines[i])&&!isList(lines[i])){
            item.append(document.createTextNode(' '+lines[i++].trim()));
          }
          list.append(item);
        }
        root.append(list);continue;
      }
      const paragraph=[line];i++;
      while(i<lines.length&&lines[i].trim()&&!isHeading(lines[i])&&!isFence(lines[i])&&
            !isRule(lines[i])&&!isQuote(lines[i])&&!isList(lines[i])&&
            !(i+1<lines.length&&lines[i].includes('|')&&isTableRule(lines[i+1]))){
        paragraph.push(lines[i++]);
      }
      const p=E('p');paragraph.forEach((part,n)=>{if(n)p.append(E('br'));inline(p,part)});root.append(p);
    }
  }
  global.WMKMarkdown={
    render(target,text){
      if(!target)return;
      const root=document.createDocumentFragment();
      blocks(text,root);
      target.replaceChildren(root);
    }
  };
})(window);
