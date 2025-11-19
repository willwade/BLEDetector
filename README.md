
#  BLE Presence Scanner**

A lightweight BLE presence-detection tool that:

* Continuously scans for BLE devices using `bleak`
* Maps BLE MAC addresses to human-readable names
* Automatically reloads `device_mappings.txt` without restarting
* Includes a CLI tool to add/update mappings

Useful for AT / AAC context-awareness (e.g., detecting which communication partner is nearby), indoor presence detection, prototyping smart environments, etc.

---

# Features

### ✔ Continuous BLE scanning

Runs a loop using `bleak` to detect:

* BLE address
* Device name
* RSSI signal strength

### ✔ Auto-reload of mapping file

Edit `device_mappings.txt` manually or programmatically and the scanner picks up changes instantly.

### ✔ CLI tool for adding devices

Easily add/update mappings from the terminal:

```bash
python add_device.py AA:BB:CC:DD:EE:FF "Alice"
```

### ✔ Simple, human-editable mapping file

Format:

```
AA:BB:CC:DD:EE:FF = Alice
11:22:33:44:55:66 = Bob
```

---

# 🛠 Installation (using uv)

Install dependencies into a venv:

```bash
uv venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
uv pip install -r requirements.txt
```

Or install directly from the `pyproject.toml`:

```bash
uv sync
```

That’s it — uv manages everything.

---

# ▶ Running the Scanner

```bash
uv run scan_ble.py
```

You’ll see output like:

```
[INFO] Scanning for BLE devices...
[KNOWN]   Alice                | RSSI -58 | AA:BB:CC:DD:EE:FF
[UNKNOWN] Name=iPhone          | RSSI -78 | C1:D2:E3:F4:A5:B6
[KNOWN]   Dining Room Beacon   | RSSI -65 | 11:22:33:44:55:66
```

Mappings update every few seconds automatically. No restart needed.

---

# ➕ Adding a Device

To add/update a friendly name:

```bash
uv run add_device.py C3:4F:89:A1:B2:C3 "Kitchen Tag"
```

Edit manually if you prefer:

```
C3:4F:89:A1:B2:C3 = Kitchen Tag
```

The running scanner will reload it automatically.

---

# 📝 device_mappings.txt Format

```
# BLE address → friendly name
# Comments allowed

AA:BB:CC:DD:EE:FF = Alice
11:22:33:44:55:66 = Bob
```

* MAC addresses are **case-insensitive**, auto-normalised to uppercase.
* Lines without `=` are ignored.

---

# ⚠ Notes on BLE Scanning

* Some devices randomize MAC addresses (Android, iOS).
* Dedicated tags (Tile, ESP32, NRF boards) are more stable.
* RSSI values are noisy; average them if you need distance estimation.

