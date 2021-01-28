import cv2
import numpy as np
import os
import time

from datetime import datetime
from dotenv import load_dotenv

from birb_alert import BirbAlert


class BirbWatcher:
    def __init__(self, url, storage_path, alert=None):
        self.alert = alert
        self.camera_url = url
        self.camera = cv2.VideoCapture(self.camera_url)
        self.writer = None
        self.last_alert = None  # Time of last sent discord alert.
        self.prev_frames = []  # Previous 30 frames with applied grayscale and smoothing for motion detection.
        self.storage_path = storage_path

    def init_writer(self, path):
        frame_width = self.camera.get(cv2.cv2.CAP_PROP_FRAME_WIDTH)
        frame_height = self.camera.get(cv2.cv2.CAP_PROP_FRAME_HEIGHT)
        frame_size = int(frame_width), int(frame_height)
        fourcc = cv2.VideoWriter_fourcc(*'X264')
        self.writer = cv2.VideoWriter(path, fourcc, 20.0, frame_size)

    def create_new_file(self):
        path = self.storage_path + datetime.now().strftime('%Y-%m-%d-%H-%M-%S') + '.avi'
        self.init_writer(path)

    def cleanup(self):
        self.camera.release()
        self.writer.release()
        cv2.destroyAllWindows()

    def handle_previous_frames(self, current_frame):
        self.prev_frames.append(current_frame)
        if len(self.prev_frames) > 10:
            self.prev_frames.pop(0)
        return cv2.absdiff(self.prev_frames[0], current_frame)

    def detect_motion(self, frame):
        grayscale = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        smoothed = cv2.GaussianBlur(grayscale, (15, 15), 0)
        diff = self.handle_previous_frames(smoothed)
        thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        vis = np.concatenate((grayscale, thresh), axis=0)
        cv2.imshow('vis', vis)
        return len(contours) > 0
        
    def run(self):
        self.create_new_file()
        while self.camera.isOpened():
            ret, frame = self.camera.read()
            if not ret:
                print('Ret was false. Did stream end? Exiting loop now...')
                break

            frametime = time.time()
            frame_timestamp = datetime.now().strftime('%Y/%m/%d %H:%M:%S.%f')[:-4]

            if self.detect_motion(frame):
                if alert and self.last_alert is None or frametime - self.last_alert > 180:
                    self.last_alert = frametime
                    msg = 'Motion detected at ' + frame_timestamp + ' Is it a birb?'
                    self.alert.send_message(msg)
                    print(msg)

            frame = self.embed_timestamp(frame, frame_timestamp)
            self.writer.write(frame)

            if int(frametime) % 1800 == 0:
                self.writer.release()
                self.create_new_file()

            key = cv2.waitKey(1) & 0xFF
            # if the `q` key is pressed, break from the lop
            if key == ord("q"):
                break
        self.cleanup()

    @staticmethod
    def embed_timestamp(frame, frame_time):
        timestamp_pos = (10, 35)
        timestamp_font = cv2.FONT_HERSHEY_COMPLEX
        timestamp_size = 1
        timestamp_color = (0, 255, 0)

        cv2.putText(frame, frame_time, timestamp_pos, timestamp_font, timestamp_size, timestamp_color, 2, cv2.LINE_AA)
        return frame


if __name__ == '__main__':
    load_dotenv()
    CAMERA_URL = os.getenv("CAMERA_URL")
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")
    STORAGE_PATH = os.getenv("STORAGE_PATH")

    alert = BirbAlert(WEBHOOK_URL)
    bw = BirbWatcher(CAMERA_URL, STORAGE_PATH, alert)
    bw.run()
