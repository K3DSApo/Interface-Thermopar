import math

__all__ = ['precision','calibracion_estatica','calibracion_dinamica','estabilidad','evaluar_estabilidad','histeresis','progreso_estatico','voltage_mv_a_lm35']

def _num(v):
    if isinstance(v, bool) or not isinstance(v, (int,float)) or not math.isfinite(v): raise ValueError('valor no finito')
    return float(v)
def _seq(a):
    if a is None or isinstance(a,(str,bytes)): raise ValueError('secuencia inválida')
    try: out=[_num(v) for v in a]
    except (TypeError,ValueError): raise ValueError('secuencia inválida')
    return out

def precision(valores):
    a=_seq(valores)
    if len(a)<2: raise ValueError('n>=2')
    n=len(a)
    try:
        mean=sum(a)/n; var=sum((v-mean)**2 for v in a)/(n-1); s=math.sqrt(var)
    except (OverflowError, FloatingPointError):
        raise ValueError('resultado no finito')
    if not all(math.isfinite(v) for v in (mean,var,s)): raise ValueError('resultado no finito')
    rsd=None if mean==0 else s/mean
    return {'n':n,'media':mean,'s':s,'s_m':s/math.sqrt(n),'rsd':rsd,'cv':None if rsd is None else 100*rsd,'varianza':var}

def calibracion_estatica(x,y):
    x=_seq(x); y=_seq(y)
    if len(x)!=len(y) or len(x)<2: raise ValueError('pares insuficientes')
    n=len(x); xm=sum(x)/n; ym=sum(y)/n
    sxx=sum((v-xm)**2 for v in x); syy=sum((v-ym)**2 for v in y); sxy=sum((a-xm)*(b-ym) for a,b in zip(x,y))
    if sxx==0 or syy==0: raise ValueError('ajuste degenerado')
    m=sxy/sxx; b=ym-m*xm
    r=sxy/math.sqrt(sxx*syy); r=max(-1.0,min(1.0,r))
    if m==0: raise ValueError('pendiente nula')
    corr=[(v-b)/m for v in y]; sigma=math.sqrt(sum((c-a)**2 for c,a in zip(corr,x))/n)
    means=[(a+bv)/2 for a,bv in zip(x,y)]; dif=[bv-a for a,bv in zip(x,y)]; bias=sum(dif)/n
    sd=math.sqrt(sum((d-bias)**2 for d in dif)/(n-1))
    lo=bias-1.96*sd; hi=bias+1.96*sd; xmin=min(x); xmax=max(x)
    return {'n':n,'m':m,'b':b,'r':r,'e_g':m-1,'e_0':b,'sigma_p':sigma,'corregidas':corr,
            'intervalos':{'k1':sigma,'k2':2*sigma,'k3':3*sigma},
            'bland_altman':{'medias':means,'diferencias':dif,'sesgo':bias,'limite_inferior':lo,'limite_superior':hi},
            'curva_ajuste':{'x':[xmin,xmax],'y':[m*xmin+b,m*xmax+b]}}

def histeresis(asc,desc,salida_min,salida_max):
    a=_seq(asc); d=_seq(desc); lo=_num(salida_min); hi=_num(salida_max)
    if not a or len(a)!=len(d) or hi<=lo: raise ValueError('datos de histéresis inválidos')
    return [100*abs(u-v)/(hi-lo) for u,v in zip(a,d)]

def voltage_mv_a_lm35(voltage_mv): return _num(voltage_mv)/10.0

def estabilidad(samples, *, window_seconds=5.0, min_samples=5, max_excursion_c=0.3):
    if isinstance(window_seconds,bool) or not isinstance(window_seconds,(int,float)) or not math.isfinite(window_seconds) or window_seconds<=0: raise ValueError('ventana inválida')
    if isinstance(min_samples,bool) or not isinstance(min_samples,int) or min_samples<1: raise ValueError('mínimo inválido')
    if isinstance(max_excursion_c,bool) or not isinstance(max_excursion_c,(int,float)) or not math.isfinite(max_excursion_c) or max_excursion_c<0: raise ValueError('excursión inválida')
    if samples is None: raise ValueError('muestras inválidas')
    s=list(samples)
    if not s: return {'ready':False,'reason':'Sin muestras','n':0,'window_seconds':0.0}
    ts=[]; vs=[]; ls=[]
    for z in s:
        if not isinstance(z,dict) or not all(k in z for k in ('t','vernier','lm35')): raise ValueError('muestra inválida')
        ts.append(_num(z['t'])); vs.append(_num(z['vernier'])); ls.append(_num(z['lm35']))
    if any(b<=a for a,b in zip(ts,ts[1:])): raise ValueError('tiempos no crecientes')
    end=ts[-1]; idx=[i for i,t in enumerate(ts) if t>=end-float(window_seconds)]
    n=len(idx); duration=ts[-1]-ts[idx[0]]
    ready=n>=min_samples and max(vs[i] for i in idx)-min(vs[i] for i in idx)<=max_excursion_c+1e-12 and max(ls[i] for i in idx)-min(ls[i] for i in idx)<=max_excursion_c+1e-12
    return {'ready':ready,'reason':'Ventana estable' if ready else ('Muestras insuficientes' if n<min_samples else 'Excursión fuera de límite'),'n':n,'window_seconds':duration}

def evaluar_estabilidad(samples, **kwargs):
    return estabilidad(samples, **kwargs)

def progreso_estatico(points):
    if points is None: raise ValueError('puntos inválidos')
    vals=[]
    for p in points:
        if not isinstance(p,dict) or 'vernier' not in p: raise ValueError('punto inválido')
        vals.append(_num(p['vernier']))
    inc=all(b>a for a,b in zip(vals,vals[1:])); span=(max(vals)-min(vals)) if vals else 0.0
    return {'count':len(vals),'span_c':span,'incremental':inc,'meets_goal':len(vals)==20 and inc and span>=50}

def calibracion_dinamica(t,y,x0,xf,t0=0.0, *, initial_window_seconds=5.0, initial_min_samples=5, initial_max_excursion_c=0.3, plateau_seconds=2.0, plateau_min_samples=5, plateau_abs_c=0.3, plateau_fraction=0.01):
    t=_seq(t); y=_seq(y); x0=_num(x0); xf=_num(xf); t0=_num(t0)
    if len(t)!=len(y) or len(t)<2 or any(b<=a for a,b in zip(t,t[1:])): raise ValueError('tiempos inválidos')
    if xf==x0: raise ValueError('entrada sin cambio')
    for v in (initial_window_seconds,plateau_seconds,plateau_abs_c):
        if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v<=0: raise ValueError('opción inválida')
    for v in (initial_min_samples,plateau_min_samples):
        if isinstance(v,bool) or not isinstance(v,int) or v<2: raise ValueError('opción inválida')
    if isinstance(plateau_fraction,bool) or not isinstance(plateau_fraction,(int,float)) or not math.isfinite(plateau_fraction) or not 0<=plateau_fraction<1: raise ValueError('opción inválida')
    pre=[i for i,u in enumerate(t) if u<=t0 and u>=t0-initial_window_seconds]
    if len(pre)<initial_min_samples or not any(u<t0 for u in (t[i] for i in pre)): raise ValueError('sin meseta inicial')
    y0=sum(y[i] for i in pre)/len(pre)
    if max(y[i] for i in pre)-min(y[i] for i in pre)>initial_max_excursion_c: raise ValueError('meseta inicial inestable')
    post=[i for i,u in enumerate(t) if u>t0]
    if len(post)<plateau_min_samples: raise ValueError('sin meseta final')
    # Sufijo que cubra simultáneamente el mínimo de muestras y duración.
    end_i=post[-1]; start_pos=max(0, len(post)-plateau_min_samples)
    while start_pos>0 and t[end_i]-t[post[start_pos]] < plateau_seconds: start_pos-=1
    if t[end_i]-t[post[start_pos]] < plateau_seconds: raise ValueError('meseta final corta')
    final=post[start_pos:]
    yf=sum(y[i] for i in final)/len(final)
    lim=max(plateau_abs_c, plateau_fraction*abs(yf-y0))
    if max(y[i] for i in final)-min(y[i] for i in final)>lim: raise ValueError('meseta final inestable')
    dy=yf-y0
    if abs(dy)<=lim: raise ValueError('cambio insignificante')
    frac=1-math.exp(-1); level=y0+frac*dy; cross=None
    for ia,ib in zip(post,post[1:]):
        qa=(y[ia]-y0)/dy; qb=(y[ib]-y0)/dy
        if (qa-frac)==0: cross=t[ia]; break
        if (qa-frac)*(qb-frac)<=0 and qb!=qa:
            cross=t[ia]+(t[ib]-t[ia])*(frac-qa)/(qb-qa); break
    if cross is None or cross<=t0: raise ValueError('sin cruce')
    tau=cross-t0; k=dy/(xf-x0)
    if k<=0: raise ValueError('ganancia inválida')
    end=max(t[-1]-t0,5*tau)
    xs=[end*i/200 for i in range(201)]; step=[y0+dy*(1-math.exp(-u/tau)) for u in xs]; imp=[k/tau*math.exp(-u/tau) for u in xs]
    ws=[(0.01/tau)*((10000)**(i/120)) for i in range(121)]; mag=[abs(k)/math.sqrt(1+(w*tau)**2) for w in ws]; phase=[-math.atan2(w*tau,1)*180/math.pi for w in ws]
    return {'k':k,'tau':tau,'y0':y0,'yf':yf,'t0':t0,'nivel_tau':level,'fraccion_tau':frac,'curvas':{'escalon':{'x':xs,'y':step},'impulso':{'x':xs,'y':imp},'magnitud':{'x':ws,'y':mag},'fase':{'x':ws,'y':phase}}}
