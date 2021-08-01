# Copyright 2021 by Daniel Springall.
# This file is part of UViewSD, and is released under the "MIT License Agreement".
# Please see the LICENSE file that should have been included as part of this package.
from uviewsd.core import usdextractor as uc_usdextractor
from uviewsd.tests import common as ut_common

import os
import unittest


class PrimDataExtractorTestCase(ut_common.CommonTestCast):
    def setUp(self):
        self._stage = None

    def test_invalidprim(self):
        self.loadStage("invalid")
        prim = self.prim()
        extractor = uc_usdextractor.PrimDataExtractor(prim)

        self.assertFalse(extractor.isValid())
        self.assertEqual(extractor.validUVNames(), [])

    def test_uvsetname(self):
        self.loadStage("multipleuvnames")
        prim = self.prim()
        extractor = uc_usdextractor.PrimDataExtractor(prim)

        self.assertTrue(extractor.isValid())
        self.assertEqual(extractor.prim(), prim)

        expectedUVSetNames = ["customName", "secondCustomName"]
        self.assertEqual(extractor.validUVNames(), expectedUVSetNames)
        for uvSetName in expectedUVSetNames:
            self.assertTrue(extractor.isUVNameValid(uvSetName))
        self.assertFalse(extractor.isUVNameValid("invalidName"))

    def test_uvdata_facevarying(self):
        uvType = "facevarying"
        self.loadStage(uvType)
        prim = self.prim()
        extractor = uc_usdextractor.PrimDataExtractor(prim)
        uvName = "st"

        self.assertTrue(extractor.isValid())
        self.assertEqual(extractor.validUVNames(), [uvName])

        expectedResults = self.getExpectedUVResults(uvType)

        uvData = extractor.data(uvName)
        self.assertEqual(expectedResults["positions"], uvData.positions())
        self.assertEqual(expectedResults["indices"], uvData.edgeIndices())
        self.assertEqual(expectedResults["borderIndices"], uvData.edgeBorderIndices())

    def test_uvdata_vertexvarying(self):
        uvType = "vertexvarying"
        self.loadStage(uvType)
        prim = self.prim()
        extractor = uc_usdextractor.PrimDataExtractor(prim)
        uvName = "st"

        self.assertTrue(extractor.isValid())
        self.assertEqual(extractor.validUVNames(), [uvName])

        expectedResults = self.getExpectedUVResults(uvType)

        uvData = extractor.data(uvName)
        self.assertEqual(expectedResults["positions"], uvData.positions())
        self.assertEqual(expectedResults["indices"], uvData.edgeIndices())
        self.assertEqual(expectedResults["borderIndices"], uvData.edgeBorderIndices())

    def test_uvdata_textures(self):
        self.loadStage("texture")
        prim = self.prim(primPath="/root{}".format(self.defaultPrimPath))
        extractor = uc_usdextractor.PrimDataExtractor(prim)

        self.assertTrue(extractor.isValid())
        shader = extractor._meshShader()
        expectedShaderPrim = self._stage.GetPrimAtPath("/root/material/PBRShader")
        self.assertEqual(expectedShaderPrim, shader.GetPrim())

        expectedTexturePaths = [
            self.getTestTextureFilePath(textureFileName)
            for textureFileName in ["texture1", "texture2"]
        ]
        texturePaths = [
            os.path.abspath(path).lower() for path in extractor.texturePaths()
        ]
        self.assertEqual(expectedTexturePaths, texturePaths)


if __name__ == "__main__":
    unittest.main()
