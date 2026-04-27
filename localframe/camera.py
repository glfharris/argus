from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from exif import Image

if TYPE_CHECKING:
    from .frame import Frame

from enum import Enum


class Quality(Enum):
    LOW = 10
    MEDIUM = 25
    HIGH = 50
    FULL = 100


class AutofocusType(Enum):
    SPOT = "SPOT"
    AVERAGE = "AVERAGE"
    CENTER_WEIGHTED = "CENTER_WEIGHTED"


class Camera:
    """Helpers for working with the Frame camera."""

    frame: "Frame" = None

    _auto_process_photo = True

    def __init__(self, frame: "Frame"):
        """Initialize the Camera with a Frame instance."""
        self.frame = frame
        self.is_awake = True

    @property
    def auto_process_photo(self) -> bool:
        """If true, the camera will automatically process the photo to correct rotation and add metadata."""
        return self._auto_process_photo

    @auto_process_photo.setter
    def auto_process_photo(self, value: bool):
        """If true, the camera will automatically process the photo to correct rotation and add metadata."""
        self._auto_process_photo = value

    async def take_photo(
        self,
        autofocus_seconds: Optional[int] = 3,
        quality: Quality = Quality.MEDIUM,
        autofocus_type: AutofocusType = AutofocusType.AVERAGE,
        exposure: Optional[float] = 0.18,
        exposure_speed: Optional[float] = 0.5,
        shutter_limit: Optional[int] = 16000,
        analog_gain_limit: Optional[int] = 248,
        white_balance_speed: Optional[float] = 0.5,
    ) -> bytes:
        """Take a photo with the camera.

        Args:
            autofocus_seconds (Optional[int]): If provided, the camera will attempt to focus for the specified number of seconds.  Defaults to 3.  If `None`, the camera will not attempt to focus at all.
            quality (Quality): The quality of the photo. Defaults to Quality.MEDIUM.
            autofocus_type (AutofocusType): The type of autofocus. Defaults to AutofocusType.AVERAGE.

        Returns:
            bytes: The photo as a byte array.

        Raises:
            Exception: If the photo capture fails.
        """

        if not self.is_awake:
            await self.frame.run_lua("frame.camera.wake()", checked=True)
            self.is_awake = True

        if type(quality) == int:
            quality = Quality(quality)
        if type(autofocus_type) == int:
            autofocus_type = AutofocusType(autofocus_type)

        await self.frame.bluetooth.send_lua(
            f"cameraCaptureAndSend({quality.value},{autofocus_seconds or 'nil'},'{autofocus_type.value}',{exposure},{exposure_speed},{shutter_limit},{analog_gain_limit},{white_balance_speed})"
        )
        image_buffer = await self.frame.bluetooth.wait_for_data()

        if image_buffer is None or len(image_buffer) == 0:
            raise Exception("Failed to get photo")

        while image_buffer[0] == 0x04 and len(image_buffer) < 5:
            print("Ignoring tap data while waiting for photo")
            image_buffer = await self.frame.bluetooth.wait_for_data()

            if image_buffer is None or len(image_buffer) == 0:
                raise Exception("Failed to get photo")

        if self.auto_process_photo:
            image_buffer = self.process_photo(image_buffer, autofocus_type)
        return image_buffer

    async def save_photo(
        self,
        filename: str,
        autofocus_seconds: Optional[int] = 3,
        quality: Quality = Quality.MEDIUM,
        autofocus_type: AutofocusType = AutofocusType.AVERAGE,
        exposure: Optional[float] = 0.18,
        exposure_speed: Optional[float] = 0.5,
        shutter_limit: Optional[int] = 16000,
        analog_gain_limit: Optional[int] = 248,
        white_balance_speed: Optional[float] = 0.5,
    ):
        """Save a photo to a file.

        Args:
            filename (str): The name of the file to save the photo.  The file will always be saved as a jpeg image regardless of the file extension.
            autofocus_seconds (Optional[int]): If provided, the camera will attempt to focus for the specified number of seconds.  Defaults to 3.  If `None`, the camera will not attempt to focus at all.
            quality (Quality): The quality of the photo. Defaults to Quality.MEDIUM.
            autofocus_type (AutofocusType): The type of autofocus. Defaults to AutofocusType.AVERAGE.
        """
        image_buffer = await self.take_photo(
            autofocus_seconds,
            quality,
            autofocus_type,
            exposure=exposure,
            exposure_speed=exposure_speed,
            shutter_limit=shutter_limit,
            analog_gain_limit=analog_gain_limit,
            white_balance_speed=white_balance_speed,
        )

        with open(filename, "wb") as f:
            f.write(image_buffer)

    def process_photo(
        self, image_buffer: bytes, autofocus_type: AutofocusType
    ) -> bytes:
        """Process a photo to correct rotation and add metadata.

        Args:
            image_buffer (bytes): The photo as a byte array.
            autofocus_type (AutofocusType): The type of autofocus that was used to capture the photo.

        Returns:
            bytes: The processed photo as a byte array.
        """
        image = Image(image_buffer)
        image.orientation = 8
        image.make = "Brilliant Labs"
        image.model = "Frame"
        image.software = "Frame Python SDK"
        if autofocus_type == AutofocusType.AVERAGE:
            image.metering_mode = 1
        elif autofocus_type == AutofocusType.CENTER_WEIGHTED:
            image.metering_mode = 2
        elif autofocus_type == AutofocusType.SPOT:
            image.metering_mode = 3
        image.datetime_original = datetime.now().strftime("%Y:%m:%d %H:%M:%S")
        return image.get_file()
