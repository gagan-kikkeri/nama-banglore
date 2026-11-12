"""
60/77 GHz FMCW Millimeter-Wave Radar & Modbus RTU / RS-485 Telemetry Emulator.
Emulates the soffit-mounted radar sensor inside Catch-Basin CB-FMCW-SB-102,
encoding live H_w(t) and dH/dt time-series into standard Modbus RTU (Function 0x03)
RS-485 frames with CRC-16 (IBM/ANSI) integrity verification.
"""

import struct
from typing import Dict, Any, List


def modbus_crc16(data: bytes) -> int:
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


def build_read_holding_registers_request(
    slave_id: int = 1,
    start_addr: int = 0,
    quantity: int = 5
) -> bytes:
    """Build a Modbus RTU Function 0x03 (Read Holding Registers) master request frame."""
    pdu = struct.pack(">BBHH", slave_id & 0xFF, 0x03, start_addr & 0xFFFF, quantity & 0xFFFF)
    crc = modbus_crc16(pdu)
    return pdu + struct.pack("<H", crc)


def build_read_holding_registers_response(
    slave_id: int,
    registers: List[int]
) -> bytes:
    """Build a Modbus RTU Function 0x03 slave response frame with CRC-16."""
    byte_count = len(registers) * 2
    header = struct.pack(">BBB", slave_id & 0xFF, 0x03, byte_count)
    payload = b"".join(struct.pack(">H", reg & 0xFFFF) for reg in registers)
    frame_wo_crc = header + payload
    crc = modbus_crc16(frame_wo_crc)
    return frame_wo_crc + struct.pack("<H", crc)


def decode_modbus_rtu_response(frame: bytes) -> Dict[str, Any]:
    """Verify CRC-16 and decode a Modbus RTU Function 0x03 response frame."""
    if len(frame) < 5:
        raise ValueError("Modbus RTU frame too short")

    body = frame[:-2]
    received_crc = struct.unpack("<H", frame[-2:])[0]
    expected_crc = modbus_crc16(body)
    if received_crc != expected_crc:
        raise ValueError(f"Modbus CRC-16 mismatch: got 0x{received_crc:04X}, expected 0x{expected_crc:04X}")

    slave_id, func_code, byte_count = struct.unpack(">BBB", body[:3])
    if func_code != 0x03:
        raise ValueError(f"Unsupported Modbus function code: 0x{func_code:02X}")

    reg_bytes = body[3:3 + byte_count]
    num_regs = byte_count // 2
    raw_regs = [struct.unpack(">H", reg_bytes[i * 2:(i + 1) * 2])[0] for i in range(num_regs)]

    def to_signed_16(val: int) -> int:
        return val - 65536 if val >= 32768 else val

    hw_cm = round(raw_regs[0] / 10.0, 2) if num_regs > 0 else 0.0
    dh_dt_cm_min = round(to_signed_16(raw_regs[1]) / 100.0, 2) if num_regs > 1 else 0.0
    rain_mmhr = round(raw_regs[2] / 10.0, 1) if num_regs > 2 else 0.0
    clog_pct = round(raw_regs[3] / 10.0, 1) if num_regs > 3 else 0.0
    delta_h = round(to_signed_16(raw_regs[4]) / 100.0, 2) if num_regs > 4 else 0.0

    return {
        "crc_valid": True,
        "slave_id": slave_id,
        "function_code": "0x03",
        "raw_registers": raw_regs,
        "hw_cm": hw_cm,
        "dh_dt_cm_min": dh_dt_cm_min,
        "rainfall_mmhr": rain_mmhr,
        "grate_obstruction_pct": clog_pct,
        "delta_h": delta_h,
    }


class FMCWRadarEmulator:
    """
    Emulates a 77 GHz FMCW radar connected over RS-485 Modbus RTU.
    Registers:
      - 0x0000: H_w(t) in tenths of cm (mm) [uint16]
      - 0x0001: dH/dt in hundredths of cm/min [int16]
      - 0x0002: Rainfall intensity in tenths of mm/hr [uint16]
      - 0x0003: Grate obstruction / silt clog in tenths of % [uint16]
      - 0x0004: Differential Inflow Index Delta-H in hundredths [int16]
    """

    def __init__(self, slave_id: int = 1, baudrate: int = 9600, frequency_ghz: float = 77.0):
        self.slave_id = slave_id
        self.baudrate = baudrate
        self.frequency_ghz = frequency_ghz

    @staticmethod
    def _encode_signed_16(val: int) -> int:
        val = max(-32768, min(32767, val))
        return val & 0xFFFF

    def sample_and_stream(
        self,
        hw_cm: float,
        dh_dt_cm_min: float,
        rainfall_mmhr: float,
        grate_obstruction_pct: float,
        delta_h: float,
    ) -> Dict[str, Any]:
        """Encode current Gazebo water telemetry into a Modbus RTU RS-485 frame and verify decode."""
        regs = [
            max(0, min(65535, int(round(hw_cm * 10.0)))),
            self._encode_signed_16(int(round(dh_dt_cm_min * 100.0))),
            max(0, min(65535, int(round(rainfall_mmhr * 10.0)))),
            max(0, min(65535, int(round(grate_obstruction_pct * 10.0)))),
            self._encode_signed_16(int(round(delta_h * 100.0))),
        ]
        req_frame = build_read_holding_registers_request(self.slave_id, 0, len(regs))
        resp_frame = build_read_holding_registers_response(self.slave_id, regs)
        decoded = decode_modbus_rtu_response(resp_frame)

        return {
            "sensor_type": f"{self.frequency_ghz:.0f} GHz FMCW Millimeter-Wave Radar",
            "bus_protocol": f"Modbus RTU / RS-485 ({self.baudrate} bps, 8N1)",
            "request_hex": req_frame.hex(" ").upper(),
            "response_hex": resp_frame.hex(" ").upper(),
            "decoded": decoded,
        }
