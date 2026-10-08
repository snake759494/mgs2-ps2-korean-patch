import json,os
R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AW=json.load(open(os.path.join(R,'translation/ascii_width.json')))
def ch_w(c):
    if c in AW: return AW[c]+1
    return 24
def line_w(s):
    return sum(ch_w(c) for c in s)
