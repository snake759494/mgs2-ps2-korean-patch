# 재빌드

이 저장소에는 **대사 번역 전문과 일본어 원문을 넣지 않았으므로**, 저장소만으로는 패치를 그대로 다시 만들 수 없습니다. 아래는 제작 환경의 빌드 순서와 각 도구의 역할을 기록한 것입니다. 번역 자료(`translation/ko_raw/*.json`, `ko_fix.json`, `tex_boxes.json`)는 제작자가 비공개로 보관합니다.

## 준비

- Python 3.12 이상과 다음 패키지: numpy, Pillow, scipy, capstone, pycdlib, zstandard
- 작업 폴더에 둘 것: 원본 `Metal Gear Solid 2 - Sons of Liberty (Japan).iso`, `NanumSquareNeo-dEb.ttf`, `NanumSquareNeo-cBd.ttf`
- 텍스처 전수조사에만 필요: Windows 10/11 의 일본어 OCR(`tools/ocr_ja.ps1`)

## 순서

```powershell
python tools/extract_iso.py   # ISO 에서 SLPM_650.78, STAGE.DAT, CODEC.DAT 추출
python tools/tex_pages.py     # 0x13 텍스처 영역 목록(work/view_index.json)
python tools/texbuild.py      # translation/tex_boxes.json -> 교체 텍스처
python tools/extract.py       # 모든 텍스트 블록 추출
python tools/make_keys.py     # 문자열 번호 -> 원문 키(비공개, 원본에서 다시 생성)
python tools/merge.py         # 번역 병합 + 문자 정규화
python tools/build.py         # 'Metal Gear Solid 2 - Sons of Liberty (Korean).iso' 생성
```

만든 이미지의 SHA-256 은 `validation/SHA256SUMS.txt` 의 결과 ISO 값과 같아야 합니다(제작 환경에서 위 순서로 재빌드해 일치를 확인).

## 주요 도구

| 파일 | 역할 |
| --- | --- |
| `stagecrypt.py`, `stage.py`, `stagepack.py` | STAGE.DAT TOC·스테이지·페이지 복호화, zlib 해제·재압축·재암호화 |
| `gcx.py` | GCX 리소스표 파싱·재구성 |
| `mgstext.py`, `decode_all.py`, `encode.py` | 게임 문자 디코드/인코드, 원문 키 생성 |
| `wrap.py`, `width.py` | 창 폭 기준 줄바꿈 |
| `hfont.py`, `elfpatch.py` | 한글 글리프 렌더, ELF 세그먼트·디코더 훅 |
| `tex13.py`, `texpatch.py`, `tex_pages.py`, `linefind.py`, `texbuild.py` | 텍스처 묶음 디코드·영역 판별·줄 분할·한글 덧칠 |
| `ocr_ja.ps1`, `ocr.py` | 일본어 OCR(텍스처 전수조사, 게임 한자 글리프 판독) |
| `build.py` | 전체 조립(ISO 복사 → CODEC/STAGE/자막 청크 → ELF 재배치) |
| `emu.py`, `keys.py`, `chunks.py`, `mips.py` | 분석·실행 검증 보조(PCSX2 PINE, 키 입력, 청크 순회, 디스어셈블) |
