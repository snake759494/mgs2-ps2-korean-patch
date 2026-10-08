"""MGS2 텍스트 인코딩"""
KANA=("ぁあぃいぅうぇえぉおかがきぎくぐけげこごさざしじすずせぜそぞただ"
"ちぢっつづてでとどなにぬねのはばぱひびぴふぶぷへべぺほぼぽまみむ"
"めもゃやゅゆょよらりるれろゎわをんァアィイゥウェエォオカガキギク"
"グケゲコゴサザシジスズセゼソゾタダチヂッツヅテデトドナニヌネノハ"
"バパヒビピフブプヘベペホボポマミムメモャヤュユョヨラリルレロヮワ"
"ヲンヴヵヶ　○△□×！？、。」』］〉》】”’ー―…‥「『〈《［【“‘")
def tokens(b):
    i=0;out=[]
    while i<len(b):
        c=b[i]
        if c<0x80: out.append(c); i+=1
        else: out.append((c<<8)|b[i+1]); i+=2
    return out
def local_index(code):
    """로컬 글리프 코드 -> (슬롯, 슬롯내 인덱스)"""
    c=code&~0x6000
    s=(c-0x8400)>>10
    v=c-s*0x400-0x8401
    return s, v-(v>>8) if v>=0 else v
def kana_index(code):
    c=code&~0x6000; hi=c>>8; lo=c&0xff
    if hi==0x81: return lo-1
    if hi==0x82: return lo+0x50
    if hi==0x83: return lo+0xa4
    return None
def decode(b,kanji=lambda s,i:'〓'):
    """kanji(slot,idx)->문자"""
    s=''
    for t in tokens(b):
        if t<0x80:
            s+= '\n' if t==0x0a else chr(t)
            continue
        c=t&~0x6000; hi=c>>8; fl=t&0x6000
        if hi==0x80:
            ch=chr(c&0xff)
            s+= {0x2000:'⟨',0x4000:'⟩'}.get(fl,'')+ch if fl else ch
        elif hi in (0x81,0x82,0x83):
            k=kana_index(t); s+= KANA[k] if 0<=k<len(KANA) else '[%04x]'%t
            if fl: s+='⁺' if fl==0x4000 else '⁻'
        else:
            sl,ix=local_index(t); s+=kanji(sl,ix)
    return s
