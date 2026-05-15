import os
import time
import json
import datetime
import threading
import hashlib
import shutil
import win32file
import win32con
import win32api
import win32event
import win32security
import winnt
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import psutil
import wmi

class WindowsFileMonitor:
    def __init__(self, path=None):
        self.wmi_client = wmi.WMI()
        self.monitoring = False
        self.monitored_paths = []
        self.file_events = []
        self.file_hashes = {}
        
        if path:
            self.add_path(path)
        
        # Set up file system observer
        self.observer = Observer()
    
    def add_path(self, path):
        """Add a path to monitor"""
        if os.path.exists(path) and path not in self.monitored_paths:
            self.monitored_paths.append(path)
            return True
        return False
    
    def remove_path(self, path):
        """Remove a path from monitoring"""
        if path in self.monitored_paths:
            self.monitored_paths.remove(path)
            return True
        return False
    
    def get_file_info(self, file_path):
        """Get detailed information about a file"""
        try:
            if not os.path.exists(file_path):
                return None
            
            stat_info = os.stat(file_path)
            
            file_info = {
                'path': file_path,
                'name': os.path.basename(file_path),
                'extension': os.path.splitext(file_path)[1],
                'size': stat_info.st_size,
                'created': datetime.fromtimestamp(stat_info.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                'modified': datetime.fromtimestamp(stat_info.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                'accessed': datetime.fromtimestamp(stat_info.st_atime).strftime('%Y-%m-%d %H:%M:%S'),
                'is_directory': os.path.isdir(file_path),
                'is_hidden': bool(os.stat(file_path).st_file_attributes & win32file.FILE_ATTRIBUTE_HIDDEN),
                'is_readonly': bool(os.stat(file_path).st_file_attributes & win32file.FILE_ATTRIBUTE_READONLY),
                'is_system': bool(os.stat(file_path).st_file_attributes & win32file.FILE_ATTRIBUTE_SYSTEM)
            }
            
            # Calculate file hash if it's a file (not directory)
            if not file_info['is_directory']:
                file_hash = self.calculate_file_hash(file_path)
                if file_hash:
                    file_info['hash'] = file_hash
            
            # Get owner information
            try:
                sd = win32security.GetFileSecurity(file_path, win32security.OWNER_SECURITY_INFORMATION)
                owner_sid = sd.GetSecurityDescriptorOwner()
                owner_name, owner_domain, _ = win32security.LookupAccountSid(None, owner_sid)
                file_info['owner'] = f"{owner_domain}\\{owner_name}"
            except:
                file_info['owner'] = "Unknown"
            
            # Get file permissions
            try:
                sd = win32security.GetFileSecurity(file_path, win32security.DACL_SECURITY_INFORMATION)
                dacl = sd.GetSecurityDescriptorDacl()
                
                permissions = []
                if dacl:
                    for i in range(dacl.GetAceCount()):
                        ace = dacl.GetAce(i)
                        account_sid = ace[2]
                        account_name, account_domain, _ = win32security.LookupAccountSid(None, account_sid)
                        
                        access_mask = ace[1]
                        access_rights = []
                        
                        if access_mask & winnt.FILE_READ_DATA:
                            access_rights.append("Read")
                        if access_mask & winnt.FILE_WRITE_DATA:
                            access_rights.append("Write")
                        if access_mask & winnt.FILE_EXECUTE:
                            access_rights.append("Execute")
                        if access_mask & winnt.DELETE:
                            access_rights.append("Delete")
                        
                        permissions.append({
                            'account': f"{account_domain}\\{account_name}",
                            'rights': access_rights
                        })
                
                file_info['permissions'] = permissions
            except:
                file_info['permissions'] = []
            
            # Get file version info if it's an executable
            if file_info['extension'] in ['.exe', '.dll']:
                try:
                    info = win32api.GetFileVersionInfo(file_path, "\\")
                    ms = info['FileVersionMS']
                    ls = info['FileVersionLS']
                    
                    file_info['version'] = f"{win32api.HIWORD(ms)}.{win32api.LOWORD(ms)}.{win32api.HIWORD(ls)}.{win32api.LOWORD(ls)}"
                except:
                    file_info['version'] = "Unknown"
            
            return file_info
            
        except Exception as e:
            print(f"Error getting file info for {file_path}: {e}")
            return None
    
    def calculate_file_hash(self, file_path, algorithm='sha256'):
        """Calculate hash of a file"""
        try:
            if algorithm == 'md5':
                hash_func = hashlib.md5()
            elif algorithm == 'sha1':
                hash_func = hashlib.sha1()
            else:  # Default to sha256
                hash_func = hashlib.sha256()
            
            with open(file_path, 'rb') as f:
                # Read file in chunks to handle large files
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_func.update(chunk)
            
            return hash_func.hexdigest()
            
        except Exception as e:
            print(f"Error calculating hash for {file_path}: {e}")
            return None
    
    def scan_directory(self, directory, recursive=True):
        """Scan a directory and return information about all files"""
        files = []
        
        try:
            if recursive:
                for root, dirs, filenames in os.walk(directory):
                    for filename in filenames:
                        file_path = os.path.join(root, filename)
                        file_info = self.get_file_info(file_path)
                        if file_info:
                            files.append(file_info)
            else:
                for item in os.listdir(directory):
                    item_path = os.path.join(directory, item)
                    file_info = self.get_file_info(item_path)
                    if file_info:
                        files.append(file_info)
            
            return files
            
        except Exception as e:
            print(f"Error scanning directory {directory}: {e}")
            return []
    
    def find_files_by_name(self, name_pattern, search_paths=None):
        """Find files by name pattern"""
        if search_paths is None:
            search_paths = self.monitored_paths
        
        found_files = []
        
        for path in search_paths:
            if os.path.exists(path):
                for root, dirs, filenames in os.walk(path):
                    for filename in filenames:
                        if name_pattern.lower() in filename.lower():
                            file_path = os.path.join(root, filename)
                            file_info = self.get_file_info(file_path)
                            if file_info:
                                found_files.append(file_info)
        
        return found_files
    
    def find_files_by_extension(self, extension, search_paths=None):
        """Find files by extension"""
        if search_paths is None:
            search_paths = self.monitored_paths
        
        found_files = []
        
        # Ensure extension starts with a dot
        if not extension.startswith('.'):
            extension = '.' + extension
        
        for path in search_paths:
            if os.path.exists(path):
                for root, dirs, filenames in os.walk(path):
                    for filename in filenames:
                        if filename.lower().endswith(extension.lower()):
                            file_path = os.path.join(root, filename)
                            file_info = self.get_file_info(file_path)
                            if file_info:
                                found_files.append(file_info)
        
        return found_files
    
    def find_files_by_size(self, min_size=None, max_size=None, search_paths=None):
        """Find files by size range (in bytes)"""
        if search_paths is None:
            search_paths = self.monitored_paths
        
        found_files = []
        
        for path in search_paths:
            if os.path.exists(path):
                for root, dirs, filenames in os.walk(path):
                    for filename in filenames:
                        file_path = os.path.join(root, filename)
                        try:
                            size = os.path.getsize(file_path)
                            
                            if (min_size is None or size >= min_size) and (max_size is None or size <= max_size):
                                file_info = self.get_file_info(file_path)
                                if file_info:
                                    found_files.append(file_info)
                        except:
                            pass
        
        return found_files
    
    def find_files_by_date(self, start_date=None, end_date=None, date_type='modified', search_paths=None):
        """Find files by date range"""
        if search_paths is None:
            search_paths = self.monitored_paths
        
        found_files = []
        
        for path in search_paths:
            if os.path.exists(path):
                for root, dirs, filenames in os.walk(path):
                    for filename in filenames:
                        file_path = os.path.join(root, filename)
                        try:
                            stat_info = os.stat(file_path)
                            
                            if date_type == 'created':
                                file_date = datetime.fromtimestamp(stat_info.st_ctime)
                            elif date_type == 'accessed':
                                file_date = datetime.fromtimestamp(stat_info.st_atime)
                            else:  # Default to modified
                                file_date = datetime.fromtimestamp(stat_info.st_mtime)
                            
                            if (start_date is None or file_date >= start_date) and (end_date is None or file_date <= end_date):
                                file_info = self.get_file_info(file_path)
                                if file_info:
                                    found_files.append(file_info)
                        except:
                            pass
        
        return found_files
    
    def find_duplicate_files(self, search_paths=None):
        """Find duplicate files based on hash"""
        if search_paths is None:
            search_paths = self.monitored_paths
        
        hash_map = {}
        duplicates = []
        
        for path in search_paths:
            if os.path.exists(path):
                for root, dirs, filenames in os.walk(path):
                    for filename in filenames:
                        file_path = os.path.join(root, filename)
                        try:
                            file_hash = self.calculate_file_hash(file_path)
                            if file_hash:
                                if file_hash in hash_map:
                                    duplicates.append({
                                        'original': hash_map[file_hash],
                                        'duplicate': file_path,
                                        'hash': file_hash,
                                        'size': os.path.getsize(file_path)
                                    })
                                else:
                                    hash_map[file_hash] = file_path
                        except Exception:
                            pass
        
        return duplicates
    
    def start_monitoring(self, callback=None):
        """Start monitoring file system changes using watchdog"""
        self.monitoring = True
        
        class FileChangeHandler(FileSystemEventHandler):
            def __init__(self, monitor, callback=None):
                super().__init__()
                self.monitor = monitor
                self.callback = callback
            
            def on_created(self, event):
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                event_data = {
                    'type': 'created',
                    'path': event.src_path,
                    'is_directory': event.is_directory,
                    'timestamp': timestamp
                }
                self.monitor.file_events.append(event_data)
                print(f"[{timestamp}] Created: {event.src_path}")
                if self.callback:
                    self.callback(event_data)
            
            def on_modified(self, event):
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                event_data = {
                    'type': 'modified',
                    'path': event.src_path,
                    'is_directory': event.is_directory,
                    'timestamp': timestamp
                }
                self.monitor.file_events.append(event_data)
                print(f"[{timestamp}] Modified: {event.src_path}")
                if self.callback:
                    self.callback(event_data)
            
            def on_deleted(self, event):
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                event_data = {
                    'type': 'deleted',
                    'path': event.src_path,
                    'is_directory': event.is_directory,
                    'timestamp': timestamp
                }
                self.monitor.file_events.append(event_data)
                print(f"[{timestamp}] Deleted: {event.src_path}")
                if self.callback:
                    self.callback(event_data)
            
            def on_moved(self, event):
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                event_data = {
                    'type': 'moved',
                    'src_path': event.src_path,
                    'dest_path': event.dest_path,
                    'is_directory': event.is_directory,
                    'timestamp': timestamp
                }
                self.monitor.file_events.append(event_data)
                print(f"[{timestamp}] Moved: {event.src_path} -> {event.dest_path}")
                if self.callback:
                    self.callback(event_data)
        
        handler = FileChangeHandler(self, callback)
        
        for path in self.monitored_paths:
            if os.path.exists(path):
                self.observer.schedule(handler, path, recursive=True)
        
        self.observer.start()
        print(f"Started monitoring {len(self.monitored_paths)} path(s)")
        return self.observer
    
    def stop_monitoring(self):
        """Stop monitoring file system changes"""
        self.monitoring = False
        self.observer.stop()
        self.observer.join()
        print("File monitoring stopped.")
    
    def get_events(self):
        """Get all recorded file system events"""
        return self.file_events
    
    def clear_events(self):
        """Clear all recorded file system events"""
        self.file_events = []
    
    def display_file_info(self, file_info):
        """Display file information in a formatted way"""
        if not file_info:
            print("No file information available.")
            return
        
        print(f"\nFile Information:")
        print(f"  Name:       {file_info.get('name', 'N/A')}")
        print(f"  Path:       {file_info.get('path', 'N/A')}")
        print(f"  Extension:  {file_info.get('extension', 'N/A')}")
        print(f"  Size:       {file_info.get('size', 0) / 1024:.2f} KB")
        print(f"  Created:    {file_info.get('created', 'N/A')}")
        print(f"  Modified:   {file_info.get('modified', 'N/A')}")
        print(f"  Accessed:   {file_info.get('accessed', 'N/A')}")
        print(f"  Owner:      {file_info.get('owner', 'N/A')}")
        print(f"  Hidden:     {file_info.get('is_hidden', False)}")
        print(f"  Read-only:  {file_info.get('is_readonly', False)}")
        print(f"  System:     {file_info.get('is_system', False)}")
        
        if 'hash' in file_info:
            print(f"  SHA-256:    {file_info['hash']}")
        if 'version' in file_info:
            print(f"  Version:    {file_info['version']}")


def main():
    """Main function to run the file monitor"""
    monitor = WindowsFileMonitor()
    
    while True:
        print("\nWindows File Monitor")
        print("1. Get file information")
        print("2. Scan directory")
        print("3. Find files by name")
        print("4. Find files by extension")
        print("5. Find files by size")
        print("6. Find duplicate files")
        print("7. Add path to monitor")
        print("8. Start monitoring")
        print("9. Stop monitoring")
        print("10. Exit")
        
        choice = input("Enter your choice (1-10): ")
        
        if choice == '1':
            file_path = input("Enter file path: ")
            file_info = monitor.get_file_info(file_path)
            monitor.display_file_info(file_info)
        elif choice == '2':
            directory = input("Enter directory path: ")
            recursive = input("Recursive? (y/n, default y): ").lower() != 'n'
            files = monitor.scan_directory(directory, recursive)
            print(f"\nFound {len(files)} files:")
            for f in files[:20]:
                print(f"  {f['name']} ({f['size'] / 1024:.2f} KB)")
            if len(files) > 20:
                print(f"  ... and {len(files) - 20} more files")
        elif choice == '3':
            pattern = input("Enter name pattern: ")
            path = input("Enter search path (or leave blank for monitored paths): ")
            search_paths = [path] if path else None
            files = monitor.find_files_by_name(pattern, search_paths)
            print(f"\nFound {len(files)} matching files:")
            for f in files:
                print(f"  {f['path']}")
        elif choice == '4':
            extension = input("Enter file extension (e.g., .txt): ")
            path = input("Enter search path (or leave blank for monitored paths): ")
            search_paths = [path] if path else None
            files = monitor.find_files_by_extension(extension, search_paths)
            print(f"\nFound {len(files)} files with extension '{extension}':")
            for f in files:
                print(f"  {f['path']}")
        elif choice == '5':
            min_size = input("Enter minimum size in bytes (or leave blank): ")
            max_size = input("Enter maximum size in bytes (or leave blank): ")
            min_size = int(min_size) if min_size else None
            max_size = int(max_size) if max_size else None
            files = monitor.find_files_by_size(min_size, max_size)
            print(f"\nFound {len(files)} files:")
            for f in files:
                print(f"  {f['name']} ({f['size'] / 1024:.2f} KB)")
        elif choice == '6':
            path = input("Enter search path (or leave blank for monitored paths): ")
            search_paths = [path] if path else None
            duplicates = monitor.find_duplicate_files(search_paths)
            if duplicates:
                print(f"\nFound {len(duplicates)} duplicate(s):")
                for dup in duplicates:
                    print(f"  Original:  {dup['original']}")
                    print(f"  Duplicate: {dup['duplicate']}")
                    print(f"  Size:      {dup['size'] / 1024:.2f} KB")
                    print()
            else:
                print("No duplicates found.")
        elif choice == '7':
            path = input("Enter path to monitor: ")
            if monitor.add_path(path):
                print(f"Added '{path}' to monitored paths.")
            else:
                print("Invalid path or already monitored.")
        elif choice == '8':
            if monitor.monitored_paths:
                monitor.start_monitoring()
                print("Press Enter to stop monitoring...")
                input()
                monitor.stop_monitoring()
            else:
                print("No paths added. Use option 7 to add paths first.")
        elif choice == '9':
            monitor.stop_monitoring()
        elif choice == '10':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()