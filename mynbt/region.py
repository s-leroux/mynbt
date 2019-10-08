""" Region files are collections of NBT data packed in a single
    file. NBT data are prefixed by a table of content

    The file is logically divided in 4KiB sectors. Offset and
    length in the header are given in sectors, not bytes

    https://minecraft.gamepedia.com/Region_file_format
"""

from mmap import mmap, PROT_READ
from struct import unpack
import zlib
import gzip

from mynbt.nbt import TAG

def bytes_to_chunk_addr(base, offset):
    # XXX should use memoryview to deal with the header.
    return (
      4096*(base[offset]*256*256+base[offset+1]*256+base[offset+2]),
      4096*base[offset+3]
      )

class Region:
    def __init__(self, data):
      self._data = data
      view = memoryview(data)
      self._locations=view[0:4096]
      self._timestamps=view[4096:8192]

      self._header_cache = {}

    def chunk_info(self, x, z):
      key = (x,z)
      result = self._header_cache.get(key, None)
      if result is None:
        idx = 4*((x & 31) + (z & 31) * 32)
        offset, size = bytes_to_chunk_addr(self._locations, idx)
        timestamp = (lambda b : (b[idx]<<24) + (b[idx+1]<<16) + (b[idx+2]<<8) + b[idx+3])(self._timestamps)

        result = (offset, size, timestamp, memoryview(self._data)[offset:][:size])
        self._header_cache[key] = result

      return result

    def chunk(self, x, z):
      _, _, _, mem = self.chunk_info(x,z)

      decompressor = {
        1: gzip.decompress,
        2: zlib.decompress,
      }
      compression = mem[4]
      data = decompressor[compression](mem[5:])
      nbt, *_ = TAG.parse(data,0)
      return nbt
      

    @staticmethod
    def open(path):
      with open(path, 'rb') as f:
        map = mmap(f.fileno(), 0, prot=PROT_READ)

      return Region(map)
