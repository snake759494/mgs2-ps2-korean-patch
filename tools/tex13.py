"""유형 0x13 스프라이트 텍스처 묶음 디코드/인코드"""
import struct,numpy as np,sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import gsmem
VM=4<<20
def _a32(bw,w,h,bp=0):
    return np.array([[gsmem.addr32(bp,bw,x,y) for x in range(w)] for y in range(h)],np.int64)
_cache={}
def a32(bw,w,h,bp=0):
    k=(bw,w,h,bp)
    if k not in _cache: _cache[k]=_a32(bw,w,h,bp)
    return _cache[k]
def a4(bp,bw,w,h):
    k=('4',bp,bw,w,h)
    if k not in _cache: _cache[k]=np.array([[gsmem.addr4(bp,bw,x,y) for x in range(w)] for y in range(h)],np.int64)
    return _cache[k]
def a8(bp,bw,w,h):
    k=('8',bp,bw,w,h)
    if k not in _cache: _cache[k]=np.array([[gsmem.addr8(bp,bw,x,y) for x in range(w)] for y in range(h)],np.int64)
    return _cache[k]
def parse(f):
    n=struct.unpack_from('<I',f,0x10)[0]
    doff,dsz=struct.unpack_from('<II',f,0x18)
    ents=[]
    for k in range(n):
        e=0x20+k*0xa0
        if f[e+0x48]!=0x16: return None
        t0=struct.unpack_from('<Q',f,e+0x50)[0]
        rect=struct.unpack_from('<4f',f,e)
        ents.append(dict(e=e,t0=t0,rect=rect,name=struct.unpack_from('<I',f,e+0x10)[0]))
    return dict(n=n,doff=doff,dsz=dsz,ents=ents)
def upload(blob):
    """폭 64 CT32 스트립으로 bp=0에 업로드한 VRAM"""
    vm=np.zeros(VM,np.uint8)
    rows=len(blob)//256
    idx=a32(1,64,rows)
    w=np.frombuffer(blob[:rows*256],np.uint8).reshape(rows,64,4)
    for k in range(4): vm[idx+k]=w[:,:,k]
    return vm,idx
def download(vm,idx):
    return np.stack([vm[idx+k] for k in range(4)],-1).tobytes()
def tex0(v): return dict(tbp=v&0x3fff,tbw=(v>>14)&0x3f,psm=(v>>20)&0x3f,tw=1<<((v>>26)&15),th=1<<((v>>30)&15),cbp=(v>>37)&0x3fff,cpsm=(v>>51)&15,csm=(v>>55)&1,csa=(v>>56)&31)
def clut(vm,t):
    c=np.stack([vm[a32(1,16,16,t['cbp'])+k] for k in range(4)],-1).reshape(256,4)
    i=np.arange(256); p=(i&~0x18)|((i&8)<<1)|((i&16)>>1)
    return c[p]
def sprite_box(t,rect):
    W,H=t['tw'],t['th']
    x0=int(round(rect[0]*W)); y0=int(round(rect[1]*H)); w=int(round(rect[2]*W)); h=int(round(rect[3]*H))
    return x0,y0,w,h
def decode(vm,ent):
    t=tex0(ent['t0']); x0,y0,w,h=sprite_box(t,ent['rect'])
    if t['psm']==0x14:
        a=a4(t['tbp'],t['tbw'],t['tw'],t['th'])[y0:y0+h,x0:x0+w]
        b=vm[a>>1]; ix=np.where(a&1,b>>4,b&15).astype(np.int32)+t['csa']*16
    elif t['psm']==0x13:
        a=a8(t['tbp'],t['tbw'],t['tw'],t['th'])[y0:y0+h,x0:x0+w]; ix=vm[a].astype(np.int32)
    else: return None,None
    c=clut(vm,t)
    return ix,c[ix]
