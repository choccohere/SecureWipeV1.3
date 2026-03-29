from dataclasses import dataclass
import platform
import subprocess
import json
import os
from typing import List, Optional

@dataclass
class DiskInfo:
    number: str
    friendly_name: str
    size_gb: float
    path: str  # For Linux /dev/sdX, for Windows disk number

class DiskManager:
    @staticmethod
    def get_disks() -> List[DiskInfo]:
        system = platform.system()
        if system == "Windows":
            return DiskManager._get_windows_disks()
        elif system == "Linux":
            return DiskManager._get_linux_disks()
        return []

    @staticmethod
    def _get_windows_disks() -> List[DiskInfo]:
        try:
            command = ["powershell", "-Command", "Get-Disk | Select-Object Number, FriendlyName, Size | ConvertTo-Json -Compress"]
            process = subprocess.run(command, capture_output=True, text=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
            output = json.loads(process.stdout)
            if isinstance(output, dict):
                output = [output]
            
            disks = []
            for disk in output:
                disks.append(DiskInfo(
                    number=str(disk['Number']),
                    friendly_name=disk['FriendlyName'],
                    size_gb=disk['Size'] / 1e9,
                    path=str(disk['Number'])
                ))
            return disks
        except Exception:
            return []

    @staticmethod
    def _get_linux_disks() -> List[DiskInfo]:
        try:
            command = ["lsblk", "-o", "NAME,SIZE,TYPE", "-d", "-n", "--json"]
            process = subprocess.run(command, capture_output=True, text=True, check=True)
            output = json.loads(process.stdout)
            disks = []
            for disk in output.get('blockdevices', []):
                if disk.get('type') == 'disk':
                    # lsblk size is often a string with units, might need parsing or better lsblk flags
                    # Let's use bytes
                    bytes_cmd = ["lsblk", "-b", "-d", "-n", "-o", "SIZE", f"/dev/{disk['name']}"]
                    size_bytes = int(subprocess.check_output(bytes_cmd).strip())
                    disks.append(DiskInfo(
                        number=disk['name'],
                        friendly_name=disk['name'],
                        size_gb=size_bytes / 1e9,
                        path=f"/dev/{disk['name']}"
                    ))
            return disks
        except Exception:
            return []

class WipeEngine:
    @staticmethod
    def get_system_wiper():
        system = platform.system()
        if system == "Windows":
            return WindowsWiper()
        elif system == "Linux":
            return LinuxWiper()
        raise NotImplementedError(f"Unsupported system: {system}")

class WindowsWiper:
    def wipe(self, disk_number: str, pattern: str = "zeros"):
        # Pattern can be "zeros" (0x00) or "ones" (0xFF)
        if pattern == "zeros":
            return ["powershell", "-Command", f"Clear-Disk -Number {disk_number} -RemoveData -Confirm:$false"]
        elif pattern == "ones":
            # Using the stream method from the original CLI
            ps_cmd = (
                f"$stream = [System.IO.File]::OpenWrite('\\\\.\\PhysicalDrive{disk_number}'); "
                "$buffer = [byte[]]::new(1MB); "
                "for($i=0; $i -lt $buffer.Length; $i++) { $buffer[$i] = 0xFF }; "
                "while($true) { $stream.Write($buffer, 0, $buffer.Length) }; "
                "$stream.Close()"
            )
            return ["powershell", "-Command", ps_cmd]
        
    def initialize_disk(self, disk_number: str):
        return ["powershell", "-Command", f"Initialize-Disk -Number {disk_number} -PartitionStyle GPT"]

    def format_disk(self, disk_number: str):
        ps_format = f"New-Partition -DiskNumber {disk_number} -UseMaximumSize | Format-Volume -FileSystem NTFS -NewFileSystemLabel 'WipedDisk' -Confirm:$false -Full"
        return ["powershell", "-Command", ps_format]

class LinuxWiper:
    def wipe(self, disk_path: str, pattern: str = "zeros"):
        if pattern == "zeros":
            return ["dd", "if=/dev/zero", f"of={disk_path}", "bs=1M", "status=progress"]
        elif pattern == "ones":
            return ["bash", "-c", f"dd if=/dev/zero bs=1M | tr '\\000' '\\377' | dd of={disk_path} bs=1M status=progress"]

    def initialize_disk(self, disk_path: str):
        return ["parted", disk_path, "--script", "--", "mklabel", "gpt"]

    def create_partition(self, disk_path: str):
        return ["parted", disk_path, "--script", "--", "mkpart", "primary", "ext4", "0%", "100%"]

    def format_disk(self, partition_path: str):
        return ["mkfs.ext4", "-c", "-c", partition_path]
