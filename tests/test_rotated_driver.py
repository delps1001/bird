from PIL import Image

from bird_listener.display.rotated_driver import RotatedDisplayDriver


class _Capture:
    def show(self, image):
        self.image = image


def test_rotates_portrait_to_panel_native():
    inner = _Capture()
    RotatedDisplayDriver(inner, 90).show(Image.new("RGB", (480, 800)))
    assert inner.image.size == (800, 480)


def test_rotation_direction_counter_clockwise():
    img = Image.new("RGB", (4, 2), (255, 255, 255))
    img.putpixel((0, 0), (255, 0, 0))  # top-left
    inner = _Capture()
    RotatedDisplayDriver(inner, 90).show(img)
    assert inner.image.getpixel((0, 3)) == (255, 0, 0)  # CCW: top-left -> bottom-left
