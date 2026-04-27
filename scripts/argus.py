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
        self.current_stats: Optional[ImageStats] = None
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

    def create_image_panel(self) -> Panel:
        """Create panel with image information"""
        if not self.current_stats:
            return Panel("No image loaded", title="Image Information")

        table = Table(show_header=False, padding=(0, 2))
        stats = self.current_stats
        table.add_row("Path", str(stats.path))
        table.add_row("Size", f"{stats.size[0]}x{stats.size[1]}")
        table.add_row("Channels", str(stats.channels))
        table.add_row("File Size", f"{stats.file_size / 1024:.1f} KB")
        table.add_row("Timestamp", stats.timestamp.strftime("%H:%M:%S.%f")[:-3])

        return Panel(table, title="Image Information")

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
                str(v["total"]) + " " + v["units"],
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
class ArgusImage:
    image: any
    captured: Optional[datetime] = None
    processed: Optional[datetime] = None
    path: Optional[Path] = None


@dataclass
class ImageStats:
    """Store image statistics"""

    path: Optional[Path]
    size: Tuple[int, int]
    channels: int
    mean_values: Tuple[float, ...]
    file_size: Optional[int]
    timestamp: datetime

    @classmethod
    def from_image(cls, img: ArgusImage):
        if img.path:
            path = img.path
            size = img.path.stat().st_size
        else:
            path = None
            size = None
        return cls(
            path=path,
            size=img.image.shape[:2],
            channels=img.image.shape[2] if len(img.image.shape) > 2 else 1,
            mean_values=tuple(np.mean(img.image, axis=(0, 1)).round(2)),
            file_size=path.stat().st_size,
            timestamp=img.captured,
        )


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
    def __init__(
        self, image_folder: str = "img/", window_size: Tuple[int, int] = (400, 400)
    ):
        self.image_queue: asyncio.Queue = asyncio.Queue()
        self.image_folder = Path(image_folder)
        self.window_size = window_size
        self.running = True
        self.frame = None
        self._active_image: Optional[ArgusImage] = None
        self.active_drug = None
        self.tap_state = TapState()
        self.display = RichDisplay()
        self.live_display: Optional[Live] = None
        self.logger = logging.getLogger(__name__)

        # Validate image folder exists
        if not self.image_folder.exists():
            raise ValueError(f"Image folder {image_folder} does not exist")

    @property
    def active_image(self) -> Optional[ArgusImage]:
        return self._active_image

    @active_image.setter
    def active_image(self, value: ArgusImage):
        self._active_image = value
        self.logger.info("New active image")

    async def capture_images(self):
        """Loops through images in a directory adding them to the image queue."""
        images = list(self.image_folder.glob("*.jpg"))

        if not images:
            raise RuntimeError(f"No jpg images found in {self.image_folder}")

        image_cycle = cycle(images)

        self.logger.info("Entering image capture")

        # try:
        cv2.namedWindow("Image", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Image", *self.window_size)

        while self.running:
            stamp = datetime.now()
            path = next(image_cycle)

            image = cv2.imread(str(path))

            if image is None:
                self.logger.error(f"Failed to load image: {path}")
                continue

            cv2.imshow("Image", image)

            img = ArgusImage(image=image, captured=stamp, path=path)
            await self.image_queue.put(img)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                self.end()
                break

            await asyncio.sleep(4)

    async def process_images(self):
        while self.running:
            img = await self.image_queue.get()
            self.display.current_stats = ImageStats.from_image(img)
            self.active_image = img

            barcodes = pyzbar.decode(img.image)
            for code in barcodes:
                code = code.data.decode("UTF-8")
                self.logger.info(f"Found barcode: {code}")
                try:
                    drug = [i for i in drugs if code == i["code"]][0]
                    self.logger.info(f"Found drug: {drug['name']}")
                    self.active_drug = drug
                    self.display.active_drug = drug
                    r,g,b = ImageColor.getrgb(drug['colour'])
                    await self.frame.run_lua(f"frame.display.assign_color('GREY', {r}, {g}, {b})",
                                             checked=True)
                    await self.frame.display.write_text(f"{drug['name']}\n{drug['dose']} {drug['units']}",
                                                        align=Alignment.MIDDLE_CENTER)
                    await self.frame.display.draw_rect(1,300,640,100,1)
                    await self.frame.display.show()
                except Exception as e:
                    raise e

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

    async def frame_display(self):
        while self.running:
            if self.active_image:
                await self.frame.display.show_text(str(self.active_image.path))
            await asyncio.sleep(1)

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
                try:
                    tasks = [
                        self.capture_images(),
                        self.process_images(),
                        # self.frame_display(),
                    ]
                    await asyncio.gather(*tasks)
                except asyncio.CancelledError:
                    self.logger.info("Tasks cancelled")
                except Exception as e:
                    self.logger.error(f"Error in main loop: {e}")
                    raise e
                finally:
                    self.end()

    def end(self):
        """Clean shutdown of the application."""
        self.running = False
        cv2.destroyAllWindows()


if __name__ == "__main__":
    try:
        argus = Argus(image_folder="img/barcodes")
        asyncio.run(argus.main())
    except KeyboardInterrupt:
        logging.info("Application terminated by user")
        argus.end()
    except Exception as e:
        logging.error(f"Application error: {e}")
        raise e
