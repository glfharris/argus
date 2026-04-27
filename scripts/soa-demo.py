import asyncio

from frame_sdk import Frame
from frame_sdk.display import Alignment, PaletteColors

from PIL import ImageColor

import datetime

from argus.drugs import drugs

async def main():
    async with Frame() as f:
        while True:

            await f.display.write_text("Hello SOA25!", align=Alignment.MIDDLE_CENTER)
            await f.display.show()

            await asyncio.sleep(2)

            for drug in drugs:
                bat = await f.get_battery_level()
                await f.display.write_text(f"Bat: {bat}%", align=Alignment.TOP_RIGHT)
                await f.display.write_text(datetime.datetime.now().strftime("%-I:%M %p"), align=Alignment.TOP_LEFT)

                await f.display.write_text("Joe Bloggs\nDOB:01-01-1970\nMRN:123456",
                                        align=Alignment.MIDDLE_CENTER)
                await f.display.write_text("HR: 65bpm",align=Alignment.BOTTOM_LEFT,color=PaletteColors.GREEN)
                await f.display.write_text("BP: 120-80",align=Alignment.BOTTOM_CENTER,color=PaletteColors.RED)
                await f.display.write_text("SpO2: 98%",align=Alignment.BOTTOM_RIGHT,color=PaletteColors.YELLOW)
                await f.display.show()

                await asyncio.sleep(2)

                message = f"{drug['name']}\n{drug['dose']} {drug['units']}"
                r,g,b = ImageColor.getrgb(drug['colour'])
                await f.run_lua(f"frame.display.assign_color('GREY',{r},{g},{b})")
                await f.display.write_text(message,align=Alignment.MIDDLE_CENTER)
                await f.display.draw_rect(1,300,640,100,1)
                await f.display.show()
                await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(main())
