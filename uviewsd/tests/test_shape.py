# Copyright 2021 by Daniel Springall.
# This file is part of UViewSD, and is released under the "MIT License Agreement".
# Please see the LICENSE file that should have been included as part of this package.
from uviewsd import shape
from pxr import Usd

import unittest
import os


USD_DATA_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")


class UVShapeExtractorTestCase(unittest.TestCase):
    def setUp(self):
        self._stage = None

    def loadTestDataPrim(self, fileName):
        filePath = os.path.join(USD_DATA_DIR, "{}.usda".format(fileName))
        self._stage = Usd.Stage.Open(filePath)
        prim = self._stage.GetPrimAtPath("/cube")
        self.assertTrue(prim.IsValid())
        return prim

    def test_invalidprim(self):
        prim = self.loadTestDataPrim("invalid")
        extractor = shape.PrimUVDataExtractor(prim)
        self.assertFalse(extractor.isValid())
        self.assertEqual(extractor.validUVNames(), [])

    def test_uvsetname(self):
        prim = self.loadTestDataPrim("mulitpleuvnames")
        extractor = shape.PrimUVDataExtractor(prim)
        self.assertTrue(extractor.isValid())
        self.assertEqual(extractor.prim(), prim)

        expectedUVSetNames = ["customName", "secondCustomName"]
        self.assertEqual(extractor.validUVNames(), expectedUVSetNames)
        for uvSetName in expectedUVSetNames:
            self.assertTrue(extractor.isUVNameValid(uvSetName))
        self.assertFalse(extractor.isUVNameValid("invalidName"))

    def test_uvdata_facevarying(self):
        prim = self.loadTestDataPrim("facevarying")
        extractor = shape.PrimUVDataExtractor(prim)
        self.assertTrue(extractor.isValid())
        uvName = "st"
        self.assertEqual(extractor.validUVNames(), [uvName])

        expectedPositions = [
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
        ]
        expectedIndices = [
            (0, 1),
            (1, 3),
            (3, 2),
            (2, 0),
            (2, 3),
            (3, 5),
            (5, 4),
            (4, 2),
            (4, 5),
            (5, 7),
            (7, 6),
            (6, 4),
            (6, 7),
            (7, 9),
            (9, 8),
            (8, 6),
            (1, 10),
            (10, 11),
            (11, 3),
            (3, 1),
            (12, 0),
            (0, 2),
            (2, 13),
            (13, 12),
        ]
        [uvPositions, edgeIndices] = extractor.data(uvName)
        self.assertEqual(expectedPositions, uvPositions)
        self.assertEqual(expectedIndices, edgeIndices)

    def test_uvdata_vertexvarying(self):
        prim = self.loadTestDataPrim("vertexvarying")
        extractor = shape.PrimUVDataExtractor(prim)
        self.assertTrue(extractor.isValid())
        uvName = "st"
        self.assertEqual(extractor.validUVNames(), [uvName])

        expectedPositions = [
            (0, 0),
            (1, 0),
            (0.16813788, 0.16813788),
            (0.8318621, 0.16813788),
            (0.16813788, 0.8318621),
            (0.8318621, 0.8318621),
            (0, 1),
            (1, 1),
        ]
        expectedIndices = [
            (0, 1),
            (1, 3),
            (3, 2),
            (2, 0),
            (2, 3),
            (3, 5),
            (5, 4),
            (4, 2),
            (4, 5),
            (5, 7),
            (7, 6),
            (6, 4),
            (1, 7),
            (7, 5),
            (5, 3),
            (3, 1),
            (6, 0),
            (0, 2),
            (2, 4),
            (4, 6),
        ]
        [uvPositions, edgeIndices] = extractor.data(uvName)
        self.assertEqual(expectedPositions, uvPositions)
        self.assertEqual(expectedIndices, edgeIndices)

    def test_uvborder(self):
        prim = self.loadTestDataPrim("uvborders")
        extractor = shape.PrimUVDataExtractor(prim)
        self.assertTrue(extractor.isValid())
        uvName = "st"
        self.assertEqual(extractor.validUVNames(), [uvName])
        [_, edgeIndices] = extractor.data(uvName)

        expectedIndices = [
            (0, 1),
            (14, 18),
            (16, 18),
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
            (14, 15),
            (3, 5),
            (15, 16),
            (2, 4),
        ]
        edgeIndices = extractor.edgeBoundariesFromEdgeIndices(edgeIndices)
        self.assertEqual(expectedIndices, edgeIndices)


if __name__ == "__main__":
    unittest.main()
