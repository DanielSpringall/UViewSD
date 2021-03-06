# Copyright 2021 by Daniel Springall.
# This file is part of UViewSD, and is released under the "MIT License Agreement".
# Please see the LICENSE file that should have been included as part of this package.
from uviewsd.core import usdextractor as uc_usdextractor
from uviewsd.gl import shape as gl_shape

import os
import logging

logger = logging.getLogger(__name__)


class SessionManager:
    # List of favoured uv names to help determine the active uv name if none was specified.
    DEFAULT_UV_SET_NAMES = ["uv", "st"]
    EDGE_BORDER_IDENTIFIER_SUFFIX = "_edgeBorders"

    def __init__(self, stage=None):
        self._stage = stage
        self._extractors = []
        self._availableUVSetNames = []
        self._activeUVSetName = None
        # List of texture paths which have been used during the session.
        self._recentTexturePaths = []
        self._availableTexturePaths = []
        self._activeTexturePath = None

    def extractors(self):
        """Return a list of the extractors for all the prims that have been added in the session.

        Returns:
            list[uc_usdextractor.PrimDataExtractor]: List of uc_usdextractor.
        """
        return self._extractors

    def refresh(self):
        """Reset any cached data."""
        for extractor in self._extractors:
            extractor.refresh()

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
            name (Usd.Stage | None):
                The usd stage to set. If None, will remove any cached data.
        Returns
            bool: True if change occurred, false otherwise.
        """
        if stage == self._stage:
            logger.debug("Usd stage already set to %s.", stage)
            return False
        self._stage = stage
        if self._stage is None:
            self.clear()
        return True

    def addPrimPaths(self, primPaths, replace=False, refresh=True):
        """Add a list of prim paths.

        Args:
            primPaths (list[str]): List of prim paths to get from the active stage.
            replace (bool): If true, remove any of the current cached uc_usdextractor.
            refresh (bool): If True and replace is True, will remove an existing extractor that matches
                            a prim, and re-evaluate it. Set to False if no change has occurred since last adding it.
        Returns
            list[uc_usdextractor.PrimDataExtractor]:
                List of any new uv extractors and list of any new texture uc_usdextractor.
        """
        stage = self.activeStage()
        if stage is None:
            logger.error("No stage set to extract prims from.")
            return []
        prims = [stage.GetPrimAtPath(primPath) for primPath in primPaths]
        return self.addPrims(prims, replace, refresh)

    def addPrims(self, prims, replace=False, refresh=True):
        """Add a list of usd prims.

        Args:
            prims (Usd.Prim): List of prims to get from the stage.
            replace (bool): If true, remove any of the current cached uc_usdextractor.
            refresh (bool): If True and replace is True, will remove an existing extractor that matches
                            a prim, and re-evaluate it. Set to False if no change has occurred since last adding it.
        Returns
            list[uc_usdextractor.PrimDataExtractor]:
                List of any new uv extractors and list of any new texture uc_usdextractor.
        """
        if replace:
            extractors = []
            if not refresh:
                for extractor in self._extractors:
                    for prim in prims:
                        if prim == extractor.prim():
                            extractors.append(extractor)
            self._extractors = extractors

        newExtractors = []
        for prim in prims:
            newExtractor = self._updateExtractors(prim)
            if newExtractor is not None:
                newExtractors.append(newExtractor)

        if newExtractors or replace:
            self._updateAvailableUVSetNames()
            self._updateAvailableTexturePaths()

        return newExtractors

    def getShapeData(self, uvSetName=None, extractors=None):
        """Get the relevant shape data to pass to the uv viewer.

        Args:
            uvSetName (str | None):
                The uv set name to use to search for uv data in the uc_usdextractor. If None is specified
                falls back on the sessions active uv set name.
            extractors (uc_usdextractor.PrimDataExtractor | None):
                The extractors to get the shape data from. If no extractors are specified
                falls back on the cached uc_usdextractor.
        Returns:
            list[gl_shape.EdgesShape]:
                List of EdgesShape objects for each current extractor.
        """
        uvName = uvSetName if uvSetName else self.activeUVSetName()
        extractors = extractors if extractors else self._extractors
        if not (extractors and uvName):
            return []

        shapeData = []
        for uvData in self._iterUVDataFromName(uvName, extractors):
            shape = gl_shape.EdgesShape(
                uvData.positions(), uvData.edgeIndices(), uvData.identifier()
            )
            shapeData.append(shape)
        return shapeData

    def getShapeEdgeBorderData(self, uvSetName=None, extractors=None):
        """Get the relevant shape edge border data to pass to the uv viewer.

        Args:
            uvSetName (str | None):
                The uv set name to use to search for uv data in the uc_usdextractor. If None is specified
                falls back on the sessions active uv set name.
            extractors (uc_usdextractor.PrimDataExtractor | None):
                The extractors to get the shape data from. If no extractors are specified
                falls back on the cached uc_usdextractor.
        Returns:
            list[gl_shape.EdgesShape]:
                List of EdgesShape objects for each current extractor.
        """
        uvName = uvSetName if uvSetName else self.activeUVSetName()
        extractors = extractors if extractors else self._extractors
        if not (extractors and uvName):
            return []

        shapeData = []
        for uvData in self._iterUVDataFromName(uvName, extractors):
            edgeIndices = uvData.edgeBorderIndices()
            if not edgeIndices:
                continue
            identifier = uvData.identifier() + self.EDGE_BORDER_IDENTIFIER_SUFFIX
            shape = gl_shape.EdgesShape(
                uvData.positions(), edgeIndices, identifier, width=2.0
            )
            shapeData.append(shape)
        return shapeData

    @staticmethod
    def _iterUVDataFromName(name, extractors):
        """Iterate over the uv data objects with a specific uv name in a given set of extractors.

        Args:
            name (str):
                The uv set name to use to search for uv data in the uc_usdextractor.
            extractors (uc_usdextractor.PrimDataExtractor):
                The extractors to get the shape data from.
        Yields:
            UVData: The uvData objects.
        """
        if not (extractors and name):
            return

        for extractor in extractors:
            if not extractor.isUVNameValid(name):
                continue
            data = extractor.data(name)
            if data is None:
                continue
            yield data

    def _updateExtractors(self, prim):
        """
        Generate an extractor for a given prim, adding them to the existing extractors
        if they don't yet exist.

        Args:
            prim (Usd.Prim): The usd prim to update the cached extractors with.
        Returns:
            list[uc_usdextractor.PrimDataExtractor]:
                List of any new extractors added to the session manager.
        """
        newExtractor = None

        for extractor in self._extractors:
            if prim == extractor.prim():
                break
        else:
            newExtractor = uc_usdextractor.PrimDataExtractor(prim)
            if not newExtractor.isValid():
                newExtractor = None
                logger.info("Invalid prim %s to extract data from.", prim)
            else:
                self._extractors.append(newExtractor)

        return newExtractor

    def clear(self):
        """Remove any cached uc_usdextractor."""
        self._extractors = []
        self._availableUVSetNames = []
        self._activeUVSetName = None
        self._availableTexturePaths = []
        self._activeTexturePath = None

    # UV SETS
    def _updateAvailableUVSetNames(self):
        """Update the available uv set names from the cached uc_usdextractor."""
        self._availableUVSetNames = []
        for extractor in self._extractors:
            for name in extractor.validUVNames():
                if name not in self._availableUVSetNames:
                    self._availableUVSetNames.append(name)
        if not self._availableUVSetNames:
            self._activeUVSetName = None

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
        Return the current active uv set name. If none is specified, first look for a matching default
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
        """Set the uv name. The name must exist in the list of available uv set names.

        Args:
            name (str): The name of the UV set to change the viewer to.
        Returns
            bool: True if change occurred, false otherwise.
        """
        if name == self._activeUVSetName:
            logger.debug("UV name already set to %s.", name)
            return False
        if name not in self._availableUVSetNames:
            logger.error("%s is not an available uv name to set.", name)
            return False
        self._activeUVSetName = name
        return True

    # TEXTURE
    def _updateAvailableTexturePaths(self):
        """Update the available texture paths from the cached uc_usdextractor.
        Tests to make sure the paths are valid file paths.
        """
        paths = []
        for extractor in self._extractors:
            paths.extend(extractor.texturePaths())
        paths = list(set(paths))
        paths.sort()
        self._availableTexturePaths = paths

    def availableTexturePaths(self):
        """Return a list of the available texture paths.

        Returns:
            list[str]: Alphabetically ordered list of available texture paths.
        """
        if not self._availableTexturePaths:
            self._updateAvailableTexturePaths()
        return self._availableTexturePaths

    def recentTexturePaths(self):
        """Return the recently used texture paths.
        Returns:
            list[str] | None: The recently used texture paths.
        """
        return self._recentTexturePaths

    def activeTexturePath(self):
        """Return the current active texture path.
        Returns:
            str | None: The active texture path, or None if one hasn't been set yet.
        """
        return self._activeTexturePath

    def setActiveTexturePath(self, path):
        """Set the texture path.
        Args:
            path (str): The texture path to add.
        Returns
            bool: True if successfully set, false otherwise.
        """
        path = os.path.abspath(path)
        if path == self._activeTexturePath:
            return True
        if path not in self._availableTexturePaths:
            if not os.path.isfile(path):
                logger.error("Invalid texture file path to set %s", path)
                return False

        # Add the path to the recently used paths.
        if path in self._recentTexturePaths:
            self._recentTexturePaths.remove(path)
        self._recentTexturePaths.insert(0, path)

        maxRecentTexturePathsTracked = 5
        if len(self._recentTexturePaths) > maxRecentTexturePathsTracked:
            self._recentTexturePaths = self._recentTexturePaths[
                :maxRecentTexturePathsTracked
            ]

        self._activeTexturePath = path
        return True
