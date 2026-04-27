import asyncio
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from itertools import cycle
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np
from pyzbar import pyzbar
from rich.align import Align
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Column, Table
from rich.text import Text

from localframe import Frame
from localframe.display import Alignment
from argus.drugs import drugs

from PIL import ImageColor

from argus import Image, Camera


class CustomLogHandler(logging.Handler):
    """Custom logging handler that stores messages for the Rich display"""

    def __init__(self, message_store: list):
        super().__init__()
        self.message_store = message_store

    def emit(self, record):
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            msg = self.format(record)
            self.message_store.append(f"[{timestamp}] {msg}")
        except Exception:
            self.handleError(record)


class RichDisplay:
    def __init__(self):
        self.layout = Layout()
        self.layout.split_row(
            Layout(name="left", ratio=1), Layout(name="logs", ratio=1)
        )
        self.layout["left"].split_column(
            Layout(name="image_info", ratio=2), Layout(name="drug_info", ratio=1)
        )
        self.log_messages: list = []
        self.active_drug: Optional[any] = None
        self.admins: dict = {}

        # Set up logging to integrate with Rich display
        self.setup_logging()

    def setup_logging(self):
        """Configure logging to store messages in our display"""
        # Remove any existing handlers
        logging.getLogger().handlers.clear()

        # Create and configure our custom handler
        handler = CustomLogHandler(self.log_messages)
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)

        # Set up root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(handler)

    def create_administrations_panel(self) -> Panel:
        table = Table(
            Column(header="Label", min_width=10),
            Column(header="Drug"),
            Column(header="Total"),
            Column(header="Last Given", min_width=8),
            expand=True,
        )

        for k, v in self.admins.items():
            table.add_row(
                Text("\u2587" * 10, style=v["colour"]),
                k,
                f"{v['total']:.1f} {v['units']}",
                v["last"].strftime("%H:%M:%S"),
            )

        return Panel(table, title="Administrations")

    def create_log_panel(self) -> Panel:
        """Create panel with log messages"""
        # Keep only the last 10 messages
        recent_logs = self.log_messages[-20:] if self.log_messages else ["No logs yet"]
        log_text = Text("\n".join(recent_logs))
        return Panel(log_text, title="Logs")

    def create_drug_panel(self) -> Panel:
        if not self.active_drug:
            return Panel("No Drug", title="Drug")
        drug = self.active_drug
        text = Text(
                f"{drug['name']}\n{drug['dose']} {drug['units']}\n", justify="center"
        )
        text.append("\u2588" * len(drug["name"]), style=drug["colour"])
        return Panel(Align.center(text, vertical="middle"), title="Drug")

    def update_display(self) -> Layout:
        """Update the layout with current information"""
        self.layout["logs"].update(self.create_log_panel())
        self.layout["image_info"].update(self.create_administrations_panel())
        self.layout["drug_info"].update(self.create_drug_panel())
        return self.layout

@dataclass
class TapState:
    """Encapsulate tap-related state and logic"""

    last_tap: Optional[datetime] = None
    MIN_TAP_INTERVAL = timedelta(seconds=0.1)
    MAX_TAP_INTERVAL = timedelta(seconds=1)

    def is_double_tap(self, current_time: datetime) -> bool:
        if not self.last_tap:
            return False
        interval = current_time - self.last_tap
        return self.MIN_TAP_INTERVAL < interval < self.MAX_TAP_INTERVAL


class Argus:
    def __init__(self):
        self.running = True
        self.frame = None
        self.active_drug = None
        self.tap_state = TapState()
        self.display = RichDisplay()
        self.live_display: Optional[Live] = None
        self.logger = logging.getLogger(__name__)

    async def set_active_drug(self, drug):
        self.active_drug = drug
        self.display.active_drug = drug

        r,g,b = ImageColor.getrgb(drug['colour'])
        await self.frame.run_lua(f"frame.display.assign_color('GREY', {r}, {g}, {b})",
                                 checked=True)

        message = f"{drug['name']}\n{drug['dose']} {drug['units']}"

        await self.frame.display.write_text(message,align=Alignment.MIDDLE_CENTER)
        await self.frame.display.draw_rect(1,300,640,100,1)
        await self.frame.display.show()

    async def capture_and_process(self):

        camera = Camera(device=2)

        while self.running:
            img = camera.capture()
            img.show()
            codes = img.decode()
            if codes:
                img.show(kind='marked')
                for code in codes:
                    try:
                        drug = [i for i in drugs if code == i['code']][0]
                        if drug != self.active_drug:
                            await self.set_active_drug(drug)
                    except:
                        pass
            await asyncio.sleep(0.1)


    def tap_callback(self, data):
        """Registers taps and detects double taps."""
        current_time = datetime.now()
        if self.tap_state.is_double_tap(current_time):
            self.tap_state.last_tap = None
            self.interact()
        else:
            self.tap_state.last_tap = current_time

    def interact(self):
        """Handle double-tap interaction."""
        self.logger.info("Double tapped!")
        if self.active_drug:
            self.logger.info(f"Administered: {self.active_drug['name']}")
        if self.active_drug:
            try:
                if self.active_drug["name"] not in self.display.admins.keys():
                    self.display.admins[self.active_drug["name"]] = {
                        "total": 0,
                        "last": datetime.now(),
                        "colour": self.active_drug["colour"],
                        "units": self.active_drug["units"],
                    }
                self.display.admins[self.active_drug["name"]]["total"] += (
                    self.active_drug["dose"]
                )
                self.display.admins[self.active_drug["name"]]["last"] = datetime.now()
            except Exception as e:
                raise e

    async def update_display_task(self):
        """Continuously update the rich live display"""
        while self.running:
            if self.live_display:
                self.live_display.update(self.display.update_display())
            await asyncio.sleep(0.1)

    @asynccontextmanager
    async def setup_frame(self):
        """Context manager for frame setup and cleanup."""
        try:
            self.logger.info("Connecting to Frame...")
            async with Frame() as frame:
                self.logger.info("Frame connected.")
                self.frame = frame
                await self.frame.motion.run_on_tap(callback=self.tap_callback)
                yield
        finally:
            self.logger.info("Frame disconnected.")
            self.frame = None

    async def main(self):
        """Main application loop."""
        with Live(
            self.display.update_display(),
            transient=True,
            refresh_per_second=10,
            auto_refresh=True,
            vertical_overflow="visible",
        ) as live:
            self.live_display = live

            # Start display task so that logs get printed
            asyncio.create_task(self.update_display_task())

            self.logger.info("Starting Argus...")
            async with self.setup_frame():
                await self.frame.display.show_text("Hello Argus", align=Alignment.MIDDLE_CENTER)
                try:
                    tasks = [
                            self.capture_and_process(),
                    ]
                    await asyncio.gather(*tasks)
                except asyncio.CancelledError:
                    self.logger.info("Tasks cancelled")
                except Exception as e:
                    self.logger.error(f"Error in main loop: {e}")
                    raise e
                finally:
                    await self.frame.display.show_text("Goodbye Argus", align=Alignment.MIDDLE_CENTER)
                    self.end()
                

    def end(self):
        """Clean shutdown of the application."""
        self.running = False
        cv2.destroyAllWindows()


if __name__ == "__main__":
    try:
        argus = Argus()
        asyncio.run(argus.main())
    except KeyboardInterrupt:
        logging.info("Application terminated by user")
        argus.end()
    except Exception as e:
        logging.error(f"Application error: {e}")
        raise e
