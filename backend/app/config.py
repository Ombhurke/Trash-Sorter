import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Veg QX — Robotic Arm Sorter IoT"
    API_PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Hardware Settings
    HARDWARE_MODE: str = "real"  # "real" or "mock"
    SERIAL_PORT: str = "COM10"
    BAUD_RATE: int = 19200

    # Vision & Camera Settings
    DEFAULT_CAMERA_INDEX: int = 0
    FRAME_WIDTH: int = 1280
    FRAME_HEIGHT: int = 720

    # AI & Decision Parameters
    THINKING_DURATION: float = 5.0
    CONFIDENCE_THRESHOLD: float = 0.45

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
