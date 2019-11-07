from array import array

""" Pack/unpack bit fields
"""
def unpack(nbits, size, data, dest=None):
    """ split data in nbits chunks

        data is an iterator on fixed size ints
    """
    if dest is None:
        dest = array('H')

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

_format = 'X' + 'B'*8 + 'H'*8 + 'L'*16 + 'Q'*32
assert len(_format) == 1+64

def pack(nbits, size, data):
    """ join data in chunks of nbits
    """
    dest = array(_format[nbits])
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
