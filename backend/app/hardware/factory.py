import logging
from backend.app.hardware.base_driver import BaseArmDriver
from backend.app.hardware.arduino_driver import ArduinoArmDriver
from backend.app.hardware.mock_driver import MockArmDriver

def get_hardware_driver(mode: str = "real", port: str = "COM3", baud_rate: int = 19200) -> BaseArmDriver:
    """
    Factory function instantiating the requested hardware driver.
    Uses ArduinoArmDriver with dynamic USB port auto-detection by default.
    """
    mode_lower = mode.lower()
    if mode_lower in ["mock", "simulation", "virtual"]:
        logging.info("Initializing MOCK Simulation Driver.")
        driver = MockArmDriver()
        driver.connect()
        return driver
    else:
        logging.info(f"Initializing Dynamic PySerial Hardware Driver (Port: {port} @ {baud_rate} Baud)...")
        driver = ArduinoArmDriver(port=port, baud_rate=baud_rate)
        driver.connect()
        return driver
