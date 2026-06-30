#!/usr/bin/env python3
# Node dashboard feeder: Cryptarchia/Logos node HTTP API + watchdog -> node-data.json.
import json, subprocess, re, time, os, sys, urllib.request
OUT="/home/vpavlin/mesh-dashboard/node-data.json"
NODE="http://localhost:8080"
def jget(path,t=4):
    try:
        with urllib.request.urlopen(NODE+path,timeout=t) as r: return json.load(r)
    except Exception: return None
def wd_restarts():
    try:
        out=subprocess.run(["journalctl","--user","-u","logos-node-watchdog","-g","restart #","-n","1","--no-pager","-o","cat"],
                           capture_output=True,text=True,timeout=8).stdout
        m=re.search(r"restart #(\d+)",out); return int(m.group(1)) if m else 0
    except Exception: return 0
def active():
    try: return subprocess.run(["systemctl","--user","is-active","logos-node"],capture_output=True,text=True).stdout.strip()=="active"
    except Exception: return False
def build():
    info=jget("/cryptarchia/info"); net=jget("/network/info")
    height=None
    if isinstance(info,dict):
        try: height=int((info.get("cryptarchia_info") or info).get("height"))
        except Exception: height=None
    mode=info.get("mode") if isinstance(info,dict) else None
    while isinstance(mode,dict): mode=next(iter(mode.values()),None)
    mode=mode if isinstance(mode,str) else None
    net=net if isinstance(net,dict) else {}
    act=active(); pid=net.get("peer_id") or ""
    d={"updated":int(time.time()),"height":height,
       "peers":net.get("n_peers"),"connections":net.get("n_connections"),"pending":net.get("n_pending_connections"),
       "peerId":pid,"peerShort":(pid[:6]+"…"+pid[-6:]) if len(pid)>14 else pid,
       "restarts":wd_restarts(),"active":act,"mode":mode}
    d["state"]=("DOWN" if not act else ("SYNCING" if mode=="Bootstrapping" else "SYNCED") if height is not None else "SYNCING" if net else "WEDGED")
    tmp=OUT+".tmp"; open(tmp,"w").write(json.dumps(d)); os.replace(tmp,OUT)
if __name__=="__main__":
    if "once" in sys.argv: build()
    else:
        while True: build(); time.sleep(10)
