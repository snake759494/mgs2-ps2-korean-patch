# 메탈기어 솔리드 2 선즈 오브 리버티 (PS2) 한글패치

PS2 일본판 **METAL GEAR SOLID 2 SONS OF LIBERTY (SLPM-65078)** 용 비공식 한국어 패치입니다. 코덱 무전, 컷신 자막, 인게임 음성 자막, 아이템·무기 설명과 게임 내 문서, 그리고 그림 속 글자(지역명 카드·조작 튜토리얼·컨트롤러 조작 도해·고지문·인용문·스태프 크레디트)를 한국어로 바꿨습니다. 현재 배포판은 **v1.0 (2026-10-08)** 입니다.

[패치 다운로드](https://github.com/snake759494/mgs2-ps2-korean-patch/releases/latest) · [기술 설명](docs/TECHNICAL.md) · [재빌드](docs/BUILD.md) · [변경 기록](CHANGELOG.md) · [권리 안내](RIGHTS.md)

릴리즈 첨부 파일은 **MGS2_PS2_KO_v1.0.xdelta 하나**입니다. 저장소에는 제작 도구·기술 문서·번역 규칙·검증 자료만 공개합니다. 원본 및 완성 디스크 이미지, 추출한 게임 파일, 글꼴 파일, 외부 실행 파일, 일본어 원문, **대사 번역 전문**은 포함하지 않습니다(번역은 패치 안에만 들어 있습니다). GitHub 가 자동 생성하는 Source code ZIP/TAR 는 저장소 소스의 압축본이며 게임 파일이 아닙니다.

## 대상 버전

이 패치는 **PS2 일본판 SLPM-65078 의 DVD ISO (2,048 바이트 섹터)** 에만 적용합니다. 파일 이름보다 아래 크기와 해시가 일치하는지가 중요합니다.

| 항목 | 값 |
| --- | --- |
| 게임 ID | SLPM-65078 |
| 원본 형식 | 수정되지 않은 일본판 DVD ISO |
| 원본 ISO 크기 | 4,648,140,800 바이트 |
| **원본 ISO MD5** | `fa759417f83449258e6d5fa17bd2c2e3` |
| 원본 ISO SHA-256 | `aa3a1d8541d01a627a203a443bfd9a8f51dc223930d42c958a8b21c529918819` |
| xdelta 파일 크기 | 254,355,897 바이트 |
| xdelta SHA-256 | `abef500d05ebebfe9f58da42a61f32e4e91cb6ab5f9bbbe8089482882c8878cd` |
| 적용 결과 ISO 크기 | 4,649,144,320 바이트 (실행 파일을 디스크 끝으로 옮겨 1,003,520 바이트 늘어남) |
| 적용 결과 ISO SHA-256 | `4ac5f9b2cf94ed092f3b8fc66601887ce584f4f60a76189808ddbd514284140c` |

## 패치 적용 방법

### Windows 에서 원본 확인

```powershell
Get-FileHash -Algorithm MD5 -LiteralPath '.\Metal Gear Solid 2 - Sons of Liberty (Japan).iso'
```

위 표와 다르면 적용을 중단하세요. CHD·CSO 등으로 변환한 이미지에는 적용할 수 없습니다.

### xdelta UI 사용

1. 릴리즈에서 `MGS2_PS2_KO_v1.0.xdelta` 를 받습니다.
2. xdelta3 패치를 지원하는 도구의 **Apply Patch** 기능을 엽니다.
3. **Patch** 에 xdelta 파일, **Source File** 에 해시가 일치하는 원본 `.iso` 를 선택합니다.
4. **Output File** 에 새 파일명(예: `Metal Gear Solid 2 - Sons of Liberty (Korean).iso`)을 지정합니다.

xdelta 는 호환성을 위해 2차 압축과 파일 경로 헤더 없이 만들었습니다(`-e -9 -S none -A`).

### 명령줄 사용

```powershell
.\xdelta3.exe -d -s '.\Metal Gear Solid 2 - Sons of Liberty (Japan).iso' '.\MGS2_PS2_KO_v1.0.xdelta' '.\Metal Gear Solid 2 - Sons of Liberty (Korean).iso'
```

## 한글화 범위

- 고유 문자열 9,398개
  - 코덱 무전 대사 (CODEC.DAT)
  - 컷신 자막 (DEMO.DAT)
  - 인게임 음성 자막 (VOX.DAT)
  - 스테이지 스크립트 문자열: 아이템·무기 설명, 메뉴 안내, 지역명, 게임 내 문서·책
  - 영문·숫자뿐인 88개는 원문 유지
- 한글 글꼴 1,182자 (NanumSquare Neo ExtraBold, 원본 24×24 2bpp 형식)
- 그림 속 글자: 텍스처 묶음 53개, 텍스처 영역 70개, 687곳
  - 지역명 카드, 조작 튜토리얼, 컨트롤러 조작 도해, 구역 표지
  - 난이도 표기, 예/아니오 버튼, 시작 고지문, 플랜트 편 인용문
  - 오프닝·엔딩 스태프 크레디트 (직함은 한국어, 일본인 인명은 한글 음역)
- 그대로 둔 것: 원래 영어인 그림(메인 메뉴 NEW GAME 등, 영문 지역명 줄), 로고, 저작권 표기

## 알려진 점

- PCSX2 v2.2.0 에서 확인한 범위는 다음과 같습니다. 전체 스토리 완주와 실기 확인은 하지 않았습니다.
  - 부팅, 새 게임 질문 화면(루비 표기 포함), 레이더 선택 화면
  - 시작 고지문, 오프닝 컷신 자막, 유조선 첫 코덱 무전, 인게임 음성 자막
- 지역명 카드·튜토리얼·조작 도해·인용문·크레디트는 교체 전후 텍스처 이미지로 검수했습니다. 실제 게임에서 해당 장면까지 진행해 확인하지는 않았습니다.
- 그림만 보고 음역한 스태프 인명은 표기가 틀릴 수 있습니다.
- 대사창 글자가 잘리거나 일본어가 남은 화면을 발견하면 이슈로 스크린샷과 함께 알려 주세요.
