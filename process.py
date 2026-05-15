import psutil
import socket
import time
import datetime
from collections import defaultdict
import platform
import subprocess

def get_network_interfaces():
    """Get information about network interfaces"""
    interfaces = {}
    
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
        
        interfaces[interface_name] = addresses
    
    # Get interface stats
    stats = {}
    for interface_name, interface_stats in psutil.net_if_stats().items():
        stats[interface_name] = {
            'isup': interface_stats.isup,
            'duplex': interface_stats.duplex,
            'speed': interface_stats.speed,
            'mtu': interface_stats.mtu
        }
    
    return interfaces, stats

def get_network_io(interval=1):
    """Get network I/O statistics"""
    net_io_before = psutil.net_io_counters(pernic=True)
    time.sleep(interval)
    net_io_after = psutil.net_io_counters(pernic=True)
    
    io_stats = {}
    for interface in net_io_before:
        bytes_sent = net_io_after[interface].bytes_sent - net_io_before[interface].bytes_sent
        bytes_recv = net_io_after[interface].bytes_recv - net_io_before[interface].bytes_recv
        packets_sent = net_io_after[interface].packets_sent - net_io_before[interface].packets_sent
        packets_recv = net_io_after[interface].packets_recv - net_io_before[interface].packets_recv
        
        io_stats[interface] = {
            'bytes_sent': bytes_sent,
            'bytes_recv': bytes_recv,
            'packets_sent': packets_sent,
            'packets_recv': packets_recv,
            'bytes_sent_rate': bytes_sent / interval,
            'bytes_recv_rate': bytes_recv / interval,
            'packets_sent_rate': packets_sent / interval,
            'packets_recv_rate': packets_recv / interval
        }
    
    return io_stats

def get_active_connections():
    """Get active network connections"""
    connections = []
    
    for conn in psutil.net_connections():
        if conn.status == 'ESTABLISHED':
            try:
                process = psutil.Process(conn.pid)
                process_name = process.name()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                process_name = "Unknown"
            
            connections.append({
                'local_address': f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "N/A",
                'remote_address': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "N/A",
                'status': conn.status,
                'pid': conn.pid,
                'process_name': process_name,
                'type': 'TCP' if conn.type == socket.SOCK_STREAM else 'UDP'
            })
    
    return connections

def get_listening_ports():
    """Get listening ports"""
    listening_ports = []
    
    for conn in psutil.net_connections():
        if conn.status == 'LISTEN':
            try:
                process = psutil.Process(conn.pid)
                process_name = process.name()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                process_name = "Unknown"
            
            listening_ports.append({
                'local_address': f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "N/A",
                'pid': conn.pid,
                'process_name': process_name,
                'type': 'TCP' if conn.type == socket.SOCK_STREAM else 'UDP'
            })
    
    return listening_ports

def ping_host(hostname, count=4):
    """Ping a host to check connectivity"""
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, str(count), hostname]
    
    try:
        output = subprocess.check_output(command, universal_newlines=True)
        return output
    except subprocess.CalledProcessError:
        return f"Ping to {hostname} failed"

def trace_route(hostname):
    """Trace route to a host"""
    param = '-h' if platform.system().lower() == 'windows' else '-m'
    command = ['tracert' if platform.system().lower() == 'windows' else 'traceroute', 
              param, '30', hostname]
    
    try:
        output = subprocess.check_output(command, universal_newlines=True)
        return output
    except (subprocess.CalledProcessError, FileNotFoundError):
        return f"Trace route to {hostname} failed or command not found"

def monitor_network(interval=5, duration=60):
    """Monitor network activity over time"""
    print(f"Monitoring network activity for {duration} seconds (updating every {interval} seconds)...")
    
    end_time = time.time() + duration
    history = defaultdict(list)
    
    while time.time() < end_time:
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        io_stats = get_network_io(interval)
        
        for interface, stats in io_stats.items():
            history[interface].append({
                'timestamp': timestamp,
                'bytes_sent_rate': stats['bytes_sent_rate'],
                'bytes_recv_rate': stats['bytes_recv_rate'],
                'packets_sent_rate': stats['packets_sent_rate'],
                'packets_recv_rate': stats['packets_recv_rate']
            })
            
            print(f"[{timestamp}] {interface}: "
                  f"↑ {stats['bytes_sent_rate']/1024:.2f} KB/s, "
                  f"↓ {stats['bytes_recv_rate']/1024:.2f} KB/s")
    
    return history

def display_interfaces(interfaces, stats):
    """Display network interface information"""
    print("\nNetwork Interfaces:")
    print(f"{'Interface':<15} {'Status':<8} {'Speed (Mbps)':<12} {'MTU':<6} {'IP Address':<20} {'Netmask':<15}")
    print("-" * 80)
    
    for interface_name, addresses in interfaces.items():
        if interface_name in stats:
            status = "Up" if stats[interface_name]['isup'] else "Down"
            speed = stats[interface_name]['speed']
            mtu = stats[interface_name]['mtu']
            
            for address in addresses:
                if address['type'] == 'IPv4':
                    print(f"{interface_name:<15} {status:<8} {speed:<12} {mtu:<6} {address['address']:<20} {address['netmask']:<15}")

def display_connections(connections, title="Active Connections"):
    """Display network connections"""
    print(f"\n{title}:")
    print(f"{'Local Address':<25} {'Remote Address':<25} {'Status':<12} {'Process':<20} {'PID':<8}")
    print("-" * 90)
    
    for conn in connections:
        print(f"{conn['local_address']:<25} {conn['remote_address']:<25} {conn['status']:<12} {conn['process_name']:<20} {conn['pid']:<8}")

def main():
    """Main function to run the network monitor"""
    while True:
        print("\nNetwork Monitor")
        print("1. View network interfaces")
        print("2. View network I/O statistics")
        print("3. View active connections")
        print("4. View listening ports")
        print("5. Monitor network activity over time")
        print("6. Ping a host")
        print("7. Trace route to a host")
        print("8. Exit")
        
        choice = input("Enter your choice (1-8): ")
        
        if choice == '1':
            interfaces, stats = get_network_interfaces()
            display_interfaces(interfaces, stats)
        elif choice == '2':
            interval = input("Enter interval in seconds (default 1): ")
            try:
                interval = float(interval) if interval else 1.0
            except ValueError:
                interval = 1.0
            
            io_stats = get_network_io(interval)
            print("\nNetwork I/O Statistics:")
            print(f"{'Interface':<15} {'Bytes Sent':<12} {'Bytes Received':<15} {'Packets Sent':<13} {'Packets Received':<16}")
            print("-" * 75)
            
            for interface, stats in io_stats.items():
                print(f"{interface:<15} {stats['bytes_sent']:<12} {stats['bytes_recv']:<15} "
                      f"{stats['packets_sent']:<13} {stats['packets_recv']:<16}")
        elif choice == '3':
            connections = get_active_connections()
            display_connections(connections)
        elif choice == '4':
            listening_ports = get_listening_ports()
            display_connections(listening_ports, "Listening Ports")
        elif choice == '5':
            interval = input("Enter interval in seconds (default 5): ")
            duration = input("Enter duration in seconds (default 60): ")
            
            try:
                interval = float(interval) if interval else 5.0
                duration = int(duration) if duration else 60
            except ValueError:
                interval = 5.0
                duration = 60
            
            monitor_network(interval, duration)
        elif choice == '6':
            hostname = input("Enter hostname or IP address: ")
            print(ping_host(hostname))
        elif choice == '7':
            hostname = input("Enter hostname or IP address: ")
            print(trace_route(hostname))
        elif choice == '8':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()