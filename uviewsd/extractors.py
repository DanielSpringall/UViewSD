# Copyright 2021 by Daniel Springall.
# This file is part of UViewSD, and is released under the "MIT License Agreement".
# Please see the LICENSE file that should have been included as part of this package.
from pxr import UsdGeom, UsdShade, Sdf

import os
import logging

logger = logging.getLogger(__name__)


VALID_PRIMVAR_TYPE_NAME = ("texCoord2f[]", "float2[]")
VALID_IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".tiff", ".bmp")


class PrimDataExtractor:
    """UV and texture path data extractor for USD prims."""
    def __init__(self, prim):
        self._mesh = UsdGeom.Mesh(prim) if prim.IsValid() else None
        self._shader = None
        self._validUVNames = None

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

    # UV
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

    def uvData(self, uvName):
        """Extract the uv data of a specific name from the mesh.

        Args:
            uvName (str): The name of the uv prim to get the data for.
        Returns:
            list[tuple(int, int)]:
                A list of tuples corresponding to an edges start and end index . e.g. [(uvPos0, uvPos1), (uvPos1, uvPos2), ...]
                where each index maps back to the uv positions. So uvPos0 -> uvPos1 would make up an edge.
        """
        if not self.isUVNameValid(uvName):
            logger.debug(
                "%s not a valid uv name for %s. Valid names: %s.",
                uvName,
                self._mesh,
                self.validUVNames(),
            )
            return None, None

        primvar = self._mesh.GetPrimvar(uvName)
        interpolation = primvar.GetInterpolation()
        if interpolation == UsdGeom.Tokens.faceVarying:
            return self._getFaceVaryingUVs(primvar)
        elif interpolation == UsdGeom.Tokens.vertex:
            return self._getVertexVaryingUVs(primvar)

        logger.error("Invalid interpolation (%s) for uv data.", interpolation)
        return None, None

    def _getFaceVaryingUVs(self, primvar):
        """Extract the face varying uv data from a primvar.

        Args:
            primvar (Usd.Primvar): The primvar to extract the uv data from.
        Returns:
            list[tuple(int, int)]:
                A list of tuples corresponding to an edges start and end index . e.g. [(uvPos0, uvPos1), (uvPos1, uvPos2), ...]
                where each index maps back to the uv positions. So uvPos0 -> uvPos1 would make up an edge.
        """
        faceVertCountList = self._mesh.GetFaceVertexCountsAttr().Get()
        uvPositions = primvar.Get()
        uvIndices = primvar.GetIndices()
        edgeIndices = self._createUVEdges(faceVertCountList, [uvIndices])
        return [uvPositions, edgeIndices]

    def _getVertexVaryingUVs(self, primvar):
        """Extract the vertex varying uv data from a primvar.

        Args:
            primvar (Usd.Primvar): The primvar to extract the uv data from.
        Returns:
            list[tuple(int, int)]:
                A list of tuples corresponding to an edges start and end index . e.g. [(uvPos0, uvPos1), (uvPos1, uvPos2), ...]
                where each index maps back to the uv positions. So uvPos0 -> uvPos1 would make up an edge.
        """
        faceVertCountList = self._mesh.GetFaceVertexCountsAttr().Get()
        faceVertexIndices = self._mesh.GetFaceVertexIndicesAttr().Get()
        uvPositions = primvar.Get()
        uvIndices = primvar.GetIndices()
        uvIndexMaps = [faceVertexIndices]
        if uvIndices:
            uvIndexMaps.append(uvIndices)
        edgeIndices = self._createUVEdges(faceVertCountList, uvIndexMaps)
        return [uvPositions, edgeIndices]

    @staticmethod
    def _createUVEdges(faceVertCountList, indexMaps):
        """Generate the uv edge indices from a given list of uv indices.

        Args:
            faceVertCountList list[int]:
                List of number of indices per face.
            indexMaps list[list[]]:
                List of index maps to map a given face vert id back to it's corresponding uv index.
        Returns:
            list[tuple(int, int)]:
                A list of tuples corresponding to an edges start and end index . e.g. [(uvPos0, uvPos1), (uvPos1, uvPos2), ...]
                where each index maps back to the uv positions. So uvPos0 -> uvPos1 would make up an edge.
        """
        edgeIndices = []
        consumedIndices = 0
        for faceVertCount in faceVertCountList:
            for i in range(faceVertCount):
                firstIndex = consumedIndices + i
                secondIndex = (
                    consumedIndices if i == (faceVertCount - 1) else firstIndex + 1
                )
                for indexMap in indexMaps:
                    firstIndex = indexMap[firstIndex]
                    secondIndex = indexMap[secondIndex]
                edgeIndices.append((firstIndex, secondIndex))
            consumedIndices += faceVertCount
        return edgeIndices

    @staticmethod
    def edgeBoundariesFromEdgeIndices(uvIndices):
        """Get the indices that make up the uv boundary edges.

        Args:
            uvIndices list[tuple(int, int)]:
                A list of tuples corresponding to an edges start and end index . e.g. [(uvPos0, uvPos1), (uvPos1, uvPos2), ...]
                where each index maps back to the uv positions. So uvPos0 -> uvPos1 would make up an edge.
        Returns:
            list[tuple(int, int)]:
                A list of tuples corresponding to start/end uv positions of boundary uv edges.
        """
        edgeCountMap = {}
        for uvEdge in uvIndices:
            edge = Edge(uvEdge[0], uvEdge[1])
            if edge in edgeCountMap:
                edgeCountMap[edge] += 1
            else:
                edgeCountMap[edge] = 1

        boundaryEdges = []
        for edge, count in edgeCountMap.items():
            if count == 1:
                boundaryEdges.append((edge.startIndex, edge.endIndex))
        return boundaryEdges

    # TEXTURE
    def textureData(self):
        """
        Get any texture file paths used as inputs to the surface shader
        on the meshes bound material.

        Returns:
            list[str]: A unique list of texture file absolute paths.
        """
        shader = self.meshShader()
        if shader is None:
            return []

        paths = []
        for path in self._getTexturesFromShader(shader):
            if path not in paths:
                paths.append(path)

        return paths

    def meshShader(self):
        """Get the shader used on the mesh if one exists.

        Returns:
            UsdShade.Shader | None: The shader if one exists, otherwise None.
        """
        if self._shader is None:
            prim = self.prim()
            binding = UsdShade.MaterialBindingAPI(prim)
            (material, _) = binding.ComputeBoundMaterial()
            if material:
                (shader, _, __) = material.ComputeSurfaceSource()
                if shader:
                    self._shader = shader
                else:
                    logger.debug("No surface shader for %s", prim)
            else:
                logger.debug("No material bound to %s", prim)
        return self._shader

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

    @classmethod
    def _getTexturesFromShader(cls, shader):
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


# UTILITIES
class Edge:
    def __init__(self, startIndex, endIndex):
        self.startIndex = min(startIndex, endIndex)
        self.endIndex = max(startIndex, endIndex)

    def __hash__(self):
        return hash((self.startIndex, self.endIndex))

    def __eq__(self, otherEdge):
        return (
            self.startIndex == otherEdge.startIndex
            and self.endIndex == otherEdge.endIndex
        )
