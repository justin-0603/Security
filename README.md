# Computer Security Monitor

A Windows utility for capturing and managing desktop screenshots and webcam photos.

## Features

- Captures the screen and attempts to take a webcam photo when monitoring starts.
- Captures the screen at a configured interval while a selected application is running.
- Detects Windows lock and unlock events. Press `Ctrl+Alt+K` to stop the current monitoring session.
- Includes a control panel for managing monitored applications, capture intervals, logs, and captured files.
- Installs missing Python packages from `requirements.txt` when the program starts.

> Screen and webcam data is saved locally. Use this tool only on a device you own or are authorized to administer, and with the consent of affected users.

## Usage

1. Install Python 3 on Windows.
2. Run `run_control_panel.vbs` to configure monitored applications and the capture interval.
3. Run `run_security.vbs` to start monitoring.

You can also run the scripts from PowerShell:

```powershell
py control_panel.py
# Run in a separate PowerShell window
py capture.py
```

Captures and logs are saved in the `Logs` folder. Settings are stored in `config.json`.
