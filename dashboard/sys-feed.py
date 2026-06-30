#!/usr/bin/env python3
# System + GPS dashboard feeder -> sys-data.json (+ cached OSM tile map.png)
import json, os, sys, time, math, subprocess, urllib.request
OUT="/home/vpavlin/mesh-dashboard/sys-data.json"
MAP="/home/vpavlin/mesh-dashboard/map.png"
_prev=[None,None]; _tile=[None]

def cpu_pct():
    try:
        with open("/proc/stat") as f: v=[int(x) for x in f.readline().split()[1:]]
        idle=v[3]+v[4]; total=sum(v); pt,pi=_prev; _prev[0],_prev[1]=total,idle
        if pt is None: return None
        dt=total-pt; di=idle-pi
        return round(100.0*(dt-di)/dt,1) if dt>0 else None
    except Exception: return None

def mem():
    try:
        d={}
        for line in open("/proc/meminfo"):
            k,_,rest=line.partition(":"); d[k]=int(rest.split()[0])
        total=d["MemTotal"]; avail=d.get("MemAvailable",d.get("MemFree",0)); used=total-avail
        return {"total":total,"used":used,"pct":round(100.0*used/total,1)}
    except Exception: return {}

def disk():
    try:
        s=os.statvfs("/"); total=s.f_blocks*s.f_frsize; free=s.f_bavail*s.f_frsize; used=total-free
        return {"total":total,"used":used,"free":free,"pct":round(100.0*used/total,1)}
    except Exception: return {}

def temp():
    try: return round(int(open("/sys/class/thermal/thermal_zone0/temp").read())/1000.0,1)
    except Exception: return None

def uptime():
    try: return int(float(open("/proc/uptime").read().split()[0]))
    except Exception: return None

def gps():
    try:
        out=subprocess.run(["gpspipe","-w","-n","25"],capture_output=True,text=True,timeout=9).stdout
        g={"mode":0}; hdop=nsat=usat=None
        for ln in out.splitlines():
            try: o=json.loads(ln)
            except Exception: continue
            c=o.get("class")
            if c=="TPV":
                if o.get("mode") is not None: g["mode"]=o["mode"]
                for k in ("lat","lon","alt","altHAE","speed","track"):
                    if o.get(k) is not None: g[k]=o[k]
            elif c=="SKY":
                if o.get("hdop") is not None: hdop=o["hdop"]
                if o.get("nSat") is not None: nsat=o["nSat"]
                if o.get("uSat") is not None: usat=o["uSat"]
                sats=o.get("satellites")
                if sats: nsat=len(sats); usat=sum(1 for s in sats if s.get("used"))
        if hdop is not None: g["hdop"]=hdop
        if nsat is not None: g["nSat"]=nsat
        if usat is not None: g["uSat"]=usat
        return g
    except Exception: return {"mode":0}

def fetch_map(lat,lon,z=14):
    try:
        n=2**z
        xf=(lon+180.0)/360.0*n; yf=(1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*n
        x,y=int(xf),int(yf)
        dot={"dotx":round((xf-x)*256),"doty":round((yf-y)*256),"z":z}
        if _tile[0]==(z,x,y) and os.path.exists(MAP): return dot
        url="https://tile.openstreetmap.org/%d/%d/%d.png"%(z,x,y)
        req=urllib.request.Request(url,headers={"User-Agent":"logos-pi-dashboard/1.0 (DWeb Camp field kit)"})
        with urllib.request.urlopen(req,timeout=8) as r: data=r.read()
        tmp=MAP+".tmp"; open(tmp,"wb").write(data); os.replace(tmp,MAP); _tile[0]=(z,x,y)
        dot["fetched"]=True; return dot
    except Exception: return None

def build():
    g=gps(); mp=None
    if g.get("mode",0)>=2 and "lat" in g and "lon" in g:
        mp=fetch_map(g["lat"],g["lon"])
    d={"updated":int(time.time()),"cpu":cpu_pct(),"mem":mem(),"disk":disk(),
       "temp":temp(),"uptime":uptime(),"gps":g,"map":mp,"hasmap":os.path.exists(MAP)}
    tmp=OUT+".tmp"; open(tmp,"w").write(json.dumps(d)); os.replace(tmp,OUT)

if __name__=="__main__":
    cpu_pct()
    if "once" in sys.argv: time.sleep(0.4); build()
    else:
        while True:
            build(); time.sleep(5)
