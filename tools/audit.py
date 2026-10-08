"""전수조사: 처리 범위 밖 일본어 텍스트 탐색"""
import sys,os,re,struct,collections
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from stagecrypt import toc,STAGE
from stage import read_stage,pages
from stagepack import page_decode_full
from gcx import parse
# 가나(0x81/0x82/0xC1/0xC2 등) 포함 2바이트 코드가 4자 이상 연속
PAT=re.compile(rb'(?:[\x81\x82\x83\xa1\xa2\xa3\xc1\xc2\xc3][\x01-\xb0]|[\x8c-\x9b][\x01-\xfe]){4,}')
def kana_ratio(b):
    n=sum(1 for i in range(0,len(b)-1,2) if b[i]&0x9f in (0x81,0x82))
    return n/(len(b)/2)
w0,t=toc(STAGE); f=open(STAGE,'rb'); end=os.path.getsize(STAGE)//0x800
hits=collections.Counter(); ex={}
for si,(name,off) in enumerate(t):
    nxt=t[si+1][1] if si+1<len(t) else end
    raw,hsz,ents=read_stage(f,w0,name,off,nxt)
    for pj,pg in enumerate(pages(raw,hsz,ents)):
        co,cl=pg['comp']; u=page_decode_full(raw[hsz+co:],cl)
        fl=sorted(pg['files'],key=lambda x:x[2])
        covered=[]
        for k,(ty,h,o) in enumerate(fl):
            e=fl[k+1][2] if k+1<len(fl) else pg['usize']
            if ty==6:
                r=parse(u[o:e])
                if r: covered.append((o+r['S'],o+r['F']))
        for m in PAT.finditer(u):
            if any(a<=m.start()<b for a,b in covered): continue
            if kana_ratio(m.group())<0.5: continue
            # 소속 파일
            ft=None
            for k,(ty,h,o) in enumerate(fl):
                if o<=m.start(): ft=(ty,h)
            key=(name,pj,ft[0] if ft else -1)
            hits[key]+=1
            ex.setdefault(key,(hex(m.start()),m.group()[:24].hex()))
for k,v in sorted(hits.items()): print(k,v,ex[k])
