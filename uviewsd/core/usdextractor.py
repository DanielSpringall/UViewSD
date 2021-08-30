# Copyright 2021 by Daniel Springall.
# This file is part of UViewSD, and is released under the "MIT License Agreement".
# Please see the LICENSE file that should have been included as part of this package.
from uviewsd.core import utils as uc_utils

from pxr import UsdGeom, UsdShade, Sdf

import os
import logging

logger = logging.getLogger(__name__)


VALID_PRIMVAR_TYPE_NAME = ("texCoord2f[]", "float2[]")
VALID_IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".tiff", ".bmp")


class UVData:
    def __init__(self, name, primPath, positions, indices, borderIndices):
        """Data class used for caching information specific to a single uv set."""
        self._name = name
        self._primPath = primPath
        self._positions = positions
        self._indices = indices
        self._borderIndices = borderIndices

    def identifier(self):
        """
        Returns:
            Str: The identifier for this uv data. Composed of primPath/uvName
        """
        return "{}/{}".format(self._primPath, self._name)

    def positions(self):
        """
        Returns:
            list[tuple(int, int)]: UV positions.
        """
        return self._positions

    def edgeIndices(self):
        """
        Returns:
            list[tuple(int, int)]: UV edge indices.
        """
        return self._indices

    def edgeBorderIndices(self):
        """
        Returns:
            list[tuple(int, int)]: UV edge border indices.
        """
        return self._borderIndices


class PrimDataExtractor:
    def __init__(self, prim):
        """
        UV and texture path data extractor from a single USD prims.
        This data is cached in a UVData class per uvName.
        """
        self._mesh = UsdGeom.Mesh(prim) if prim.IsValid() else None

        # Cached data
        self._validUVNames = None
        self._texurePaths = None
        self._uvData = {}

    def prim(self):
        return self._mesh.GetPrim()

    def isValid(self):
        """Test a given USDGeom mesh has the relveant data to extract uv's from.

        Returns:
            bool: True if the mesh has the relevant data to extract uv's for. False otherwise.
        """
        if not self._mesh:
            logger.debug("Invalid mesh for uv data. %s.", self._mesh)
            return False
        if not self._mesh.GetFaceVertexCountsAttr().HasValue():
            logger.debug(
                "Invalid mesh for uv data. %s. Missing face vertex count attribute.",
                self._mesh,
            )
            return False
        if not self._mesh.GetFaceVertexIndicesAttr().HasValue():
            logger.debug(
                "Invalid mesh for uv data. %s. Missing face vertex indices attribute.",
                self._mesh,
            )
            return False
        return True

    def refresh(self):
        """Reset any cached data."""
        self._validUVNames = None
        self._texurePaths = None
        self._uvData = {}

    # UV
    def data(self, uvName):
        """Extract the uv data of a specific name from the mesh.

        Args:
            uvName (str): The name of the uv attribute used on the prim to get the data from.
        Returns:
            uvData | None:
                Class containing the UVData information, or None if no data could be found.
        """
        data = self._uvData.get(uvName)
        if data is not None:
            return data

        if not self.isUVNameValid(uvName):
            logger.debug(
                "%s not a valid uv name for %s. Valid names: %s.",
                uvName,
                self._mesh,
                self.validUVNames(),
            )
            self._uvData[uvName] = None
            return None

        primvar = self._mesh.GetPrimvar(uvName)
        interpolation = primvar.GetInterpolation()

        positions = None
        indices = None
        if interpolation == UsdGeom.Tokens.faceVarying:
            positions, indices, borderIndices = self._getFaceVaryingUVs(primvar)
        elif interpolation == UsdGeom.Tokens.vertex:
            positions, indices, borderIndices = self._getVertexVaryingUVs(primvar)
        else:
            logger.error("Invalid interpolation (%s) for uv data.", interpolation)

        if not (positions and indices):
            logger.debug("No uv data exists for %s on %s", uvName, self._mesh)
            self._uvData[uvName] = None
            return None

        primPath = self.prim().GetPath().pathString
        uvData = UVData(uvName, primPath, positions, indices, borderIndices)
        self._uvData[uvName] = uvData
        return uvData

    def validUVNames(self):
        """Get a list of uv names that are valid on the mesh.

        Returns:
            list[str]: List of valid uv names.
        """
        if self._validUVNames is None:
            self._validUVNames = []
            if self.isValid():
                for primvar in self._mesh.GetPrimvars():
                    if primvar.GetTypeName() not in VALID_PRIMVAR_TYPE_NAME:
                        continue
                    self._validUVNames.append(primvar.GetPrimvarName())
        return self._validUVNames

    def isUVNameValid(self, uvName):
        return uvName in self.validUVNames()

    def _getFaceVaryingUVs(self, primvar):
        """Extract the face varying uv data from a primvar.

        Args:
            primvar (Usd.Primvar): The primvar to extract the uv data from.
        Returns:
            list[tuple(int, int)], list[tuple(int, int)], list[tuple(int, int)]:
                UV position values, UV edge indices, UV edge border indices.
        """
        faceVertCountList = self._mesh.GetFaceVertexCountsAttr().Get()
        uvPositions = primvar.Get()
        if len(uvPositions) == 0:
            return None, None, None

        uvIndices = primvar.GetIndices()
        if len(uvIndices) == 0:
            edgeIndices, borderIndices = self._createUVEdgesFromPositions(faceVertCountList)
        else:
            edgeIndices, borderIndices = self._createUVEdges(faceVertCountList, [uvIndices])
        return uvPositions, edgeIndices, borderIndices

    def _getVertexVaryingUVs(self, primvar):
        """Extract the vertex varying uv data from a primvar.

        Args:
            primvar (Usd.Primvar): The primvar to extract the uv data from.
        Returns:
            list[tuple(int, int)], list[tuple(int, int)], list[tuple(int, int)]:
                UV position values, UV edge indices, UV edge border indices.
        """
        faceVertCountList = self._mesh.GetFaceVertexCountsAttr().Get()
        faceVertexIndices = self._mesh.GetFaceVertexIndicesAttr().Get()
        uvPositions = primvar.Get()
        if len(uvPositions) == 0:
            return None, None, None

        uvIndices = primvar.GetIndices()
        uvIndexMaps = [faceVertexIndices]
        if uvIndices:
            uvIndexMaps.append(uvIndices)
        edgeIndices, borderIndices = self._createUVEdges(faceVertCountList, uvIndexMaps)
        return uvPositions, edgeIndices, borderIndices

    @staticmethod
    def _createUVEdges(faceVertCountList, indexMaps):
        """Generate the uv edge indices from a given list of uv indices.

        Args:
            faceVertCountList list[int]:
                List of number of indices per face.
            indexMaps list[list[]]:
                An ordered list of index maps to map a given face vert id back to it's corresponding uv index.
        Returns:
            list[tuple(int, int)], list[tuple(int, int)]:
                UV edge indices, UV edge border indices.
        """
        consumedIndices = 0
        edgeCountMap = {}
        edgeIndices = []
        for faceVertCount in faceVertCountList:
            for i in range(faceVertCount):
                firstIndex = consumedIndices + i
                secondIndex = (
                    consumedIndices if i == (faceVertCount - 1) else firstIndex + 1
                )
                for indexMap in indexMaps:
                    firstIndex = indexMap[firstIndex]
                    secondIndex = indexMap[secondIndex]
                edge = uc_utils.Edge(firstIndex, secondIndex)

                if edge in edgeCountMap:
                    edgeCountMap[edge] += 1
                else:
                    edgeCountMap[edge] = 1
                    edgeIndices.append(edge.indices())
            consumedIndices += faceVertCount

        borderIndices = []
        for edge, count in edgeCountMap.items():
            if count == 1:
                borderIndices.append(edge.indices())

        return edgeIndices, borderIndices

    @staticmethod
    def _createUVEdgesFromPositions(faceVertCountList):
        """Generate the uv edge indices from the face indices.
        This is done if no uvIndices exist.

        Note: We could use the first uvPosition of an index and any subsequent matching
              positions use this same index. But that assumes there are no uvs that
              have the same position but different indices, which is entirely plausible.
              So instead just build the entirety of the edge indices and return an empty border
              indices as we won't be able to accurately determine borders.

        Args:
            faceVertCountList list[int]:
                List of number of indices per face.
        Returns:
            list[tuple(int, int)], list[tuple(int, int)]:
                UV edge indices, UV edge border indices.
        """
        consumedIndices = 0
        edgeIndices = []
        for faceVertCount in faceVertCountList:
            for i in range(faceVertCount):
                firstIndex = consumedIndices + i
                secondIndex = (
                    consumedIndices if i == (faceVertCount - 1) else firstIndex + 1
                )
                edgeIndices.append((firstIndex, secondIndex))
            consumedIndices += faceVertCount
        return edgeIndices, []

    # TEXTURE
    def texturePaths(self):
        """
        Get any texture file paths used as inputs to the surface shader
        on the meshes bound material.

        Returns:
            list[str]: A unique list of texture file absolute paths.
        """
        if self._texurePaths is None:
            self._texurePaths = []
            shader = self._meshShader()
            if shader is not None:
                for path in self._getTexturePathsFromShader(shader):
                    if path not in self._texurePaths:
                        self._texurePaths.append(path)
        return self._texurePaths

    def _meshShader(self):
        """Get the shader used on the mesh if one exists.

        Returns:
            UsdShade.Shader | None: The shader if one exists, otherwise None.
        """
        prim = self.prim()
        binding = UsdShade.MaterialBindingAPI(prim)
        (material, _) = binding.ComputeBoundMaterial()
        if material:
            (shader, _, __) = material.ComputeSurfaceSource()
            if shader:
                return shader
            logger.debug("No surface shader for %s", prim)
        else:
            logger.debug("No material bound to %s", prim)
        return None

    @classmethod
    def _getTexturePathsFromShader(cls, shader):
        """Extract all texture file paths used in a shader.

        Returns:
            list[str]: A unique list of texture file paths.
        """
        inputs = []
        for input in shader.GetInputs():
            inputs.append(input)
            cls._getUpStreamInputs(input, inputs)

        paths = []
        for input in inputs:
            attribute = input.GetAttr().Get()
            if not isinstance(attribute, Sdf.AssetPath):
                continue
            path = attribute.resolvedPath
            if (
                os.path.isfile(path)
                and os.path.splitext(path)[-1] in VALID_IMAGE_EXTENSIONS
            ):
                paths.append(os.path.abspath(path))
        return paths

    @classmethod
    def _getUpStreamInputs(cls, input, inputsVisited):
        """Recursively search upstream for all possible inputs.
        Args:
            input(UsdShade.Input):
                The input to start the search from.
            inputsVisited(list[UsdShade.Input]):
                List of previously visited input nodes to compare against to ensure no
                search recursion occurs. New inputs discovered will be added to this list.
        """
        for connection in input.GetConnectedSources():
            if not connection:
                continue
            for input in connection[0].source.GetInputs():
                if input in inputsVisited:
                    continue
                inputsVisited.append(input)
                cls._getUpStreamInputs(input, inputsVisited)
