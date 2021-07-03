# Copyright 2021 by Daniel Springall.
# This file is part of UViewSD, and is released under the "MIT License Agreement".
# Please see the LICENSE file that should have been included as part of this package.
from uviewsd import shape

import logging

logger = logging.getLogger(__name__)


class SessionManager:
    # Used to determine the uv set name if none has been specified.
    DEFAULT_UV_SET_NAMES = ["uv", "st"]

    def __init__(self, stage=None):
        self._stage = stage
        self._uvExtractors = []
        self._availableUVSetNames = []
        self._activeUVSetName = None

    def extractors(self):
        """Return a list of the extractors for all the prims that have been added in the session.

        Returns:
            list[shape.PrimUVDataExtractor]: List of extractors.
        """
        return self._uvExtractors

    # USD
    def activeStage(self):
        """Return the active usd stage.

        Returns:
            Usd.Stage | None: The active usd stage, or None if one hasn't been set.
        """
        return self._stage

    def setStage(self, stage):
        """Set the active stage for the session.

        Args:
            name (Usd.Stage): The usd stage to set.
        Returns
            bool: True if change occured, false otherwise.
        """
        if stage == self._stage:
            logger.debug("Usd stage already set to %s.", stage)
            return False
        self._stage = stage
        return True

    def addPrimPaths(self, primPaths, replace=False):
        """Add a list of prim paths.

        Args:
            primPaths (list[str]): List of prim paths to get from the active stage.
            replace (bool): If true, remove any of the current cached extractors.
        Returns
            list[shape.PrimUVDataExtractor]:
                List of any new uv extractors and list of any new texture extractors.
        """
        stage = self.activeStage()
        if stage is None:
            logger.error("No stage set to extract prims from.")
            return []
        prims = [stage.GetPrimAtPath(primPath) for primPath in primPaths]
        return self.addPrims(prims, replace)

    def addPrims(self, prims, replace=False):
        """Add a list of usd prims.

        Args:
            prims (Usd.Prim): List of prims to get from the stage.
            replace (bool): If true, remove any of the current cached extractors.
        Returns
            list[shape.PrimUVDataExtractor]:
                List of any new uv extractors and list of any new texture extractors.
        """
        if replace:
            self._uvExtractors = []

        newUVExtractors = []
        for prim in prims:
            uvExtractor = self._updateExtractors(prim)
            newUVExtractors.append(uvExtractor)

        if newUVExtractors or replace:
            self._updateAvailableUVSetNames()

        return newUVExtractors

    def getShapeData(self, uvSetName=None, extractors=None):
        """Get the relevant shape data to pass to the uv viewer from a list of extractors.

        Args:
            uvSetName (str | None):
                The uv set name to use to search for uv data in the extractors. If None is specified
                falls back on the sessions active uv set name.
            extractors (shape.PrimUVDataExtractor | None):
                The extractors to get the shape data from. If no extractors are specified
                falls back on the cached extractors.
        Returns:
            list[shape.UVShape]:
                List of UVShape objects for each current extractor.
        """
        uvName = uvSetName if uvSetName else self.activeUVSetName()
        extractors = extractors if extractors else self._uvExtractors
        if not (extractors and uvName):
            return []

        shapeData = []
        for extractor in extractors:
            if not extractor.isUVNameValid(uvName):
                continue
            [positions, indices] = extractor.data(uvName)
            if not (positions and indices):
                continue

            identifier = extractor.prim().GetPath().pathString
            shapeData.append(shape.UVShape(positions, indices, identifier))
        return shapeData

    def _updateExtractors(self, prim):
        """
        Generate uv extractors, adding them to the existing extractors
        if they don't yet exist.

        Args:
            prim (Usd.Prim): The usd prim to update the cached extractors with.
        Returns:
            list[shape.PrimUVDataExtractor]:
                List of any new uv extractors and list of any new texture extractors.
        """
        # UV extractor
        uvExtractor = None
        for _extractor in self._uvExtractors:
            if prim == _extractor.prim():
                break
        else:
            uvExtractor = shape.PrimUVDataExtractor(prim)
            if not uvExtractor.isValid():
                uvExtractor = None
                logger.info("Invalid prim %s to extract uv data from.", prim)
            else:
                self._uvExtractors.append(uvExtractor)
        return uvExtractor

    def clear(self):
        """Remove any cached extractors."""
        self._uvExtractors = []

    # UV SETS
    def _updateAvailableUVSetNames(self):
        """Update the available uv set names from the cached extractors."""
        self._availableUVSetNames = []
        for extractor in self._uvExtractors:
            for name in extractor.validUVNames():
                if name not in self._availableUVSetNames:
                    self._availableUVSetNames.append(name)
        self._availableUVSetNames.sort()

    def availableUVSetNames(self):
        """Return a list of the available uv set names.

        Returns:
            list[str]: Alphabetically ordered list of available uv set names.
        """
        if not self._availableUVSetNames:
            self._updateAvailableUVSetNames()
        return self._availableUVSetNames

    def activeUVSetName(self):
        """
        Return the current active uv set name. If none is specified, first look for a matching defualt
        uv name. If none can be found return the first name from the available uv names.

        Returns:
            str | None: The active uv set name, or None if no available names exist.
        """
        if self._activeUVSetName is None and self._availableUVSetNames:
            for name in self.DEFAULT_UV_SET_NAMES:
                if name in self._availableUVSetNames:
                    self._activeUVSetName = name
                    break
            else:
                self._activeUVSetName = self._availableUVSetNames[0]
        return self._activeUVSetName

    def setActiveUVSetName(self, name):
        """Set the uv name. The name must exist in the list of avaiable uv set names.

        Args:
            name (str): The name of the UV set to change the viewer to.
        Returns
            bool: True if change occured, false otherwise.
        """
        if name == self._activeUVSetName:
            logger.debug("UV name already set to %s.", name)
            return False
        if name not in self._availableUVSetNames:
            logger.error("%s is not an available uv name to set.", name)
            return False
        self._activeUVSetName = name
        return True
