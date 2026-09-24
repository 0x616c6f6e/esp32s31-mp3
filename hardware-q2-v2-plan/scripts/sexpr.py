import re, json
class S(str): pass
def parse(text):
    tokens=re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+',text)
    stack=[]; root=None
    for t in tokens:
        if t=='(':
            v=[]
            if stack: stack[-1].append(v)
            stack.append(v)
        elif t==')': root=stack.pop()
        else:
            if t.startswith('"'):
                try: t=S(json.loads(t))
                except: t=S(t[1:-1].replace('\\"','"').replace('\\\\','\\'))
            stack[-1].append(t)
    return root
def children(n,key): return [v for v in n if isinstance(v,list) and v and v[0]==key]
def get(n,key,default=None): return next(iter(children(n,key)),default)
def prop(n,key): return next((v for v in children(n,'property') if v[1]==key),None)
def dump(n,depth=0):
    if isinstance(n,S): return json.dumps(n,ensure_ascii=False)
    if not isinstance(n,list): return str(n)
    if not any(isinstance(x,list) for x in n): return '('+' '.join(dump(x) for x in n)+')'
    out='('
    for i,x in enumerate(n):
        out+= ('\n'+'\t'*(depth+1) if isinstance(x,list) else (' ' if i else ''))+dump(x,depth+1)
    return out+'\n'+'\t'*depth+')'
