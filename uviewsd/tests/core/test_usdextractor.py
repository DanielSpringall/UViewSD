# Copyright 2021 by Daniel Springall.
# This file is part of UViewSD, and is released under the "MIT License Agreement".
# Please see the LICENSE file that should have been included as part of this package.
from uviewsd.core import usdextractor as uc_usdextractor
from uviewsd.tests import common as ut_common


class PrimDataExtractorTestCase(ut_common.CommonTestCast):
    def setUp(self):
        self._stage = None

    def test_invalidprim(self):
        prim = self.loadTestDataPrim("invalid")
        extractor = uc_usdextractor.PrimDataExtractor(prim)
        self.assertFalse(extractor.isValid())
        self.assertEqual(extractor.validUVNames(), [])

    def test_uvsetname(self):
        prim = self.loadTestDataPrim("mulitpleuvnames")
        extractor = uc_usdextractor.PrimDataExtractor(prim)
        self.assertTrue(extractor.isValid())
        self.assertEqual(extractor.prim(), prim)

        expectedUVSetNames = ["customName", "secondCustomName"]
        self.assertEqual(extractor.validUVNames(), expectedUVSetNames)
        for uvSetName in expectedUVSetNames:
            self.assertTrue(extractor.isUVNameValid(uvSetName))
        self.assertFalse(extractor.isUVNameValid("invalidName"))

    def test_uvdata_facevarying(self):
        prim = self.loadTestDataPrim("facevarying")
        extractor = uc_usdextractor.PrimDataExtractor(prim)
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
        ]
        expectedBorderIndices = [
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
        ]

        uvData = extractor.data(uvName)
        self.assertEqual(expectedPositions, uvData.positions())
        self.assertEqual(expectedIndices, uvData.edgeIndices())
        self.assertEqual(expectedBorderIndices, uvData.edgeBorderIndices())

    def test_uvdata_vertexvarying(self):
        prim = self.loadTestDataPrim("vertexvarying")
        extractor = uc_usdextractor.PrimDataExtractor(prim)
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
        ]
        expectedBorderIndices = [(0, 1), (6, 7), (1, 7), (0, 6)]

        uvData = extractor.data(uvName)
        self.assertEqual(expectedPositions, uvData.positions())
        self.assertEqual(expectedIndices, uvData.edgeIndices())
        self.assertEqual(expectedBorderIndices, uvData.edgeBorderIndices())


if __name__ == "__main__":
    import unittest

    unittest.main()
