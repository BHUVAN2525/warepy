import os
import time
import datetime
import json
import threading
import wmi
import win32api
import win32con
import win32file
import win32event
import win32gui
import win32process
from datetime import datetime
import psutil
import ctypes
from ctypes import wintypes

class USBHubMonitor:
    def __init__(self):
        self.wmi_client = wmi.WMI()
        self.usb_devices = []
        self.monitoring = False
        self.device_change_handlers = []
        
    def get_usb_devices(self):
        """Get all connected USB devices"""
        devices = []
        
        try:
            # Get USB devices using WMI
            for device in self.wmi_client.Win32_PnPEntity():
                dev_id = getattr(device, 'DeviceID', '') or ''
                dev_desc = getattr(device, 'Description', '') or ''
                if 'USB' in dev_id or 'USB' in dev_desc:
                    devices.append({
                        'name': device.Name,
                        'description': device.Description,
                        'device_id': device.DeviceID,
                        'pnp_class': device.PNPClass,
                        'manufacturer': device.Manufacturer,
                        'status': device.Status,
                        'present': device.Present,
                        'service': device.Service
                    })
            
            # Get USB controllers
            for controller in self.wmi_client.Win32_USBController():
                devices.append({
                    'name': controller.Name,
                    'description': controller.Description,
                    'device_id': controller.DeviceID,
                    'pnp_class': 'USBController',
                    'manufacturer': controller.Manufacturer,
                    'status': controller.Status
                })
            
            # Get USB hub information
            for hub in self.wmi_client.Win32_USBHub():
                devices.append({
                    'name': hub.Name,
                    'description': hub.Description,
                    'device_id': hub.DeviceID,
                    'pnp_class': 'USBHub',
                    'status': hub.Status
                })
            
            # Get connected USB devices
            for device in self.wmi_client.Win32_LogicalDisk():
                if device.DriveType == 2:  # Removable disk
                    try:
                        # Get additional info for removable drives
                        size = 0
                        free_space = 0
                        try:
                            size = device.Size
                            free_space = device.FreeSpace
                        except:
                            pass
                        
                        devices.append({
                            'name': device.Caption,
                            'description': 'Removable Disk',
                            'device_id': device.DeviceID,
                            'pnp_class': 'DiskDrive',
                            'volume_name': device.VolumeName,
                            'file_system': device.FileSystem,
                            'size': size,
                            'free_space': free_space,
                            'status': 'Connected'
                        })
                    except:
                        pass
            
            self.usb_devices = devices
            return devices
            
        except Exception as e:
            print(f"Error getting USB devices: {e}")
            return []
    
    def get_usb_hub_details(self):
        """Get detailed information about USB hubs"""
        hubs = []
        
        try:
            for hub in self.wmi_client.Win32_USBHub():
                hub_info = {
                    'name': hub.Name,
                    'description': hub.Description,
                    'device_id': hub.DeviceID,
                    'status': hub.Status,
                    'ports': []
                }
                
                # Get associated hub ports
                for port in self.wmi_client.Win32_USBHubDevice():
                    if port.Dependent and hub.DeviceID in port.Dependent:
                        hub_info['ports'].append({
                            'dependent': port.Dependent,
                            'antecedent': port.Antecedent
                        })
                
                hubs.append(hub_info)
            
            return hubs
            
        except Exception as e:
            print(f"Error getting USB hub details: {e}")
            return []
    
    def get_usb_controller_info(self):
        """Get information about USB controllers"""
        controllers = []
        
        try:
            for controller in self.wmi_client.Win32_USBController():
                controller_info = {
                    'name': controller.Name,
                    'description': controller.Description,
                    'device_id': controller.DeviceID,
                    'manufacturer': controller.Manufacturer,
                    'status': controller.Status,
                    'protocol_version': getattr(controller, 'ProtocolVersion', 'Unknown'),
                    'max_packet_size': getattr(controller, 'MaxPacketSize', 'Unknown')
                }
                
                controllers.append(controller_info)
            
            return controllers
            
        except Exception as e:
            print(f"Error getting USB controller info: {e}")
            return []
    
    def get_connected_drives_info(self):
        """Get information about connected USB drives"""
        drives = []
        
        try:
            for device in self.wmi_client.Win32_LogicalDisk():
                if device.DriveType == 2:  # Removable disk
                    drive_info = {
                        'letter': device.Caption,
                        'label': device.VolumeName,
                        'file_system': device.FileSystem,
                        'size': device.Size,
                        'free_space': device.FreeSpace,
                        'used_space': device.Size - device.FreeSpace,
                        'serial_number': device.VolumeSerialNumber,
                        'status': 'Connected'
                    }
                    
                    drives.append(drive_info)
            
            return drives
            
        except Exception as e:
            print(f"Error getting connected drives info: {e}")
            return []
    
    def monitor_usb_changes(self, callback=None):
        """Monitor for USB device changes"""
        self.monitoring = True
        
        def monitor_thread():
            try:
                # Register for device notifications
                # This is a simplified version - a full implementation would require
                # more complex Windows API calls
                
                last_devices = self.get_usb_devices()
                
                while self.monitoring:
                    current_devices = self.get_usb_devices()
                    
                    # Check for new devices
                    for device in current_devices:
                        if device not in last_devices:
                            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            print(f"[{timestamp}] USB Device Connected: {device['name']} ({device['description']})")
                            
                            if callback:
                                callback('connected', device)
                    
                    # Check for removed devices
                    for device in last_devices:
                        if device not in current_devices:
                            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            print(f"[{timestamp}] USB Device Disconnected: {device['name']} ({device['description']})")
                            
                            if callback:
                                callback('disconnected', device)
                    
                    last_devices = current_devices
                    time.sleep(2)  # Check every 2 seconds
                    
            except Exception as e:
                print(f"Error in USB monitoring thread: {e}")
            finally:
                self.monitoring = False
        
        # Start monitoring in a separate thread
        monitor_thread = threading.Thread(target=monitor_thread)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        return monitor_thread
    
    def stop_monitoring(self):
        """Stop monitoring USB changes"""
        self.monitoring = False
    
    def eject_usb_drive(self, drive_letter):
        """Eject a USB drive"""
        try:
            # Get the logical disk
            for disk in self.wmi_client.Win32_LogicalDisk(DeviceID=drive_letter):
                # Get the physical drive
                for physical_disk in self.wmi_client.Win32_PhysicalMedia():
                    if physical_disk.SerialNumber == disk.VolumeSerialNumber:
                        # Eject the drive
                        for ejectable in self.wmi_client.Win32_Volume(DeviceID=disk.DeviceID):
                            ejectable.Eject()
                            return True
            
            return False
            
        except Exception as e:
            print(f"Error ejecting USB drive: {e}")
            return False
    
    def get_usb_device_history(self):
        """Get history of USB devices (requires Windows event logs)"""
        history = []
        
        try:
            # This would require accessing Windows Event Logs
            # which is more complex and might require additional permissions
            # For now, we'll return an empty list
            
            # In a full implementation, you would:
            # 1. Query the Windows Event Log for USB device events
            # 2. Parse the events to extract device information
            # 3. Return a list of device connection/disconnection events
            
            return history
            
        except Exception as e:
            print(f"Error getting USB device history: {e}")
            return []
    
    def get_usb_performance_stats(self):
        """Get performance statistics for USB devices"""
        stats = {}
        
        try:
            # Get performance counters for USB devices
            # This is a simplified version - a full implementation would
            # use Windows Performance Counters
            
            for device in self.usb_devices:
                if device['pnp_class'] == 'DiskDrive':
                    try:
                        # Get disk performance stats
                        disk_letter = device.get('name', '').replace('\\', '')
                        if disk_letter and len(disk_letter) == 1:
                            disk_letter += ':'
                            disk_usage = psutil.disk_usage(disk_letter)
                            
                            stats[disk_letter] = {
                                'read_bytes': psutil.disk_io_counters(perdisk=True).get(disk_letter, {}).read_bytes,
                                'write_bytes': psutil.disk_io_counters(perdisk=True).get(disk_letter, {}).write_bytes,
                                'total_space': disk_usage.total,
                                'used_space': disk_usage.used,
                                'free_space': disk_usage.free
                            }
                    except:
                        pass
            
            return stats
            
        except Exception as e:
            print(f"Error getting USB performance stats: {e}")
            return {}
    
    def display_usb_devices(self):
        """Display USB devices in a formatted table"""
        devices = self.get_usb_devices()
        
        if not devices:
            print("No USB devices found.")
            return
        
        print(f"\nUSB Devices ({len(devices)} found):")
        print(f"{'#':<3} {'Name':<45} {'Class':<15} {'Status':<10}")
        print("-" * 75)
        
        for i, device in enumerate(devices, 1):
            name = device.get('name', 'Unknown')[:44]
            pnp_class = device.get('pnp_class', 'N/A')[:14]
            status = device.get('status', 'N/A')
            
            print(f"{i:<3} {name:<45} {pnp_class:<15} {status:<10}")
    
    def display_usb_drives(self):
        """Display connected USB drives with details"""
        drives = self.get_connected_drives_info()
        
        if not drives:
            print("No USB drives connected.")
            return
        
        print(f"\nConnected USB Drives ({len(drives)} found):")
        print("-" * 60)
        
        for drive in drives:
            print(f"\n  Drive: {drive.get('letter', 'N/A')}")
            print(f"    Label:       {drive.get('label', 'N/A')}")
            print(f"    File System: {drive.get('file_system', 'N/A')}")
            if drive.get('size'):
                print(f"    Total Size:  {int(drive['size']) / (1024**3):.2f} GB")
            if drive.get('free_space'):
                print(f"    Free Space:  {int(drive['free_space']) / (1024**3):.2f} GB")
            if drive.get('used_space'):
                print(f"    Used Space:  {int(drive['used_space']) / (1024**3):.2f} GB")
            print(f"    Serial:      {drive.get('serial_number', 'N/A')}")
    
    def save_device_info(self, filename=None):
        """Save USB device information to a file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"usb_devices_{timestamp}.json"
        
        try:
            devices = self.get_usb_devices()
            hubs = self.get_usb_hub_details()
            controllers = self.get_usb_controller_info()
            drives = self.get_connected_drives_info()
            
            data = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'devices': devices,
                'hubs': hubs,
                'controllers': controllers,
                'drives': drives
            }
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=4, default=str)
            
            print(f"USB device info saved to {filename}")
            return filename
        except Exception as e:
            print(f"Error saving USB device info: {e}")
            return None


def main():
    """Main function to run the USB hub monitor"""
    monitor = USBHubMonitor()
    
    while True:
        print("\nUSB Hub Monitor")
        print("1. List USB devices")
        print("2. Show USB hub details")
        print("3. Show USB controller info")
        print("4. Show connected USB drives")
        print("5. Monitor USB changes")
        print("6. Get USB performance stats")
        print("7. Eject USB drive")
        print("8. Save device info to file")
        print("9. Exit")
        
        choice = input("Enter your choice (1-9): ")
        
        if choice == '1':
            monitor.display_usb_devices()
        elif choice == '2':
            hubs = monitor.get_usb_hub_details()
            if hubs:
                for hub in hubs:
                    print(f"\n  Hub: {hub['name']}")
                    print(f"    Status:  {hub['status']}")
                    print(f"    Ports:   {len(hub['ports'])}")
            else:
                print("No USB hubs found.")
        elif choice == '3':
            controllers = monitor.get_usb_controller_info()
            if controllers:
                for ctrl in controllers:
                    print(f"\n  Controller: {ctrl['name']}")
                    print(f"    Manufacturer: {ctrl['manufacturer']}")
                    print(f"    Status:       {ctrl['status']}")
            else:
                print("No USB controllers found.")
        elif choice == '4':
            monitor.display_usb_drives()
        elif choice == '5':
            print("Monitoring USB changes. Press Enter to stop...")
            monitor.monitor_usb_changes()
            input()
            monitor.stop_monitoring()
        elif choice == '6':
            stats = monitor.get_usb_performance_stats()
            if stats:
                for drive, data in stats.items():
                    print(f"\n  Drive {drive}:")
                    print(f"    Read:  {data.get('read_bytes', 0) / (1024**2):.2f} MB")
                    print(f"    Write: {data.get('write_bytes', 0) / (1024**2):.2f} MB")
            else:
                print("No USB performance stats available.")
        elif choice == '7':
            letter = input("Enter drive letter (e.g., E:): ").strip()
            if monitor.eject_usb_drive(letter):
                print(f"Drive {letter} ejected successfully.")
            else:
                print(f"Failed to eject drive {letter}.")
        elif choice == '8':
            monitor.save_device_info()
        elif choice == '9':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()