import os
from datetime import datetime, date
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Date
from sqlalchemy.orm import declarative_base, sessionmaker

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "waste_sorter.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Detection(Base):
    __tablename__ = "detections"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    category = Column(String, index=True)
    display_name = Column(String)
    confidence = Column(Float)
    letter_code = Column(String)
    status = Column(String, default="PROCESSED")

class SystemLog(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    level = Column(String, default="INFO")
    source = Column(String, default="SYSTEM")
    message = Column(String)

class UserAction(Base):
    __tablename__ = "actions"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    action_type = Column(String)
    payload = Column(String, nullable=True)
    triggered_by = Column(String, default="USER")

class SystemStatus(Base):
    __tablename__ = "system_status"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    arduino_connected = Column(Boolean, default=True)
    camera_active = Column(Boolean, default=True)
    model_running = Column(Boolean, default=True)
    motors_ready = Column(Boolean, default=True)
    db_connected = Column(Boolean, default=True)

def init_db():
    Base.metadata.create_all(bind=engine)

# Ensure tables exist immediately upon module load
init_db()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Database Helper Functions
def log_detection(category: str, display_name: str, confidence: float, letter_code: str, status: str = "PROCESSED"):
    db = SessionLocal()
    try:
        detection = Detection(
            timestamp=datetime.utcnow(),
            category=category,
            display_name=display_name,
            confidence=confidence,
            letter_code=letter_code,
            status=status
        )
        db.add(detection)
        db.commit()
        db.refresh(detection)
        return detection
    except Exception as e:
        db.rollback()
        return None
    finally:
        db.close()

def log_system_event(level: str, source: str, message: str):
    db = SessionLocal()
    try:
        entry = SystemLog(
            timestamp=datetime.utcnow(),
            level=level,
            source=source,
            message=message
        )
        db.add(entry)
        db.commit()
        return entry
    except Exception as e:
        db.rollback()
        return None
    finally:
        db.close()

def log_action(action_type: str, payload: str = None, triggered_by: str = "USER"):
    db = SessionLocal()
    try:
        act = UserAction(
            timestamp=datetime.utcnow(),
            action_type=action_type,
            payload=payload,
            triggered_by=triggered_by
        )
        db.add(act)
        db.commit()
        return act
    except Exception as e:
        db.rollback()
        return None
    finally:
        db.close()

def get_today_statistics():
    db = SessionLocal()
    try:
        today_start = datetime.combine(date.today(), datetime.min.time())
        all_items = db.query(Detection).filter(Detection.timestamp >= today_start).all()
        
        counts = {
            "plastic": 0,
            "paper": 0,
            "cardboard": 0,
            "glass": 0,
            "metal": 0
        }
        total = 0
        
        # Standard hourly tracking slots for dashboard (08:00 - 17:00)
        current_hour = datetime.now().hour
        start_hour = max(0, min(8, current_hour - 4))
        end_hour = max(17, current_hour + 2)
        hourly_map = {f"{h:02d}": 0 for h in range(start_hour, min(24, end_hour + 1))}
        
        for item in all_items:
            cat = item.category.lower() if item.category else "plastic"
            if cat in counts:
                counts[cat] += 1
            total += 1
            
            if item.timestamp:
                hr_str = f"{item.timestamp.hour:02d}"
                if hr_str in hourly_map:
                    hourly_map[hr_str] += 1
                else:
                    hourly_map[hr_str] = hourly_map.get(hr_str, 0) + 1
                    
        # Sort hours chronologically
        sorted_hours = sorted(hourly_map.keys())
        hourly_list = [{"hour": f"{hr}:00", "items": hourly_map[hr]} for hr in sorted_hours]
        
        return {
            "today": date.today().isoformat(),
            "counts": counts,
            "total": total,
            "hourly": hourly_list
        }
    finally:
        db.close()
