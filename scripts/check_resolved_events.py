"""Propagate a supplied resolved finite event graph and check interval capacities."""
import json
import sys
from pathlib import Path

def score(case):
    pending={v['id']:v for v in case['operations']}
    if len(pending)!=len(case['operations']): raise ValueError('duplicate operation')
    times={}; events=[]; lanes={}
    while pending:
        ready=sorted(k for k,v in pending.items() if set(v['parents'])<=times.keys())
        if not ready: raise ValueError('cyclic or missing dependency')
        for k in ready:
            v=pending.pop(k)
            start=max([times[p][1] for p in v['parents']]+[0])
            end=start+v['duration_s']
            if end<=start: raise ValueError('nonpositive duration')
            times[k]=(start,end)
            lanes.setdefault(v['lane'],[]).append((start,end,k))
            for d,size in v.get('acquire_GiB',{}).items(): events.append((start,1,k,d,size))
            for d,size in v.get('release_GiB',{}).items(): events.append((end,0,k,d,-size))
    for intervals in lanes.values():
        intervals.sort()
        for a,b in zip(intervals,intervals[1:]):
            if a[1]>b[0]+1e-12: raise ValueError('lane overlap')
    live=dict(case['initial_GiB']); peak=dict(live)
    for d,cap in case['capacity_GiB'].items():
        if not 0<=live[d]<=cap: raise ValueError('invalid initial state')
    for time,kind,k,d,delta in sorted(events):
        live[d]+=delta; peak[d]=max(peak[d],live[d])
        if not -1e-12<=live[d]<=case['capacity_GiB'][d]+1e-12: raise ValueError('capacity violation')
    finish={q:max(times[k][1] for k in v['terminal']) for q,v in case['queries'].items()}
    value=sum(v.get('weight',1)*(finish[q]-v.get('arrival_s',0)) for q,v in case['queries'].items())
    return {'intervals_s':times,'completion_s':finish,'objective_s':value,'peak_GiB':peak}

if __name__=='__main__':
    path=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]/'examples/heterogeneous_events.json'
    print(json.dumps(score(json.loads(path.read_text(encoding='utf-8'))),indent=2))
