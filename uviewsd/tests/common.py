# Copyright 2021 by Daniel Springall.
# This file is part of UViewSD, and is released under the "MIT License Agreement".
# Please see the LICENSE file that should have been included as part of this package.
from pxr import Usd

import unittest
import os


class CommonTestCast(unittest.TestCase):
    defaultPrimPath = "/cube"
    usdDataDir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")
    textureDir = os.path.join(usdDataDir, "textures")

    def getTestUsdFilePath(cls, fileName):
        return os.path.abspath(
            os.path.join(cls.usdDataDir, "{}.usda".format(fileName))
        ).lower()

    def getTestTextureFilePath(cls, fileName):
        return os.path.abspath(
            os.path.join(cls.textureDir, "{}.png".format(fileName))
        ).lower()

    def loadStage(self, fileName):
        """Load a specific stage from the usd test data."""
        self._stage = Usd.Stage.Open(self.getTestUsdFilePath(fileName))

    def prim(self, primPath=None):
        """Get a prim from the currently loaded stage."""
        self.assertIsNotNone(self._stage, "No stage loaded to extract prim from.")
        primPath = primPath if primPath else self.defaultPrimPath
        prim = self._stage.GetPrimAtPath(primPath)
        self.assertTrue(prim.IsValid(), "Invalid prim path {}.".format(primPath))
        return prim

    def getExpectedUVResults(self, uvType):
        self.assertIn(
            uvType,
            list(expectedDataMap.keys()),
            "Missing expected data results for uv type: {}.".format(uvType),
        )
        return expectedDataMap[uvType]


faceVaryingDataResults = {
    "positions": [
        (0.375, 0),
        (0.625, 0),
        (0.375, 0.25),
        (0.625, 0.25),
        (0.375, 0.5),
        (0.625, 0.5),
        (0.375, 0.75),
        (0.625, 0.75),
        (0.375, 1),
        (0.625, 1),
        (0.875, 0),
        (0.875, 0.25),
        (0.125, 0),
        (0.125, 0.25),
    ],
    "indices": [
        (0, 1),
        (1, 3),
        (2, 3),
        (0, 2),
        (3, 5),
        (4, 5),
        (2, 4),
        (5, 7),
        (6, 7),
        (4, 6),
        (7, 9),
        (8, 9),
        (6, 8),
        (1, 10),
        (10, 11),
        (3, 11),
        (0, 12),
        (2, 13),
        (12, 13),
    ],
    "borderIndices": [
        (0, 1),
        (3, 5),
        (2, 4),
        (5, 7),
        (4, 6),
        (7, 9),
        (8, 9),
        (6, 8),
        (1, 10),
        (10, 11),
        (3, 11),
        (0, 12),
        (2, 13),
        (12, 13),
    ],
}

vertexVaryingDataResults = {
    "positions": [
        (0, 0),
        (1, 0),
        (0.16813788, 0.16813788),
        (0.8318621, 0.16813788),
        (0.16813788, 0.8318621),
        (0.8318621, 0.8318621),
        (0, 1),
        (1, 1),
    ],
    "indices": [
        (0, 1),
        (1, 3),
        (2, 3),
        (0, 2),
        (3, 5),
        (4, 5),
        (2, 4),
        (5, 7),
        (6, 7),
        (4, 6),
        (1, 7),
        (0, 6),
    ],
    "borderIndices": [
        (0, 1),
        (6, 7),
        (1, 7),
        (0, 6),
    ],
}

expectedDataMap = {
    "facevarying": faceVaryingDataResults,
    "vertexvarying": vertexVaryingDataResults,
}
