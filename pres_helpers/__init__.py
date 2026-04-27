import threading
import cv2
import time

from pathlib import Path
from rich.console import Console
from itertools import cycle

from pyzbar.pyzbar import decode
import numpy as np

console = Console(color_system="truecolor", log_path=False, width=50)
print = console.log

def change_image(path, before, after):
    path = Path(path)
    new = path.read_text().replace(f"\n![]({before})",f"\n![]({after})")
    path.write_text(new)
    return True

def show_image(image):
    if isinstance(image, str):
        image = cv2.imread(image)
    cv2.imshow("OpenCV", image)
    cv2.waitKey(1)
    return image

def show_images(images, pause=1):

    if isinstance(images, list):
        image_cycle = cycle(images)
        while True:
            cv2.imshow("OpenCV", next(image_cycle))
            time.sleep(pause)

            if cv2.waitKey(1) & 0xFF == ord('c'):
                cv2.destroyAllWindows()
                break

def window():
    cv2.namedWindow("OpenCV", cv2.WINDOW_NORMAL)

def hold_open():
    while True:
        if cv2.waitKey(1) & 0xFF == ord('c'):
            cv2.destroyAllWindows()
            break

def pg_to_pl(polygon):
    pts = np.array(polygon, dtype=np.int32).reshape((-1,1,2))
    return pts

def get_pts(barcode):
    poly = barcode.polygon
    return pg_to_pl(poly)

def mark_image(image):
    codes = []
    for barcode in decode(image):
        codes.append(barcode.data.decode("UTF-8"))
        pts = get_pts(barcode)
        image = cv2.polylines(image, [pts],True,(0,255,0),5)
    return image, codes


def carrier(func):
    global running
    running = True

    def input_thread():
        global running
        input()
        running = False
        cv2.destroyAllWindows()
    
    threading.Thread(target=input_thread, 
                     args=(),
                     name="input_thread", 
                     daemon=True).start()

    while running:
        func()


