"""GCX 리소스표(문자열/폰트) 파서"""
import struct
MAGIC=struct.pack('<I',0x3bc4f833)
def find_table(g):
    """g: gcx 바이트. 리소스표 시작 T 반환"""
    end=len(g)
    for T in range(len(g)-16,0,-1):
        tot,ten,sr,fr=struct.unpack_from('<4I',g,T)
        if ten!=0x10 or sr<0x10 or (sr-0x10)%4 or fr>tot or sr>tot: continue
        if not (0<=end-(T+tot)<16): continue
        n=(sr-0x10)//4
        ok=True
        for k in range(n):
            e=struct.unpack_from('<I',g,T+0x10+4*k)[0]&0x7fffffff
            if T+sr+e>T+fr+4 and e!=0: ok=False;break
        if ok: return T
    return None
def parse(g):
    T=find_table(g)
    if T is None: return None
    tot,ten,sr,fr=struct.unpack_from('<4I',g,T)
    n=(sr-0x10)//4
    ents=[struct.unpack_from('<I',g,T+0x10+4*k)[0] for k in range(n)]
    S=T+sr; F=T+fr
    fsz=struct.unpack_from('<I',g,F)[0]
    strs=[]
    for e in ents:
        o=S+(e&0x7fffffff)
        if e>>31:
            z=g.index(b'\0',o); strs.append(g[o:z])
        else: strs.append(None)
    return dict(T=T,tot=tot,sr=sr,fr=fr,ents=ents,S=S,F=F,fsz=fsz,strs=strs,glyphs=g[F+4:F+4+fsz])
def split_codec(d):
    pos=[];i=0
    while (i:=d.find(MAGIC,i))>=0: pos.append(i); i+=4
    return [(p,(pos[j+1] if j+1<len(pos) else len(d))) for j,p in enumerate(pos)]
def has_local(b):
    """바이트열에 로컬 글리프 코드(0x8C~0x9B)가 있는가"""
    i=0
    while i<len(b):
        c=b[i]
        if c<0x80: i+=1; continue
        hi=c&0x9f
        if hi>=0x8c: return True
        i+=2
    return False
def rebuild(g,newstr):
    """newstr: {엔트리번호: 새 바이트(NUL 제외)}. 같은 길이의 gcx 반환"""
    r=parse(g); T,S,F=r['T'],r['S'],r['F']
    ents=r['ents']
    groups={}
    for k,e in enumerate(ents): groups.setdefault(e&0x7fffffff,[]).append(k)
    offs=sorted(groups)
    region=bytearray(); newoff={}
    for j,o in enumerate(offs):
        e=offs[j+1] if j+1<len(offs) else F-S
        ks=groups[o]; flagged=[k for k in ks if ents[k]>>31]
        if flagged:
            k0=flagged[0]; s=newstr.get(k0,r['strs'][k0])
            for k in flagged[1:]:
                if newstr.get(k,s)!=s: raise ValueError('공유 문자열 불일치')
            pos=len(region); region+=s+b'\0'
            # 같은 오프셋의 비문자열(길이 0 가정)
            for k in ks: newoff[k]=pos
        else:
            al=o%16
            while len(region)%16!=al: region+=b'\0'
            pos=len(region); region+=g[S+o:S+e]
            for k in ks: newoff[k]=pos
    allstr=[newstr.get(k,r['strs'][k]) for k in range(len(ents)) if ents[k]>>31]
    keepfont=any(has_local(x) for x in allstr)
    font=r['glyphs'] if keepfont else b''
    fr=(S-T)+len(region)
    out=bytearray(g[:T])
    tot=fr+4+len(font)
    out+=struct.pack('<4I',tot,0x10,r['sr'],fr)
    for k in range(len(ents)): out+=struct.pack('<I',(ents[k]&0x80000000)|newoff[k])
    assert len(out)==S
    out+=region+struct.pack('<I',len(font))+font
    if len(out)>len(g): raise OverflowError('gcx 넘침 %d>%d'%(len(out),len(g)))
    out+=b'\0'*(len(g)-len(out))
    return bytes(out)
