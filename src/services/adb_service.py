"""ADB Service for Android device communication"""
import subprocess
import re
import logging
import sys
import os
import shutil
from dataclasses import dataclass
from typing import List, Optional, Tuple, Set, Dict
from pathlib import Path

logger = logging.getLogger(__name__)

# Windows flag to hide console window
CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0


class ADBDeviceError(Exception):
    """Raised when device is disconnected or unauthorized"""
    pass


class ADBCommandError(Exception):
    """Raised when ADB command fails"""
    pass


@dataclass
class Device:
    """Represents an Android device connected via ADB"""
    serial: str
    status: str  # device, unauthorized, offline
    model: str = ""
    product: str = ""
    device_name: str = ""

    def __str__(self):
        return f"{self.model or self.serial} ({self.serial}) - {self.status}"


@dataclass
class Package:
    """Represents an Android package/app"""
    package_name: str
    label: str = ""  # Human-readable app name
    is_system: bool = False
    version: str = ""
    apk_path: str = ""

    def __str__(self):
        return f"{self.label or self.package_name} ({self.package_name})"


# Dictionary of well-known package names mapped to user-friendly display labels
KNOWN_APP_LABELS: Dict[str, str] = {
    # Popular Android Apps
    "com.google.android.youtube": "YouTube",
    "com.google.android.apps.maps": "Google Maps",
    "com.google.android.gm": "Gmail",
    "com.google.android.googlequicksearchbox": "Google Search",
    "com.android.chrome": "Google Chrome",
    "com.google.android.apps.photos": "Google Photos",
    "com.google.android.calendar": "Google Calendar",
    "com.google.android.keep": "Google Keep",
    "com.google.android.apps.docs": "Google Drive",
    "com.facebook.katana": "Facebook",
    "com.facebook.orca": "Messenger",
    "com.facebook.lite": "Facebook Lite",
    "com.instagram.android": "Instagram",
    "com.zhiliaoapp.musically": "TikTok",
    "com.ss.android.ugc.trill": "TikTok",
    "com.whatsapp": "WhatsApp",
    "com.whatsapp.w4b": "WhatsApp Business",
    "org.telegram.messenger": "Telegram",
    "com.spotify.music": "Spotify",
    "com.netflix.mediaclient": "Netflix",
    "com.twitter.android": "X (Twitter)",
    "com.discord": "Discord",
    "com.viber.voip": "Viber",
    "com.snapchat.android": "Snapchat",
    "com.lazada.android": "Lazada",
    "com.shopee.ph": "Shopee",
    "com.globe.gcash.android": "GCash",
    "com.paymaya": "Maya",
    "com.grabtaxi.passenger": "Grab",
    "tv.twitch.android.app": "Twitch",
    "com.reddit.frontpage": "Reddit",
    "com.pinterest": "Pinterest",
    "com.linkedin.android": "LinkedIn",
    "com.microsoft.teams": "Microsoft Teams",
    "com.microsoft.office.outlook": "Outlook",
    # Finance & Lock apps
    "com.payjoy.access": "Payjoy Access (Finance Lock)",
    "com.payjoy.service": "Payjoy Service (Finance Lock)",
    "com.payjoy.status": "Payjoy Status (Finance Lock)",
    "com.homecredit.ph": "Home Credit (Finance Lock)",
    "com.homecredit.myhomecredit": "My Home Credit",
    "ph.billease.app": "BillEase (Finance Lock)",
    "com.salmon.app": "Salmon (Finance Lock)",
    "com.tala.ph": "Tala Philippines",
    # System apps commonly seen
    "com.android.settings": "Settings",
    "com.android.phone": "Phone",
    "com.android.dialer": "Phone Dialer",
    "com.android.contacts": "Contacts",
    "com.android.mms": "Messages",
    "com.android.camera": "Camera",
    "com.android.calculator2": "Calculator",
    "com.android.deskclock": "Clock",
}


def clean_package_label(package_name: str) -> str:
    """Derive a clean, readable display label from a package name without blocking ADB calls"""
    if package_name in KNOWN_APP_LABELS:
        return KNOWN_APP_LABELS[package_name]

    parts = package_name.split('.')
    if len(parts) >= 2:
        last = parts[-1]
        # Ignore common boilerplate end segments
        if last.lower() in ('android', 'app', 'client', 'mobile', 'lite', 'service', 'ui') and len(parts) >= 3:
            name_part = parts[-2]
        else:
            name_part = last

        # Handle underscores and hyphens
        name_part = name_part.replace('_', ' ').replace('-', ' ')
        # Split CamelCase or PascalCase into separate words
        formatted = re.sub(r'([a-z0-9])([A-Z])', r'\1 \2', name_part).strip()
        return formatted.title()

    return package_name


class ADBService:
    """Service for communicating with Android devices via ADB"""

    def __init__(self, adb_path: str = "adb"):
        self.adb_path = self._find_adb(adb_path)
        self._label_cache: Dict[str, str] = {}
        self._verify_adb()

    def _find_adb(self, default_path: str = "adb") -> str:
        """Find ADB executable, looking in PATH and common installation directories"""
        # First check if default_path is directly executable
        found = shutil.which(default_path)
        if found:
            return found

        # Common locations on Windows
        if sys.platform == "win32":
            candidates = [
                Path("adb.exe"),
                Path.cwd() / "adb.exe",
                Path(os.environ.get("LOCALAPPDATA", "")) / "Android" / "Sdk" / "platform-tools" / "adb.exe",
                Path(os.environ.get("USERPROFILE", "")) / "AppData" / "Local" / "Android" / "Sdk" / "platform-tools" / "adb.exe",
                Path("C:/platform-tools/adb.exe"),
                Path("C:/Program Files/platform-tools/adb.exe"),
            ]
            for cand in candidates:
                if cand.is_file():
                    logger.info(f"Auto-detected ADB at: {cand}")
                    return str(cand)

        return default_path

    def _verify_adb(self) -> bool:
        """Verify ADB is available and working"""
        try:
            result = subprocess.run(
                [self.adb_path, "version"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=5,
                creationflags=CREATE_NO_WINDOW
            )
            if result.returncode == 0:
                logger.info(f"ADB found: {result.stdout.strip()}")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
            logger.error(f"ADB verification failed: {e}")
        return False

    def _run_adb(self, args: List[str], device_serial: Optional[str] = None,
                 timeout: int = 30) -> Tuple[bool, str, str]:
        """Run ADB command and return (success, stdout, stderr)"""
        cmd = [self.adb_path]
        if device_serial:
            cmd.extend(["-s", device_serial])
        cmd.extend(args)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                creationflags=CREATE_NO_WINDOW
            )

            stdout = result.stdout or ""
            stderr = result.stderr or ""
            combined = (stderr + " " + stdout).lower()

            # Check for device-specific errors in both stdout and stderr
            if "device" in combined and ("unauthorized" in combined or "offline" in combined or "not found" in combined or "no device" in combined or "disconnected" in combined):
                # Don't raise device error on simple 'adb devices' scan
                if not (len(args) > 0 and args[0] == "devices"):
                    raise ADBDeviceError(stderr.strip() or stdout.strip())

            return result.returncode == 0, stdout, stderr
        except subprocess.TimeoutExpired:
            return False, "", f"Command timed out after {timeout}s"
        except ADBDeviceError:
            raise
        except Exception as e:
            return False, "", str(e)

    def get_devices(self) -> List[Device]:
        """Get list of connected devices"""
        try:
            success, stdout, stderr = self._run_adb(["devices", "-l"], timeout=10)
            if not success:
                logger.error(f"Failed to get devices: {stderr}")
                return []
        except ADBDeviceError:
            return []

        devices = []
        for line in stdout.strip().split('\n')[1:]:  # Skip header
            line = line.strip()
            if not line:
                continue

            parts = line.split()
            if len(parts) < 2:
                continue

            serial = parts[0]
            status = parts[1]

            model = ""
            product = ""
            device_name = ""

            for part in parts[2:]:
                if part.startswith("model:"):
                    model = part[6:]
                elif part.startswith("product:"):
                    product = part[8:]
                elif part.startswith("device:"):
                    device_name = part[7:]

            devices.append(Device(serial, status, model, product, device_name))

        return devices

    def get_device_model(self, serial: str) -> str:
        """Get device model name"""
        success, stdout, stderr = self._run_adb(
            ["shell", "getprop", "ro.product.model"],
            device_serial=serial,
            timeout=5
        )
        if success:
            return stdout.strip()
        return ""

    def get_packages(self, serial: str, third_party_only: bool = True) -> List[Package]:
        """Get installed packages on device with fast O(1) classification"""
        # 1. Fetch third-party package list in ONE command
        third_party_packages: Set[str] = set()
        success_3, stdout_3, _ = self._run_adb(["shell", "pm", "list", "packages", "-3"],
                                               device_serial=serial, timeout=15)
        if success_3:
            for line in stdout_3.strip().split('\n'):
                line = line.strip()
                if line.startswith("package:"):
                    third_party_packages.add(line[8:])

        # 2. If all packages requested, fetch all
        if third_party_only:
            package_names = sorted(third_party_packages)
        else:
            success_all, stdout_all, stderr_all = self._run_adb(
                ["shell", "pm", "list", "packages"],
                device_serial=serial,
                timeout=15
            )
            if not success_all:
                logger.error(f"Failed to get packages: {stderr_all}")
                return []
            
            package_names_set = set()
            for line in stdout_all.strip().split('\n'):
                line = line.strip()
                if line.startswith("package:"):
                    package_names_set.add(line[8:])
            package_names = sorted(package_names_set)

        # 3. Create Package objects with fast label derivation
        packages: List[Package] = []
        for pkg_name in package_names:
            is_system = pkg_name not in third_party_packages
            # Check label cache or generate clean label instantly
            label = self._label_cache.get(pkg_name) or clean_package_label(pkg_name)
            packages.append(Package(
                package_name=pkg_name,
                label=label,
                is_system=is_system
            ))

        return packages

    def uninstall_package(self, serial: str, package_name: str,
                          user_only: bool = True) -> Tuple[bool, str]:
        """Uninstall a package from device"""
        args = ["shell", "pm", "uninstall"]
        if user_only:
            args.extend(["--user", "0"])
        args.append(package_name)

        try:
            success, stdout, stderr = self._run_adb(args, device_serial=serial, timeout=30)
            output = (stdout.strip() + " " + stderr.strip()).strip()

            if success or "success" in output.lower():
                return True, output or "Success"
            else:
                return False, output or "Uninstall failed"
        except ADBDeviceError as e:
            logger.error(f"Device error during uninstall: {e}")
            raise

    def is_package_installed(self, serial: str, package_name: str) -> bool:
        """Check if a specific package is installed"""
        success, stdout, stderr = self._run_adb(
            ["shell", "pm", "list", "packages", package_name],
            device_serial=serial,
            timeout=5
        )
        return success and f"package:{package_name}" in stdout

    def install_apk(self, serial: str, apk_path: str,
                    allow_downgrade: bool = False, allow_test: bool = False) -> Tuple[bool, str]:
        """Install an APK file on the device
        
        Args:
            serial: Device serial number
            apk_path: Path to the APK file on the computer
            allow_downgrade: Allow version code downgrade (-d flag)
            allow_test: Allow test packages (-t flag)
            
        Returns:
            Tuple of (success, message)
        """
        args = ["install"]
        if allow_downgrade:
            args.append("-d")
        if allow_test:
            args.append("-t")
        args.extend(["-r", apk_path])  # -r = replace existing

        try:
            success, stdout, stderr = self._run_adb(args, device_serial=serial, timeout=120)
            output = (stdout.strip() + " " + stderr.strip()).strip()

            if success or "success" in output.lower():
                return True, output or "Success"
            else:
                return False, output or "Install failed"
        except ADBDeviceError as e:
            logger.error(f"Device error during install: {e}")
            raise


# Global instance
_adb_service: Optional[ADBService] = None


def get_adb_service() -> ADBService:
    """Get or create global ADB service instance"""
    global _adb_service
    if _adb_service is None:
        _adb_service = ADBService()
    return _adb_service
