import cv2
import os

from .image import Image

class Camera:
    def __init__(self, device=0):
        self.device = device
        self.cap = cv2.VideoCapture(device)

        if device == 2:
            self.setup_brio()

    def setup_brio(self):
        os.system("v4l2-ctl -d 2 -c focus_automatic_continuous=0")
        os.system("v4l2-ctl -d 2 -c focus_absolute=70")
        os.system("v4l2-ctl -d 2 -c zoom_absolute=300")


    def capture(self):
        ret, image = self.cap.read()
        return Image(image=image)

class PiCamera:
    def __init__(self):
        self.picamera = Picamera2()

        config = self.picamera.create_preview_configuration({"size": (1920,1080)})
        self.picamera.configure(config)
        self.picamera.start()


    def capture(self):
        return Image(image=self.picamera.capture_array())




if __name__ == "__main__":
    cam = Camera()
    image = cam.capture()
    image.show(hold=True)
