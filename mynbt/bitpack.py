from array import array

""" Bit fields manipulation
"""

# ====================================================================
# Constants
# ====================================================================
UINT_SIZE={}
for fmt in "BHILQ":
    UINT_SIZE[array(fmt).itemsize] = fmt

UINT_8 = UINT_SIZE[1]
UINT_16 = UINT_SIZE[2]
UINT_32 = UINT_SIZE[4]
UINT_64 = UINT_SIZE[8]

UINT_FORMAT = 'X' + UINT_8*8 + UINT_16 *8 + UINT_32*16 + UINT_64*32

# ====================================================================
# Global functions
# ====================================================================
def unpack(nbits, size, data, dest=None):
    """ split data in nbits chunks

        data is an iterator on fixed size ints
    """
    if dest is None:
        try:
            fmt = UINT_FORMAT[nbits]
        except IndexError:
            raise OverflowError("Cannot pack/unpack {} bits wide data".format(nbits))

        dest = array(fmt)

    mask = (1<<nbits)-1
    umask = (1<<size)-1 # mask to avoid sign bit extension
    remaining = 0
    acc = 0
    for n in data:
        acc |= ((n&umask) << remaining)
        remaining += size

        while remaining >= nbits:
            dest.append(acc & mask)
            remaining -= nbits
            acc >>= nbits

    assert not acc, "unexpected trailing data {} [{} of {}]".format(bin(acc), remaining, nbits)

    return dest

def pack(nbits, size, data):
    """ join data in chunks of nbits
    """
    try:
        dest = array(UINT_FORMAT[nbits])
    except IndexError:
        raise OverflowError("Cannot pack/unpack {} bits wide data".format(nbits))

    busy = 0
    acc = 0
    mask = (1<<nbits)-1

    for n in data:
        acc |= (n<<busy)
        busy += size
        while busy >= nbits:
            dest.append(acc & mask)
            acc >>= nbits
            busy -= nbits

    assert not acc

    return dest
