from array import array

""" Pack/unpack bit fields
"""

def idx2pos(idx):
    r,x = divmod(idx, 16)
    y,z = divmod(r, 16)

    return (x,y,z)

def pos2idx(x,y,z):
    return (y*16+z)*16+x

def unpack(nbits, size, data):
    """ split data in nbits chunks

        data is an iterator on fixed size ints
    """
    dest = array('H')

    mask = (1<<nbits)-1
    remaining = 0
    acc = 0
    for n in data:
        acc |= (n << remaining)
        remaining += size

        while remaining >= nbits:
            dest.append(acc & mask)
            remaining -= nbits
            acc >>= nbits

    if acc:
        print("Relicat: " + str(acc))

    return dest

