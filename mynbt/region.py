""" Region files are collections of NBT data packed in a single
    file. NBT data are prefixed by a table of content

    The file is logically divided in 4KiB sectors. Offset and
    length in the header are given in sectors, not bytes

    https://minecraft.gamepedia.com/Region_file_format
"""

from mmap import mmap, PROT_READ
from time import time
from struct import unpack
import zlib
import gzip
import io

from mynbt.nbt import TAG

PAGE_SIZE=4096
""" Page-size (in bytes) in the region file
"""

GLIB=b"\x01"
ZLIB=b"\x02"
COMPRESSOR = {
  GLIB: gzip.compress,
  ZLIB: zlib.compress,
}
DECOMPRESSOR = {
  GLIB: gzip.decompress,
  ZLIB: zlib.decompress,
}

def assert_in_range(x, start, end, msg="value"):
    if start <= x < end:
      return

    raise ValueError("{msg} must be in the [{start},{end}) range".format(msg=msg,start=start,end=end))

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

EmptyPage = bytes(PAGE_SIZE)
from collections import namedtuple
ChunkInfo = namedtuple('ChunkInfo', ['addr', 'size', 'timestamp', 'x', 'z', 'data'])
EmptyChunk = ChunkInfo(0,0,0,0,0,memoryview(EmptyPage[0:0]))

class Region:
    def __init__(self, data=bytes(2*PAGE_SIZE)):
      view = memoryview(data)
      locations=view[0:PAGE_SIZE].cast('i')
      timestamps=view[PAGE_SIZE:2*PAGE_SIZE].cast('i')

      self._chunks = [EmptyChunk]*1024

      for i in range(1024):
        location = int.from_bytes(locations[i:][:1], 'big')
        if location != 0:
            timestamp = int.from_bytes(timestamps[i:][:1], 'big')
            addr, size = location>>8,location&0xFF # Addr and size in 4KiB pages
            self._chunks[i] = ChunkInfo(addr, size, timestamp, *divmod(i,32), view[addr*PAGE_SIZE:][:size*PAGE_SIZE])

    def chunk_info(self, x, z):
      idx = z*32+x
      return self._chunks[idx]

    def parse_chunk(self, x, z):
      *_, mem = self.chunk_info(x,z)
      if mem is None:
        return None

      compression = mem[4:5]
      data = DECOMPRESSOR[compression](mem[5:])
      nbt, *_ = TAG.parse(data,0)
      return nbt

    def set_chunk(self, x, z, chunk, *, compression=ZLIB):
        assert_in_range(x, 0, 32, 'x')
        assert_in_range(z, 0, 32, 'z')

        chunk_info = self.chunk_info(x,z)
        
        data = io.BytesIO()
        chunk.write_to(data)
        dump = data.getbuffer()
        dump = COMPRESSOR[compression](dump)

        logical_size = len(dump)
        dump = logical_size.to_bytes(4, 'big') + compression + dump

        size = addr = -1
        timestamp = int(time())

        idx = z*32+x
        self._chunks[idx] = ChunkInfo(addr, size, timestamp, x, z, dump)

    def chunk(self, x, z):
      """ Return a context manager to modify and update a chunk from the region
      """
      return ChunkContextManager(self, x, z);

    def write_to(self, output, *, filter=lambda x,y:True):
        """ Write the current region file to the given output
            Output should support the 'write' operations
        """

        # walk over the chunk list to write the chunk offset and size in the file
        addr = 2
        for chunk in self._chunks:
            
            size = (len(chunk.data)+4095)//4096
            if size == 0:
                word = b"\x00\x00\x00\x00"
            else:
                word = ((addr<<8) | (size&0xFF)).to_bytes(4, 'big')
                addr += size

            output.write(word)

        # walk over the chunk list to write the timestamps
        for chunk in self._chunks:
            output.write(chunk.timestamp.to_bytes(4, 'big'))


        # walk over the chunk list to write the data
        for chunk in self._chunks:
            output.write(chunk.data)
            
            pad = len(chunk.data)%4096
            if pad > 0:
                output.write(EmptyPage[-pad:])

    @staticmethod
    def open(path):
      with open(path, 'rb') as f:
        map = mmap(f.fileno(), 0, prot=PROT_READ)

      return Region(map)
