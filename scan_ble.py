# scan_ble.py
import asyncio
import time
from pathlib import Path

from bleak import BleakScanner


MAPPING_FILE = "device_mappings.txt"
SCAN_INTERVAL = 5        # seconds between scans
RELOAD_INTERVAL = 5      # seconds between mapping reloads

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



async def continuous_scan(
    mapping_path: str = MAPPING_FILE,
    scan_interval: int = SCAN_INTERVAL,
    reload_interval: int = RELOAD_INTERVAL,
):
    device_map = load_device_mappings(mapping_path)
    last_reload = time.time()

    print("[INFO] Initial mappings:")
    if device_map:
        for ident, name in device_map.items():
            print(f"  {ident} -> {name}")
    else:
        print("  (none yet)")
    print()

    try:
        while True:
            now = time.time()

            # --- Reload mapping file periodically ---
            if now - last_reload >= reload_interval:
                new_map = load_device_mappings(mapping_path)
                if new_map != device_map:
                    print("\n[INFO] Device mappings updated:")
                    for ident, name in new_map.items():
                        print(f"  {ident} -> {name}")
                    print()
                    device_map = new_map
                last_reload = now

            print("[INFO] Scanning for BLE devices...")
            devices = await BleakScanner.discover(timeout=scan_interval)

            if not devices:
                print("  No devices found.\n")
            else:
                for d in devices:
                    addr = d.address or ""
                    name_raw = d.name or "N/A"

                    # Normalised keys
                    addr_key = addr.upper()
                    name_key = name_raw.strip().upper()

                    # Try mapping by address OR by name
                    friendly = (
                        device_map.get(addr_key)
                        or device_map.get(name_key)
                    )

                    # RSSI still best-effort (macOS often won't give it)
                    rssi = None
                    if hasattr(d, "rssi"):
                        rssi = d.rssi
                    elif hasattr(d, "metadata") and isinstance(d.metadata, dict):
                        rssi = d.metadata.get("rssi")
                    rssi_str = str(rssi) if rssi is not None else "N/A"

                    if friendly:
                        print(
                            f"[KNOWN]   {friendly:<20} | RSSI {rssi_str:>4} "
                            f"| Name={name_raw:<15} | ID={addr}"
                        )
                    else:
                        print(
                            f"[UNKNOWN] Name={name_raw:<15} | RSSI {rssi_str:>4} "
                            f"| ID={addr}"
                        )
                print()

            await asyncio.sleep(0.1)

    except KeyboardInterrupt:
        print("\n[INFO] Stopped by user (Ctrl+C).")

if __name__ == "__main__":
    asyncio.run(
        continuous_scan(
            mapping_path=MAPPING_FILE,
            scan_interval=SCAN_INTERVAL,
            reload_interval=RELOAD_INTERVAL,
        )
    )
