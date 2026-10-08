import struct
M=0xffffffff
def keyinit(h):
    k=(h^0x9385)&0xffff
    return ((((k^0x6576)<<16)|k)&M, (k*0x116)&M)
def crypt(buf,key,inc):
    n=len(buf)//4; w=list(struct.unpack('<%dI'%n,buf[:n*4]))
    for i in range(n):
        w[i]^=key; key=(key*0x02e90edd+inc)&M
    return struct.pack('<%dI'%n,*w)+buf[n*4:],key
def strcode(s):
    h=0
    for c in s.encode():
        h=((h>>19)|(h<<5))&0xffffff; h=(h+c)&0xffffff
    return h
STAGE='extract/STAGE.DAT'
def toc(path=STAGE):
    f=open(path,'rb'); d=f.read(0x800)
    w0=struct.unpack_from('<I',d,0)[0]
    hdr,k=crypt(d[4:16],w0,w0^0xf0f0)
    n=struct.unpack_from('<H',hdr,4)[0]
    t,k=crypt(d[16:16+n*12],k,w0^0xf0f0)
    out=[]
    for i in range(n):
        name=t[i*12:i*12+8].split(b'\0')[0].decode(); off=struct.unpack_from('<I',t,i*12+8)[0]
        out.append((name,off))
    return w0,out
def stage_key(w0,name):
    a=strcode(name)
    return (a*129+w0+0xa78925d9)&M,(a*129+0x7a88fb59)&M
import zlib
def page_decode(raw):
    h=struct.unpack_from('<H',raw,0)[0]
    k,i=keyinit(h)
    out,_=crypt(raw,k,i)
    out=bytearray(out); v=(struct.unpack_from('<H',out,0)[0]+0x8f3)&0xffff; struct.pack_into('<H',out,0,v)
    return bytes(out)
