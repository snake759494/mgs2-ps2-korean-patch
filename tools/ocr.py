"""글리프 OCR: JIS 문자 렌더링과 상관계수 매칭"""
import pickle,numpy as np,os,sys
from PIL import Image,ImageDraw,ImageFont,ImageFilter
R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def g2a(g):
    a=np.zeros((24,24),np.float32)
    for i in range(576):
        a[i//24,i%24]=(g[i//4]>>(6-2*(i%4)))&3
    return a/3
def cands():
    cs=[]
    for hi in range(0x81,0xa0):
        for lo in range(0x40,0xfd):
            try: ch=bytes([hi,lo]).decode('cp932')
            except: continue
            if len(ch)==1: cs.append(ch)
    for hi in range(0xe0,0xeb):
        for lo in range(0x40,0xfd):
            try: ch=bytes([hi,lo]).decode('cp932')
            except: continue
            if len(ch)==1: cs.append(ch)
    return cs
FONTS=[('C:/Windows/Fonts/msgothic.ttc',0),('C:/Windows/Fonts/BIZ-UDGothicB.ttc',0),('C:/Windows/Fonts/YuGothB.ttc',0),('C:/Windows/Fonts/meiryob.ttc',0)]
def render(ch,font,size=22):
    im=Image.new('L',(24,24),0); d=ImageDraw.Draw(im)
    bb=d.textbbox((0,0),ch,font=font)
    w,h=bb[2]-bb[0],bb[3]-bb[1]
    d.text(((24-w)//2-bb[0],(24-h)//2-bb[1]),ch,font=font,fill=255)
    a=np.asarray(im,np.float32)/255
    if DIL: a=np.asarray(Image.fromarray((a*255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3)),np.float32)/255
    return a
DIL=False
def feat(a,N=32):
    m=a>0.4
    ys,xs=np.where(m)
    if len(ys)==0: return np.zeros(N*N,np.float32)
    y0,y1,x0,x1=ys.min(),ys.max()+1,xs.min(),xs.max()+1
    # 정사각형 기준으로 비율 유지(작은 글자 보존)
    h,w=y1-y0,x1-x0; S=max(h,w,12)
    cy,cx=(y0+y1)/2,(x0+x1)/2
    im=Image.fromarray((m*255).astype(np.uint8)).crop((int(cx-S/2),int(cy-S/2),int(cx-S/2)+S,int(cy-S/2)+S)).resize((N,N),Image.BILINEAR)
    im=im.filter(ImageFilter.GaussianBlur(1.5))
    v=np.asarray(im,np.float32).ravel(); v=v-v.mean(); n=np.linalg.norm(v)
    return v/(n if n else 1)
def main():
    blocks=pickle.load(open(os.path.join(R,'work/blocks.pkl'),'rb'))
    gl=sorted(set(g for b in blocks for g in b['glyphs']))
    cs=cands(); print(len(gl),'glyphs',len(cs),'cands')
    G=np.stack([feat(g2a(g)) for g in gl])
    best=np.full(len(gl),-9.0); arg=np.zeros(len(gl),int); second=[None]*len(gl)
    scores=np.zeros((len(gl),len(cs)),np.float32)
    global DIL
    for fp,ix in FONTS:
      for DIL in (False,True):
        for sz in (22,):
            f=ImageFont.truetype(fp,sz,index=ix)
            C=np.stack([feat(render(c,f,sz)) for c in cs])
            s=G@C.T; scores=np.maximum(scores,s)
            print(fp,sz,'done')
    order=np.argsort(-scores,axis=1)[:,:5]
    res={g:([cs[j] for j in order[i]],[float(scores[i,j]) for j in order[i]]) for i,g in enumerate(gl)}
    pickle.dump(res,open(os.path.join(R,'work/ocr.pkl'),'wb'))
    sc=np.array([v[1][0] for v in res.values()]); print('score quantiles',np.quantile(sc,[0.01,0.05,0.1,0.5]))
if __name__=='__main__': main()
