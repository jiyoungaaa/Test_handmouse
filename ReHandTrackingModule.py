"""
Hand Tracing Module
By: Murtaza Hassan
Youtube: http://www.youtube.com/c/MurtazasWorkshopRoboticsandAI
Website: https://www.murtazahassan.com/
"""

import cv2
import mediapipe as mp
import time
import math
import numpy as np


class handDetector():
    def __init__(self, mode=False, maxHands=2, modelC = 1, detectionCon=0.8, trackCon=0.8):
        self.mode = mode
        self.maxHands = maxHands
        self.modelC = modelC
        self.detectionCon = detectionCon
        self.trackCon = trackCon

        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(self.mode, self.maxHands, self.modelC,
                                        self.detectionCon, self.trackCon)
        self.mpDraw = mp.solutions.drawing_utils
        self.tipIds = [4, 8, 12, 16, 20]

    def findHands(self, img, draw=True):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)
        # print(results.multi_hand_landmarks)

        if self.results.multi_hand_landmarks:
            for handLms in self.results.multi_hand_landmarks:
                if draw:
                    self.mpDraw.draw_landmarks(img, handLms,
                                               self.mpHands.HAND_CONNECTIONS)

        return img

    def findPosition(self, img, handNo=0, draw=True):
        xList =[]
        yList = []
        bbox = []
        self.lmList = []
        if self.results.multi_hand_landmarks:
            myHand = self.results.multi_hand_landmarks[handNo]
            for id, lm in enumerate(myHand.landmark):
                # print(id, lm)
                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                xList.append(cx)
                yList.append(cy)
                # print(id, cx, cy)
                self.lmList.append([id, cx, cy])
                if draw:
                    cv2.circle(img, (cx, cy), 5, (255, 0, 255), cv2.FILLED)

            xmin, xmax = min(xList), max(xList)
            ymin, ymax = min(yList), max(yList)
            bbox = xmin, ymin, xmax, ymax

            if draw:
                cv2.rectangle(img, (xmin - 20, ymin - 20), (xmax + 20, ymax + 20),
                              (0, 255, 0), 2)

        return self.lmList, bbox

    def fingersUp(self):  # 벡터을 통한 손가라 구부림 관계
        fingers = []
        zero_dot = [self.lmList[0][1], self.lmList[0][2]]

        cor_degree = self.sol_degree(zero_dot[0], zero_dot[1], self.lmList[17][1], self.lmList[17][2])
        # Thumb
        try:
            Thumb_1 = [self.lmList[self.tipIds[0]][1], self.lmList[self.tipIds[0]][2]]
            Thumb_2 = [self.lmList[self.tipIds[0] - 1][1], self.lmList[self.tipIds[0] - 1][2]]
            Thumb_f1 = self.retouchHands((math.pi/2)-cor_degree, zero_dot[0], zero_dot[1], Thumb_1[0], Thumb_1[1])
            Thumb_f2 = self.retouchHands((math.pi/2)-cor_degree, zero_dot[0], zero_dot[1], Thumb_2[0], Thumb_2[1])
            if abs(Thumb_f1[0]) > abs(Thumb_f2[0]):
                fingers.append(1)
            else:
                fingers.append(0)
        except: fingers.append(0)

        # Fingers
        for id in range(1, 5):
            try:
                Fingers_1 = [self.lmList[self.tipIds[id]][1], self.lmList[self.tipIds[id]][2]]
                Fingers_2 = [self.lmList[self.tipIds[id] - 2][1], self.lmList[self.tipIds[id] - 2][2]]
                vec_t1 = ((Fingers_1[0] - zero_dot[0]) ** 2 + (Fingers_1[1] - zero_dot[1]) ** 2) ** 0.5
                vec_t2 = ((Fingers_2[0] - zero_dot[0]) ** 2 + (Fingers_2[1] - zero_dot[1]) ** 2) ** 0.5
                if vec_t1 > vec_t2:
                    fingers.append(1)
                else:
                    fingers.append(0)
            except: fingers.append(0)

        # totalFingers = fingers.count(1)

        return fingers

    def findDistance(self, p1, p2, img, draw=True,r=15, t=3):
        x1, y1 = self.lmList[p1][1:]
        x2, y2 = self.lmList[p2][1:]
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

        if draw:
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), t)
            cv2.circle(img, (x1, y1), r, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (x2, y2), r, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (cx, cy), r, (0, 0, 255), cv2.FILLED)
        length = math.hypot(x2 - x1, y2 - y1)

        return length, img, [x1, y1, x2, y2, cx, cy]

    def retouchHands(self, co_degree, zx, zy, fx, fy):
        f_degree = self.sol_degree(zx, zy, fx, fy)
        R = ((fx - zx)**2 + (fy - zy)**2)**0.5
        co_x = math.cos(f_degree + co_degree) * R
        co_y = math.sin(f_degree + co_degree) * R
        return [co_x, co_y]

    def sol_degree(self, zx, zy, fx, fy):
        try:
            re = math.atan((fy - zy) / (fx - zx))
        except:
            if fy > zy: re = math.pi / 2
            else: re = (math.pi * 2) * 3 / 4
        return re

def main():
    pTime = 0
    cTime = 0
    cap = cv2.VideoCapture(1)
    detector = handDetector()
    while True:
        success, img = cap.read()
        img = detector.findHands(img)
        lmList, bbox = detector.findPosition(img)
        if len(lmList) != 0:
            print(lmList[4])

        cTime = time.time()
        fps = 1 / (cTime - pTime)
        pTime = cTime

        cv2.putText(img, str(int(fps)), (10, 70), cv2.FONT_HERSHEY_PLAIN, 3,
                    (255, 0, 255), 3)

        cv2.imshow("Image", img)
        cv2.waitKey(1)


if __name__ == "__main__":
    main()