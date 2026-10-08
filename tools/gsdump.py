"""PCSX2 GS 덤프에서 이미지 업로드 추출"""
import struct,sys,glob
def uploads(d):
    out=[]; i=0
    pat=bytes([0x52,0,0,0,0,0,0,0])
    while (i:=d.find(pat,i))>=0:
        j=i-8
        w,h=struct.unpack_from('<II',d,j)
        # 앞쪽 BITBLTBUF(0x50)
        bb=None
        for k in range(j-16,j-80,-16):
            if d[k+8]==0x50 and not any(d[k+9:k+16]): bb=struct.unpack_from('<Q',d,k)[0]; break
        # 뒤쪽 TRXDIR(0x53) 다음 IMAGE 태그
        p=j+16
        img=None
        for k in range(p,p+64,16):
            if d[k+8]==0x53:
                tag=struct.unpack_from('<Q',d,k+16)[0]
                nloop=tag&0x7fff; flg=(tag>>58)&3
                if flg==2: img=(k+32,nloop*16)
                break
        if bb is not None and img and 0<w<=2048 and 0<h<=2048:
            dbp=(bb>>32)&0x3fff; dbw=(bb>>48)&0x3f; dpsm=(bb>>56)&0x3f
            out.append(dict(w=w,h=h,dbp=dbp,dbw=dbw,psm=dpsm,off=img[0],size=img[1],data=d[img[0]:img[0]+img[1]]))
        i+=1
    return out
if __name__=='__main__':
    d=open(sys.argv[1],'rb').read()
    for u in uploads(d): print(u['w'],u['h'],u['dbp'],u['dbw'],hex(u['psm']),u['size'])
