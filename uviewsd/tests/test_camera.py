# Copyright 2021 by Daniel Springall.
# This file is part of UViewSD, and is released under the "MIT License Agreement".
# Please see the LICENSE file that should have been included as part of this package.
from uviewsd import camera

import unittest


class CameraTestCase(unittest.TestCase):
    def setup(self):
        self.initialWidth = 100
        self.initialHeight = 100
        self._camera = camera(self.initialWidth, self.initialHeight)

    def test_camerasetup(self):
        pass

    def test_cameraresize(self):
        pass

    def test_cameramapping(self):
        pass

    def test_camerapan(self):
        pass

    def test_camerazoom(self):
        pass

    def test_camerafocusregion(self):
        pass
