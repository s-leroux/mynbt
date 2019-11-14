from mynbt.bitpack import unpack, UINT_16, INT_64

from pprint import pprint
from array import array

def idx2pos(idx):
    r,x = divmod(idx, 16)
    y,z = divmod(r, 16)

    return (x,y,z)

def pos2idx(x,y,z):
    return (y*16+z)*16+x

def block_state_index(palette, **blockstate):
    """ Returns the index in the palette of the given block state

        If the block state is not already in the palette it is
        added.
    """
    try:
        return palette.index(blockstate)
    except ValueError:
        palette.append(blockstate)
        return len(palette)-1

def blitter(src_palette, src_blocks, src_row_span, src_plane_span,
            dst_palette, dst_blocks, dst_row_span, dst_plane_span):
    """ Return a blitter function to copy blocks from src to dst
    """

    def _blit(src_start, dst_start, width, height, depth):
        # src_start and dst_start assumed to be (x,y,z) tuples
        src_base = src_start[1]*src_plane_span+src_start[2]*src_row_span+src_start[0]
        dst_base = dst_start[1]*dst_plane_span+dst_start[2]*dst_row_span+dst_start[0]

        map = []
        map_ext = [None]*10

        for y in range(height):
            src_idx = src_base
            dst_idx = dst_base
            src_base += src_plane_span
            dst_base += dst_plane_span
            for z in range(depth):
                for x in range(width):
                    blk = src_blocks[src_idx+x]
                    while blk > len(map):
                        map.extend(map_ext)

                    if map[blk] is None:
                        map[blk] = block_state_index(dst_palette, **src_palette[blk])

                    dst_blocks[dst_idx+x] = map[blk]

                src_idx += src_row_span
                dst_idx += dst_row_span

    return _blit


# ====================================================================
# Section
# ====================================================================
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

    @classmethod
    def copy(cls, section, rx, ry, rz):
        """ Create a partial copy of a section.

            Blocks that aren't copied are filled with "minecraft:air"
        """
        result = cls(section._cx,section._cy,section._cz)
        map = []
        def _copy(section, blocks, row, *args):
            for n in range(row.start, row.stop):
                blk = blocks[n]
                while blk > len(map):
                    map.extend([None]*10)

                if map[blk] is None:
                    map[blk] = result.block_state_index(**section._palette[blk])

                result._blocks[n] = map[blk]

        section.row_apply(_copy, rx,ry,rz)

        return result

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
        return block_state_index(self._palette, **blockstate)

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

    def fill(self, xrange=range(0,16), yrange=range(0,16), zrange=range(0,16), **blockstate):
        """ Fill a range of blocks
        """
        blk = self.block_state_index(**blockstate)
        seq = array(self._blocks.typecode, (blk for i in xrange))

        def fct(section, blocks, row, *args):
            blocks[row] = seq

        self.row_apply(fct, xrange, yrange, zrange)


