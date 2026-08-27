import logging
from backend.hardware.drivers.base_driver import BaseArmDriver
from backend.hardware.drivers.arduino_driver import ArduinoArmDriver
from backend.hardware.drivers.mock_driver import MockArmDriver

def get_hardware_driver(mode: str = "mock", port: str = "COM3", baud_rate: int = 19200) -> BaseArmDriver:
    """
    Factory function instantiating the requested hardware driver based on mode.
    Mode: 'real' | 'mock'
    """
    mode_lower = mode.lower()
    if mode_lower in ["real", "hardware", "pyserial"]:
        logging.info(f"Initializing REAL PySerial Hardware Driver on {port} @ {baud_rate} Baud.")
        driver = ArduinoArmDriver(port=port, baud_rate=baud_rate)
        if not driver.connect():
            logging.warning("Physical hardware connection failed. Falling back to Mock Simulation Driver.")
            driver = MockArmDriver()
            driver.connect()
        return driver
    else:
        logging.info("Initializing MOCK Simulation Driver.")
        driver = MockArmDriver()
        driver.connect()
        return driver
