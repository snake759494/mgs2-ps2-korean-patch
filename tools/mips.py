"""ELF helper: disassemble / find lui+addiu xrefs in SLPM_650.78 (vaddr = off - 0x80 + 0x100000)."""
import struct, sys, capstone
ELF = open(__file__.rsplit('tools', 1)[0] + 'extract/SLPM_650.78', 'rb').read()
BASE, OFF, TEXT_END = 0x100000, 0x80, 0x1b0000
md = capstone.Cs(capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS64 | capstone.CS_MODE_LITTLE_ENDIAN)
md.skipdata = True
def rd(va, n): return ELF[va - BASE + OFF: va - BASE + OFF + n]
def u32(va): return struct.unpack('<I', rd(va, 4))[0]
def dis(va, n=40):
    for i in md.disasm(rd(va, n * 4), va): print(f"{i.address:08x}: {i.mnemonic:8s} {i.op_str}")
def xrefs(target, lo=BASE, hi=0x1ad000):
    """find lui rX,hi ... (addiu|lw|sw..) rY,lo(rX) within 40 insns"""
    res = []; hi16 = (target + 0x8000) >> 16; lo16 = target & 0xffff
    for va in range(lo, hi, 4):
        w = u32(va)
        if w >> 26 == 0xf and w & 0xffff == hi16:
            r = (w >> 16) & 31
            for k in range(1, 40):
                w2 = u32(va + 4 * k)
                if (w2 >> 21) & 31 == r and w2 & 0xffff == lo16 and w2 >> 26 != 0xf:
                    res.append(va + 4 * k); break
    return res
def words(target):
    return [BASE + i - OFF for i in range(OFF, len(ELF) - 3, 4) if struct.unpack_from('<I', ELF, i)[0] == target]
if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'dis': dis(int(sys.argv[2], 16), int(sys.argv[3]) if len(sys.argv) > 3 else 40)
    if cmd == 'x': print([hex(x) for x in xrefs(int(sys.argv[2], 16))], [hex(x) for x in words(int(sys.argv[2], 16))])
