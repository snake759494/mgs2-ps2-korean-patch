"""모든 텍스트 블록 추출 -> work/blocks.pkl"""
import sys,os,struct,pickle,hashlib
sys.path.insert(0,os.path.dirname(__file__))
from gcx import parse,split_codec
from chunks import walk
import glob
R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def sub_parse(c):
    """자막 청크(type4) 파싱"""
    fo=struct.unpack_from('<I',c,0x10)[0]
    F=0x14+fo; ents=[]; p=0x14
    xtra=struct.unpack_from('<I',c,0xc)[0]
    if F>len(c)-4: return None
    while p<F-xtra:
        st,en,spk,ln=struct.unpack_from('<4I',c,p)
        if ln<16 or p+ln>F-xtra: return None
        txt=c[p+16:p+ln]; z=txt.find(b'\0'); ents.append((st,en,spk,txt[:z]))
        p+=ln
    fsz=struct.unpack_from('<I',c,F)[0]
    return ents,c[F+4:F+4+fsz]
def glyph_list(raw):
    return [raw[i*144:(i+1)*144] for i in range(len(raw)//144)]
def main():
    blocks=[]
    d=open(os.path.join(R,'extract/CODEC.DAT'),'rb').read()
    for j,(a,b) in enumerate(split_codec(d)):
        r=parse(d[a:b])
        blocks.append(dict(src='codec',id=j,off=a,strs=r['strs'],glyphs=glyph_list(r['glyphs']),kind='gcx'))
    sys.path.insert(0,os.path.join(R,'tools'))
    from stage import toc,read_stage,pages,decode_page,STAGE
    w0,t=toc(os.path.join(R,STAGE)); f=open(os.path.join(R,STAGE),'rb'); end=os.path.getsize(os.path.join(R,STAGE))//0x800
    for si,(name,off) in enumerate(t):
        nxt=t[si+1][1] if si+1<len(t) else end
        raw,hsz,ents=read_stage(f,w0,name,off,nxt)
        for pi,pg in enumerate(pages(raw,hsz,ents)):
            gfiles=[x for x in pg['files'] if x[0]==6]
            if not gfiles: continue
            u=decode_page(raw,hsz,pg)
            fl=sorted(pg['files'],key=lambda x:x[2])
            for ty,h,o in gfiles:
                k=[x[2] for x in fl].index(o); e=fl[k+1][2] if k+1<len(fl) else pg['usize']
                g=u[o:e]; r=parse(g)
                if r is None: print('no table',name,hex(h)); continue
                blocks.append(dict(src='stage',id=(name,pi,h),strs=r['strs'],glyphs=glyph_list(r['glyphs']),kind='gcx'))
    for nm in ('DEMO','VOX'):
        for pos,ty,s,get in walk(nm,os.path.join(R,"Metal Gear Solid 2 - Sons of Liberty (Japan).iso")):
            if ty!=4: continue
            r=sub_parse(get())
            if r is None: print('skip',nm,hex(pos)); continue
            ents,gl=r
            blocks.append(dict(src=nm.lower(),id=pos,strs=[e[3] for e in ents],meta=[e[:3] for e in ents],glyphs=glyph_list(gl),kind='sub'))
    pickle.dump(blocks,open(os.path.join(R,'work/blocks.pkl'),'wb'))
    print(len(blocks), sum(len(b['strs']) for b in blocks))
    allg=set(g for b in blocks for g in b['glyphs']); print('unique glyphs',len(allg))
if __name__=='__main__': main()
