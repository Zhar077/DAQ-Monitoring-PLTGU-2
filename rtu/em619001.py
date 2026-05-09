from pymodbus.client import AsyncModbusSerialClient

from helper.parse import parse_em619001_signed_32

from config import RTU_BAUD, RTU_PARITY, RTU_PORT, RTU_EM619001_STOPBITS


async def read_em619001(device_id):
    client = AsyncModbusSerialClient(
        port=RTU_PORT,
        baudrate=RTU_BAUD,
        parity=RTU_PARITY,
        stopbits=RTU_EM619001_STOPBITS,
        bytesize=8,
        timeout=1,
    )

    data = {}

    await client.connect()

    if not client.connected:
        print(f"Error reading EM619001 {device_id}: connection failed")
        return data

    try:
        # Voltage (1 register, scale 0.1)
        result = await client.read_holding_registers(
            0x0131, count=1, device_id=device_id
        )
        if result.isError():
            print(f"Error reading EM619001 {device_id} voltage: {result}")
        else:
            data["voltage"] = result.registers[0] / 10.0

        # Current (2 register, signed, scale 0.001)
        result = await client.read_holding_registers(
            0x0139, count=2, device_id=device_id
        )
        if result.isError():
            print(f"Error reading EM619001 {device_id} current: {result}")
        else:
            data["current"] = parse_em619001_signed_32(result.registers) / 1000.0

        # Active Power (2 register, signed, scale 0.1, unit Watt)
        result = await client.read_holding_registers(
            0x0141, count=2, device_id=device_id
        )
        if result.isError():
            print(f"Error reading EM619001 {device_id} power: {result}")
        else:
            data["power"] = parse_em619001_signed_32(result.registers) / 10.0

        # Energy Total (2 register, scale 0.01)
        result = await client.read_holding_registers(
            0x0000, count=2, device_id=device_id
        )
        if result.isError():
            print(f"Error reading EM619001 {device_id} energy_total: {result}")
        else:
            raw = (result.registers[0] << 16) | result.registers[1]
            data["energy_total"] = raw / 100.0

        # Energy Forward (2 register, scale 0.01)
        result = await client.read_holding_registers(
            0x0014, count=2, device_id=device_id
        )
        if result.isError():
            print(f"Error reading EM619001 {device_id} energy_forward: {result}")
        else:
            raw = (result.registers[0] << 16) | result.registers[1]
            data["energy_forward"] = raw / 100.0

        # Energy Reverse (2 register, scale 0.01)
        result = await client.read_holding_registers(
            0x001E, count=2, device_id=device_id
        )
        if result.isError():
            print(f"Error reading EM619001 {device_id} energy_reverse: {result}")
        else:
            raw = (result.registers[0] << 16) | result.registers[1]
            data["energy_reverse"] = raw / 100.0

        # Alarm Status (1 register, bitmask)
        result = await client.read_holding_registers(
            0x0073, count=1, device_id=device_id
        )
        if result.isError():
            print(f"Error reading EM619001 {device_id} alarm: {result}")
        else:
            data["alarm_status"] = result.registers[0]

    except Exception as e:
        print(f"Error reading EM619001 {device_id}: {e}")

    finally:
        client.close()

    return data
