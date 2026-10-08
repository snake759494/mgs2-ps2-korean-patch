# 권리 및 외부 자료

이 저장소는 비공식 한국어 패치의 제작 도구·기술 문서·검증 자료 공개용입니다. 원작 게임 「METAL GEAR SOLID 2 SONS OF LIBERTY」(PS2, KONAMI)와 그 텍스트·이미지·음성·영상·실행 코드의 권리는 원 권리자(ⓒKONAMI 등)에게 있습니다. 원본 게임, 패치 적용 게임, 게임에서 추출한 실행파일·텍스처·동영상·음성·글꼴은 배포하지 않으며, 릴리즈에는 원본 디스크 이미지가 있어야만 쓸 수 있는 차분 파일(xdelta)만 첨부합니다.

이 저장소에는 **일본어 원문과 대사 번역 전문을 넣지 않았습니다.** 번역은 패치(xdelta) 안에만 들어 있습니다. `translation/glyph_chars.json` 은 게임 글리프 비트맵의 MD5 해시와 문자 한 글자의 대응표로, 빌드할 때 사용자의 원본 이미지에서 원문을 다시 읽는 데만 씁니다(비트맵 자체는 넣지 않음).

저장소 공개 자체가 모든 파일에 동일한 오픈소스 라이선스를 부여한다는 뜻은 아닙니다. 자체 제작 코드에 대한 별도 포괄 라이선스는 현재 지정하지 않았습니다.

NanumSquare Neo 는 SIL Open Font License 1.1 을 따르며 전문을 `LICENSES/NanumSquareNeo-OFL-1.1.txt` 에 보존했습니다(`docs/FONT_CREDITS.md`). xdelta, PCSX2, Python 라이브러리(numpy, Pillow, scipy, capstone, pycdlib, zstandard) 등 외부 도구는 각 프로젝트의 라이선스를 따르며 바이너리를 재배포하지 않습니다. 게임 코드의 디스어셈블 결과물은 넣지 않았고, 해석한 내용만 `docs/TECHNICAL.md` 에 정리했습니다.
