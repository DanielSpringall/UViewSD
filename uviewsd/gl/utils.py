# Copyright 2021 by Daniel Springall.
# This file is part of UViewSD, and is released under the "MIT License Agreement".
# Please see the LICENSE file that should have been included as part of this package.


class AABBox:
    def __init__(self, pos0, pos1):
        """Utility class for holding and expanding an axis aligned bounding box.

        Args:
            pos0 (tuple(float, float)):
                The first corner position to make up an aabbox.
            pos1 (tuple(float, float)):
                The second corner position to make up an aabbox.
        """
        self.xMin = min(pos0[0], pos1[0])
        self.xMax = max(pos0[0], pos1[0])
        self.yMin = min(pos0[1], pos1[1])
        self.yMax = max(pos0[1], pos1[1])

    def addPosition(self, pos):
        """Extend the bbox with a given position.

        Args:
            pos (tuple(float, float)):
                The x and y position value to add to the bbox.
        """
        if self.xMin > pos[0]:
            self.xMin = pos[0]
        elif self.xMax < pos[0]:
            self.xMax = pos[0]
        if self.yMin > pos[1]:
            self.yMin = pos[1]
        elif self.yMax < pos[1]:
            self.yMax = pos[1]

    def addAABBox(self, other):
        """Extend the bbox with another bbox.

        Args:
            other (AABBox):
                The bounding box to add to the current bounding box.
        """
        if self.xMin > other.xMin:
            self.xMin = other.xMin
        if self.xMax < other.xMax:
            self.xMax = other.xMax
        if self.yMin > other.yMin:
            self.yMin = other.yMin
        if self.yMax > other.yMax:
            self.yMax = other.yMax
