import cv2
import time
import logging
import threading
import queue
from collections import defaultdict
from backend.phase1 import config
from backend.ml.inference.classifier import OptimizedWasteClassifier
from backend.hardware.serial.iiot_communicator import IIoTCommunicator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

class ThreadSafeStateMachine:
    """
    Thread-safe State Machine matching robotic_hand.ino protocol:
    - WAITING       : Empty ROI target box. Vision model active.
    - THINKING      : 2.5s observation & multi-frame consensus gathering.
    - DECIDED       : Single letter latched and sent ONCE to robotic arm.
    - ARM_OPERATING : Mechanical arm is picking/throwing trash. Vision model PAUSED!
                      Blocks all new commands until Arduino sends "Done" acknowledgement.
    """
    STATE_WAITING = "WAITING FOR ITEM"
    STATE_THINKING = "ANALYZING ITEM..."
    STATE_DECIDED = "DECIDED & LATCHED"
    STATE_ARM_OPERATING = "ARM OPERATING (MODEL PAUSED)"

    def __init__(self, iiot):
        self.iiot = iiot
        self.lock = threading.Lock()

        self.state = self.STATE_WAITING
        self.thinking_start_time = None
        self.accumulated_scores = defaultdict(float)
        self.sample_count = 0

        self.latched_category = None
        self.latched_letter = None
        self.latched_display_name = None
        self.latched_confidence = 0.0

    def handle_arduino_done(self):
        """Called when Arduino emits 'Done' signal over Serial."""
        with self.lock:
            logging.info("[STATE MACHINE] Robotic arm finished task. Resuming vision model guessing.")
            self._reset_nolock()

    def reload_reset(self):
        """Manual Reload/Reset button trigger to clear any locks and return to start phase."""
        with self.lock:
            logging.info("[MANUAL RELOAD] System manually reset to start phase.")
            self._reset_nolock()

    def update_analysis(self, analysis):
        with self.lock:
            current_time = time.time()

            if self.state == self.STATE_ARM_OPERATING:
                return

            is_valid = analysis["is_valid"] if analysis else False
            best_cat = analysis["best_category"] if analysis else None

            if self.state == self.STATE_WAITING:
                if is_valid and best_cat:
                    self.state = self.STATE_THINKING
                    self.thinking_start_time = current_time
                    self.accumulated_scores.clear()
                    self.sample_count = 0
                    logging.info("Item detected in ROI target. Entering THINKING phase (2.5s)...")

            elif self.state == self.STATE_THINKING:
                if is_valid and analysis:
                    probs = analysis["probabilities"]
                    for cat_key, prob in probs.items():
                        self.accumulated_scores[cat_key] += prob
                    self.sample_count += 1

                elapsed = current_time - self.thinking_start_time

                if elapsed >= config.THINKING_DURATION:
                    if self.sample_count > 0 and self.accumulated_scores:
                        final_cat = max(self.accumulated_scores, key=self.accumulated_scores.get)
                        avg_prob = self.accumulated_scores[final_cat] / self.sample_count
                        
                        cat_info = config.CATEGORIES[final_cat]
                        self.latched_category = final_cat
                        self.latched_display_name = cat_info["display_name"]
                        self.latched_letter = cat_info["letter"]
                        self.latched_confidence = avg_prob

                        self.state = self.STATE_ARM_OPERATING
                        logging.info(f"DECISION LOCKED -> Transmitting Code [{self.latched_letter}] ({self.latched_display_name}) to Arduino.")
                        self.iiot.send_code(self.latched_letter)
                    else:
                        self.state = self.STATE_WAITING

    def get_snapshot(self):
        with self.lock:
            current_time = time.time()
            progress = 1.0
            if self.state == self.STATE_THINKING and self.thinking_start_time:
                progress = min(1.0, (current_time - self.thinking_start_time) / config.THINKING_DURATION)

            return {
                "state": self.state,
                "progress": progress,
                "letter": self.latched_letter,
                "display_name": self.latched_display_name,
                "category": self.latched_category,
                "confidence": self.latched_confidence
            }

    def _reset_nolock(self):
        self.state = self.STATE_WAITING
        self.thinking_start_time = None
        self.accumulated_scores.clear()
        self.sample_count = 0
        self.latched_category = None
        self.latched_letter = None
        self.latched_display_name = None
        self.latched_confidence = 0.0

def ai_worker_thread(classifier, state_machine, frame_queue, stop_event):
    while not stop_event.is_set():
        try:
            roi_crop = frame_queue.get(timeout=0.05)
            if roi_crop is not None:
                snapshot = state_machine.get_snapshot()
                if snapshot["state"] != ThreadSafeStateMachine.STATE_ARM_OPERATING:
                    analysis = classifier.analyze_frame(roi_crop)
                    state_machine.update_analysis(analysis)
            frame_queue.task_done()
        except queue.Empty:
            continue
        except Exception as e:
            logging.error(f"Error in AI worker thread: {e}")

def draw_hud(frame, snapshot, iiot, fps):
    h, w, _ = frame.shape
    roi_size = min(w, h) // 2
    rx1 = (w - roi_size) // 2
    ry1 = (h - roi_size) // 2
    rx2 = rx1 + roi_size
    ry2 = ry1 + roi_size

    state = snapshot["state"]
    letter = snapshot["letter"]
    display_name = snapshot["display_name"]
    confidence = snapshot["confidence"]
    progress = snapshot["progress"]

    if state == ThreadSafeStateMachine.STATE_ARM_OPERATING or state == ThreadSafeStateMachine.STATE_DECIDED:
        box_color = config.CATEGORIES[snapshot["category"]]["color"] if snapshot["category"] else (0, 165, 255)
    elif state == ThreadSafeStateMachine.STATE_THINKING:
        box_color = (0, 200, 255)
    else:
        box_color = (120, 120, 120)

    cv2.rectangle(frame, (rx1, ry1), (rx2, ry2), box_color, 2)
    cv2.putText(frame, "TARGET ZONE", (rx1, ry1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.55, box_color, 1, cv2.LINE_AA)

    cv2.rectangle(frame, (0, 0), (w, 55), (15, 15, 15), -1)
    cv2.putText(frame, "PHASE 1 VISION WASTE SORTER", (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)

    hw_text = f"FPS: {fps:.1f} | Serial: {iiot.port} (19200 Baud)" if not iiot.mock else f"FPS: {fps:.1f} | Serial: MOCK MODE"
    cv2.putText(frame, hw_text, (w - 360, 35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 180), 1, cv2.LINE_AA)

    return frame

def main():
    state_machine = None

    def on_done():
        if state_machine:
            state_machine.handle_arduino_done()

    iiot = IIoTCommunicator(port=config.SERIAL_PORT, baud_rate=config.BAUD_RATE, 
                            mock=config.MOCK_SERIAL, on_done_callback=on_done)
    state_machine = ThreadSafeStateMachine(iiot)

    logging.info("Initializing Vision Engine...")
    classifier = OptimizedWasteClassifier()

    frame_queue = queue.Queue(maxsize=1)
    stop_event = threading.Event()

    worker_thread = threading.Thread(target=ai_worker_thread, args=(classifier, state_machine, frame_queue, stop_event), daemon=True)
    worker_thread.start()

    cap = cv2.VideoCapture(config.DEFAULT_CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)

    if not cap.isOpened():
        logging.error(f"Cannot open camera index {config.DEFAULT_CAMERA_INDEX}.")
        stop_event.set()
        return

    print("\n=======================================================")
    print("  PHASE 1 ROBOTIC ARM TRASH SORTER")
    print("=======================================================\n")

    prev_time = time.time()
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            curr_time = time.time()
            fps = 1.0 / (curr_time - prev_time + 1e-6)
            prev_time = curr_time

            h, w, _ = frame.shape
            roi_size = min(w, h) // 2
            rx1 = (w - roi_size) // 2
            ry1 = (h - roi_size) // 2
            roi_crop = frame[ry1:ry1+roi_size, rx1:rx1+roi_size].copy()

            if frame_queue.full():
                try:
                    frame_queue.get_nowait()
                except queue.Empty:
                    pass
            frame_queue.put_nowait(roi_crop)

            snapshot = state_machine.get_snapshot()
            display_frame = draw_hud(frame, snapshot, iiot, fps)
            cv2.imshow("Phase 1 Vision Waste Sorter", display_frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                break
            elif key == ord('r') or key == ord('R'):
                state_machine.reload_reset()

    finally:
        stop_event.set()
        cap.release()
        cv2.destroyAllWindows()
        iiot.close()
        logging.info("Phase 1 shutdown cleanly.")

if __name__ == "__main__":
    main()
