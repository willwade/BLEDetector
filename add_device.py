# add_device.py
import argparse
from pathlib import Path

DEFAULT_MAPPING_FILE = "device_mappings.txt"


def upsert_device_mapping(
    address: str, name: str, path: str = DEFAULT_MAPPING_FILE
) -> None:
    address = address.strip().upper()
    name = name.strip()

    p = Path(path)

    if not p.exists():
        # Create new file with a header comment
        lines = [
            "# Device mappings: ADDRESS = Friendly Name",
            "# Lines starting with # are comments.",
            "",
            f"{address} = {name}",
            "",
        ]
        p.write_text("\n".join(lines), encoding="utf-8")
        print(f"[INFO] Created {path} and added {address} -> {name}")
        return

    # Read existing lines
    with p.open("r", encoding="utf-8") as f:
        lines = f.readlines()

    updated = False
    new_lines = []

    for line in lines:
        stripped = line.strip()

        # Keep comments / empty lines
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            new_lines.append(line)
            continue

        existing_addr, existing_name = stripped.split("=", 1)
        existing_addr = existing_addr.strip().upper()

        if existing_addr == address:
            # Replace this line with updated mapping
            new_line = f"{address} = {name}\n"
            new_lines.append(new_line)
            updated = True
        else:
            new_lines.append(line)

    if not updated:
        # Append at the end (ensure an empty line before, if needed)
        if new_lines and not new_lines[-1].endswith("\n"):
            new_lines[-1] = new_lines[-1] + "\n"
        if new_lines and new_lines[-1].strip():
            new_lines.append("\n")
        new_lines.append(f"{address} = {name}\n")

    with p.open("w", encoding="utf-8") as f:
        f.writelines(new_lines)

    action = "Updated" if updated else "Added"
    print(f"[INFO] {action} mapping: {address} -> {name} in {path}")


def main():
    parser = argparse.ArgumentParser(
        description="Add or update a BLE device mapping in device_mappings.txt"
    )
    parser.add_argument("address", help="BLE device address (e.g. AA:BB:CC:DD:EE:FF)")
    parser.add_argument("name", help="Friendly name (e.g. 'Alice')")
    parser.add_argument(
        "-f",
        "--file",
        default=DEFAULT_MAPPING_FILE,
        help=f"Path to mapping file (default: {DEFAULT_MAPPING_FILE})",
    )

    args = parser.parse_args()
    upsert_device_mapping(args.address, args.name, args.file)


if __name__ == "__main__":
    main()
