import unittest

from nutrition_coach.services.image_processing import (
    ImageValidationError,
    validate_and_encode_image,
)


class ImageProcessingTests(unittest.TestCase):
    def test_rejects_an_invalid_image(self):
        with self.assertRaises(ImageValidationError):
            validate_and_encode_image(b"not an image", "image/png", 1024)

    def test_rejects_unsupported_type(self):
        with self.assertRaises(ImageValidationError):
            validate_and_encode_image(b"hello", "application/pdf", 1024)
