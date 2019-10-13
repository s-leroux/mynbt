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
import io

from mynbt.nbt import TAG

PAGE=4096
""" Page-size (in bytes) in the region file
"""

def bytes_to_chunk_addr(base, offset):
    # XXX should use memoryview to deal with the header.
    return (
      base[offset]*256*256+base[offset+1]*256+base[offset+2],
      base[offset+3]
      )

class ChunkContextManager:
    def __init__(self, region, x, z):
        self._region = region
        self._x = x
        self._z = z

    def __enter__(self):
        self._chunk = self._region.parse_chunk(self._x, self._z)
        return self._chunk

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            self._region.set_chunk(self._x, self._z, self._chunk) 

class Region:
    def __init__(self, data=bytes(2*PAGE)):
      self._data = data
      view = memoryview(data)
      self._locations=view[0:PAGE].cast('i')
      self._timestamps=view[PAGE:2*PAGE].cast('i')
      self._header_cache = {}
      self._eof = len(data)

    def chunk_info(self, x, z):
      key = (x,z)
      result = self._header_cache.get(key, None)
      if result is None:
        idx = 4*((x & 31) + (z & 31) * 32)
        addr = int.from_bytes(self._locations[idx:idx+1], 'big')
        addr, size = addr>>8,addr&0xFF # Addr and size in 4KiB pages
        timestamp = self._timestamps[idx]
        buffer = memoryview(self._data)[PAGE*addr:][:PAGE*size] if addr and size else None
        
        result = (addr, size, timestamp, buffer)
        # XXX should sanitize the result in case of addr or addr+size beyond the end of file
        self._header_cache[key] = result

      return result

    def parse_chunk(self, x, z):
      _, _, _, mem = self.chunk_info(x,z)
      if mem is None:
        return None

      decompressor = {
        1: gzip.decompress,
        2: zlib.decompress,
      }
      compression = mem[4]
      data = decompressor[compression](mem[5:])
      nbt, *_ = TAG.parse(data,0)
      return nbt

    def set_chunk(self, x, z, chunk):
        chunk_info = self.chunk_info(x,z)
        
        data = io.BytesIO()
        data.write(
          b'\x00\x00\x00\x00'     # chunk length placeholder
          b'\x02'                 # compression format
        )
        chunk.write(data)
        dump = data.getbuffer()

        logical_size = len(dump)-5
        dump[:4] = logical_size.to_bytes(4, 'big')

        physical_size = (logical_size+5+PAGE-1)//PAGE
        if physical_size > chunk_info[1]:
            # not enought room available; append the item at the end of the file
            addr = (self._eof+PAGE-1)//PAGE # ensure we are at a page boundary. This should be the case unless the file was damaged
            self._eof += physical_size*PAGE
        else:
            addr = chunk_info[0]

        timestamp = chunk_info[3]

        chunk_info = (addr, physical_size, timestamp, dump)

    def chunk(self, x, z):
      """ Return a context manager to modify and update a chunk from the region
      """
      return ChunkContextManager(self, x, z);

    def write_to(self, output, *, filter=lambda x,y:True):
        """ Write the current region file to the given output
            Output should support the 'write' and 'seek' operations
        """
        # Copy headers
        header1=memoryview(bytearray(self._locations))
        header2=memoryview(bytearray(self._timestamps))
        
        # Overwrite header data with cached chunk infos
        for (x,y), info in self._header_cache.item():
            idx = 4*((x & 31) + (z & 31) * 32)
            header1[4*idx:][:4] = (((info[0]//4096)<<8)|((info[1]//4096)&0xFF)).to_bytes(4,'big')
            header2[4*idx:][:4] = int(time.time()).to_bytes(4, 'big')

    @staticmethod
    def open(path):
      with open(path, 'rb') as f:
        map = mmap(f.fileno(), 0, prot=PROT_READ)

      return Region(map)
