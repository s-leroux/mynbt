""" Region files are collections of NBT data packed in a single
    file. NBT data are prefixed by a table of content

    The file is logically divided in 4KiB sectors. Offset and
    length in the header are given in sectors, not bytes

    https://minecraft.gamepedia.com/Region_file_format
"""

from mmap import mmap, PROT_READ

def bytes_to_chunk_addr(base, offset):
    # XXX should use memoryview to deal with the header.
    return dict(
      offset=4096*(base[offset]*256*256+base[offset+1]*256+base[offset+2]),
      size=4096*base[offset+3]
      )

class Region:
    def __init__(self, data):
      self._data = data

      self._header = {(n % 32, n // 32): bytes_to_chunk_addr(data, n*4) for n in range(1024)}
      for i in self._header.items():
        print(i)

    @staticmethod
    def open(path):
      with open(path, 'rb') as f:
        map = mmap(f.fileno(), 0, prot=PROT_READ)

      return Region(map)
