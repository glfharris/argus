import cv2
import numpy as np
from pyzbar import pyzbar
from pathlib import Path

from .vendor.pylibdmtx import pylibdmtx

class Image:
    def __init__(self, path=None, image=None, window_name="Argus"):
        if path and image:
            raise ValueError("Found both `path` and `image`")
        elif path is None and image is None:
            raise ValueError("`path` and `image` cannot both be None")

        if path:
            self.raw_image = cv2.imread(str(path))
        elif image.any():
            self.raw_image = image

        self.window_name = window_name
        self.barcodes = []
        self.datamatrices = []
        self.versions = {}

    def show(self, kind="raw", hold=False):
        if kind == "raw":
            image = self.raw_image
        if kind == "gray":
            if "gray" in self.versions.keys():
                image = self.versions["gray"]
            else:
                image = cv2.cvtColor(self.raw_image, cv2.COLOR_BGR2GRAY)
                self.versions["gray"] = image
        if kind == "marked":
            image = self.versions['marked']

        self._setup_cv_window()
        cv2.imshow(self.window_name, image)
        cv2.waitKey(1)

        if hold:
            cv2.waitKey(0)

    @classmethod
    def close(cls):
        cv2.destroyAllWindows()

    def _setup_cv_window(self):
        cv2.namedWindow("Argus", cv2.WINDOW_NORMAL)

    def decode(self, kind="barcode", mark=True, thickness=5):
        if kind == "barcode":
            self.barcodes = pyzbar.decode(self.raw_image)
        if kind == "dmtx":
            self.barcodes = pylibdmtx.decode(self.raw_image)

        if mark:
            marked = self.raw_image.copy()
            polygons = []
            for bc in self.barcodes:
                pts = np.array(bc.polygon, dtype=np.int32).reshape((-1,1,2))
                polygons.append(pts)

            for poly in polygons:
                marked = cv2.polylines(marked, [poly], True, (0,255,0), thickness)

            self.versions['marked'] = marked

        return [ bc.data.decode("UTF-8") for bc in self.barcodes ]
