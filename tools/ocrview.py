import pickle,sys,os,numpy as np
from PIL import Image,ImageDraw,ImageFont
sys.path.insert(0,'tools'); from ocr import g2a
res=pickle.load(open('work/ocr.pkl','rb'))
items=sorted(res.items(),key=lambda kv:kv[1][1][0])
a,b=int(sys.argv[1]),int(sys.argv[2]); sel=items[a:b]
f=ImageFont.truetype('C:/Windows/Fonts/msgothic.ttc',24)
fs=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',13)
cols=6; W=200; H=54
im=Image.new('L',(cols*W,((len(sel)+cols-1)//cols)*H),255); d=ImageDraw.Draw(im)
for i,(g,(cs,sc)) in enumerate(sel):
    x=i%cols*W; y=i//cols*H
    gi=Image.fromarray((255-g2a(g)*255).astype(np.uint8)).resize((48,48),Image.NEAREST); im.paste(gi,(x+2,y+3))
    d.text((x+52,y+2),str(a+i),font=fs,fill=0)
    d.text((x+52,y+22),''.join(cs[:5]),font=f,fill=0)
    d.line((x+W-2,y,x+W-2,y+H),fill=180); d.line((x,y+H-1,x+W,y+H-1),fill=180)
im.save(sys.argv[3])
