#!/usr/bin/env python3
# Dashboard feeder: gateway SQLite + journal -> data.json (channels/nodes/health/messages).
import sqlite3, json, subprocess, re, time, os, sys, hashlib
DB="/home/vpavlin/.local/share/logos_host/mesh_gateway/gateway.db"
OUT="/home/vpavlin/mesh-dashboard/data.json"
NAMECACHE="/home/vpavlin/mesh-dashboard/.nodename"
DWEB=[("Public","8b3387e9c5cdea6ac9e5edbaa115cd72"),
      ("#dwebcamp","b8769b859a18cb47fa326c79bc04e2da"),
      ("#schedule","03a5bab42c9d3535b69f259f338be9ea"),
      ("#workshop","3862ef52df5e5966eb10751b83788bc5"),
      ("#bot","eb50a1bcb3e4e5d7bf69a57c9dada211"),
      ("#berlinmesh","c5ead1d8a7647a63fd37d156cdc3e257"),
      ("#berlinbrandenburg","625ff2a308bbe3a4c90da77979b7a4fc")]
def topic(n,s): return "/mesh/1/"+hashlib.md5(n.encode()+bytes.fromhex(s)).hexdigest()[:16]+"/proto"
T2N={topic(n,s):n for n,s in DWEB}
def jlast(pat):
    try: return subprocess.run(["journalctl","--user","-u","meshtastic-gateway","-g",pat,"-n","1","--no-pager","-o","cat"],capture_output=True,text=True,timeout=8).stdout.strip()
    except Exception: return ""
def active():
    try: return subprocess.run(["systemctl","--user","is-active","meshtastic-gateway"],capture_output=True,text=True).stdout.strip()=="active"
    except Exception: return False
def radio_up():
    try: return subprocess.run(["fuser","/dev/ttyACM0"],capture_output=True).returncode==0
    except Exception: return False
def node_name():
    m=re.search(r'name "([^"]+)"', jlast("SELF_INFO name"))
    if m:
        try: open(NAMECACHE,"w").write(m.group(1))
        except Exception: pass
        return m.group(1)
    try: return open(NAMECACHE).read().strip() or "?"
    except Exception: return "?"
def logos_up():
    try:
        out=subprocess.run(["journalctl","--user","-u","meshtastic-gateway","-g","delivery_module","-n","1","--no-pager","-o","short-unix"],capture_output=True,text=True,timeout=8).stdout.strip()
        m=re.match(r"(\d+)", out)
        return bool(m) and (time.time()-float(m.group(1)))<60
    except Exception: return False
def build():
    act=active()
    m=re.search(r"nodes \S+ (\d+)", jlast("meshcore_radio: nodes")); ncount=int(m.group(1)) if m else 0
    node=node_name()
    d={"health":{"state":"ONLINE" if act else "OFFLINE","radio":"up" if (act and radio_up()) else "down",
                 "logos":"up" if (act and logos_up()) else "down","node":node,"nodes":ncount},
       "channels":[],"nodes":[],"messages":[],"updated":int(time.time())}
    senders=set()
    try:
        c=sqlite3.connect("file:%s?mode=ro"%DB,uri=True); cur=c.cursor()
        relset={r[0] for r in cur.execute("select topic from channel_prefs where relaying=1")}
        cnt=dict(cur.execute("select topic,count(*) from messages group by topic"))
        for n,s in DWEB:
            tp=topic(n,s); d["channels"].append({"name":n,"msgs":cnt.get(tp,0),"relaying":tp in relset})
        for tpc,sender,text,origin,outgoing in cur.execute("select topic,sender,text,origin,outgoing from messages order by rowid desc limit 18"):
            text=text or ""
            name,body=(text.split(": ",1) if ": " in text else [(sender or "?"),text])
            if (origin=="mesh") and name: senders.add(name)
            d["messages"].append({"chan":T2N.get(tpc,"?"),"name":name,"body":body,"origin":origin or ""})
        c.close()
    except Exception as e: d["err"]=str(e)
    nl=[{"name":node,"self":True}] if node!="?" else []
    for s in sorted(senders):
        if s!=node: nl.append({"name":s,"self":False})
    d["nodes"]=nl
    d["health"]["nodes"]=ncount or len(nl)
    tmp=OUT+".tmp"; open(tmp,"w").write(json.dumps(d)); os.replace(tmp,OUT)
if __name__=="__main__":
    if "once" in sys.argv: build()
    else:
        while True: build(); time.sleep(5)
