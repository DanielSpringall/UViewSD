# Copyright 2021 by Daniel Springall.
# This file is part of UViewSD, and is released under the "MIT License Agreement".
# Please see the LICENSE file that should have been included as part of this package.
from uviewsd.gl import camera as gl_camera
from uviewsd.tests import common as ut_common


class CameraTestCase(ut_common.CommonTestCast):
    def setUp(self):
        self.initialWidth = 100
        self.initialHeight = 100
        self.camera = gl_camera.Camera2D(self.initialWidth, self.initialHeight)

    def _assertFocusRegion(self, expectedRegion):
        self._assertListsAlmostEqual(self.camera.getFocusRegion(), expectedRegion)

    def _assertListsAlmostEqual(self, actual, expected):
        for value, expectedValue in zip(actual, expected):
            self.assertAlmostEqual(value, expectedValue)

    def test_camerasetup(self):
        self.assertEqual(self.camera._screenWidth, self.initialWidth)
        self.assertEqual(self.camera._screenHeight, self.initialHeight)
        self.assertEqual(
            self.camera._screenAspectRatio, self.initialWidth / self.initialHeight
        )
        bufferScale = self.camera._defaultBufferScale
        self._assertFocusRegion(
            (0.0 - bufferScale, 1.0 + bufferScale, 1.0 + bufferScale, 0.0 - bufferScale)
        )

    def test_cameraresize(self):
        # Focus with no buffer to make testing focus region easier.
        self.camera.focus(0.0, 1.0, 1.0, 0.0, bufferScale=0.0)
        self._assertFocusRegion((0.0, 1.0, 1.0, 0.0))

        # Resizing should maintain width. And scale the height around the vertical mid point.
        self.camera.resize(200.0, 100.0)
        self._assertFocusRegion((0.0, 1.0, 0.75, 0.25))
        self.camera.resize(100.0, 100.0)
        self._assertFocusRegion((0.0, 1.0, 1.0, 0.0))
        self.camera.resize(100.0, 200.0)
        self._assertFocusRegion((0.0, 1.0, 1.5, -0.5))

    def test_camerapan(self):
        # Focus with no buffer to make testing focus region easier.
        self.camera.focus(0.0, 1.0, 1.0, 0.0, bufferScale=0.0)
        self._assertFocusRegion((0.0, 1.0, 1.0, 0.0))

        self.camera.pan(1.0, 1.0)
        self._assertFocusRegion((1.0, 2.0, 2.0, 1.0))

        self.camera.pan(-3.0, -2.0)
        self._assertFocusRegion((-2.0, -1.0, 0.0, -1.0))

    def test_camerazoom(self):
        # Focus with no buffer to make testing focus region easier.
        self.camera.focus(0.0, 1.0, 1.0, 0.0, bufferScale=0.0)
        self._assertFocusRegion((0.0, 1.0, 1.0, 0.0))

        self.camera.zoom((0.5, 0.5), 0.5)
        self._assertFocusRegion((-0.5, 1.5, 1.5, -0.5))
        self.camera.zoom((0.5, 0.5), 2.0)
        self._assertFocusRegion((0.0, 1.0, 1.0, 0.0))

        self.camera.zoom((1.0, 1.0), 0.5)
        self._assertFocusRegion((-1.0, 1.0, 1.0, -1.0))
        self.camera.zoom((1.0, 1.0), 2.0)
        self._assertFocusRegion((0.0, 1.0, 1.0, 0.0))

    def test_cameramapping(self):
        # Focus with no buffer to make testing focus region easier.
        self.camera.focus(0.0, 1.0, 1.0, 0.0, bufferScale=0.0)
        self._assertFocusRegion((0.0, 1.0, 1.0, 0.0))

        self._assertListsAlmostEqual(
            (50.0, 50.0),
            self.camera.mapWorldToScreen((0.5, 0.5)),
        )
        self._assertListsAlmostEqual(
            (0.75, 0.75),
            self.camera.mapGlToWorld((0.5, 0.5)),
        )
        self._assertListsAlmostEqual(
            (1.0, 0.0),
            self.camera.mapScreenToWorld((100.0, 100.0)),
        )
        self._assertListsAlmostEqual(
            (0.5, -0.5),
            self.camera.mapScreenToGl((75.0, 75.0)),
        )
        self._assertListsAlmostEqual(
            (25.0, 25.0),
            self.camera.mapGlToScreen((-0.5, 0.5)),
        )


if __name__ == "__main__":
    import unittest

    unittest.main()
