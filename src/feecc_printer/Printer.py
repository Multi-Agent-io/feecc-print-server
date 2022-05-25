import io
import os
import re
import textwrap
import typing as tp
from statistics import mean
from string import ascii_letters
from subprocess import check_output

from PIL import Image, ImageDraw, ImageFont
from PIL.ImageFont import FreeTypeFont
from brother_ql import BrotherQLRaster, conversion
from brother_ql.backends.helpers import send
from loguru import logger
from typed_getenv import getenv

PAPER_WIDTH: str = getenv("PAPER_WIDTH", var_type=str)
PRINTER_MODEL: str = getenv("PRINTER_MODEL", var_type=str)
RED: bool = getenv("RED", var_type=bool)

assert PAPER_WIDTH, "Missing PAPER_WIDTH environment variable"
assert PRINTER_MODEL, "Missing PRINTER_MODEL environment variable"


class Printer:
    """a printing task for the label printer. executed at init"""

    def __init__(self) -> None:
        self._paper_width: str = PAPER_WIDTH
        self._model: str = PRINTER_MODEL

    @property
    def _address(self) -> tp.Optional[str]:
        """Get printer USB bus address"""
        try:
            command: str = f'lsusb | grep "{self._model}"'
            output: str = check_output(command, shell=True, text=True)
            addresses: tp.List[str] = re.findall("[0-9a-fA-F]{4}:[0-9a-fA-F]{4}", output)
            address: tp.List[str] = addresses[0].split(":")
            bus_address: str = f"usb://0x{address[0]}:0x{address[1]}"
            return bus_address

        except Exception as e:
            logger.warning("Could not get the printer USB bus address. The printer may be disconnected.")
            logger.debug(f"An error occurred while parsing USB address: {e}")
            return None

    def print_image(self, image_data: tp.Union[str, bytes], annotation: tp.Optional[str] = None) -> None:
        """execute the task"""
        if not self._address:
            message = "Printer disconnected. Task dropped."
            logger.info(message)
            raise BrokenPipeError(message)

        logger.info("Printing task created for image")

        image: Image = self._get_image(image_data)

        if annotation:
            image = self._annotate_image(image, annotation)

        self._print_image(image)
        logger.info("Printing task done")

    def _get_image(self, image_data: tp.Union[str, bytes]) -> Image:
        """prepare and resize the image before printing"""
        if isinstance(image_data, str):
            image: Image = Image.open(image_data)
        else:
            image = Image.open(io.BytesIO(image_data))

        w, h = image.size
        target_w = 696 if self._paper_width == "62" else 554
        target_h = int(h * (target_w / w))
        image = image.resize((target_w, target_h))
        return image

    def _print_image(self, image: Image) -> None:
        """print provided image"""
        logger.info(f"Printing image of size {image.size}")
        qlr: BrotherQLRaster = BrotherQLRaster(self._model)
        conversion.convert(qlr, [image], self._paper_width, red=RED)

        # need to provide multiple fallbacks as the QL library us pretty unstable
        # while printer keeps getting different addresses so we need to try them all
        directory = "/dev/usb"
        usb_devices = (f"{directory}/{desc}" for desc in os.listdir(directory) if desc.startswith("lp"))
        backends = [("linux_kernel", dev) for dev in usb_devices]
        backends.insert(0, ("pyusb", str(self._address)))
        success = False

        for backend, address in backends:
            try:
                status = send(
                    instructions=qlr.data,
                    backend_identifier=backend,
                    printer_identifier=address,
                )
                logger.debug(f"Printing succeeded using {backend=}, {address=}.")
                logger.debug(f"Job status: {status}")
                success = True
                break

            except Exception as e:
                logger.warning(f"Execution of 'brother_ql.backends.helpers.send()' failed. {backend=}, {address=}. {e}")

        if not success:
            raise BrokenPipeError("Printing failed. No backend was able to to handle the task.")

    @staticmethod
    def _annotate_image(image: Image, text: str) -> Image:
        """add an annotation to the bottom of the image"""
        # wrap the message
        font_path = "feecc_printer/fonts/helvetica-cyrillic-bold.ttf"
        assert os.path.exists(font_path), f"Cannot open font at {font_path=}. No such file."
        font: FreeTypeFont = ImageFont.truetype(font_path, 24)
        avg_char_width: float = mean((font.getsize(char)[0] for char in ascii_letters))
        img_w, img_h = image.size
        max_chars_in_line: int = int(img_w * 0.95 / avg_char_width)
        wrapped_text: str = textwrap.fill(text, max_chars_in_line)

        # get message size
        sample_draw: ImageDraw.Draw = ImageDraw.Draw(image)
        _, txt_h = sample_draw.textsize(wrapped_text, font)
        # https://stackoverflow.com/questions/59008322/pillow-imagedraw-text-coordinates-to-center/59008967#59008967
        txt_h += font.getoffset(text)[1]

        # draw the message
        annotated_image: Image = Image.new(mode="RGB", size=(img_w, img_h + txt_h + 5), color=(255, 255, 255))
        annotated_image.paste(image, (0, 0))
        new_img_w, new_img_h = annotated_image.size
        txt_draw: ImageDraw.Draw = ImageDraw.Draw(annotated_image)
        text_pos: tp.Tuple[int, int] = (
            int(new_img_w / 2),
            int((new_img_h - img_h) / 2 + img_h),
        )
        txt_draw.text(
            text_pos,
            wrapped_text,
            font=font,
            fill=(0, 0, 0),
            anchor="mm",
            align="center",
        )

        return annotated_image
