import sys
from PIL import Image
def render(d,base,n,w=24,h=24,cols=16,scale=2):
    gb=w*h//4; rows=(n+cols-1)//cols
    im=Image.new('L',(cols*(w+2),rows*(h+2)),40)
    for g in range(n):
        b=d[base+g*gb:base+(g+1)*gb]
        for y in range(h):
            for x in range(w):
                i=y*w+x; v=(b[i//4]>>(6-2*(i%4)))&3
                im.putpixel((g%cols*(w+2)+x,g//cols*(h+2)+y),v*85)
    return im.resize((im.width*scale,im.height*scale))
if __name__=='__main__':
    d=open(sys.argv[1],'rb').read()
    render(d,int(sys.argv[2],16),int(sys.argv[3])).save(sys.argv[4])
