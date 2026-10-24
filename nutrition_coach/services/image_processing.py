from __future__ import annotations

import base64
from dataclasses import dataclass
from io import BytesIO

from PIL import Image, UnidentifiedImageError

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}


class ImageValidationError(ValueError):
    pass


@dataclass(frozen=True)
class ProcessedImage:
    base64_data: str
    media_type: str


def validate_and_encode_image(
    raw: bytes, declared_type: str, max_bytes: int
) -> ProcessedImage:
    if not raw:
        raise ImageValidationError("The uploaded image is empty.")
    if len(raw) > max_bytes:
        raise ImageValidationError(
            "The image is larger than the configured upload limit."
        )
    if declared_type not in ALLOWED_IMAGE_TYPES:
        raise ImageValidationError("Use a JPEG, PNG, or WebP image.")
    try:
        with Image.open(BytesIO(raw)) as image:
            image.verify()
    except (UnidentifiedImageError, OSError, SyntaxError) as error:
        raise ImageValidationError(
            "The uploaded file is not a readable image."
        ) from error
    return ProcessedImage(base64.b64encode(raw).decode("ascii"), declared_type)
