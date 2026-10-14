#!/usr/bin/env python3
"""Validate content and emit a self-contained FDE HTML explorer."""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path

def require(ok, message):
    if not ok:
        raise ValueError(message)

def texts(obj, keys, where):
    for key in keys:
        require(isinstance(obj.get(key), str) and obj[key].strip(), f'{where}: missing text {key}')

def number(value):
    return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value)

def identifier(value):
    return isinstance(value,str) and re.fullmatch(r'[a-z][a-z0-9-]*',value) is not None

def node_valid(node,width,height):
    texts(node,['id','label','sub'],'node')
    require(identifier(node['id']),'node IDs must use lowercase letters, digits and hyphens')
    require(node.get('role','component') in ('component','data','branch','observation'), 'invalid node role')
    require(all(number(node.get(k)) for k in ('x','y')) and number(node.get('w',178)) and number(node.get('h',70)), 'finite numeric node geometry required')
    require(node.get('w',178)>0 and node.get('h',70)>0, 'positive node dimensions required')
    require(node['x']>=0 and node['y']>=0 and node['x']+node.get('w',178)<=width and node['y']+node.get('h',70)<=height, f'node {node["id"]} outside viewBox')

def edges_valid(edges, ids):
    require(isinstance(edges, list), 'edges must be a list')
    for edge in edges:
        require(edge.get('from') in ids and edge.get('to') in ids, 'edge references unknown node')
        require(edge.get('kind', 'flow') in ('flow','data','branch','observation'), 'invalid edge kind')
        if 'points' in edge:
            require(isinstance(edge['points'],list) and len(edge['points']) >= 2 and all(isinstance(p,list) and len(p)==2 and all(number(v) for v in p) for p in edge['points']), 'invalid edge points')
        for key in ('labelX','labelY'):
            require(key not in edge or number(edge[key]),'finite numeric edge label position required')

def validate(data):
    texts(data, ['title'], 'explorer')
    require(isinstance(data.get('systems'),list) and data['systems'], 'at least one system required')
    source_ids=[s['id'] for s in data.get('sources',[])]
    require(len(source_ids)==len(set(source_ids)), 'duplicate source IDs')
    for src in data.get('sources',[]):
        texts(src,['id','title','note'],'source')
        require(identifier(src['id']),'invalid source ID')
        require(not src.get('url') or src['url'].startswith('https://'), 'only HTTPS source URLs allowed')
    system_ids=[s['id'] for s in data['systems']]
    require(len(system_ids)==len(set(system_ids)), 'duplicate system IDs')
    for s in data['systems']:
        texts(s,['id','name','nav','family','tag','description','question','scope','provenance'],'system')
        require(identifier(s['id']),'invalid system ID')
        require(set(s.get('sourceIds',[]))<=set(source_ids), 'unknown source')
        d=s['diagram']; nodes=d['nodes']; ids={n['id'] for n in nodes}
        require(ids and len(ids)==len(nodes), 'duplicate or empty node IDs')
        width,height=d.get('width',960),d.get('height',470)
        require(number(width) and number(height) and width>0 and height>0,'positive diagram dimensions required')
        for n in nodes:
            node_valid(n,width,height)
        edges_valid(d.get('edges',[]),ids)
        require(s.get('scenarios'), 'missing scenarios')
        sc_ids=[sc['id'] for sc in s['scenarios']]
        require(len(sc_ids)==len(set(sc_ids)), 'duplicate scenario IDs')
        for sc in s['scenarios']:
            texts(sc,['id','label','outcome'],'scenario')
            require(identifier(sc['id']),'invalid scenario ID')
            overrides=sc.get('nodeOverrides',{})
            require(isinstance(overrides,dict) and set(overrides)<=ids,'unknown override node')
            for node_id,override in overrides.items():
                require(isinstance(override,dict) and set(override)<={'label','sub','x','y','w','h'},'invalid override fields')
                node_valid({**next(n for n in nodes if n['id']==node_id),**override},width,height)
            require(sc.get('stages'), 'no stages')
            skipped=set(sc.get('skipNodes',[])); referenced=set()
            require(skipped<=ids, 'unknown skipped node')
            for st in sc['stages']:
                texts(st,['title','component','short','what','why','next'],'stage')
                require('input' in st and 'output' in st, 'missing input/output')
                require(st.get('nodeIds') and set(st['nodeIds'])<=ids, 'missing/unknown node mapping')
                referenced.update(st['nodeIds'])
                require(isinstance(st.get('checks'),list) and st['checks'], 'missing checks')
                for c in st['checks']:
                    texts(c,['text'],'check')
                    require(c.get('kind') in ('Exact','Judge','Offline','Observe'), 'invalid check kind')
            require(not skipped & referenced, 'skipped node maps to active stage')
            require(referenced|skipped==ids, f'unmapped nodes: {ids-referenced-skipped}')
            edges=sc.get('edges',d.get('edges',[]));edges_valid(edges,ids)
            require(not any(e['from'] in skipped or e['to'] in skipped for e in edges), 'edges execute skipped nodes; override scenario edges')
        r=s['revision'];texts(r,['pitch','flow','tradeoff','failure','remember'],'revision')
        require(len(r.get('discovery',[]))>=2, 'two discovery questions required')
        require(len(r.get('requirements',[]))>=2, 'functional and non-functional requirements required')
        require(len(r.get('ops',[]))==4, 'four production talking points required')
        require({p[0].lower() for p in r['requirements']} >= {'functional','non-functional'},'functional/non-functional labels required')
        require({p[0].lower() for p in r['ops']} == {'scale','latency','cost','evaluation'},'scale/latency/cost/evaluation labels required')
        for label,value in r['requirements']+r['ops']:
            require(isinstance(label,str) and isinstance(value,str) and value.strip(), 'invalid revision pair')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    args=p.parse_args();data=json.loads(args.data.read_text(encoding='utf-8'));validate(data)
    template=(Path(__file__).resolve().parents[1]/'assets/explorer-template.html').read_text(encoding='utf-8')
    require(template.count('__FDE_DATA_JSON__')==1,'missing/duplicate data slot')
    serialized=json.dumps(data,ensure_ascii=False).replace('&','\\u0026').replace('<','\\u003c').replace('>','\\u003e')
    html=template.replace('__FDE_DATA_JSON__',serialized)
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(html,encoding='utf-8')
    print(json.dumps({'output':str(args.output.resolve()),'systems':len(data['systems']),'scenarios':sum(len(s['scenarios']) for s in data['systems']),'sha256':hashlib.sha256(html.encode()).hexdigest(),'validation':'content/schema passed; browser QA is separate'}))

if __name__=='__main__':
    main()
