"""ELF 패치: 한글 폰트 세그먼트 추가 + 글리프 디코더 분기"""
import struct
HSEG=0x90000           # 세그먼트 가상주소(코드)
HFONT=0x90100          # 폰트 시작
DECODER=0x115ce8
def asm_hook():
    # MIPS 명령 인코딩
    def R(op,rs,rt,rd,sh,fn): return (op<<26)|(rs<<21)|(rt<<16)|(rd<<11)|(sh<<6)|fn
    def I(op,rs,rt,imm): return (op<<26)|(rs<<21)|(rt<<16)|(imm&0xffff)
    def J(op,tgt): return (op<<26)|((tgt>>2)&0x3ffffff)
    zero,v0,v1,a0,a1,a2,a3,t0,t1,t2,t3,t4,t5,ra=0,2,3,4,5,6,7,8,9,10,11,12,13,31
    code=[
        I(0x0c,a0,t0,0x9fff),        # andi t0,a0,0x9fff
        R(0,0,t0,t1,8,2),            # srl t1,t0,8
        I(0x09,t1,t1,-0x84),         # addiu t1,t1,-0x84
        I(0x0b,t1,t2,8),             # sltiu t2,t1,8
        I(0x04,t2,zero,10),          # beq t2,zero,orig (+10)
        I(0x0c,t0,t3,0xff),          # andi t3,t0,0xff (delay)
        R(0,0,t1,t4,8,0),            # sll t4,t1,8
        R(0,t4,t1,t4,0,0x23),        # subu t4,t4,t1
        R(0,t4,t3,t4,0,0x21),        # addu t4,t4,t3
        I(0x09,t4,t4,-1),            # addiu t4,t4,-1
        R(0,0,t4,t5,3,0),            # sll t5,t4,3
        R(0,t5,t4,t5,0,0x21),        # addu t5,t5,t4
        R(0,0,t5,t5,4,0),            # sll t5,t5,4
        I(0x0f,0,v0,HFONT>>16),      # lui v0,hi
        R(0,ra,0,0,0,8),             # jr ra
        I(0x09,t5,v0,0),             # addiu v0,t5,0 -> 아래에서 or
    ]
    # 마지막: v0 = HFONT + t5 (lui 결과에 더하기)
    code[-1]=R(0,v0,t5,v0,0,0x21)    # addu v0,v0,t5  (delay slot)
    # HFONT 하위 16비트 보정
    code.insert(14,I(0x09,v0,v0,HFONT&0xffff))  # addiu v0,v0,lo
    # orig: (beq 오프셋 재계산)
    orig_idx=len(code)
    code+=[
        I(0x09,zero,v1,-0x6001),     # addiu v1,zero,-0x6001
        I(0x0f,0,v0,0xffff),         # lui v0,0xffff
        J(0x02,DECODER+8),           # j 0x115cf0
        0,                           # nop
    ]
    code[4]=I(0x04,t2,zero,orig_idx-5)
    return b''.join(struct.pack('<I',w) for w in code)
def patch(elf,font):
    elf=bytearray(elf)
    phoff=struct.unpack_from('<I',elf,0x1c)[0]; n=struct.unpack_from('<H',elf,0x2c)[0]
    # 기존 데이터 세그먼트에서 디코더 위치(파일 오프셋)
    seg=[struct.unpack_from('<8I',elf,phoff+i*32) for i in range(n)]
    load=[s for s in seg if s[0]==1][0]
    def foff(va): return va-load[2]+load[1]
    hook=asm_hook()
    assert len(hook)<=0x100
    blob=hook.ljust(HFONT-HSEG,b'\0')+font
    off=(len(elf)+0xf)&~0xf
    elf+=b'\0'*(off-len(elf))+blob
    # REGINFO(0x70000000) 헤더를 PT_LOAD로 교체
    ri=[i for i,s in enumerate(seg) if s[0]==0x70000000][0]
    struct.pack_into('<8I',elf,phoff+ri*32,1,off,HSEG,HSEG,len(blob),len(blob),7,0x10)
    # 디코더 진입부: j HSEG ; nop
    struct.pack_into('<II',elf,foff(DECODER),(0x02<<26)|(HSEG>>2),0)
    return bytes(elf)
