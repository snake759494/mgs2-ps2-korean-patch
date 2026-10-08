"""블록 문자열 디코딩 -> 고유 원문 목록(translation/src.tsv)"""
import pickle,json,sys,os,collections,hashlib
sys.path.insert(0,'tools')
from mgstext import decode,tokens,local_index
G=json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'translation/glyph_chars.json'),encoding='utf8'))
def block_kanji(b):
    gl=b['glyphs']
    def k(slot,idx):
        if b['kind']=='sub': i=idx if slot==3 else None
        else: i=idx if slot==2 else (idx+1020 if slot==4 else None)
        if i is None or i<0 or i>=len(gl): return '[%d:%d]'%(slot,idx)
        return G[hashlib.md5(gl[i]).hexdigest()]
    return k
def text_of(b,s): return decode(s,block_kanji(b))
if __name__=='__main__':
    blocks=pickle.load(open('work/blocks.pkl','rb'))
    uniq=collections.OrderedDict(); bad=0
    for bi,b in enumerate(blocks):
        k=block_kanji(b)
        for si,s in enumerate(b['strs']):
            if s is None: continue
            t=decode(s,k)
            if '[' in t and ':' in t: bad+=1
            uniq.setdefault(t,[]).append((bi,si))
    print('unique',len(uniq),'bad',bad, 'chars',sum(len(t) for t in uniq))
    for src in ('codec','stage','demo','vox'):
        u=set(t for t,refs in uniq.items() if any(blocks[bi]['src']==src for bi,si in refs))
        print(src,len(u),sum(len(t) for t in u))
    pickle.dump(uniq,open('work/uniq.pkl','wb'))
