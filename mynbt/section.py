from mynbt.bitpack import unpack

from pprint import pprint
from array import array

def idx2pos(idx):
    r,x = divmod(idx, 16)
    y,z = divmod(r, 16)

    return (x,y,z)

def pos2idx(x,y,z):
    return (y*16+z)*16+x

class Section:
    def __init__(self, cx, cy, cz, palette, blocks):
        if palette == []:
            palette=[dict(Name="minecraft:air")]
        if not len(blocks):
            blocks = array(blocks.typecode, (0 for i in range(4096)))

        self._cx = cx
        self._cy = cy
        self._cz = cz
        self._palette = palette
        self._blocks = blocks

        assert len(blocks) == 4096

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
        palette = section.get('Palette', {})
        blockstates = section.get('BlockStates', [])

        blocks = unpack(max(4,(len(palette)-1).bit_length()), 64, blockstates)

        return Section(cx, section['Y'], cz, palette, blocks)

    def block(self, x,y,z):
        """ Get block at (x,y,z) in section's coordinates
        """
        assert 0 <= x < 16
        assert 0 <= y < 16
        assert 0 <= z < 16

        block = self._blocks[pos2idx(x,y,z)]
        return self._palette[block]

    def fill(self, xrange, yrange, zrange, **blockstate):
        """ Fill a range of blocks
        """
        blk = self.block_state_index(**blockstate)
        base = pos2idx(xrange.start, yrange.start, zrange.start)
        
        seq = array(self._blocks.typecode, (blk for i in xrange))

        for z in zrange:
            idx = base
            base += 256
            for y in yrange:
                self._blocks[idx:idx+len(xrange)] = seq
                idx += 16

    def block_state_index(self, **blockstate):
        """ Returns the index in the palette of the given block state
        
            If the block state is not already in the palette it is
            added.
        """
        try:
            return self._palette.index(blockstate)
        except ValueError:
            self._palette.append(blockstate)
            return len(self._palette)-1
