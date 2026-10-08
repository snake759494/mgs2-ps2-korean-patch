import sys
d=open(sys.argv[1],'rb').read()
good=bytes(1 if all(((b>>k)&3) in (0,3) for k in (0,2,4,6)) else 0 for b in range(256))
step=48
runs=[];cur=None
for i in range(0,len(d)-144,step):
    blk=d[i:i+144]
    sc=sum(good[c] for c in blk)/144; nz=sum(1 for c in blk if c)/144
    if sc>0.95 and 0.1<nz<0.9:
        if cur is None: cur=i
    else:
        if cur is not None and i-cur>=144*8: runs.append((hex(cur),(i-cur)//144))
        cur=None
print(runs)
