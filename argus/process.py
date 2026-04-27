import cv2
import numpy as np
from pyzbar import pyzbar


def process_and_display(image, display=True):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    barcodes = pyzbar.decode(gray)

    codes = []
    for barcode in barcodes:
        code = barcode.data.decode("UTF-8")
        pts = barcode.polygon
        pts = np.array(pts, dtype=np.int32)
        pts = pts.reshape((-1, 1, 2))
        cv2.polylines(gray, [pts], True, (0, 255, 0), 10)
        codes.append(code)

    if display:
        cv2.imshow("OpenCV", gray)

    return codes


if __name__ == "__main__":
    from pathlib import Path

    cv2.namedWindow("OpenCV", cv2.WINDOW_NORMAL)

    # for img in Path("/home/glfharris/src/argus/img/barcodes/").glob("*.jpg"):
    #     image = cv2.imread(str(img))
    #     process_and_display(image)
    #     import time

    # time.sleep(1)
    cap = cv2.VideoCapture(2)

    while True:
        ret, image = cap.read()
        process_and_display(image)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
