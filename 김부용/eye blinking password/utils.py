import cv2
from queue import Queue
from threading import Thread
import numpy as np
from imutils import face_utils
import dlib
import pygame as pg
import time
from settings import *

IMG_SIZE = (34, 26)

def blinking_time_clac(isClose):
    start = time.time()
    end = time.time()

def crop_eye(img, eye_points):
  x1, y1 = np.amin(eye_points, axis=0)
  x2, y2 = np.amax(eye_points, axis=0)
  cx, cy = (x1 + x2) / 2, (y1 + y2) / 2

  w = (x2 - x1) * 1.2
  h = w * IMG_SIZE[1] / IMG_SIZE[0]

  margin_x, margin_y = w / 2, h / 2

  min_x, min_y = int(cx - margin_x), int(cy - margin_y)
  max_x, max_y = int(cx + margin_x), int(cy + margin_y)

  eye_rect = np.rint([min_x, min_y, max_x, max_y]).astype(np.int)

  eye_img = img[eye_rect[1]:eye_rect[3], eye_rect[0]:eye_rect[2]]

  return eye_img, eye_rect

class VideoStream:
    def __init__(self, game, device=0, size=10, model = None):
        if model == None:
            print('error: Model not found!')
            exit()
        else:
            self.model = model
            self.model._make_predict_function() # 초기화
        
        self.game = game
        self.stream = cv2.VideoCapture(device)
        self.stream.set(cv2.CAP_PROP_FPS, 10)
        self.stopped = False
        self.queue = Queue(maxsize=size)

        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor("data/shape_predictor_68_face_landmarks.dat")

        self.blink_record = list() # 눈 깜빡임 시간 기록 [open/close, time]
        self.eye_state = True  # 눈을 뜨고 시작한다고 가정
        self.start_open_time = time.time()  # 눈을 뜨기 시작한 시간
        self.end_close_time = time.time()

        self.open_idx = 0
        self.close_idx = 0

        self.font = cv2.FONT_HERSHEY_PLAIN

    def start(self):
        thread = Thread(target=self.update, args=())
        thread.daemon = True
        thread.start()
        return self

    def update(self):
        
        while self.stopped == False:
            ret, img = self.stream.read()

            if not ret:
                self.stop()
                return

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            faces = self.detector(gray)

            for face in faces:
                try:
                    landmarks = self.predictor(gray, face)
                    landmarks = face_utils.shape_to_np(landmarks)

                    eye_img_l, eye_rect_l = crop_eye(gray, eye_points=landmarks[36:42]) # 왼쪽눈을 가리키는 포인트
                    eye_img_r, eye_rect_r = crop_eye(gray, eye_points=landmarks[42:48]) # 오른눈을 가리키는 포인트

                    eye_img_l = cv2.resize(eye_img_l, dsize=IMG_SIZE)
                    eye_img_r = cv2.resize(eye_img_r, dsize=IMG_SIZE)
                    eye_img_r = cv2.flip(eye_img_r, flipCode=1)

                    eye_input_l = eye_img_l.copy().reshape((1, IMG_SIZE[1], IMG_SIZE[0], 1)).astype(np.float32) / 255.
                    eye_input_r = eye_img_r.copy().reshape((1, IMG_SIZE[1], IMG_SIZE[0], 1)).astype(np.float32) / 255.

                    pred_l = self.model.predict(eye_input_l)
                    pred_r = self.model.predict(eye_input_r)

                    # visualize
                    if pred_l + pred_r > 0.2:
                        self.eye_state = True
                        text = 'OPEN'
                    else:
                        if self.eye_state == True:
                            self.eye_state = False
                            self.game.blink_sound.play()
                            pg.event.post(self.game.blink_event)
                            text = 'CLOSE'
                    cv2.putText(img, text, tuple(landmarks[18]), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0))
                except:
                    pass

            self.queue.put(img)

    def read(self):
        return self.queue.get()

    def check_queue(self):
        return self.queue.qsize() > 0

    def stop(self):
        self.stopped = True
        self.stream.release()
        cv2.destroyAllWindows()
