import argparse
import cv2
import time

from datetime import datetime


CAMERA_URL = 'rtsp://10.0.2.51:8080/video/h264'


class BirbWatcher:
    def __init__(self, url, storage_path):
        self.camera_url = url
        self.camera = cv2.VideoCapture(self.camera_url)
        self.storage_path = storage_path
        self.writer = None

    def init_writer(self, path):
        frame_width = self.camera.get(cv2.cv2.CAP_PROP_FRAME_WIDTH)
        frame_height = self.camera.get(cv2.cv2.CAP_PROP_FRAME_HEIGHT)
        frame_size = int(frame_width), int(frame_height)
        fourcc = cv2.VideoWriter_fourcc(*'X264')
        self.writer = cv2.VideoWriter(path, fourcc, 20.0, frame_size)

    def create_new_file(self):
        path = self.storage_path + datetime.now().strftime('%Y-%m-%d-%H-%M-%S') + '.avi'
        self.init_writer(path)

    @staticmethod
    def embed_timestamp(frame):
            frame_time = datetime.now().strftime('%Y/%m/%d %H:%M:%S:%f')[:-4]
            timestamp_pos = (10, 35)
            timestamp_font = cv2.FONT_HERSHEY_COMPLEX
            timestamp_size = 1
            timestamp_color = (0, 255, 0)

            cv2.putText(frame,
                        frame_time,
                        timestamp_pos, 
                        timestamp_font, 
                        timestamp_size, 
                        timestamp_color, 
                        2, cv2.LINE_AA)

            return frame
        
    def run(self):
        self.create_new_file()
        while self.camera.isOpened():
            ret, frame = self.camera.read()

            if ret == False:
                print('Ret was false!')

            frame = self.embed_timestamp(frame)
            self.writer.write(frame)
            cv2.imshow('frame',frame)

            if int(time.time()) % 1800 == 0:
                self.writer.release()
                self.create_new_file()
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.cleanup()
    
    def cleanup(self):
        self.camera.release()
        self.writer.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Birb Watcher')

    parser.add_argument('camera-url', type=str, required=True,
                        help='URL pointing to your IP Camera')
    parser.add_argument('storage-path', type=str, required=False, default='', 
                        help='Path of your video storage directory')

    args = parser.parse_args()

    bw = BirbWatcher(args.camera_url, args.storage_path)
    bw.run()
