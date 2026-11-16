# Computer Security Monitor

Windows용 화면·웹캠 캡처 및 관리 도구입니다.

## 주요 기능

- 시작 시 화면을 캡처하고 웹캠 사진 촬영을 시도합니다.
- 설정한 프로그램이 실행 중이면 지정한 간격으로 화면을 캡처합니다.
- Windows 잠금/해제 상태를 감지하며, `Ctrl+Alt+K`로 현재 감시를 중지할 수 있습니다.
- 제어판에서 감시 대상 프로그램, 캡처 간격, 로그와 캡처 파일을 관리합니다.
- 필요한 Python 패키지가 없으면 실행 시 `requirements.txt`를 기준으로 자동 설치합니다.

> 화면과 웹캠 자료가 저장되므로, 소유하거나 관리 권한이 있는 PC에서 관련 사용자의 동의를 받고 사용하세요.

## 사용법

1. Windows에 Python 3을 설치합니다.
2. `run_control_panel.vbs`를 실행해 감시 대상과 캡처 간격을 설정합니다.
3. `run_security.vbs`를 실행해 감시를 시작합니다.

명령줄에서 실행할 수도 있습니다:

```powershell
py control_panel.py
# 다른 PowerShell 창에서 실행
py capture.py
```

캡처 파일과 로그는 `Logs` 폴더에 저장됩니다. 설정은 `config.json`에서 확인할 수 있습니다.
