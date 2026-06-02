# Clipboard Manager

Windows용 클립보드 히스토리 매니저 — PyQt6 기반 다크 테마 UI

![Python](https://img.shields.io/badge/Python-3.10+-blue) ![PyQt6](https://img.shields.io/badge/PyQt6-6.x-green) ![Windows](https://img.shields.io/badge/Windows-10%2F11-lightgrey)

## 기능

- 복사한 텍스트 · 이미지를 자동으로 카드 형태로 저장
- **단축키** (기본: CapsLock) 로 커서 위치에 팝업 즉시 호출
- 카드 클릭 한 번으로 클립보드 복사 + 자동 붙여넣기
- 텍스트 편집 (Ctrl+휠 줌) / 이미지 드로잉 (Undo · Redo · Clear)
- 핀 고정 — 상단 유지 및 삭제 방지
- 중복 감지 — 동일 내용 재복사 시 기존 카드 상단 이동
- 멀티모니터 지원 — 커서가 있는 모니터에 팝업 표시
- 시스템 트레이 최소화 / Windows 시작프로그램 등록
- 파일 저장 경로: `~/Pictures/ClipboardSaver`

## 설치 및 실행

### 실행 파일 (권장)
`dist/ClipboardManager.exe` 를 직접 실행

### 소스에서 실행
```bash
pip install PyQt6
python clipboard_manager.py
```

## 설정

우상단 ⚙️ 버튼에서 변경 가능:

| 항목 | 설명 |
|------|------|
| 자동 실행 | Windows 시작 시 자동 실행 |
| 시작 시 트레이 | 실행 시 트레이로 최소화 |
| 팝업 단축키 | CapsLock 외 원하는 키로 변경 |

## 요구 사항

- Windows 10 / 11
- Python 3.10+ (소스 실행 시)
- PyQt6

## 라이선스

MIT License — 자세한 내용은 [LICENSE](LICENSE) 참고
