import csv, json
from pathlib import Path

class SessionStore:
    def __init__(self,root): self.root=Path(root); self.root.mkdir(parents=True,exist_ok=True); self.sid=None
    def _dir(self,sid): d=self.root/sid; d.mkdir(parents=True,exist_ok=True); return d
    def append_sample(self,row):
        d=self._dir(row['session_id']); path=d/'samples.csv'; new=not path.exists()
        with path.open('a',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=['session_id','mode','t','vernier','lm35']);
            if new:w.writeheader()
            w.writerow({k:row[k] for k in w.fieldnames})
    def save_results(self,sid,state,samples):
        d=self._dir(sid)
        temporary=d/'results.json.tmp'
        temporary.write_text(json.dumps({'sample_count':len(samples),'state':state},ensure_ascii=False,allow_nan=False),encoding='utf-8')
        temporary.replace(d/'results.json')
        if not (d/'samples.csv').exists():
            with (d/'samples.csv').open('w',newline='',encoding='utf-8') as f:
                w=csv.DictWriter(f,fieldnames=['session_id','mode','t','vernier','lm35']);w.writeheader();w.writerows(samples)
