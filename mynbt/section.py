from mynbt.bitpack import unpack, UINT_16, INT_64

from pprint import pprint
from array import array

def idx2pos(idx):
    r,x = divmod(idx, 16)
    y,z = divmod(r, 16)

    return (x,y,z)

def pos2idx(x,y,z):
    return (y*16+z)*16+x

class Section:
    #------------------------------------
    # Ctor / Factories
    #------------------------------------
    def __init__(self, cx, cy, cz, palette=None, blocks=None):
        if not palette:
            palette=[dict(Name="minecraft:air")]
        if not blocks:
            blocks = array(UINT_16, (0 for i in range(4096)))

        self._cx = cx
        self._cy = cy
        self._cz = cz
        self._palette = palette
        self._blocks = blocks

        assert len(blocks) == 4096

    @classmethod
    def fromNBT(cls, cx, cz, section):
        palette = section.get('Palette')
        if not palette:
            section['Palette'] = dict(Name="minecraft:air")
            palette = section['Palette']

        nbits = lambda : max(4,(len(palette)-1).bit_length())

        blockstate = section.get('BlockStates')
        if not blockstate:
            section['BlockState'] = array(INT_64, (0 for x in range(16*16*16*nbits()//64)))
            blockstate = section['BlockState']

        blockstate.reshape(nbits)
        return cls(cx, section['Y'], cz, palette, blockstate)

    @classmethod
    def new(cls, cx, cy, cz):
        return cls(cx, cy, cz)

    #------------------------------------
    # String conversion
    #------------------------------------
    def __repr__(self):
        return "Section({_cx},{_cy},{_cz},{_palette},{_blocks})".format(**vars(self))

    def __str__(self):
        return "Section({_cx},{_cy},{_cz})".format(**vars(self))

    #------------------------------------
    # Utilities
    #------------------------------------
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

    #------------------------------------
    # Properties
    #------------------------------------
    @property
    def x(self):
        return self._cx

    @property
    def y(self):
        return self._cy

    @property
    def z(self):
        return self._cz

    @property
    def width(self):
        return 16

    @property
    def height(self):
        return 16

    @property
    def depth(self):
        return 16

    #------------------------------------
    # Block access
    #------------------------------------
    def block(self, x,y,z):
        """ Get block at (x,y,z) in section's coordinates
        """
        assert 0 <= x < 16
        assert 0 <= y < 16
        assert 0 <= z < 16

        block = self._blocks[pos2idx(x,y,z)]
        return self._palette[block]

    def __setitem__(self, idx, blk):
        x,y,z = idx

        self.fill(range(x,x+1),range(y,y+1),range(z,z+1), **blk)

    def xz_plane(self, y):
        """ Return a 2D array representing the xz plane at height y

            Mostly for testing purposes
        """
        result = []
        base = pos2idx(0, y, 0)
        depth = self.depth
        width = self.width
        for z in range(0, depth):
            result.append([x for x in self._blocks[base:base+width]])
            base += width

        return result

    #------------------------------------
    # World modifications
    #------------------------------------
    def row_apply(self, fct, xrange, yrange, zrange):
        """ Apply a function to each x-row of the range

            `fct` is a callable with the signature `fct(section, block, slice, y, z)`
            `block[slice]` is the section of a row where the function
            should apply.
        """
        base = pos2idx(xrange.start, yrange.start, zrange.start)

        row_size = self.width
        plane_size = self.depth*row_size
        blocks = self._blocks

        for y in yrange:
            idx = base
            base += plane_size
            for z in zrange:
                fct(self, blocks, slice(idx,idx+len(xrange)), y, z)
                idx += row_size

    def fill(self, xrange, yrange, zrange, **blockstate):
        """ Fill a range of blocks
        """
        blk = self.block_state_index(**blockstate)
        seq = array(self._blocks.typecode, (blk for i in xrange))

        def fct(section, blocks, row, *args):
            blocks[row] = seq

        self.row_apply(fct, xrange, yrange, zrange)


