import psutil
import time
import logging
import json
from datetime import datetime
import schedule
import subprocess
import socket
import sys
from ping3 import ping
import speedtest

try:
    import wmi
    WMI_AVAILABLE = True
except ImportError:
    WMI_AVAILABLE = False
    print("[WARNING] WMI not available for temperature monitoring")

from config import *

logging.basicConfig(level=logging.INFO)

class TemperatureMonitor:
    """مانیتورینگ دمای قطعات"""
    
    def __init__(self):
        self.has_wmi = WMI_AVAILABLE
        self.temps = {}
    
    def get_temperatures_windows(self):
        """دریافت دما در ویندوز با WMI"""
        try:
            w = wmi.WMI(namespace="root\\OpenHardwareMonitor")
            temperature_sensors = w.Sensor(SensorType='Temperature')
            
            temps = {}
            for sensor in temperature_sensors:
                if sensor.Value:
                    name = sensor.Name.replace('Temperature', '').strip()
                    if name and name != '':
                        temps[name] = round(sensor.Value, 1)
            
            return temps if temps else {"CPU": self.get_cpu_temp_alternative()}
        except:
            return {"CPU": self.get_cpu_temp_alternative()}
    
    def get_cpu_temp_alternative(self):
        """روش جایگزین برای دمای CPU"""
        try:
            # روش از طریق psutil
            if hasattr(psutil, 'sensors_temperatures'):
                temps = psutil.sensors_temperatures()
                if temps:
                    for name, entries in temps.items():
                        if entries:
                            return entries[0].current
            
            # روش ویندوز با PowerShell
            if sys.platform == "win32":
                cmd = "powershell -Command \"Get-WmiObject MSAcpi_ThermalZoneTemperature -Namespace 'root/wmi' | Select CurrentTemperature\""
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.stdout and 'CurrentTemperature' in result.stdout:
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if line.strip().isdigit():
                            temp = int(line.strip()) / 10 - 273.15
                            return round(temp, 1)
            return "N/A"
        except:
            return "N/A"
    
    def get_all_temperatures(self):
        """دریافت همه دماها"""
        if self.has_wmi:
            self.temps = self.get_temperatures_windows()
        else:
            cpu_temp = self.get_cpu_temp_alternative()
            if cpu_temp and cpu_temp != "N/A":
                self.temps = {"CPU": cpu_temp}
            else:
                self.temps = {"CPU": "N/A", "GPU": "N/A", "Disk": "N/A"}
        
        return self.temps

class InternetMonitor:
    """مانیتورینگ اینترنت و پینگ"""
    
    def __init__(self):
        self.ping_history = []
        self.speed_history = []
        
    def ping_host(self, host="8.8.8.8"):
        """پینگ به یک هاست"""
        try:
            response = ping(host, timeout=2)
            if response is not None:
                return round(response * 1000, 2)
            return None
        except:
            return None
    
    def check_internet_connection(self):
        """بررسی اتصال اینترنت"""
        hosts = ["8.8.8.8", "1.1.1.1", "208.67.222.222"]
        
        for host in hosts:
            result = self.ping_host(host)
            if result:
                return True, result
        
        return False, None
    
    def get_network_speed(self):
        """تست سرعت اینترنت"""
        try:
            st = speedtest.Speedtest()
            st.get_best_server()
            
            download = st.download() / 1_000_000
            upload = st.upload() / 1_000_000
            ping = st.results.ping
            
            return {
                "download": round(download, 2),
                "upload": round(upload, 2),
                "ping": round(ping, 2)
            }
        except:
            return None
    
    def get_ping_stats(self):
        """آمار پینگ"""
        if not self.ping_history:
            return None
        
        return {
            "min": min(self.ping_history),
            "max": max(self.ping_history),
            "avg": sum(self.ping_history) / len(self.ping_history),
            "last": self.ping_history[-1] if self.ping_history else None
        }

class BatteryMonitor:
    """مانیتورینگ باتری (لپ‌تاپ)"""
    
    def get_battery_info(self):
        """دریافت اطلاعات باتری"""
        try:
            battery = psutil.sensors_battery()
            
            if battery is None:
                return None
            
            seconds_left = battery.secsleft
            if seconds_left == psutil.POWER_TIME_UNLIMITED:
                time_left = "Unlimited"
            elif seconds_left == psutil.POWER_TIME_UNKNOWN:
                time_left = "Unknown"
            else:
                hours = seconds_left // 3600
                minutes = (seconds_left % 3600) // 60
                time_left = f"{hours}h {minutes}m"
            
            return {
                "percent": battery.percent,
                "power_plugged": battery.power_plugged,
                "seconds_left": time_left,
                "status": "Charging 🔌" if battery.power_plugged else "Discharging 🔋"
            }
        except:
            return None

class PortMonitor:
    """مانیتورینگ پورت‌های شبکه"""
    
    def __init__(self):
        self.common_ports = {
            20: "FTP Data",
            21: "FTP Control",
            22: "SSH",
            23: "Telnet",
            25: "SMTP",
            53: "DNS",
            80: "HTTP",
            110: "POP3",
            143: "IMAP",
            443: "HTTPS",
            3306: "MySQL",
            5432: "PostgreSQL",
            27017: "MongoDB",
            6379: "Redis",
            8080: "HTTP-Alt",
            3389: "RDP"
        }
    
    def get_open_ports(self):
        """دریافت پورت‌های باز"""
        open_ports = []
        
        for port, service in self.common_ports.items():
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.3)
            result = sock.connect_ex(('127.0.0.1', port))
            if result == 0:
                open_ports.append({
                    "port": port,
                    "service": service,
                    "status": "Open"
                })
            sock.close()
        
        return open_ports
    
    def get_connections(self):
        """دریافت اتصالات فعال شبکه"""
        connections = []
        
        for conn in psutil.net_connections():
            if conn.status == 'ESTABLISHED' and conn.laddr and conn.raddr:
                connections.append({
                    "local_ip": f"{conn.laddr.ip}:{conn.laddr.port}",
                    "remote_ip": f"{conn.raddr.ip}:{conn.raddr.port}",
                    "pid": conn.pid,
                    "status": conn.status
                })
        
        return connections[:20]

class ServerMonitor:
    """کلاس اصلی مانیتورینگ سرور"""
    
    def __init__(self):
        self.history = []
        self.alerts = []
        self.temp_monitor = TemperatureMonitor()
        self.internet_monitor = InternetMonitor()
        self.battery_monitor = BatteryMonitor()
        self.port_monitor = PortMonitor()
    
    def get_cpu_usage(self):
        """دریافت مصرف CPU"""
        return psutil.cpu_percent(interval=1)
    
    def get_ram_usage(self):
        """دریافت مصرف RAM"""
        ram = psutil.virtual_memory()
        return {
            "total": ram.total // (1024**3),
            "used": ram.used // (1024**3),
            "percent": ram.percent
        }
    
    def get_disk_usage(self):
        """دریافت مصرف دیسک"""
        disks = []
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disks.append({
                    "device": partition.device,
                    "mountpoint": partition.mountpoint,
                    "total": usage.total // (1024**3),
                    "used": usage.used // (1024**3),
                    "percent": usage.percent
                })
            except:
                continue
        return disks
    
    def get_network_info(self):
        """دریافت اطلاعات شبکه"""
        net_io = psutil.net_io_counters()
        return {
            "bytes_sent": net_io.bytes_sent // (1024**2),
            "bytes_recv": net_io.bytes_recv // (1024**2),
            "connections": len(psutil.net_connections())
        }
    
    def get_process_info(self):
        """دریافت فرآیندهای پرمصرف"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except:
                continue
        processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
        return {
            "top_cpu": processes[:5],
            "top_memory": sorted(processes, key=lambda x: x['memory_percent'] or 0, reverse=True)[:5]
        }
    
    def get_system_info(self):
        """دریافت اطلاعات کلی سیستم"""
        uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time())
        return {
            "hostname": socket.gethostname(),
            "boot_time": datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S"),
            "uptime": str(uptime).split('.')[0]
        }
    
    def collect_all_metrics(self):
        """جمع‌آوری همه متریک‌ها"""
        
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "cpu": self.get_cpu_usage(),
            "ram": self.get_ram_usage(),
            "disk": self.get_disk_usage(),
            "network": self.get_network_info(),
            "processes": self.get_process_info(),
            "system": self.get_system_info(),
            "temperatures": self.temp_monitor.get_all_temperatures(),
            "internet": {
                "connected": self.internet_monitor.check_internet_connection()[0],
                "ping": self.internet_monitor.ping_host(),
                "speed": self.internet_monitor.get_network_speed()
            },
            "battery": self.battery_monitor.get_battery_info(),
            "ports": {
                "open": self.port_monitor.get_open_ports(),
                "connections": self.port_monitor.get_connections()
            }
        }
        
        self.history.append(metrics)
        
        if len(self.history) > 1000:
            self.history = self.history[-1000:]
        
        try:
            with open(f"{LOG_DIR}/metrics.json", 'w', encoding='utf-8') as f:
                json.dump(self.history[-100:], f, indent=2, ensure_ascii=False)
        except:
            pass
        
        self.check_alerts(metrics)
        
        return metrics
    
    def check_alerts(self, metrics):
        """بررسی هشدارها"""
        alerts = []
        
        # CPU
        if metrics['cpu'] > CPU_THRESHOLD:
            alerts.append(f"⚠️ CPU Alert: {metrics['cpu']}%")
        
        # RAM
        if metrics['ram']['percent'] > RAM_THRESHOLD:
            alerts.append(f"⚠️ RAM Alert: {metrics['ram']['percent']}%")
        
        # Disk
        for disk in metrics['disk']:
            if disk['percent'] > DISK_THRESHOLD:
                alerts.append(f"⚠️ Disk Alert: {disk['device']} is {disk['percent']}% full")
        
        # Temperature
        for component, temp in metrics['temperatures'].items():
            if isinstance(temp, (int, float)) and temp > TEMP_THRESHOLD:
                alerts.append(f"🌡️ Temperature Alert: {component} is {temp}°C")
        
        # Internet
        if not metrics['internet']['connected']:
            alerts.append(f"🌍 Internet Alert: No internet connection!")
        elif metrics['internet']['ping'] and metrics['internet']['ping'] > PING_THRESHOLD:
            alerts.append(f"🌍 High Ping Alert: {metrics['internet']['ping']}ms")
        
        # Battery
        if metrics['battery']:
            if metrics['battery']['percent'] < BATTERY_THRESHOLD and not metrics['battery']['power_plugged']:
                alerts.append(f"🔋 Low Battery Alert: {metrics['battery']['percent']}% remaining")
        
        # Ports
        sensitive_ports = [22, 3389, 3306, 5432, 27017]
        for port in metrics['ports']['open']:
            if port['port'] in sensitive_ports:
                alerts.append(f"🔌 Sensitive Port Open: {port['port']} ({port['service']})")
        
        if alerts:
            for alert in alerts:
                logging.warning(alert)
                self.alerts.append({"time": datetime.now().isoformat(), "message": alert})
            
            try:
                from telegram_bot import send_alert
                send_alert("\n".join(alerts))
            except:
                pass
    
    def get_summary(self):
        """گرفتن خلاصه وضعیت"""
        if not self.history:
            return None
        
        latest = self.history[-1]
        
        return {
            "status": "Good" if latest['cpu'] < CPU_THRESHOLD and latest['ram']['percent'] < RAM_THRESHOLD else "Warning",
            "cpu": latest['cpu'],
            "ram": latest['ram']['percent'],
            "uptime": latest['system']['uptime'],
            "timestamp": latest['timestamp']
        }