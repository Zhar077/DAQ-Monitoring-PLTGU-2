# EM619001 Integration ke solar-panel-daq

Driver baru untuk DC Energy Meter EM619001 (200A/1000VDC bidirectional)
yang **kompatibel dengan project solar-panel-daq yang sudah ada**.

Mengikuti pattern yang sama dengan driver `rtu/ddsu.py`, `rtu/pzem.py`,
dst, sehingga tinggal di-merge ke project tanpa rewrite.

## Apa yang Berubah

### File Baru (tambahkan ke project)

1. `rtu/em619001.py` - Driver Modbus untuk EM619001

### File yang Dimodifikasi

1. `helper/parse.py` - Tambah fungsi `parse_em619001_signed_32`
2. `config.py` - Tambah `EM619001_PV_IDS`, `EM619001_BAT_IDS`, `RTU_EM619001_STOPBITS`
3. `main.py` - Import dan integrate driver baru

## Cara Pasang ke Project

### Step 1: Backup project lama

```bash
cd ~/projects/python
cp -r solar-panel-daq solar-panel-daq.backup
```

### Step 2: Copy file baru

```bash
cp em619001_integration/rtu/em619001.py solar-panel-daq/rtu/
```

### Step 3: Update file yang dimodifikasi

Untuk `helper/parse.py`, tambahkan fungsi baru di akhir file
(JANGAN replace, append saja):

```python
# Tambahkan di akhir helper/parse.py
def parse_em619001_signed_32(registers):
    """Converts 2 registers (32-bit) to signed integer."""
    if len(registers) < 2:
        return 0
    raw = (registers[0] << 16) | registers[1]
    if raw >= 0x80000000:
        raw -= 0x100000000
    return raw
```

Untuk `config.py`, tambahkan:

```python
# Tambahkan setelah RTU_BMS_STOPBITS = 1
RTU_EM619001_STOPBITS = 1

# Tambahkan setelah BMS_IDS = [9]
EM619001_PV_IDS = [10, 30]      # ganti sesuai slave_id meter Anda
EM619001_BAT_IDS = [20, 40]
```

Untuk `main.py`, tambahkan:

```python
# Tambah import (setelah import rtu lainnya)
from rtu.em619001 import read_em619001

# Tambah di import config
from config import (
    ...,
    EM619001_PV_IDS,
    EM619001_BAT_IDS,
)

# Di dalam modbus_reader(), tambah setelah loop SHT:
for sid in EM619001_PV_IDS:
    em_data = await read_em619001(sid)
    data.append({"id": sid, "type": "EM619001_PV", "data": em_data})

for sid in EM619001_BAT_IDS:
    em_data = await read_em619001(sid)
    data.append({"id": sid, "type": "EM619001_BAT", "data": em_data})

# Di dalam flush_bucket(), tambah handler untuk type baru:
elif entry["type"] == "EM619001_PV":
    url = f"http://{BACKEND_HOST}:{BACKEND_PORT}/api/v1/em619001-pv/create"

elif entry["type"] == "EM619001_BAT":
    url = f"http://{BACKEND_HOST}:{BACKEND_PORT}/api/v1/em619001-bat/create"
```

### Step 4: Konfigurasi slave_id meter EM619001

Sebelum jalankan DAQ, pastikan setiap meter EM619001 punya slave_id unik.
Pakai utility script saya yang sebelumnya: `configure_meter.py`.

Contoh setting yang konsisten dengan config:

```
Meter PV System A    → slave_id = 10
Meter Battery A      → slave_id = 20 (mode bidirectional)
Meter PV System B    → slave_id = 30
Meter Battery B      → slave_id = 40 (mode bidirectional)
```

(Ganti nilai 10, 20, 30, 40 di config.py kalau Anda pakai slave_id berbeda)

### Step 5: Set bidirectional mode untuk meter battery

```bash
python set_metering_mode.py 20 0   # battery A bidirectional
python set_metering_mode.py 40 0   # battery B bidirectional
```

### Step 6: Test

```bash
cd ~/projects/python/solar-panel-daq
source .venv/bin/activate     # kalau ada virtualenv
python main.py
```

Output akan include data EM619001 di samping DDSU/PZEM/SHT yang sudah ada.

## Output Data Format

WebSocket dan HTTP forward akan kirim data dengan format:

```json
{
  "ts": 1697049600,
  "data": [
    {
      "id": 2,
      "type": "DDSU",
      "data": { "voltage": 230.5, ... }
    },
    {
      "id": 10,
      "type": "EM619001_PV",
      "data": {
        "voltage": 380.5,
        "current": 7.483,
        "power": 2845.3,
        "energy_total": 1234.56,
        "energy_forward": 1234.56,
        "energy_reverse": 0.0,
        "alarm_status": 0
      }
    },
    {
      "id": 20,
      "type": "EM619001_BAT",
      "data": {
        "voltage": 51.2,
        "current": -25.3,
        "power": -1295.4,
        "energy_total": 44.1,
        "energy_forward": 856.2,
        "energy_reverse": 812.1,
        "alarm_status": 0
      }
    }
  ]
}
```

Note: untuk EM619001_BAT, current/power negatif = discharging,
positif = charging (asumsi konvensi shunt standar).

## Backend Endpoint yang Dibutuhkan

DAQ akan POST ke endpoint berikut tiap jam (setelah averaging):

- `POST /api/v1/em619001-pv/create`
- `POST /api/v1/em619001-bat/create`

Endpoint ini perlu dibuat di backend FastAPI. Akan dibahas di
dokumen integrasi backend.

## Register Map yang Dibaca

Driver membaca register-register berikut dari setiap meter EM619001:

| Parameter | Address | Count | Decode | Unit |
|---|---:|:---:|---|---|
| Voltage | 0x0131 | 1 | raw / 10 | V |
| Current | 0x0139 | 2 | signed_32 / 1000 | A |
| Power | 0x0141 | 2 | signed_32 / 10 | W |
| Energy Total | 0x0000 | 2 | unsigned_32 / 100 | kWh |
| Energy Forward | 0x0014 | 2 | unsigned_32 / 100 | kWh |
| Energy Reverse | 0x001E | 2 | unsigned_32 / 100 | kWh |
| Alarm Status | 0x0073 | 1 | bitmask | bits |

Semua via Function Code 0x03 (Read Holding Registers).

## Troubleshooting

**"Error reading EM619001 X: connection failed"**
- Cek wiring RS485 (A-B konsisten)
- Cek slave_id sesuai dengan EM619001_PV_IDS atau EM619001_BAT_IDS
- Cek meter dapat power supply

**Data current/power selalu positif (tidak ada sign)**
- Meter masih dalam mode 1 (unidirectional)
- Set ke mode 0 dengan `set_metering_mode.py <slave_id> 0`

**Data 0 semua**
- Meter idle (no current flowing)
- Bisa juga register kosong; pastikan terminal V+ dan V- terhubung

**Cycle time terlalu lama (DAQ poll < interval)**
- 4 meter EM619001 + AC sensors total bisa makan 3-5 detik per cycle
- Naikkan POLL_INTERVAL di config.py
- Atau naikkan baudrate ke 19200 (perlu konfigurasi semua meter)

## Berbeda dari Project Asli?

Tidak ada breaking change. Semua sensor lama (DDSU, PZEM, SHT)
tetap berjalan sama persis. EM619001 hanya ditambahkan sebagai
sensor baru di pipeline yang sudah ada.

Pattern yang dipakai:
- Same async pattern dengan AsyncModbusSerialClient
- Same connection open-close per polling cycle
- Same data structure di WebSocket payload
- Same hour bucket averaging untuk HTTP forward
- Same error handling style

## File-file di Folder Ini

```
em619001_integration/
├── README.md                  ← dokumen ini
├── rtu/
│   └── em619001.py            ← driver baru, copy ke solar-panel-daq/rtu/
├── helper/
│   └── parse.py               ← versi update, merge dengan yang ada
├── config.py                  ← versi update, merge dengan yang ada
└── main.py                    ← versi update, merge dengan yang ada
```
# PLTGU-Monitoring-2
# PLTGU-Monitoring-2
