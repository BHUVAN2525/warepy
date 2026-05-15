import os
import time
import json
import datetime
import threading
import requests
import ctypes
from ctypes import wintypes
import win32api
import win32con
import win32security
import win32process
import win32gui
import wmi
import psutil
from datetime import datetime
import socket

class WindowsLocationMonitor:
    def __init__(self):
        self.wmi_client = wmi.WMI()
        self.monitoring = False
        
        # Windows API definitions for location services
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32
        
        # Define Windows API structures and functions
        class LOCATION_API(ctypes.Structure):
            pass
        
        # Try to load the location API library
        try:
            self.location_api = ctypes.windll.locationapi
        except:
            self.location_api = None
            print("Windows Location API not available")
    
    def get_ip_geolocation(self):
        """Get location based on IP address"""
        try:
            # Get public IP address
            response = requests.get('https://api.ipify.org?format=json', timeout=5)
            ip_data = response.json()
            public_ip = ip_data.get('ip')
            
            # Get location data based on IP
            response = requests.get(f'https://ipapi.co/{public_ip}/json/', timeout=5)
            location_data = response.json()
            
            return {
                'source': 'IP Geolocation',
                'ip': public_ip,
                'city': location_data.get('city'),
                'region': location_data.get('region'),
                'country': location_data.get('country_name'),
                'latitude': location_data.get('latitude'),
                'longitude': location_data.get('longitude'),
                'postal_code': location_data.get('postal'),
                'timezone': location_data.get('timezone'),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception as e:
            print(f"Error getting IP geolocation: {e}")
            return None
    
    def get_windows_location(self):
        """Get location using Windows Location Services"""
        if not self.location_api:
            return None
        
        try:
            # This is a simplified version - a full implementation would require
            # more complex Windows API calls to access the location sensor
            
            # Define the necessary Windows API functions and structures
            # This is a placeholder for the actual implementation
            
            # For now, we'll return None as a placeholder
            return None
            
        except Exception as e:
            print(f"Error getting Windows location: {e}")
            return None
    
    def get_wifi_location(self):
        """Get location based on nearby WiFi networks"""
        try:
            # Get WiFi network information using WMI
            wifi_networks = []
            
            for network in self.wmi_client.Win32_NetworkAdapterConfiguration():
                if network.IPEnabled and network.MACAddress:
                    wifi_networks.append({
                        'ssid': getattr(network, 'SSID', 'Unknown'),
                        'mac_address': network.MACAddress,
                        'signal_strength': getattr(network, 'SignalStrength', 0)
                    })
            
            # This would typically require a geolocation service that can
            # determine location based on nearby WiFi networks
            # For now, we'll return the WiFi network information
            
            return {
                'source': 'WiFi Networks',
                'networks': wifi_networks,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            print(f"Error getting WiFi location: {e}")
            return None
    
    def get_gps_location(self):
        """Get location from GPS device"""
        try:
            # Check for GPS devices using WMI
            gps_devices = []
            
            for device in self.wmi_client.Win32_PnPEntity():
                description = getattr(device, 'Description', '') or ''
                name = getattr(device, 'Name', '') or ''
                if 'GPS' in description.upper() or 'GPS' in name.upper():
                    gps_devices.append({
                        'name': name,
                        'description': description,
                        'device_id': getattr(device, 'DeviceID', None),
                        'status': getattr(device, 'Status', None)
                    })
            
            if not gps_devices:
                return None
            
            # This would typically require communicating with the GPS device
            # For now, we'll return the GPS device information
            
            return {
                'source': 'GPS Device',
                'devices': gps_devices,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            print(f"Error getting GPS location: {e}")
            return None
    
    def get_cell_tower_location(self):
        """Get location based on cell tower information"""
        try:
            # Check for cellular modems using WMI
            cellular_devices = []
            
            for device in self.wmi_client.Win32_PnPEntity():
                description = getattr(device, 'Description', '') or ''
                name = getattr(device, 'Name', '') or ''
                if 'CELLULAR' in description.upper() or 'MOBILE BROADBAND' in description.upper() or 'CELLULAR' in name.upper() or 'MOBILE BROADBAND' in name.upper():
                    cellular_devices.append({
                        'name': name,
                        'description': description,
                        'device_id': getattr(device, 'DeviceID', None),
                        'status': getattr(device, 'Status', None)
                    })
            
            if not cellular_devices:
                return None
            
            # This would typically require accessing cellular modem information
            # For now, we'll return the cellular device information
            
            return {
                'source': 'Cell Tower',
                'devices': cellular_devices,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            print(f"Error getting cell tower location: {e}")
            return None
    
    def get_all_location_sources(self):
        """Get location information from all available sources"""
        location_data = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'sources': []
        }
        
        # Try IP geolocation
        ip_location = self.get_ip_geolocation()
        if ip_location:
            location_data['sources'].append(ip_location)
        
        # Try Windows Location Services
        windows_location = self.get_windows_location()
        if windows_location:
            location_data['sources'].append(windows_location)
        
        # Try WiFi-based location
        wifi_location = self.get_wifi_location()
        if wifi_location:
            location_data['sources'].append(wifi_location)
        
        # Try GPS
        gps_location = self.get_gps_location()
        if gps_location:
            location_data['sources'].append(gps_location)
        
        # Try cell tower location
        cell_location = self.get_cell_tower_location()
        if cell_location:
            location_data['sources'].append(cell_location)
        
        return location_data
    
    def monitor_location_changes(self, interval=60, callback=None):
        """Monitor for location changes"""
        self.monitoring = True
        last_location = self.get_all_location_sources()
        
        def monitor_thread():
            try:
                while self.monitoring:
                    current_location = self.get_all_location_sources()
                    
                    # Check for location changes
                    if self.location_changed(last_location, current_location):
                        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        print(f"[{timestamp}] Location changed")
                        
                        if callback:
                            callback('location_changed', current_location)
                    
                    last_location = current_location
                    time.sleep(interval)
                    
            except Exception as e:
                print(f"Error in location monitoring thread: {e}")
            finally:
                self.monitoring = False
        
        # Start monitoring in a separate thread
        monitor_thread = threading.Thread(target=monitor_thread)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        return monitor_thread
    
    def stop_monitoring(self):
        """Stop monitoring location changes"""
        self.monitoring = False
    
    def location_changed(self, old_location, new_location):
        """Check if location has changed"""
        # This is a simplified comparison - a full implementation would
        # compare specific location coordinates with a threshold
        
        if not old_location or not new_location:
            return False
        
        # Check if any source has changed
        for new_source in new_location.get('sources', []):
            source_type = new_source.get('source')
            
            # Find matching source in old location
            old_source = None
            for source in old_location.get('sources', []):
                if source.get('source') == source_type:
                    old_source = source
                    break
            
            if old_source:
                # Compare coordinates if available
                if (old_source.get('latitude') and old_source.get('longitude') and
                    new_source.get('latitude') and new_source.get('longitude')):
                    
                    # Calculate distance between coordinates
                    # This is a simplified check - a full implementation would
                    # use the Haversine formula to calculate distance
                    
                    lat_diff = abs(old_source.get('latitude') - new_source.get('latitude'))
                    lon_diff = abs(old_source.get('longitude') - new_source.get('longitude'))
                    
                    # If coordinates changed by more than 0.001 degrees (approximately 100m)
                    if lat_diff > 0.001 or lon_diff > 0.001:
                        return True
        
        return False
    
    def save_location_data(self, filename=None):
        """Save location data to a file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"location_data_{timestamp}.json"
        
        try:
            location_data = self.get_all_location_sources()
            
            with open(filename, 'w') as f:
                json.dump(location_data, f, indent=4, default=str)
            
            print(f"Location data saved to {filename}")
            return filename
            
        except Exception as e:
            print(f"Error saving location data: {e}")
            return None
    
    def display_location(self, location_data=None):
        """Display location data in a formatted way"""
        if location_data is None:
            location_data = self.get_all_location_sources()
        
        print(f"\nLocation Data (collected at {location_data.get('timestamp', 'N/A')})")
        print("=" * 60)
        
        for source in location_data.get('sources', []):
            source_type = source.get('source', 'Unknown')
            print(f"\n  Source: {source_type}")
            print(f"  {'-' * 40}")
            
            if source_type == 'IP Geolocation':
                print(f"    IP:          {source.get('ip', 'N/A')}")
                print(f"    City:        {source.get('city', 'N/A')}")
                print(f"    Region:      {source.get('region', 'N/A')}")
                print(f"    Country:     {source.get('country', 'N/A')}")
                print(f"    Latitude:    {source.get('latitude', 'N/A')}")
                print(f"    Longitude:   {source.get('longitude', 'N/A')}")
                print(f"    Postal Code: {source.get('postal_code', 'N/A')}")
                print(f"    Timezone:    {source.get('timezone', 'N/A')}")
            elif source_type == 'WiFi Networks':
                networks = source.get('networks', [])
                print(f"    Found {len(networks)} network(s):")
                for net in networks:
                    print(f"      SSID: {net.get('ssid', 'N/A')} | MAC: {net.get('mac_address', 'N/A')}")
            elif source_type == 'GPS Device':
                devices = source.get('devices', [])
                print(f"    Found {len(devices)} GPS device(s):")
                for dev in devices:
                    print(f"      {dev.get('name', 'N/A')} - {dev.get('status', 'N/A')}")
            elif source_type == 'Cell Tower':
                devices = source.get('devices', [])
                print(f"    Found {len(devices)} cellular device(s):")
                for dev in devices:
                    print(f"      {dev.get('name', 'N/A')} - {dev.get('status', 'N/A')}")
        
        if not location_data.get('sources'):
            print("  No location sources available.")


def main():
    """Main function to run the location monitor"""
    monitor = WindowsLocationMonitor()
    
    while True:
        print("\nWindows Location Monitor")
        print("1. Get IP geolocation")
        print("2. Get WiFi-based location")
        print("3. Get GPS location")
        print("4. Get cell tower location")
        print("5. Get all location sources")
        print("6. Monitor location changes")
        print("7. Save location data")
        print("8. Exit")
        
        choice = input("Enter your choice (1-8): ")
        
        if choice == '1':
            location = monitor.get_ip_geolocation()
            if location:
                monitor.display_location({'timestamp': location.get('timestamp'), 'sources': [location]})
            else:
                print("Could not get IP geolocation.")
        elif choice == '2':
            location = monitor.get_wifi_location()
            if location:
                monitor.display_location({'timestamp': location.get('timestamp'), 'sources': [location]})
            else:
                print("Could not get WiFi location.")
        elif choice == '3':
            location = monitor.get_gps_location()
            if location:
                monitor.display_location({'timestamp': location.get('timestamp'), 'sources': [location]})
            else:
                print("No GPS device found.")
        elif choice == '4':
            location = monitor.get_cell_tower_location()
            if location:
                monitor.display_location({'timestamp': location.get('timestamp'), 'sources': [location]})
            else:
                print("No cellular devices found.")
        elif choice == '5':
            monitor.display_location()
        elif choice == '6':
            interval = input("Enter check interval in seconds (default 60): ")
            try:
                interval = int(interval) if interval else 60
            except ValueError:
                interval = 60
            print("Monitoring location changes. Press Enter to stop...")
            monitor.monitor_location_changes(interval=interval)
            input()
            monitor.stop_monitoring()
        elif choice == '7':
            filename = input("Enter filename (or leave blank for auto): ")
            filename = filename if filename else None
            monitor.save_location_data(filename)
        elif choice == '8':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()