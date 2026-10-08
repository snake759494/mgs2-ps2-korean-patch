"""PCSX2 PINE 제어: 세이브스테이트 생성/RAM 추출 (로컬 QA 전용)"""
from pathlib import Path
import socket,struct,time,zipfile,sys,subprocess,zstandard
R=Path(__file__).resolve().parents[1]; D=R/'work/emu'
def command(payload):
    with socket.create_connection(('127.0.0.1',28127),10) as s:
        s.sendall(struct.pack('<I',len(payload)+4)+payload)
        def recv(n):
            out=b''
            while len(out)<n:
                c=s.recv(n-len(out))
                if not c: raise EOFError
                out+=c
            return out
        size=struct.unpack('<I',recv(4))[0];out=recv(size-4);assert out[0]==0,out;return out[1:]
def read32(a): return struct.unpack('<I',command(struct.pack('<BI',2,a)))[0]
def write32(a,v): command(struct.pack('<BII',6,a,v))
def write8(a,v): command(struct.pack('<BIB',4,a,v))
def launch(iso):
    return subprocess.Popen([str(D/'pcsx2-qt.exe'),'-batch','-fastboot','--',str(iso)],cwd=str(D))
def latest():
    ps=list((D/'sstates').glob('*.p2s'))
    return max(ps,key=lambda p:p.stat().st_mtime) if ps else None
def savestate(slot=1):
    old=latest(); t=old.stat().st_mtime_ns if old else 0
    command(bytes([9,slot]))
    for _ in range(300):
        p=latest()
        if p and p.stat().st_mtime_ns>t:
            time.sleep(1); return p
        time.sleep(.1)
    raise TimeoutError
def member(p,name):
    with zipfile.ZipFile(p) as z:
        i=z.getinfo(name)
        if i.compress_type!=93: return z.read(i)
    with open(p,'rb') as f:
        f.seek(i.header_offset);h=f.read(30);n,e=struct.unpack_from('<HH',h,26);f.seek(n+e,1)
        return zstandard.ZstdDecompressor().decompress(f.read(i.compress_size),max_output_size=i.file_size)
def dump(tag):
    p=savestate()
    (R/f'work/ram_{tag}.bin').write_bytes(member(p,'eeMemory.bin'))
    (R/f'work/gs_{tag}.bin').write_bytes(member(p,'GS.bin'))
    try: (R/f'work/shot_{tag}.png').write_bytes(member(p,'Screenshot.png'))
    except KeyError: pass
    print('saved',tag)
if __name__=='__main__':
    if sys.argv[1]=='launch': launch(sys.argv[2]); print('launched')
    if sys.argv[1]=='dump': dump(sys.argv[2])
