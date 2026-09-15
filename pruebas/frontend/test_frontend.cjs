// Todos los datos de esta suite son sintéticos. Ejecutar: node --test pruebas/frontend/test_frontend.cjs
const {test} = require('node:test');
const assert = require('node:assert/strict');
const {ApiClient, Frontend, buildPlots, drawPlot, formatNumber} = require('../../app/web/app.js');

class Element {
  constructor(tag = 'div') { this.tagName = tag; this.children = []; this.dataset = {}; this.listeners = {}; this.value = ''; this.textContent = ''; this.hidden = false; this.disabled = false; this.attributes = {}; this.style = {}; this.classList = {toggle() {}}; }
  addEventListener(type, fn) { (this.listeners[type] ||= []).push(fn); }
  async fire(type) { if (this.disabled) return; for (const fn of this.listeners[type] || []) await fn({preventDefault() {}, target:this}); }
  setAttribute(k,v) { this.attributes[k] = String(v); }
  removeAttribute(k) { delete this.attributes[k]; }
  append(...items) { this.children.push(...items); }
  replaceChildren(...items) { this.children = items; }
  focus() {}
  reportValidity() { return true; }
  getBoundingClientRect() { return {width:600,height:310}; }
}
function documentDouble() {
  const elements = new Map();
  const nav = ['live','static','dynamic','config'].map(id => {const el=new Element('button'); el.dataset.tab=id; return el;});
  const png = ['liveChart','fitChart','baChart','transChart','stepChart','impChart','magChart','phaseChart'].map(id=>{const el=new Element('button');el.dataset.canvas=id; return el;});
  return {elements, nav, png, activeElement:null, getElementById(id) {if(!elements.has(id)) elements.set(id,new Element()); return elements.get(id);}, createElement(tag) {return new Element(tag);}, querySelectorAll(query) {return query==='[data-tab]'? nav : query==='[data-canvas]'?png:[];}};
}
function state(overrides={}) {
  return {session_id:'sintetica-1',mode:'demo',running:false,connection:{esp32:'disconnected',vernier:'disconnected'},samples:[],points:[],static_result:null,dynamic_result:null,error:null,config:{mode:'demo',port:'',baudrate:115200,sample_interval:0.5,vernier_connection:'usb',vernier_device_name:'',vernier_channel:null,demo_initial_c:25,demo_target_c:25},dynamic:{active:false,x0:null,xf:null,t0:null,samples:[]},stability:{ready:false,reason:'Faltan muestras',n:0,window_seconds:5},static_progress:{count:0,span_c:0,incremental:true,meets_goal:false},...overrides};
}
const running = () => state({running:true,connection:{esp32:'simulated',vernier:'simulated'},samples:[{t:1,vernier:25,lm35:25.1}],stability:{ready:true,reason:'Ventana estable',n:6,window_seconds:5}});
function fixture(initial=state()) {
  const doc=documentDouble(), calls=[], downloads=[], plots=[];
  let current=initial, failure=null;
  const api={async request(path,options={}) {calls.push({path,...options}); if(failure) throw failure; if(path==='/api/ports') return {ports:['COM7','COM12']}; if(path==='/api/export'||path==='/api/results') return new Blob(['datos sintéticos']); return current;}};
  const app=new Frontend({document:doc,api,plot:(canvas,spec)=>plots.push({id:canvas.id,spec}),download:(blob,name)=>downloads.push({blob,name}),setTimeout:()=>1,clearTimeout:()=>{}});
  app.bind(); app.accept(initial); app.render();
  return {app,doc,calls,downloads,plots,setState(s){current=s;},fail(e){failure=e;}};
}
test('estado vacío no presenta temperaturas, permite configuración y distingue null de cero',()=>{
  const {doc}=fixture();
  assert.equal(doc.getElementById('temperature-lm35').textContent,'—');
  assert.equal(doc.getElementById('point').disabled,true);
  assert.equal(doc.getElementById('start').disabled,false);
  assert.equal(formatNumber(null),'—'); assert.equal(formatNumber(0),'0.00');
});
test('eventos de inicio/detención usan POST y estado confirmado, no alternan solo texto',async()=>{
  const f=fixture(); f.setState(running()); await f.doc.getElementById('start').fire('click');
  assert.deepEqual(f.calls[0],{path:'/api/start',method:'POST',body:{}});
  assert.equal(f.doc.getElementById('start').disabled,true);
  f.setState(state()); await f.doc.getElementById('stop').fire('click');
  assert.equal(f.calls[1].path,'/api/stop'); assert.equal(f.app.state.running,false);
});
test('punto estable rechazado muestra error y no aumenta contador',async()=>{
  const f=fixture(running());f.fail(new Error('Se necesitan 5 muestras nuevas'));
  await f.doc.getElementById('point').fire('click');
  assert.equal(f.calls[0].path,'/api/point');
  assert.match(f.doc.getElementById('error').textContent,/5 muestras nuevas/);
  assert.equal(f.app.state.points.length,0);
});
test('configuración real envía campos explícitos y puertos se cargan sin COM4 inventado',async()=>{
  const f=fixture(); await f.doc.getElementById('refresh-ports').fire('click');
  assert.deepEqual(f.doc.getElementById('port').children.map(c=>c.value),['','COM7','COM12']);
  for(const [id,value] of Object.entries({mode:'real',port:'COM7',baudrate:'115200','sample-interval':'0.5','vernier-connection':'usb','vernier-device-name':'GDX confirmado','vernier-channel':'3','demo-initial':'25'})) f.doc.getElementById(id).value=value;
  await f.doc.getElementById('config-form').fire('submit');
  assert.deepEqual(f.calls.at(-1),{path:'/api/config',method:'POST',body:{mode:'real',port:'COM7',baudrate:115200,sample_interval:0.5,vernier_connection:'usb',vernier_device_name:'GDX confirmado',vernier_channel:3,demo_initial_c:25}});
});
test('objetivo demo usa actualización parcial durante adquisición',async()=>{
  const f=fixture(running());f.doc.getElementById('demo-target').value='65';
  await f.doc.getElementById('demo-form').fire('submit');
  assert.deepEqual(f.calls[0],{path:'/api/config',method:'POST',body:{demo_target_c:65}});
});
test('inicio y fin dinámicos envían entradas declaradas y no calculan resultados locales',async()=>{
  const f=fixture(running());f.doc.getElementById('x0').value='25';f.doc.getElementById('xf').value='70';
  const active=running();active.dynamic={active:true,x0:25,xf:70,t0:1,samples:[]};f.setState(active);
  await f.doc.getElementById('dynamic-form').fire('submit');
  assert.deepEqual(f.calls[0],{path:'/api/dynamic/start',method:'POST',body:{x0:25,xf:70}});
  assert.equal(f.app.state.dynamic.active,true);
  f.setState(running());await f.doc.getElementById('dynamic-finish').fire('click');
  assert.equal(f.calls[1].path,'/api/dynamic/finish');assert.equal(f.app.state.dynamic_result,null);
});
test('descargas CSV y JSON pasan por API y reset envía POST',async()=>{
  const f=fixture(); await f.doc.getElementById('export-csv').fire('click');await f.doc.getElementById('export-json').fire('click');
  assert.deepEqual(f.calls.map(c=>c.path),['/api/export','/api/results']);
  assert.match(f.downloads[0].name,/\.csv$/);assert.match(f.downloads[1].name,/\.json$/);
  f.setState(state({session_id:'sintetica-2'}));await f.doc.getElementById('reset').fire('click');
  assert.equal(f.calls.at(-1).path,'/api/reset');assert.equal(f.app.state.session_id,'sintetica-2');
});
test('503 real no cambia modo ni muestra muestra retenida como actual',async()=>{
  const f=fixture(state({mode:'real',running:false,error:'Sensor desconectado',samples:[{t:4,vernier:50,lm35:51}],connection:{esp32:'error',vernier:'disconnected'}}));
  assert.equal(f.doc.getElementById('temperature-lm35').textContent,'—');
  f.fail(new Error('503: dependencia no disponible'));await f.doc.getElementById('start').fire('click');
  assert.equal(f.app.state.mode,'real');assert.match(f.doc.getElementById('error').textContent,/503/);
  assert.equal(f.calls.length,1);
});
test('sondeo anterior a reset no restaura sesión vieja y no se solapan sondeos',async()=>{
  const f=fixture();let resolve;let reads=0;
  f.app.api.request=async(path)=>{if(path==='/api/state'){reads++;return new Promise(r=>resolve=r);}return state({session_id:'nueva'});};
  const poll=f.app.poll();await f.app.poll();assert.equal(reads,1);
  await f.doc.getElementById('reset').fire('click');resolve(state());await poll;
  assert.equal(f.app.state.session_id,'nueva');
});
test('doble acción no duplica POST mientras servidor responde',async()=>{
  const f=fixture();let resolve;
  f.app.api.request=(path,options)=>{f.calls.push({path,...options});return new Promise(r=>resolve=r);};
  const first=f.app.mutate('/api/start');const second=f.app.mutate('/api/start');
  assert.equal(f.calls.length,1);resolve(running());await Promise.all([first,second]);
});
test('fallo de sondeo marca historial y conserva formulario que se está editando',async()=>{
  const f=fixture(running());f.doc.getElementById('demo-target').value='82';
  f.fail(new Error('Sin respuesta'));await f.app.poll();
  assert.equal(f.doc.getElementById('temperature-vernier').textContent,'—');
  assert.match(f.doc.getElementById('data-status').textContent,/Sin comunicación/);
  assert.equal(f.doc.getElementById('demo-target').value,'82');
});
test('series estáticas y dinámicas usan backend incluso con valores no habituales',()=>{
  const s=running();s.points=[{index:1,vernier:20,lm35:22,precision:{n:6,media:22,s:0,s_m:0,rsd:null,cv:null,varianza:0}}];
  s.static_result={m:-2,b:3,r:-1,e_g:-3,e_0:3,sigma_p:0,intervalos:{k1:0,k2:0,k3:0},curva_ajuste:{x:[20,40],y:[91,92]},bland_altman:{medias:[21,30],diferencias:[2,3],sesgo:7,limite_inferior:-8,limite_superior:9}};
  s.dynamic={active:false,x0:25,xf:70,t0:100,samples:[{t:100,vernier:25,lm35:28},{t:107,vernier:70,lm35:54}]};
  const curve={x:[0,7],y:[101,103]};s.dynamic_result={k:0.8,tau:7,t0:100,y0:28,yf:71,nivel_tau:54,fraccion_tau:0.63212,curvas:{escalon:curve,impulso:curve,magnitud:{x:[.1,1],y:[9,8]},fase:{x:[.1,1],y:[-33,-44]}}};
  const plots=buildPlots(s);
  assert.deepEqual(plots.fitChart.series[1].points,[[20,91],[40,92]]);
  assert.equal(plots.baChart.series[0].kind,'scatter');assert.deepEqual(plots.baChart.horizontal.map(l=>l.value),[7,-8,9]);
  assert.deepEqual(plots.transChart.marker,{x:107,y:54,label:'τ = 7.00 s'});
  assert.deepEqual(plots.stepChart.series[0].points,[[0,101],[7,103]]);
  assert.deepEqual(plots.magChart.series[0].points,[[.1,9],[1,8]]);assert.equal(plots.magChart.logX,true);
  const f=fixture(s);assert.equal(f.doc.getElementById('metric-r').textContent,'-1.0000');assert.equal(f.doc.getElementById('precision-cv').textContent,'—');
});
test('canvas dibuja dispersión, curvas constantes y vacías sin coordenadas no finitas',()=>{
  const coordinates=[], ctx=new Proxy({measureText:t=>({width:t.length*6})},{get(obj,key){if(key in obj)return obj[key];return(...args)=>{coordinates.push(...args.filter(v=>typeof v==='number'));};},set(obj,key,value){obj[key]=value;return true;}});
  const canvas=new Element('canvas');canvas.getContext=()=>ctx;
  drawPlot(canvas,{series:[{kind:'scatter',points:[[2,3],[2,3]],color:'#d92f83'}],xlabel:'x',ylabel:'y'});
  drawPlot(canvas,{series:[],xlabel:'x',ylabel:'y'});
  drawPlot(canvas,{series:[{points:[[.1,-20],[1,-40]]}],logX:true,xlabel:'ω [rad/s]',ylabel:'fase [°]'});
  assert.ok(coordinates.length>20);assert.ok(coordinates.every(Number.isFinite));
});
test('navegación y PNG operan sobre panel y canvas existentes',async()=>{
  const f=fixture(running());await f.doc.nav[2].fire('click');
  assert.equal(f.doc.getElementById('dynamic').hidden,false);assert.equal(f.doc.getElementById('live').hidden,true);
  const canvas=f.doc.getElementById('transChart');canvas.toBlob=fn=>fn(new Blob(['png'],{type:'image/png'}));
  await f.doc.png.find(b=>b.dataset.canvas==='transChart').fire('click');
  assert.match(f.downloads[0].name,/transChart.*\.png$/);
});
test('ApiClient interpreta errores HTTP y descarga cuerpo solo en éxito',async()=>{
  const api=new ApiClient(async()=>new Response(JSON.stringify({error:'Sin meseta'}),{status:409,headers:{'Content-Type':'application/json'}}));
  await assert.rejects(()=>api.request('/api/dynamic/finish',{method:'POST',body:{}}),/Sin meseta/);
  await assert.rejects(()=>api.request('/api/export',{blob:true}),/Sin meseta/);
  const calls=[];const ok=new ApiClient(async(url,options)=>{calls.push({url,options});return new Response('session_id,mode,t,vernier,lm35\n');});
  const blob=await ok.request('/api/export',{blob:true});assert.match(await blob.text(),/session_id/);assert.equal(calls[0].url,'/api/export');
});

test('progreso, métricas y tabla reflejan el resultado recibido',()=>{
  const s=running();s.static_progress={count:2,span_c:50,incremental:true,meets_goal:false};
  s.points=[{index:1,vernier:25,lm35:26,precision:{n:6,media:26,s:.1,s_m:.04,rsd:.004,cv:.4,varianza:.01}},{index:2,vernier:75,lm35:76,precision:{n:7,media:76,s:.2,s_m:.08,rsd:.003,cv:.3,varianza:.04}}];
  s.static_result={m:1,b:1,r:1,e_g:0,e_0:1,sigma_p:0,intervalos:{k1:0,k2:0,k3:0},bland_altman:{sesgo:1,limite_inferior:1,limite_superior:1}};
  const f=fixture(s);
  assert.equal(f.doc.getElementById('progress').textContent,'2 / 20 mediciones');
  assert.equal(f.doc.getElementById('span').textContent,'50.00');
  assert.equal(f.doc.getElementById('metric-sigma').textContent,'0.00');
  assert.equal(f.doc.getElementById('metric-eg').textContent,'0.00');
  assert.equal(f.doc.getElementById('points-body').children.length,2);
  assert.equal(f.doc.getElementById('precision-mean').textContent,'76.00');
});

test('curva dinámica y mediciones comparten tiempo de sesión',()=>{
  const s=running();s.dynamic={samples:[{t:100,lm35:25},{t:107,lm35:50}]};
  s.dynamic_result={t0:100,tau:7,nivel_tau:50,curvas:{escalon:{x:[0,7],y:[25,50]}}};
  const p=buildPlots(s);
  assert.deepEqual(p.transChart.series[0].points,p.transChart.series[1].points);
  assert.equal(p.transChart.marker.x,107);
  assert.deepEqual(p.stepChart.series[0].points,[[0,25],[7,50]]);
});

test('error de acción permanece visible después del sondeo',async()=>{
  const f=fixture(running());f.fail(new Error('meseta final inestable'));
  await f.app.mutate('/api/dynamic/finish');f.fail(null);await f.app.poll();
  assert.match(f.doc.getElementById('error').textContent,/meseta final inestable/);
});

test('recarga repone configuración guardada sin borrar edición al sondear',async()=>{
  const s=state();s.config.demo_target_c=65;s.config.vernier_channel=0;
  const f=fixture(s);
  assert.equal(f.doc.getElementById('demo-target').value,'65');
  assert.equal(f.doc.getElementById('vernier-channel').value,'0');
  f.doc.getElementById('demo-target').value='72';await f.app.poll();
  assert.equal(f.doc.getElementById('demo-target').value,'72');
});
