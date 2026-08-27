from abc import ABC, abstractmethod
from typing import Callable, Dict, Any, Optional

class BaseArmDriver(ABC):
    """
    Abstract Hardware Driver Interface for Robotic Arm Manipulator.
    Isolates physical PySerial communication from business logic & API services.
    """
    
    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to arm controller hardware/simulator."""
        pass

    @abstractmethod
    def disconnect(self):
        """Cleanly close connection."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Return boolean hardware connection status."""
        pass

    @abstractmethod
    def get_hardware_status(self) -> Dict[str, Any]:
        """Return dynamic diagnostic hardware status dict."""
        pass

    @abstractmethod
    def send_command(self, code: str) -> bool:
        """
        Send single-letter control command code:
        'P' -> Plastic, 'A' -> Paper, 'C' -> Cardboard, 'G' -> Glass, 'M' -> Metal,
        'H' -> Home Position, 'E' -> Emergency Stop
        """
        pass

    @abstractmethod
    def get_servo_angles(self) -> Dict[str, float]:
        """Return current 6-DOF joint angles dictionary."""
        pass

    @abstractmethod
    def register_done_callback(self, callback: Callable[[], None]):
        """Register callback function invoked when arm completes physical movement."""
        pass
