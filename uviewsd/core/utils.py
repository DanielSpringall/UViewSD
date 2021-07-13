# Copyright 2021 by Daniel Springall.
# This file is part of UViewSD, and is released under the "MIT License Agreement".
# Please see the LICENSE file that should have been included as part of this package.


class Edge:
    def __init__(self, startIndex, endIndex):
        """Utility class for edge comparison."""
        self.startIndex = min(startIndex, endIndex)
        self.endIndex = max(startIndex, endIndex)

    def indices(self):
        return (self.startIndex, self.endIndex)

    def __hash__(self):
        return hash((self.startIndex, self.endIndex))

    def __eq__(self, otherEdge):
        return (
            self.startIndex == otherEdge.startIndex
            and self.endIndex == otherEdge.endIndex
        )
