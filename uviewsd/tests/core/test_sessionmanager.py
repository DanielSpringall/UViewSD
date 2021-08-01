# Copyright 2021 by Daniel Springall.
# This file is part of UViewSD, and is released under the "MIT License Agreement".
# Please see the LICENSE file that should have been included as part of this package.
from uviewsd.core import sessionmanager as uc_sessionmanager
from uviewsd.tests import common as ut_common

import os
import unittest


class PrimDataExtractorTestCase(ut_common.CommonTestCast):
    def setUp(self):
        self.loadStage("combined")
        self.sessionManager = uc_sessionmanager.SessionManager()

        # PRIM PATH DATA
        self.faceVaryingPrimPath = "/facevarying{}".format(self.defaultPrimPath)
        self.multipleUVNamesPrimPath = "/multipleuvnames{}".format(self.defaultPrimPath)
        self.texturePrimPath = "/texture{}{}".format(
            self.defaultPrimPath, self.defaultPrimPath
        )
        self.uvBordersPrimPath = "/uvborders{}".format(self.defaultPrimPath)
        self.primPaths = [
            self.faceVaryingPrimPath,
            self.multipleUVNamesPrimPath,
            self.texturePrimPath,
            self.uvBordersPrimPath,
        ]

        # UV NAME DATA
        self.uvNameMap = {
            self.faceVaryingPrimPath: ["st"],
            self.multipleUVNamesPrimPath: ["customName", "secondCustomName"],
            self.texturePrimPath: ["st"],
            self.uvBordersPrimPath: ["st"],
        }
        self.availableUVNames = []
        for uvNames in self.uvNameMap.values():
            for uvName in uvNames:
                if uvName not in self.availableUVNames:
                    self.availableUVNames.append(uvName)
        self.defaultUVName = None
        for uvName in uc_sessionmanager.SessionManager.DEFAULT_UV_SET_NAMES:
            if uvName in self.availableUVNames:
                self.defaultUVName = uvName
                break
        self.assertTrue(
            self.defaultUVName,
            "No default UV name used in test data. Consider updating test data, or manually setting default UV name for tests.",
        )

        # TEXTURE DATA
        self.texturePathMap = {
            self.faceVaryingPrimPath: [],
            self.multipleUVNamesPrimPath: [],
            self.texturePrimPath: [
                self.getTestTextureFilePath(textureFileName)
                for textureFileName in ["texture1", "texture2"]
            ],
            self.uvBordersPrimPath: [],
        }
        self.availableTexturePaths = []
        for texturePaths in self.texturePathMap.values():
            for texturePath in texturePaths:
                if texturePath not in self.availableTexturePaths:
                    self.availableTexturePaths.append(texturePath)

        # EXPECTED RESULTS DATA
        self.expectedResultsMap = {
            self.faceVaryingPrimPath: "facevarying",
            self.multipleUVNamesPrimPath: "facevarying",
            self.texturePrimPath: "vertexvarying",
            self.uvBordersPrimPath: "facevarying",
        }

    def _addPrimsToSessionManager(self, asPrims=True, primPaths=None):
        primPaths = primPaths if primPaths else self.primPaths
        numPrimsAdded = len(primPaths)
        if asPrims:
            prims = [self.prim(primPath) for primPath in primPaths]
            results = self.sessionManager.addPrims(prims)
            self.assertEqual(len(results), numPrimsAdded)
            self.assertEqual(len(self.sessionManager._extractors), numPrimsAdded)
        else:
            results = self.sessionManager.addPrimPaths(primPaths)
            self.assertEqual(len(results), numPrimsAdded)
            self.assertEqual(len(self.sessionManager._extractors), numPrimsAdded)

    def test_stage(self):
        sm = self.sessionManager
        self.assertIsNone(sm.activeStage())
        sm.setStage(self._stage)
        self.assertEqual(sm.activeStage(), self._stage)

        # Add a valid prim to cache some data on the session manager.
        sm.addPrimPaths([self.texturePrimPath])
        self.prim(self.texturePrimPath)
        self.assertTrue(sm._extractors)
        self.assertTrue(sm.availableUVSetNames())
        self.assertTrue(sm.availableTexturePaths())

        # Clear the stage.
        sm.setStage(None)
        self.assertIsNone(sm.activeStage())
        # Ensure when clearing the stage, any cached data is removed.
        self.assertFalse(sm._extractors)
        self.assertFalse(sm.availableUVSetNames())
        self.assertFalse(sm.availableTexturePaths())

    def test_addPrims(self):
        sm = self.sessionManager
        sm.setStage(self._stage)
        self._addPrimsToSessionManager(asPrims=True)

        self.assertEqual(
            sorted(self.availableUVNames), sorted(sm.availableUVSetNames())
        )
        self.assertEqual(self.defaultUVName, sm.activeUVSetName())
        texturePaths = [path.lower() for path in sm.availableTexturePaths()]
        self.assertEqual(self.availableTexturePaths, texturePaths)

    def test_addPrimPaths(self):
        sm = self.sessionManager

        # Trying to add primpaths before stage set shouldn't work
        results = sm.addPrimPaths(self.primPaths)
        self.assertEqual(len(results), 0)

        sm.setStage(self._stage)
        self._addPrimsToSessionManager(asPrims=False)

        self.assertEqual(
            sorted(self.availableUVNames), sorted(sm.availableUVSetNames())
        )
        self.assertEqual(self.defaultUVName, sm.activeUVSetName())
        texturePaths = [path.lower() for path in sm.availableTexturePaths()]
        self.assertEqual(self.availableTexturePaths, texturePaths)

    def test_uvNames(self):
        sm = self.sessionManager
        sm.setStage(self._stage)
        self._addPrimsToSessionManager()

        self.assertEqual(
            sorted(self.availableUVNames), sorted(sm.availableUVSetNames())
        )
        self.assertEqual(self.defaultUVName, sm.activeUVSetName())

        # Try and set an invalid uvSetName (i.e. a uvSetName that doesn't exist on any of the prims)
        invalidUVSetName = "invalidUVSetName"
        self.assertNotIn(invalidUVSetName, self.availableUVNames)
        success = sm.setActiveUVSetName(invalidUVSetName)
        self.assertFalse(success)
        # Original default name should still be active
        self.assertEqual(self.defaultUVName, sm.activeUVSetName())

        # Set a new valid uvSetName (i.e. a uvSetName that does exist on a prim)
        newUVSetName = None
        for uvSetName in self.availableUVNames:
            if uvSetName != self.defaultUVName:
                newUVSetName = uvSetName
                break
        self.assertIsNotNone(
            newUVSetName, "Not enough available uv set names to properly test uv names."
        )

        success = sm.setActiveUVSetName(newUVSetName)
        self.assertTrue(success)
        self.assertEqual(newUVSetName, sm.activeUVSetName())

    def test_textures(self):
        sm = self.sessionManager
        sm.setStage(self._stage)
        self._addPrimsToSessionManager()

        texturePaths = sm.availableTexturePaths()
        self.assertTrue(texturePaths)
        texturePaths = [
            os.path.abspath(path).lower() for path in sm.availableTexturePaths()
        ]
        self.assertEqual(self.availableTexturePaths, texturePaths)
        self.assertFalse(sm.recentTexturePaths())
        self.assertIsNone(sm.activeTexturePath())

        # Try and set an invalid texture path.
        invalidTexturePath = (
            "this/should/be/an/invalid/path/or/you/have/weird/filepaths.jpg"
        )
        self.assertFalse(os.path.isfile(invalidTexturePath))
        success = sm.setActiveTexturePath(invalidTexturePath)
        self.assertFalse(success)
        self.assertFalse(sm.recentTexturePaths())
        self.assertIsNone(sm.activeTexturePath())

        # Set the active texture path to one that is available.
        pathToSet = texturePaths[0]
        success = sm.setActiveTexturePath(pathToSet)
        self.assertTrue(success)
        self.assertEqual(pathToSet, os.path.abspath(sm.activeTexturePath()).lower())
        # We should now have 1 path cached in the recent paths.
        recentPaths = sm.recentTexturePaths()
        self.assertEqual(len(recentPaths), 1)
        self.assertEqual(pathToSet, os.path.abspath(recentPaths[0]).lower())

        # Add a path that isn't in use in any of the prims.
        newTexturePath = self.getTestTextureFilePath("texture3")
        self.assertNotIn(newTexturePath, texturePaths)
        success = sm.setActiveTexturePath(newTexturePath)
        self.assertTrue(success)
        self.assertEqual(
            newTexturePath, os.path.abspath(sm.activeTexturePath()).lower()
        )
        # We should now have 2 paths cached in the recent paths.
        recentPaths = [
            os.path.abspath(path).lower() for path in sm.recentTexturePaths()
        ]
        self.assertEqual(len(recentPaths), 2)
        self.assertListEqual(sorted([pathToSet, newTexturePath]), sorted(recentPaths))

    def test_uvdata(self):
        sm = self.sessionManager
        sm.setStage(self._stage)
        self._addPrimsToSessionManager()

        # Query uv data for a uvName that exists on some, but not all of the current prims.
        uvName = "st"
        sm.setActiveUVSetName(uvName)
        count = 0
        for uvNames in self.uvNameMap.values():
            if uvName in uvNames:
                count += 1
        self.assertTrue(count != 0 and count != len(self.primPaths))

        # Ensure we are getting shape data
        shapes = sm.getShapeData()
        self.assertEqual(len(shapes), count)
        for shape in shapes:
            self.assertTrue(shape._positions.any())
            self.assertTrue(shape._indices.any())

        shapes = sm.getShapeEdgeBorderData()
        self.assertEqual(len(shapes), count)
        for shape in shapes:
            self.assertTrue(shape._positions.any())
            self.assertTrue(shape._indices.any())


if __name__ == "__main__":
    unittest.main()
