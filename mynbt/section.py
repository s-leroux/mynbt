from mynbt.bitpack import unpack

class Section:
    def __init__(self, cx, cy, cz, palette, blocks):
        self._cx = cx
        self._cy = cy
        self._cz = cz
        self._palette = palette
        self._blocks = blocks

    @property
    def x(self):
        return self._cx

    @property
    def y(self):
        return self._cy

    @property
    def z(self):
        return self._cz

    @classmethod
    def fromNBT(cls, cx, cz, section):
        palette = section.get('Palette')
        blockstates = section.get('BlockStates')

        blocks = None
        # blocks = unpack(len(palette).bit_length(), 64, section['BlockStates'])

        return Section(cx, section.Y, cz, palette, blocks)



