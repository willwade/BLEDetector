# scan_ble.py
import asyncio
import time
from pathlib import Path
from dataclasses import dataclass, field

from bleak import BleakScanner


MAPPING_FILE = "device_mappings.txt"
PRINT_INTERVAL = 5      # how often to print the table (seconds)
RELOAD_INTERVAL = 5     # how often to reload mappings (seconds)
STALE_AFTER = 30        # hide devices not seen for this many seconds


def load_device_mappings(path: str = MAPPING_FILE) -> dict:
    """
    Load mappings of IDENTIFIER -> friendly name.

    IDENTIFIER can be:
      - a BLE address / UUID
      - a BLE device name (e.g. 'iPhone iWill')
    Matching is done case-insensitively on the identifier.
    """
    mapping = {}
    p = Path(path)

    if not p.exists():
        print(f"[INFO] Mapping file {path} does not exist yet.")
        return mapping

    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if "=" not in line:
                print(f"[WARN] Ignoring malformed line in {path!r}: {line}")
                continue

            identifier, name = line.split("=", 1)
            key = identifier.strip().upper()
            mapping[key] = name.strip()

    return mapping


@dataclass
class SeenDevice:
    addr: str
    name: str
    rssi: int | None = None
    last_seen: float = field(default_factory=time.time)


class DeviceTracker:
    def __init__(self, mapping_path: str = MAPPING_FILE):
        self.mapping_path = mapping_path
        self.mapping = load_device_mappings(mapping_path)
        self.last_reload = time.time()
        self.devices: dict[str, SeenDevice] = {}

        print("[INFO] Initial mappings:")
        if self.mapping:
            for ident, name in self.mapping.items():
                print(f"  {ident} -> {name}")
        else:
            print("  (none yet)")
        print()

    def maybe_reload_mapping(self):
        now = time.time()
        if now - self.last_reload >= RELOAD_INTERVAL:
            new_map = load_device_mappings(self.mapping_path)
            if new_map != self.mapping:
                print("\n[INFO] Device mappings updated:")
                for ident, name in new_map.items():
                    print(f"  {ident} -> {name}")
                print()
                self.mapping = new_map
            self.last_reload = now

    def detection_callback(self, device, advertisement_data):
        """Called by Bleak every time an advertisement is seen."""
        addr = device.address or ""
        name = device.name or "N/A"
        rssi = advertisement_data.rssi  # <- this is the good bit on macOS

        key = addr or name  # use address if present, else name
        now = time.time()

        existing = self.devices.get(key)
        if existing:
            existing.rssi = rssi
            existing.name = name
            existing.last_seen = now
        else:
            self.devices[key] = SeenDevice(addr=addr, name=name, rssi=rssi, last_seen=now)

    def _friendly_name(self, dev: SeenDevice) -> str | None:
        # Match by address OR by name (case-insensitive)
        addr_key = (dev.addr or "").upper()
        name_key = dev.name.strip().upper() if dev.name else ""

        return self.mapping.get(addr_key) or self.mapping.get(name_key)

    def print_OLD_table(self):
        now = time.time()

        # Drop stale devices
        self.devices = {
            k: v for k, v in self.devices.items()
            if now - v.last_seen <= STALE_AFTER
        }

        if not self.devices:
            print("[INFO] No recent devices.\n")
            return

        print("[INFO] Recently seen devices (last ~30s):")
        print("-" * 80)
        print(f"{'KNOWN?':<8} {'Friendly':<20} {'RSSI':<6} {'Name':<20} {'ID':<20}")
        print("-" * 80)

        for dev in self.devices.values():
            friendly = self._friendly_name(dev)
            known = "YES" if friendly else "NO"
            label = friendly or ""
            rssi_str = str(dev.rssi) if dev.rssi is not None else "N/A"
            print(
                f"{known:<8} {label:<20} {rssi_str:<6} "
                f"{dev.name:<20} {dev.addr:<20}"
            )

        print("-" * 80)
        print()

    def print_table(self):
        now = time.time()

        # Drop stale devices
        self.devices = {
            k: v for k, v in self.devices.items()
            if now - v.last_seen <= STALE_AFTER
        }

        if not self.devices:
            print("[INFO] No recent devices.\n")
            return

        print("[INFO] Recently seen devices (last ~30s):")

        # -------- SORTING --------
        # Split into known and unknown devices
        known = []
        unknown = []

        for dev in self.devices.values():
            friendly = self._friendly_name(dev)
            if friendly:
                known.append((friendly, dev))
            else:
                unknown.append(dev)

        # Sort known devices by RSSI (higher is closer)
        known.sort(key=lambda kv: (kv[1].rssi if kv[1].rssi is not None else -999), reverse=True)

        # Sort unknown devices by RSSI too (optional)
        unknown.sort(key=lambda d: (d.rssi if d.rssi is not None else -999), reverse=True)

        # -------- PRINTING --------
        print("-" * 80)
        print("KNOWN DEVICES (closest first)")
        print("-" * 80)
        print(f"{'Friendly':<20} {'RSSI':<6} {'Name':<20} {'ID':<20}")
        print("-" * 80)
        for friendly, dev in known:
            rssi_str = str(dev.rssi) if dev.rssi is not None else "N/A"
            print(f"{friendly:<20} {rssi_str:<6} {dev.name:<20} {dev.addr:<20}")
        if not known:
            print("(none)")
        print()

        print("-" * 80)
        print("UNKNOWN DEVICES")
        print("-" * 80)
        print(f"{'RSSI':<6} {'Name':<20} {'ID':<20}")
        print("-" * 80)
        for dev in unknown:
            rssi_str = str(dev.rssi) if dev.rssi is not None else "N/A"
            print(f"{rssi_str:<6} {dev.name:<20} {dev.addr:<20}")
        if not unknown:
            print("(none)")
        print()

        print("-" * 80)
        print()



async def main():
    tracker = DeviceTracker(MAPPING_FILE)

    scanner = BleakScanner(detection_callback=tracker.detection_callback)

    await scanner.start()
    print("[INFO] Scanner started. Press Ctrl+C to stop.\n")

    try:
        while True:
            tracker.maybe_reload_mapping()
            tracker.print_table()
            await asyncio.sleep(PRINT_INTERVAL)
    except KeyboardInterrupt:
        print("\n[INFO] Stopping scanner...")
    finally:
        await scanner.stop()
        print("[INFO] Scanner stopped.")


if __name__ == "__main__":
    asyncio.run(main())