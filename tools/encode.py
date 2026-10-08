"""한국어 텍스트 -> MGS2 바이트 인코딩"""
import re,json,os
R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from mgstext import KANA
# 가나표에서 쓸 수 있는 전각 기호
SYM={ch:i for i,ch in enumerate(KANA) if i>=0xa5}
def kana_code(i):
    if i<0x50: return 0x8100+i+1
    if i<0xa4: return 0x8200+i-0x50
    return 0x8300+i-0xa4
HANGUL_BASE_HI=0x84
CAP=255*8
def hcode(idx):
    assert idx<CAP
    return ((HANGUL_BASE_HI+idx//255)<<8)|(idx%255+1)
class Encoder:
    def __init__(self,charlist):
        self.cmap={c:hcode(i) for i,c in enumerate(charlist)}
    def enc(self,text,ruby_tail=True):
        out=bytearray(); i=0
        def put(code): out.extend(bytes([code>>8,code&0xff]))
        while i<len(text):
            ch=text[i]
            if ch=='{':
                j=text.index('}',i); base,ruby=text[i+1:j].split(':',1)
                put(0x8023); put(0xa07b); out.extend(self.enc(base)); put(0xc308); out.extend(self.enc(ruby)); put(0xc07d)
                if ruby_tail: put(0x8023)
                i=j+1; continue
            if ch=='\n': out.append(0x0a)
            elif ch==' ': out.append(0x20)
            elif ch in self.cmap: put(self.cmap[ch])
            elif 0x21<=ord(ch)<0x7f: put(0x8000|ord(ch))
            elif ch in SYM: put(kana_code(SYM[ch]))
            else: raise ValueError('인코딩 불가 문자 %r in %r'%(ch,text))
            i+=1
        return bytes(out)
