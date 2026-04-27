import asyncio

import cv2
from picamera2 import Picamera2

from rich.live import Live
from rich.table import Table
from rich.text import Text

from argus.drugs import drugs
from argus.process import process_and_display


def gen_table(data, tapped=0):
    tab = Table()
    tab.add_column("")
    tab.add_column("Drug")
    tab.add_column("Count")

    # tab.add_row("Tapped", str(tapped))
    for k, v in data.items():
        try:
            drug = [i for i in drugs if k == i['code']][0]
            tab.add_row(
                    Text("\u2587" * 10, style=drug['colour']),
                    drug['name'],
                    str(v))
        except:
            pass
    return tab


async def main():
    last_found = None
    data = {}
    tapped = 0
    cv2.namedWindow("OpenCV", cv2.WINDOW_NORMAL)

    camera = Picamera2()
    camera.start()

    with Live(gen_table(data), transient=True, auto_refresh=True, refresh_per_second=4) as live:
        while True:
            image = camera.capture_array()
            codes = process_and_display(image)
            for code in codes:
                if code != last_found:
                    live.console.print(
                        f"Found new code: {code}. Last found: {last_found}"
                    )
                    if code not in data.keys():
                        data[code] = 1
                    else:
                        data[code] += 1
                    last_found = code

            live.update(gen_table(data, tapped=tapped))
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    asyncio.run(main())
