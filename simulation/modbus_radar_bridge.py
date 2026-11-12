"""
Namma Bengaluru - HK-RHS (Hydro-Kinetic Road Hazard System)
60/77 GHz FMCW Millimeter-Wave Radar -> Modbus RTU / RS-485 Telemetry Bridge.

Register Map (Holding Registers, Slave ID 0x01, Function Code 0x03):
  - Reg 0x0000: H_w(t) Water Level (unsigned 16-bit, 0.1 mm resolution -> cm * 100)
  - Reg 0x0001: dH/dt Differential Inflow Rate (signed 16-bit, 0.01 cm/min resolution)
  - Reg 0x0002: Delta-H Catch-Basin Blockage Index (unsigned 16-bit, 0.01 resolution)
  - Reg 0x0003: Rainfall Intensity R(t) (unsigned 16-bit, 0.1 mm/hr resolution)
  - Reg 0x0004: Culvert Capacity Utilization % (unsigned 16-bit, 0.1 % resolution)
  - Reg 0x0005: Radome & Sensor Status Word (0x0001 = HDPE_SEALED_NOMINAL)
"""

import struct
import time
from typing import Dict, Any, List


def crc16_modbus(data: bytes) -> int:
    """Compute standard Modbus RTU CRC-16 (polynomial 0xA001, init 0xFFFF)."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc & 0xFFFF


def verify_modbus_crc(frame: bytes) -> bool:
    """Verify trailing little-endian CRC-16/MODBUS checksum on a binary RTU frame."""
    if len(frame) < 4:
        return False
    payload, rx_crc = frame[:-2], struct.unpack("<H", frame[-2:])[0]
    return crc16_modbus(payload) == rx_crc


class ModbusRTURadarSlave:
    """
    Emulates the soffit-mounted 60/77 GHz FMCW millimeter-wave radar node
    communicating over RS-485 half-duplex serial using Modbus RTU.
    """

    def __init__(self, slave_id: int = 0x01, baudrate: int = 9600, port_name: str = "RS485-COM-RADAR01"):
        self.slave_id = slave_id
        self.baudrate = baudrate
        self.port_name = port_name
        self.holding_registers: List[int] = [0] * 6
        self.last_updated_ts: float = time.time()

    def update_from_gazebo_radar(
        self,
        water_level_cm: float,
        dh_dt_cm_min: float,
        delta_h: float,
        rainfall_mmhr: float,
        max_capacity_cm: float = 120.0,
        status_word: int = 0x0001,
    ) -> None:
        """Encode physical Gazebo FMCW radar readings into 16-bit Modbus holding registers."""
        hw_reg = max(0, min(65535, int(round(water_level_cm * 100.0))))
        # Signed 16-bit representation for dH/dt (can be negative during drainage recession)
        dh_dt_scaled = max(-32768, min(32767, int(round(dh_dt_cm_min * 100.0))))
        dh_dt_reg = dh_dt_scaled & 0xFFFF
        delta_h_reg = max(0, min(65535, int(round(delta_h * 100.0))))
        rain_reg = max(0, min(65535, int(round(rainfall_mmhr * 10.0))))
        cap_pct = max(0.0, min(100.0, (water_level_cm / max(1.0, max_capacity_cm)) * 100.0))
        cap_reg = int(round(cap_pct * 10.0))

        self.holding_registers = [
            hw_reg,
            dh_dt_reg,
            delta_h_reg,
            rain_reg,
            cap_reg,
            status_word & 0xFFFF,
        ]
        self.last_updated_ts = time.time()

    def handle_rtu_request(self, request_frame: bytes) -> bytes:
        """
        Process an incoming Modbus RTU binary request frame (Function 0x03)
        and return a CRC-protected Modbus RTU response frame.
        """
        if len(request_frame) != 8 or not verify_modbus_crc(request_frame):
            raise ValueError("Invalid Modbus RTU request frame or CRC mismatch")

        slave, func_code, start_addr, reg_count = struct.unpack(">BBHH", request_frame[:6])
        if slave != self.slave_id:
            raise ValueError(f"Slave ID mismatch: expected {self.slave_id}, got {slave}")
        if func_code != 0x03:
            # Modbus exception response (Illegal Function 0x01)
            err = struct.pack(">BBB", self.slave_id, func_code | 0x80, 0x01)
            return err + struct.pack("<H", crc16_modbus(err))
        if start_addr + reg_count > len(self.holding_registers):
            err = struct.pack(">BBB", self.slave_id, func_code | 0x80, 0x02)
            return err + struct.pack("<H", crc16_modbus(err))

        selected = self.holding_registers[start_addr : start_addr + reg_count]
        byte_count = reg_count * 2
        header = struct.pack(">BBB", self.slave_id, func_code, byte_count)
        body = b"".join(struct.pack(">H", reg) for reg in selected)
        pdu = header + body
        return pdu + struct.pack("<H", crc16_modbus(pdu))


class ModbusRTUMasterPoller:
    """
    Polls the emulated RS-485 radar slave via Modbus RTU Function 0x03
    and decodes H_w(t) and dH/dt telemetry for the FastAPI broker.
    """

    def __init__(self, slave: ModbusRTURadarSlave):
        self.slave = slave
        self.frames_polled = 0

    def poll_telemetry(self) -> Dict[str, Any]:
        """Execute a full Modbus RTU request/response cycle over RS-485."""
        # Build Function 0x03 request: Slave 0x01, Read 6 Registers from 0x0000
        req_pdu = struct.pack(">BBHH", self.slave.slave_id, 0x03, 0x0000, 6)
        req_frame = req_pdu + struct.pack("<H", crc16_modbus(req_pdu))

        resp_frame = self.slave.handle_rtu_request(req_frame)
        crc_ok = verify_modbus_crc(resp_frame)
        if not crc_ok:
            raise RuntimeError("RS-485 Modbus RTU response CRC-16 verification failed")

        _, func_code, byte_count = struct.unpack(">BBB", resp_frame[:3])
        if func_code != 0x03 or byte_count != 12:
            raise RuntimeError(f"Unexpected Modbus RTU response: func={func_code}, bytes={byte_count}")

        regs = struct.unpack(">6H", resp_frame[3:15])
        hw_cm = round(regs[0] / 100.0, 2)
        # Convert unsigned 16-bit back to signed 16-bit for dH/dt
        raw_dh_dt = regs[1] - 0x10000 if (regs[1] & 0x8000) else regs[1]
        dh_dt_cm_min = round(raw_dh_dt / 100.0, 2)
        delta_h = round(regs[2] / 100.0, 2)
        rainfall_mmhr = round(regs[3] / 10.0, 1)
        capacity_pct = round(regs[4] / 10.0, 1)
        status_word = regs[5]

        self.frames_polled += 1
        return {
            "protocol": "Modbus RTU / RS-485",
            "serial_bus": self.slave.port_name,
            "baudrate": self.slave.baudrate,
            "slave_id": f"0x{self.slave.slave_id:02X}",
            "function_code": "0x03 (Read Holding Registers)",
            "crc16_valid": crc_ok,
            "frames_polled": self.frames_polled,
            "tx_frame_hex": req_frame.hex(" ").upper(),
            "rx_frame_hex": resp_frame.hex(" ").upper(),
            "raw_registers": list(regs),
            "decoded": {
                "water_level_hw_cm": hw_cm,
                "inflow_rate_dh_dt_cm_min": dh_dt_cm_min,
                "delta_h_index": delta_h,
                "rainfall_rate_mmhr": rainfall_mmhr,
                "culvert_capacity_pct": capacity_pct,
                "sensor_status": "HDPE_SEALED_NOMINAL" if status_word == 0x0001 else f"WARN_0x{status_word:04X}",
            },
        }
