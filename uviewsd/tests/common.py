# Copyright 2021 by Daniel Springall.
# This file is part of UViewSD, and is released under the "MIT License Agreement".
# Please see the LICENSE file that should have been included as part of this package.
from pxr import Usd

import unittest
import os


USD_DATA_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")


class CommonTestCast(unittest.TestCase):
    def loadTestDataPrim(self, fileName):
        filePath = os.path.join(USD_DATA_DIR, "{}.usda".format(fileName))
        self._stage = Usd.Stage.Open(filePath)
        prim = self._stage.GetPrimAtPath("/cube")
        self.assertTrue(prim.IsValid())
        return prim
