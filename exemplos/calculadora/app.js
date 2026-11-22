'use strict';
// WMK Calculator — exemplo sem eval() e sem dependências.
const display = document.querySelector('#display');
let current = '0';
let previous = null;
let operator = null;
let shouldReset = false;
function format(value) {
  if (!Number.isFinite(value)) return 'Erro';
  return String(Number(value.toPrecision(12)));
}
function render(){display.textContent = current.replace('.', ',');}
function digit(value){
  if (current === 'Erro' || shouldReset) {current='0'; shouldReset=false;}
  if (current.replace(/[^0-9]/g,'').length >= 13) return;
  current = current==='0' ? value : current+value;
  render();
}
function decimal(){
  if(current==='Erro'||shouldReset){current='0';shouldReset=false;}
  if(!current.includes('.')) current+='.';
  render();
}
function clear(){current='0';previous=null;operator=null;shouldReset=false;render();}
function backspace(){
  if(shouldReset || current==='Erro'){current='0';shouldReset=false;}
  else current=current.length<=1 || (current.length===2&&current[0]==='-') ? '0' : current.slice(0,-1);
  render();
}
function compute(a,b,op){
  if(op==='+')return a+b;
  if(op==='-')return a-b;
  if(op==='*')return a*b;
  if(op==='/')return b===0?NaN:a/b;
  return b;
}
function operation(op){
  const number=Number(current);
  if(!Number.isFinite(number)) return;
  if(operator && previous!==null && !shouldReset){
    current=format(compute(previous,number,operator));
    if(current==='Erro'){previous=null;operator=null;render();return;}
  }
  previous=Number(current);operator=op;shouldReset=true;render();
}
function equals(){
  if(operator===null || previous===null||shouldReset) return;
  current=format(compute(previous,Number(current),operator));
  previous=null;operator=null;shouldReset=true;render();
}
function action(name){
  if(name==='clear')return clear();
  if(name==='backspace')return backspace();
  if(name==='decimal')return decimal();
  if(current==='Erro')return;
  if(name==='percent')current=format(Number(current)/100);
  if(name==='sign')current=format(-Number(current));
  render();
}
document.querySelector('.keys').addEventListener('click',event=>{
  const button=event.target.closest('button');
  if(!button)return;
  if(button.dataset.digit!==undefined)digit(button.dataset.digit);
  else if(button.dataset.op)operation(button.dataset.op);
  else if(button.dataset.action==='equals')equals();
  else if(button.dataset.action)action(button.dataset.action);
});
document.addEventListener('keydown',event=>{
  if(event.ctrlKey||event.altKey||event.metaKey)return;
  const key=event.key;
  if(/^\d$/.test(key))digit(key);
  else if(key==='.'||key===',')decimal();
  else if(['+','-','*','/'].includes(key)){event.preventDefault();operation(key);}
  else if(key==='Enter'||key==='='){event.preventDefault();equals();}
  else if(key==='Backspace')backspace();
  else if(key==='Escape')clear();
});
render();
