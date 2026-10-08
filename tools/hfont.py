"""한글 글리프 생성: 24x24 2bpp"""
import numpy as np
from PIL import Image,ImageDraw,ImageFont
def render_glyph(ch,fontpath,size=22,yoff=0,thr=(70,150,220)):
    S=4; big=Image.new('L',(24*S,24*S),0); d=ImageDraw.Draw(big)
    f=ImageFont.truetype(fontpath,size*S)
    bb=d.textbbox((0,0),ch,font=f); w=bb[2]-bb[0]; h=bb[3]-bb[1]
    # 가로 중앙, 세로는 폰트 em 기준 중앙
    asc,desc=f.getmetrics()
    x=(24*S-w)//2-bb[0]; y=(24*S-(asc+desc))//2+yoff*S
    d.text((x,y),ch,font=f,fill=255)
    a=np.asarray(big.resize((24,24),Image.LANCZOS),np.float32)
    q=np.zeros((24,24),np.uint8)
    q[a>=thr[0]]=1; q[a>=thr[1]]=2; q[a>=thr[2]]=3
    return q
def pack(q):
    out=bytearray(144)
    for i in range(576):
        out[i//4]|=int(q[i//24,i%24])<<(6-2*(i%4))
    return bytes(out)
