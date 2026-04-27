import asyncio

import cv2

from frame_sdk import Frame
from frame_sdk.camera import Quality, AutofocusType

async def main():

    async with Frame() as f:

        while True:

            await f.display.show_text("Hello Camera")

            await f.camera.save_photo("frame-test.jpg", autofocus_seconds=1,
                                      quality=Quality.VERY_HIGH,
                                      resolution=720,
                                      autofocus_type=AutofocusType.CENTER_WEIGHTED)
            image = cv2.imread("frame-test.jpg")
            cv2.imshow("Frame Test", image)

            cv2.waitKey(1000)

            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            blur = cv2.GaussianBlur(image,(3,3),0)
            ret, image = cv2.threshold(blur,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
            cv2.imshow("Frame Test", image)

            cv2.waitKey(1000)


if __name__ == "__main__":
    asyncio.run(main())
