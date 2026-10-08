"""원본 ISO에서 빌드에 필요한 파일 추출 -> extract/"""
import os, pycdlib
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ISO = os.path.join(R, "Metal Gear Solid 2 - Sons of Liberty (Japan).iso")
os.makedirs(os.path.join(R, 'extract'), exist_ok=True)
iso = pycdlib.PyCdlib()
iso.open(ISO)
for p, o in [('/SLPM_650.78;1', 'SLPM_650.78'), ('/MGS2/STAGE.DAT;1', 'STAGE.DAT'), ('/MGS2/CODEC.DAT;1', 'CODEC.DAT')]:
    iso.get_file_from_iso(os.path.join(R, 'extract', o), iso_path=p)
iso.close()
print('추출 완료')
