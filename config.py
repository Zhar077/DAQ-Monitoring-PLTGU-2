# ================= CONFIG =================

POLL_INTERVAL = 60  # seconds

RTU_PORT = "/dev/ttyUSB0"
RTU_BAUD = 9600
RTU_PARITY = "N"

RTU_DDSU_STOPBITS = 1
RTU_SHT_STOPBITS = 1
RTU_PZEM_STOPBITS = 1
RTU_BMS_STOPBITS = 1
RTU_EM619001_STOPBITS = 1   # NEW

# Existing AC sensors
DDSU_IDS = [2, 4, 5, 6, 7, 8]
PZEM_IDS = [3]
SHT_IDS = [1]
BMS_IDS = [9]

# DC sensors (NEW)
# EM619001 4 unit di topologi PLTS hybrid:
# - PV side: meter di antara panel dan inverter (unidirectional)
# - Battery side: meter di antara inverter dan baterai (bidirectional, mode=0)
EM619001_PV_IDS = [10, 30]      # 2 meter PV (slave 10 untuk system A, 30 untuk system B)
EM619001_BAT_IDS = [20, 40]     # 2 meter Battery (slave 20 untuk system A, 40 untuk system B)

WS_HOST = "0.0.0.0"
WS_PORT = 8765

BACKEND_HOST = "0.0.0.0"
BACKEND_PORT = 8080
# =========================================
