"""DEMO/VOX/MOVIE 청크 스트림 순회"""
import struct,sys,collections
ISO="Metal Gear Solid 2 - Sons of Liberty (Japan).iso"
FILES={'DEMO':(470469,1792903168),'VOX':(1695572,1174542336),'MOVIE':(982,961509376)}
def walk(name,iso=ISO):
    lba,size=FILES[name]
    f=open(iso,'rb'); base=lba*2048
    pos=0; buf=b''; bstart=0
    def rd(p,n):
        nonlocal buf,bstart
        if not (bstart<=p and p+n<=bstart+len(buf)):
            f.seek(base+p); buf=f.read(max(n,1<<22)); bstart=p
        return buf[p-bstart:p-bstart+n]
    while pos<size:
        h=rd(pos,16)
        t,s=struct.unpack_from('<II',h)
        if t==0 and s==0:
            pos=(pos+0x800)&~0x7ff; continue
        yield pos,t,s,(lambda p=pos,s=s: rd(p,s))
        pos+=s
        if t==0xf0: pos=(pos+0x7ff)&~0x7ff
if __name__=='__main__':
    c=collections.Counter(); last=0
    for pos,t,s,get in walk(sys.argv[1]):
        c[t]+=1; last=pos+s
    print(c.most_common(), hex(last), hex(FILES[sys.argv[1]][1]))
