"""PCSX2 창에 키 입력 전송 (로컬 QA 전용). 사용: python keys.py Return 1.0 Down K ..."""
import ctypes, time, sys
from ctypes import wintypes
u = ctypes.windll.user32
VK = {'Return': 0x0D, 'Up': 0x26, 'Down': 0x28, 'Left': 0x25, 'Right': 0x27, 'Backspace': 0x08,
      'K': 0x4B, 'L': 0x4C, 'I': 0x49, 'J': 0x4A, 'Q': 0x51, 'E': 0x45, '1': 0x31, '3': 0x33, 'F8': 0x77, 'Shift': 0x10}


def find():
    res = []
    pid = wintypes.DWORD()

    @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    def cb(h, l):
        if u.IsWindowVisible(h):
            n = u.GetWindowTextLengthW(h)
            b = ctypes.create_unicode_buffer(n + 1)
            u.GetWindowTextW(h, b, n + 1)
            t = b.value
            if 'PCSX2' in t or 'Metal Gear' in t or 'METAL GEAR' in t or 'SLPM' in t:
                res.append((h, t))
        return True
    u.EnumWindows(cb, 0)
    return res


def focus():
    ws = find()
    # 게임 화면 창 우선
    ws.sort(key=lambda x: ('PCSX2' in x[1] and len(x[1]) < 20))
    h = ws[0][0]
    u.keybd_event(0x12, 0, 0, 0)
    u.SetForegroundWindow(h)
    u.keybd_event(0x12, 0, 2, 0)
    time.sleep(0.3)
    return ws


def press(k, hold=0.12):
    vk = VK[k]
    sc = u.MapVirtualKeyW(vk, 0)
    ext = 1 if k in ('Up', 'Down', 'Left', 'Right') else 0
    u.keybd_event(vk, sc, ext, 0)
    time.sleep(hold)
    u.keybd_event(vk, sc, ext | 2, 0)
    time.sleep(0.15)


if __name__ == '__main__':
    print(focus())
    for a in sys.argv[1:]:
        if a=='GSDUMP':
            u.keybd_event(0x10,0,0,0); time.sleep(0.1); press('F8'); u.keybd_event(0x10,0,2,0); continue
        try:
            time.sleep(float(a))
        except ValueError:
            press(a)
