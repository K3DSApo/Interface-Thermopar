(function(root,factory){
  if(typeof module==='object'&&module.exports) module.exports=factory();
  else root.LM35Frontend=factory();
})(typeof self!=='undefined'?self:this,function(){
  const finite=v=>typeof v==='number'&&Number.isFinite(v);
  function formatNumber(v){return finite(v)?v.toFixed(2):'—';}
  class ApiClient{
    constructor(fetchImpl){this.fetch=fetchImpl||(typeof fetch!=='undefined'?fetch.bind(globalThis):null);}
    async request(path,options={}){
      if(!this.fetch) throw new Error('Fetch no disponible');
      const opts={method:options.method||'GET',headers:{...(options.headers||{})}};
      if(options.body!==undefined){opts.headers['Content-Type']='application/json';opts.body=JSON.stringify(options.body);}
      const response=await this.fetch(path,opts);
      if(!response.ok){let msg='HTTP '+response.status;try{const j=await response.json();if(j&&j.error)msg=j.error;}catch{} throw new Error(msg);}
      if(options.blob)return response.blob();
      const type=response.headers&&response.headers.get?response.headers.get('content-type'):'';
      if(type&&type.includes('json'))return response.json();
      try{return await response.json();}catch{return response.text();}
    }
  }
  function pairs(curve){if(!curve)return []; if(Array.isArray(curve))return curve.filter(a=>Array.isArray(a)&&a.length>=2&&finite(a[0])&&finite(a[1])).map(a=>[a[0],a[1]]); const x=curve.x||[],y=curve.y||[];return x.map((v,i)=>[v,y[i]]).filter(a=>finite(a[0])&&finite(a[1]));}
  function buildPlots(state){
    const sr=state.static_result||{}, dr=state.dynamic_result||{}, ba=sr.bland_altman||{};
    const curves=dr.curvas||{}; const dynamicSamples=(state.dynamic&&state.dynamic.samples)||[];
    const exp=dynamicSamples.map(s=>[s.t,s.lm35]).filter(a=>finite(a[0])&&finite(a[1]));
    const step=pairs(curves.escalon), trans=step.map(([x,y])=>[x+(finite(dr.t0)?dr.t0:0),y]);
    const marker=dr.tau!=null?{x:finite(dr.t0)?dr.t0+dr.tau:dr.tau,y:dr.nivel_tau,label:'τ = '+Number(dr.tau).toFixed(2)+' s'}:null;
    return {
      liveChart:{xlabel:'Tiempo de sesión [s]',ylabel:'Temperatura [°C]',series:[{points:(state.samples||[]).map(s=>[s.t,s.vernier]).filter(a=>finite(a[0])&&finite(a[1])),color:'#d92f83'},{points:(state.samples||[]).map(s=>[s.t,s.lm35]).filter(a=>finite(a[0])&&finite(a[1])),color:'#8651bd'}]},
      fitChart:{xlabel:'Vernier [°C]',ylabel:'LM35 [°C]',series:[{kind:'scatter',points:(state.points||[]).map(p=>[p.vernier,p.lm35]).filter(a=>finite(a[0])&&finite(a[1])),color:'#d92f83'},{points:pairs(sr.curva_ajuste),color:'#8651bd'}]},
      baChart:{xlabel:'Media de ambos [°C]',ylabel:'LM35 − Vernier [°C]',series:[{kind:'scatter',points:(ba.medias||[]).map((x,i)=>[x,(ba.diferencias||[])[i]]).filter(a=>finite(a[0])&&finite(a[1])),color:'#d92f83'}],horizontal:[{value:ba.sesgo},{value:ba.limite_inferior},{value:ba.limite_superior}] .filter(l=>finite(l.value))},
      transChart:{xlabel:'Tiempo de sesión [s]',ylabel:'Temperatura [°C]',series:[{points:exp,color:'#d92f83'},{points:trans,color:'#8651bd'}],marker},
      stepChart:{xlabel:'Tiempo desde escalón [s]',ylabel:'Temperatura [°C]',series:[{points:step,color:'#d92f83'}]},impChart:{xlabel:'Tiempo desde escalón [s]',ylabel:'Respuesta [1/s]',series:[{points:pairs(curves.impulso),color:'#8651bd'}]},
      magChart:{xlabel:'ω [rad/s]',ylabel:'Magnitud',series:[{points:pairs(curves.magnitud),color:'#d92f83'}],logX:true},phaseChart:{xlabel:'ω [rad/s]',ylabel:'Fase [°]',series:[{points:pairs(curves.fase),color:'#8651bd'}],logX:true}
    };
  }
  function drawPlot(canvas,spec){
    if(!canvas||!canvas.getContext)return;
    const ctx=canvas.getContext('2d'); if(!ctx)return;
    const r=canvas.getBoundingClientRect?canvas.getBoundingClientRect():{width:600,height:310};
    if(!r.width||!r.height)return;
    const w=r.width,h=r.height,d=typeof devicePixelRatio==='number'?devicePixelRatio:1;
    canvas.width=w*d;canvas.height=h*d;ctx.setTransform(d,0,0,d,0,0);ctx.clearRect(0,0,w,h);
    const valid=a=>finite(a[0])&&finite(a[1])&&(!spec.logX||a[0]>0);
    const all=(spec.series||[]).flatMap(s=>(s.points||[]).filter(valid));
    if(spec.marker&&valid([spec.marker.x,spec.marker.y]))all.push([spec.marker.x,spec.marker.y]);
    const xs=all.map(p=>p[0]),ys=all.map(p=>p[1]);
    (spec.horizontal||[]).forEach(l=>{if(finite(l.value))ys.push(l.value);});
    let xmin=xs.length?Math.min(...xs):(spec.logX?.1:0),xmax=xs.length?Math.max(...xs):1;
    let ymin=ys.length?Math.min(...ys):0,ymax=ys.length?Math.max(...ys):1;
    if(xmin===xmax){if(spec.logX){xmin/=10;xmax*=10;}else{xmin-=1;xmax+=1;}}
    if(ymin===ymax){ymin-=1;ymax+=1;}
    const margin=(ymax-ymin)*.08;ymin-=margin;ymax+=margin;
    const p={l:66,r:18,t:32,b:56};
    const xx=x=>spec.logX?Math.log10(x):x,lo=xx(xmin),hi=xx(xmax);
    const X=x=>p.l+(xx(x)-lo)/(hi-lo)*(w-p.l-p.r);
    const Y=y=>h-p.b-(y-ymin)/(ymax-ymin)*(h-p.t-p.b);
    const tick=v=>Math.abs(v)>=10000||(v!==0&&Math.abs(v)<.01)?v.toExponential(1):Number(v.toFixed(2)).toString();
    ctx.font='11px Segoe UI, Arial';ctx.lineWidth=1;
    for(let i=0;i<=4;i++){
      const f=i/4,y=ymin+f*(ymax-ymin),x=spec.logX?10**(lo+f*(hi-lo)):xmin+f*(xmax-xmin);
      ctx.strokeStyle='#ead7e2';ctx.beginPath();ctx.moveTo(p.l,Y(y));ctx.lineTo(w-p.r,Y(y));ctx.stroke();
      ctx.fillStyle='#625762';ctx.textAlign='right';ctx.fillText(tick(y),p.l-7,Y(y)+4);
      ctx.textAlign='center';ctx.fillText(tick(x),X(x),h-p.b+18);
    }
    ctx.strokeStyle='#bfa9b6';ctx.beginPath();ctx.moveTo(p.l,p.t);ctx.lineTo(p.l,h-p.b);ctx.lineTo(w-p.r,h-p.b);ctx.stroke();
    (spec.series||[]).forEach(s=>{
      const pts=(s.points||[]).filter(valid);if(!pts.length)return;
      ctx.strokeStyle=s.color||'#d92f83';ctx.fillStyle=s.color||'#d92f83';ctx.lineWidth=2;
      if(s.kind==='scatter'||pts.length===1){pts.forEach(([x,y])=>{ctx.beginPath();ctx.arc(X(x),Y(y),3,0,Math.PI*2);ctx.fill();});}
      else{ctx.beginPath();pts.forEach(([x,y],i)=>i?ctx.lineTo(X(x),Y(y)):ctx.moveTo(X(x),Y(y)));ctx.stroke();}
    });
    (spec.horizontal||[]).forEach(l=>{if(!finite(l.value))return;ctx.setLineDash([5,4]);ctx.strokeStyle='#8651bd';ctx.beginPath();ctx.moveTo(p.l,Y(l.value));ctx.lineTo(w-p.r,Y(l.value));ctx.stroke();ctx.setLineDash([]);});
    if(spec.marker&&finite(spec.marker.x)&&finite(spec.marker.y)){
      const m=spec.marker;ctx.fillStyle='#9c2e70';ctx.beginPath();ctx.arc(X(m.x),Y(m.y),5,0,Math.PI*2);ctx.fill();
      ctx.textAlign='left';ctx.fillText(m.label,Math.min(X(m.x)+8,w-120),Math.max(p.t+12,Y(m.y)-10));
    }
    ctx.fillStyle='#625762';ctx.textAlign='center';ctx.fillText(spec.xlabel||'',w/2,h-8);
    ctx.textAlign='left';ctx.fillText(spec.ylabel||'',p.l,16);
    if(!all.length){ctx.textAlign='center';ctx.fillText('Sin datos',w/2,h/2);}
  }
  class Frontend{
    constructor({document,api,plot=drawPlot,download}={}){
      this.document=document||(typeof window!=='undefined'?window.document:null);
      this.api=api||new ApiClient();this.plot=plot;
      this.download=download||((blob,name)=>{const a=this.document.createElement('a');const url=URL.createObjectURL(blob);a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
      this.state={};this.busy=false;this.polling=false;this.generation=0;this.actionError='';this.tableKey='';this.selectedPoint='';this.connected=false;
    }
    el(id){return this.document&&this.document.getElementById(id);}
    option(value,label){const o=this.document.createElement('option');o.value=String(value);o.textContent=label;return o;}
    bind(){
      const d=this.document;if(!d)return;
      d.querySelectorAll('[data-tab]').forEach(b=>b.addEventListener('click',()=>{
        d.querySelectorAll('[data-tab]').forEach(x=>{x.classList.remove?.('active');x.setAttribute?.('aria-current','false');});
        b.classList.add?.('active');b.setAttribute?.('aria-current','page');
        ['live','static','dynamic','config'].forEach(id=>{const e=this.el(id);if(e)e.hidden=id!==b.dataset.tab;});this.render();
      }));
      const on=(id,fn,event='click')=>this.el(id)?.addEventListener(event,fn);
      on('start',()=>this.mutate('/api/start'));on('stop',()=>this.mutate('/api/stop'));
      on('point',()=>this.mutate('/api/point'));on('dynamic-finish',()=>this.mutate('/api/dynamic/finish'));
      on('reset',()=>this.mutate('/api/reset'));on('refresh-ports',()=>this.refreshPorts());
      on('export-csv',()=>this.export('/api/export','session.csv'));on('export-json',()=>this.export('/api/results','session.json'));
      on('precision-point',()=>{this.selectedPoint=this.el('precision-point').value;this.render();},'change');
      on('config-form',e=>{
        e.preventDefault?.();const n=id=>this.el(id)?.value;
        return this.mutate('/api/config',{mode:n('mode')||'demo',port:n('port')||'',baudrate:Number(n('baudrate')||115200),
          sample_interval:Number(n('sample-interval')||.5),vernier_connection:n('vernier-connection')||'usb',
          vernier_device_name:n('vernier-device-name')||'',vernier_channel:n('vernier-channel')!==''?Number(n('vernier-channel')):null,
          demo_initial_c:n('demo-initial')!==''?Number(n('demo-initial')):25});
      },'submit');
      on('demo-form',e=>{e.preventDefault?.();return this.mutate('/api/config',{demo_target_c:Number(this.el('demo-target')?.value)});},'submit');
      on('dynamic-form',e=>{e.preventDefault?.();return this.mutate('/api/dynamic/start',{x0:Number(this.el('x0')?.value),xf:Number(this.el('xf')?.value)});},'submit');
      d.querySelectorAll('[data-canvas]').forEach(b=>b.addEventListener('click',()=>{
        const c=this.el(b.dataset.canvas);if(c&&c.toBlob)c.toBlob(blob=>{if(blob)this.download(blob,b.dataset.canvas+'.png');},'image/png');
      }));
    }
    async refreshPorts(){
      try{
        const data=await this.api.request('/api/ports'),p=this.el('port');
        if(p){const selected=p.value;const values=[...new Set([...(data.ports||[]),...(selected?[selected]:[])])];
          p.replaceChildren(this.option('',values.length?'Selecciona un puerto':'No se detectaron puertos'),...values.map(v=>this.option(v,v)));p.value=selected;}
      }catch(e){this.actionError=e.message;this.showError(e);}
    }
    syncForms(){
      const c=this.state.config||{},map={mode:'mode',port:'port',baudrate:'baudrate','sample-interval':'sample_interval',
        'vernier-connection':'vernier_connection','vernier-device-name':'vernier_device_name','vernier-channel':'vernier_channel',
        'demo-initial':'demo_initial_c','demo-target':'demo_target_c'};
      Object.entries(map).forEach(([id,key])=>{const el=this.el(id);if(!el)return;
        if(id==='port'&&c[key]&&!Array.from(el.children||[]).some(o=>o.value===c[key]))el.append(this.option(c[key],c[key]));
        el.value=c[key]==null?'':String(c[key]);});
      for(const key of ['x0','xf'])if(this.el(key))this.el(key).value=this.state.dynamic?.[key]??'';
    }
    accept(s){
      const fresh=!this.state.session_id||this.state.session_id!==s?.session_id;
      this.state=s||{};this.connected=true;
      if(fresh){this.tableKey='';this.selectedPoint='';this.syncForms();}
      this.render();
    }
    showError(e){const x=this.el('error');if(x)x.textContent=e?.message||String(e);}
    async mutate(path,body={}){
      if(this.busy)return;this.busy=true;this.generation++;this.actionError='';this.render();
      try{
        const s=await this.api.request(path,{method:'POST',body});
        if(s&&typeof s==='object'&&!(s instanceof Blob)){
          if(path==='/api/point')this.selectedPoint='';
          this.accept(s);
          if(['/api/config','/api/reset'].includes(path))this.syncForms();
          if(path==='/api/dynamic/start'&&this.el('demo-target'))this.el('demo-target').value=String(s.config.demo_target_c);
        }
        return s;
      }catch(e){this.actionError=e.message;this.showError(e);return null;}
      finally{this.busy=false;this.generation++;this.render();}
    }
    async export(path,name){try{const blob=await this.api.request(path,{blob:true});this.download(blob,name);}catch(e){this.actionError=e.message;this.showError(e);}}
    async poll(){
      if(this.polling||this.busy)return;this.polling=true;const g=this.generation;
      try{const s=await this.api.request('/api/state');if(g===this.generation)this.accept(s);}
      catch(e){if(g===this.generation){this.connected=false;this.state={...this.state,error:e.message,connection:{esp32:'error',vernier:'error'},samples:[]};this.render();}}
      finally{this.polling=false;}
    }
    render(){
      const s=this.state||{},points=s.points||[],sr=s.static_result||{},dr=s.dynamic_result||{},dy=s.dynamic||{},progress=s.static_progress||{};
      const current=s.running&&['connected','simulated'].includes(s.connection?.esp32)&&['connected','simulated'].includes(s.connection?.vernier);
      const latest=current?(s.samples||[]).at(-1):null;
      const set=(id,value)=>{const el=this.el(id);if(el)el.textContent=value;};
      const num=(id,value)=>set(id,formatNumber(value));
      const disabled=(id,value)=>{const el=this.el(id);if(el)el.disabled=!!value;};
      set('mode-label',s.mode==='demo'?'DEMO · Datos simulados':s.mode==='real'?'REAL · Sensores físicos':'Sin conexión');
      set('data-status',!this.connected?'Sin comunicación':s.error?'Sin comunicación: '+s.error:s.running?(latest?'Adquisición en curso':'Esperando lecturas'):s.samples?.length?'Adquisición detenida':'Sin datos');
      set('error',this.actionError||s.error||'');
      num('temperature-vernier',latest?.vernier);num('temperature-lm35',latest?.lm35);
      const names={disconnected:'desconectado',connecting:'conectando',connected:'conectado',simulated:'simulado',error:'error'};
      for(const [key,label] of [['esp32','ESP32'],['vernier','Vernier']]){const status=s.connection?.[key]||'disconnected';set('conn-'+key,label+' · '+(names[status]||status));const dot=this.el('dot-'+key);if(dot)dot.dataset.state=status;}
      set('progress',`${progress.count??points.length} / 20 mediciones`);num('span',progress.span_c);
      set('goal-status',`${progress.count??points.length} / 20 niveles · Rango ${formatNumber(progress.span_c)} °C · ${progress.meets_goal?'Objetivo de mediciones cumplido':'Se requieren 20 niveles ascendentes y un rango de al menos 50 °C'}`);
      set('stability-status',s.stability?.reason||'Sin datos');
      disabled('start',s.running||this.busy||!this.connected);disabled('stop',!s.running||this.busy);
      disabled('point',!s.running||this.busy||!(s.capture_ready??s.stability?.ready));disabled('reset',s.running||this.busy);
      disabled('dynamic-start',!s.running||this.busy||dy.active||!s.stability?.ready);
      disabled('dynamic-finish',!dy.active||!s.running||this.busy);
      disabled('x0',dy.active);disabled('xf',dy.active);
      for(const id of ['mode','port','baudrate','sample-interval','vernier-connection','vernier-device-name','vernier-channel','demo-initial','save-config','refresh-ports'])disabled(id,s.running||this.busy);
      const demo=this.el('demo-form');if(demo)demo.hidden=s.mode!=='demo';
      disabled('demo-target',this.busy||dy.active);disabled('demo-apply',this.busy||dy.active);
      set('config-status',s.running?'Detenga la adquisición para cambiar esta configuración.':s.samples?.length?'Para cambiar sensores o modo, cree una nueva sesión.':'');
      const key=JSON.stringify(points.map(p=>[p.index,p.vernier,p.lm35]));
      if(key!==this.tableKey){
        this.tableKey=key;
        const tbody=this.el('points-body');
        if(tbody){const rows=points.map(p=>{const row=this.document.createElement('tr');for(const value of [p.index,formatNumber(p.vernier),formatNumber(p.lm35),'Estable']){const cell=this.document.createElement('td');cell.textContent=String(value);row.append(cell);}return row;});tbody.replaceChildren(...rows);}
        const select=this.el('precision-point');if(select)select.replaceChildren(...(points.length?points.map(p=>this.option(p.index,`Medición ${p.index} · ${formatNumber(p.vernier)} °C`)):[this.option('','Sin puntos')]));
      }
      const point=points.find(p=>String(p.index)===this.selectedPoint)||points.at(-1),pr=point?.precision||{};
      if(this.el('precision-point'))this.el('precision-point').value=point?String(point.index):'';
      for(const [id,key] of [['n','n'],['mean','media'],['s','s'],['sm','s_m'],['rsd','rsd'],['cv','cv'],['variance','varianza']])num('precision-'+id,pr[key]);
      set('precision-n',finite(pr.n)?String(pr.n):'—');
      for(const [id,key] of [['m','m'],['b','b'],['eg','e_g'],['e0','e_0'],['sigma','sigma_p']])num('metric-'+id,sr[key]);
      set('metric-r',finite(sr.r)?sr.r.toFixed(4):'—');
      for(let i=1;i<=3;i++)num('interval-'+i,sr.intervalos?.['k'+i]);
      num('ba-bias',sr.bland_altman?.sesgo);num('ba-low',sr.bland_altman?.limite_inferior);num('ba-high',sr.bland_altman?.limite_superior);
      set('static-formula',finite(sr.m)?`LM35 = ${formatNumber(sr.m)} · Vernier + (${formatNumber(sr.b)})`:'LM35 = m · Vernier + b');
      set('correction-formula',finite(sr.m)?`Temperatura corregida = (LM35 − (${formatNumber(sr.b)})) / ${formatNumber(sr.m)}`:'Temperatura corregida = (LM35 − b) / m');
      for(const [id,key] of [['k','k'],['tau','tau'],['y0','y0'],['yf','yf'],['t0','t0'],['level','nivel_tau']])num('dynamic-'+id,dr[key]);
      set('dynamic-status',dy.active?'Ensayo en curso. Espere la meseta final antes de calcular.':s.dynamic_result?'Ensayo calculado':dy.t0!=null?'Ensayo detenido sin resultado':'Sin ensayo');
      set('dynamic-formula',finite(dr.k)?`H(s) = ${formatNumber(dr.k)} / (1 + ${formatNumber(dr.tau)}s)`:'H(s) = K / (1 + τs)');
      const plots=buildPlots(s);Object.entries(plots).forEach(([id,spec])=>{const canvas=this.el(id);if(canvas){canvas.id=id;this.plot(canvas,spec);}});
    }
  }
  if(typeof document!=='undefined')document.addEventListener('DOMContentLoaded',()=>{
    const f=new Frontend();f.bind();f.poll();setInterval(()=>f.poll(),500);window.addEventListener('resize',()=>f.render());
  });
  return {ApiClient,Frontend,buildPlots,drawPlot,formatNumber};
});
