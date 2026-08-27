import time
import logging
import threading

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

class IIoTCommunicator:
    """
    Communicates with the robotic arm (robotic_hand.ino) over Serial (19200 baud).
    Transmits single-letter codes:
      'P' -> Plastic Waste
      'A' -> Paper Waste
      'C' -> Cardboard Waste
      'G' -> Glass Waste
      'M' -> Metal Waste
      
    Listens for 'Done' acknowledgement from Arduino when operation completes.
    """
    def __init__(self, port="COM3", baud_rate=19200, mock=True, on_done_callback=None):
        self.port = port
        self.baud_rate = baud_rate
        self.mock = mock
        self.on_done_callback = on_done_callback
        
        self.connection = None
        self.reader_thread = None
        self.stop_reader = threading.Event()
        
        if not self.mock and SERIAL_AVAILABLE:
            self.connect()
        else:
            logging.info("IIoT Communicator initialized in MOCK MODE (No physical hardware needed).")

    @staticmethod
    def list_available_ports():
        if not SERIAL_AVAILABLE:
            return []
        ports = serial.tools.list_ports.comports()
        return [p.device for p in ports]

    def connect(self):
        if not SERIAL_AVAILABLE:
            logging.warning("PySerial not installed. Falling back to Mock Mode.")
            self.mock = True
            return False

        try:
            self.connection = serial.Serial(self.port, self.baud_rate, timeout=1)
            time.sleep(2.0)
            logging.info(f"Connected to Robotic Arm on port {self.port} at {self.baud_rate} baud.")
            self.mock = False
            
            self.stop_reader.clear()
            self.reader_thread = threading.Thread(target=self._read_serial_loop, daemon=True)
            self.reader_thread.start()
            return True
        except Exception as e:
            logging.warning(f"Failed to connect to Serial Port {self.port}: {e}. Operating in MOCK MODE.")
            self.mock = True
            return False

    def _read_serial_loop(self):
        while not self.stop_reader.is_set() and self.connection and self.connection.is_open:
            try:
                line = self.connection.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    logging.info(f"[ARDUINO RESPONSE] -> {line}")
                    if "Done" in line or "Robotic Arm Ready" in line:
                        logging.info("[ACKNOWLEDGEMENT RECEIVED] Robotic arm finished action & returned Home.")
                        if self.on_done_callback:
                            self.on_done_callback()
            except Exception as e:
                logging.error(f"Error reading serial line: {e}")
                time.sleep(0.5)

    def send_code(self, letter: str) -> bool:
        valid_codes = ["P", "A", "C", "G", "M", "H", "E"]
        if not letter or letter.upper() not in valid_codes:
            logging.warning(f"Invalid code '{letter}'. Valid codes: {valid_codes}")
            return False

        letter_char = letter.upper()

        if self.mock or not self.connection or not self.connection.is_open:
            logging.info(f"[IIoT MOCK TRANSMISSION] -> Robotic Arm Command: Single Letter '{letter_char}'")
            threading.Thread(target=self._simulate_mock_done, daemon=True).start()
            return True

        try:
            payload = letter_char.encode('utf-8')
            self.connection.write(payload)
            self.connection.flush()
            logging.info(f"[IIoT HARDWARE TRANSMISSION] Sent '{letter_char}' to Robotic Arm over {self.port}.")
            return True
        except Exception as e:
            logging.error(f"Failed to transmit code '{letter_char}': {e}")
            return False

    def _simulate_mock_done(self):
        time.sleep(3.0)
        logging.info("[MOCK ACKNOWLEDGEMENT] Simulated Robotic Arm 'Done' signal received.")
        if self.on_done_callback:
            self.on_done_callback()

    def close(self):
        self.stop_reader.set()
        if self.connection and self.connection.is_open:
            self.connection.close()
            logging.info("Serial Connection closed.")
