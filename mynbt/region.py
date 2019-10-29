""" Region files are collections of NBT data packed in a single
    file. NBT data are prefixed by a table of content

    The file is logically divided in 4KiB sectors. Offset and
    length in the header are given in sectors, not bytes

    https://minecraft.gamepedia.com/Region_file_format
"""

from mmap import mmap, PROT_READ
from time import time
from struct import unpack
from array import array
from warnings import warn
from collections import namedtuple
import zlib
import gzip
import io
import itertools

from mynbt.nbt import TAG, EmptyChunkError
from mynbt.error import *
from mynbt.utils import hexdump, patch, withsave

PAGE_SIZE=4096
""" Page-size (in bytes) in the region file
"""

EMPTY_PAGE = bytes(PAGE_SIZE)
""" An page full of \x00 bytes
"""

ChunkInfo = namedtuple('ChunkInfo', ['addr', 'size', 'timestamp', 'x', 'z', 'data'])
def EMPTY_CHUNK(x,z):
    return ChunkInfo(None,None,0,x,z,EMPTY_PAGE[0:0])
EMPTY_CHUNKS = tuple(
    EMPTY_CHUNK(x,z) for z in range(32) for x in range(32)
)

#
# XXX Avoid module's global namespace polution by defining the
#     following constents in their own namespace (or in the Region class?)
#
NONE=b"\x00" # not found in official MC files
GLIB=b"\x01"
ZLIB=b"\x02"
COMPRESSOR = {
  NONE: lambda data : data,
  GLIB: gzip.compress,
  ZLIB: zlib.compress,
}
DECOMPRESSOR = {
  NONE: lambda data : data,
  GLIB: gzip.decompress,
  ZLIB: zlib.decompress,
}

# ====================================================================
# Errors
# ====================================================================
class RegionError(MyNBTError):
    """ Base class for all errors issued by the Region class
    """
    pass

class BadChunkError(RegionError):
    def __init__(self, region, chunk_info, msg="", **kwargs):
        self._chunk = chunk_info
        super().__init__(
            "Header for chunk ({x},{z}) in {region} does not seem valid:\n{msg}\n{dump}",
            x=chunk_info.x, z=chunk_info.z,
            region=region,msg=msg,
            dump="\n".join(hexdump(chunk_info.data, maxlines=10))
        )

class UnknownCompressionError(BadChunkError):
    def __init__(self, region, chunk_info, **kwargs):
        super().__init__(
            chunk_info=chunk_info,
            region=region,
            msg="Unknown compression code {code}".format(code=chunk_info.data[4:5].hex())
        )

class MissingDataError(BadChunkError):
    def __init__(self, region, chunk_info, **kwargs):
        super().__init__(
            chunk_info=chunk_info,
            region=region,
            msg="Chunck logical size greater than its physical size"
        )

# ====================================================================
# Warnings
# ====================================================================
class RegionWarning(MyNBTWarning):
    """ Base class for all warnings issued by the Region class
    """
    pass

class BadChunk(RegionWarning):
    def __init__(self, chunk_info, msg, **kwargs):
        self._chunk = chunk_info
        super().__init__(msg, **kwargs)

class BadChunkHeader(BadChunk):
    def __init__(self, chunk_info, **kwargs):
        data = chunk_info.data
        if len(data) < 5:
            msg = "Not enougth data ({:d} bytes)".format(len(data))
        else:
            length, compression, data = parse_chunk_header(data)
            msg = "Bad header for chunk ({x},{z}): length={length:d} compression={compression:d}".format(
              x=chunk_info.x,z=chunk_info.z,
              length=length,
              compression=compression[0]
            )

        super().__init__(
            chunk_info,
            msg,
        )

class ChunkDataInHeader(BadChunk):
    def __init__(self, chunk_info, **kwargs):
        super().__init__(
            chunk_info,
            "Data for chunk ({x},{z}) points to the header",
            x=chunk_info.x,z=chunk_info.z
        )

class MissingData(BadChunk):
    def __init__(self, chunk_info, **kwargs):
        super().__init__(
            chunk_info,
            "Missing data for chunk ({x},{z})",
            x=chunk_info.x,z=chunk_info.z
        )

class InconsistentLocation(BadChunk):
    def __init__(self, region, nbt, chunk_info, lloc, **kwargs):
        self._nbt = nbt
        ploc = (chunk_info.x, chunk_info.z)
        super().__init__(
            chunk_info,
            "Chunk {ploc} shouldn't contain data for chunk {lloc}",
            ploc=ploc,
            lloc=lloc,
            region=region
        )

class DuplicatePage(RegionWarning):
    def __init__(self, region, page, chunks, **kwargs):
        super().__init__(
            "Page {page} of {region} is used by multiple chunks: {chunks}",
            region=region,
            page=page,
            chunks=chunks
        )

# ====================================================================
# Utilities
# ====================================================================
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

def chunk_to_index(x, z):
    assert_in_range(x, 0, 32)
    assert_in_range(z, 0, 32)
    return 32*z+x

def parse_chunk_header(chunk_data):
    """ Return the various part of a chunk header.
        Do not perform any validation
    """
    return (
      int.from_bytes(chunk_data[:4], 'big'),
      chunk_data[4:5],
      chunk_data[5:]
    )

# ====================================================================
# Chunk
# ====================================================================
class Chunk:
    """ Act as proxy to a chunk
    """
    def __init__(self, region, x, z):
        self._region = region
        self._x = x
        self._z = z

    def __str__(self):
        return "Chunk({x},{z})".format(x=self.x, z=self.z)

    x = property(lambda self: self._x)
    z = property(lambda self: self._z)

    def parse(self):
        """ Parse the chuck and returns the corresponding
            NBT object wrapped in a context manager
            to update the chunk on exit
        """
        chunk = self
        nbt = self._region.parse_chunk(self._x, self._z)
        if not nbt:
            raise EmptyChunkError(self._region, self._x, self._z)

        old_version = nbt._version

        class ContextManager:
            def __getattr__(self, name):
                return getattr(nbt, name)

            def __setattr__(self, name, value):
                return setattr(nbt, name, value)

            def __str__(self):
                return str(nbt)

            def __enter__(self):
                return self

            def __exit__(self, exc_type, *args):
                if exc_type is None and nbt._version > old_version:
                    chunk.write(nbt)

        return ContextManager()

    def write(self, nbt):
        self._region.write_chunk(self._x, self._z, nbt)

    def kill(self):
        self._region.kill_chunk(self._x, self._z)

    # data = property(
    #   lambda self: self._region.get_chunk(self._x, self._z),
    #   lambda self, data: self._region.set_chunk(self._x, self._z, data)
    # )

# ====================================================================
# Region
# ====================================================================
class Region:
    def __init__(self, data=b"", *, name=None):
      """ Create a new region from binary data following the MC region format
          descibed in https://minecraft.gamepedia.com/Region_file_format.
      """
      self._name = name or super().__str__()
      self._bitmap = None
      self._issues = []
      self._version = 0

      # ensure the region file contains at least the 2-page header
      if len(data) < 2*PAGE_SIZE:
          data = (data + bytes(2*PAGE_SIZE))[:2*PAGE_SIZE]

      # This is the _logical_ page count. Not necessary the _physical_ page count
      self._pagecount = 2

      view = memoryview(data)
      locations=view[0:PAGE_SIZE].cast('i')
      timestamps=view[PAGE_SIZE:2*PAGE_SIZE].cast('i')

      self._chunks = list(EMPTY_CHUNKS)

      for i in range(1024):
        z, x = divmod(i, 32)
        assert self._chunks[i].x == x
        assert self._chunks[i].z == z
        location = int.from_bytes(locations[i:][:1], 'big')
        if location != 0:
            issues = []

            timestamp = int.from_bytes(timestamps[i:][:1], 'big')
            addr, size = location>>8,location&0xFF # Addr and size in 4KiB pages
            if addr < 2:
                issues.append(ChunkDataInHeader)

            data = view[addr*PAGE_SIZE:][:size*PAGE_SIZE]

            # Deal with missing data
            missing_data = size*PAGE_SIZE - len(data)
            if missing_data:
                issues.append(MissingData)
                data = bytes(data) + bytes(missing_data)

            self._pagecount = max(self._pagecount, addr+size)

            self._chunks[i] = ci = ChunkInfo(addr, size, timestamp, x, z, data)
            for issue in issues:
                self.track(issue(ci))

    def __str__(self):
        return self._name

    def invalidate(self):
        """ Invalidate cached data.
        """
        self._version += 1
        self._bitmap = None

    #------------------------------------
    # Issue management
    #------------------------------------
    def check(self):
        """ Run all diagnosis function
        """
        self.bitmap()

    def track(self, issue):
        """ Track an issue
        """
        self._issues.append(issue)
        #print(issue)
        warn(issue, stacklevel=2)

    def fix(self, max_attempts=5):
        """ (Try to) fix all tracked issues.
            Return a _new_ region object with the issues fixed
        """
        # XXX Issue fixing might be implemented using a modified
        #     visitor pattern in an itertion loop so each chunk
        #     is touched only once before rechecking for issues

        raise NotImplementedError

    #------------------------------------
    # Low level region access
    #------------------------------------
    def bitmap(self):
        """ Compute the file's page usage bitmap.
        """
        duplicate_pages = {}

        if self._bitmap is None:
            bitmap = [()]*self._pagecount
            for chunk in self._chunks:
                if chunk.addr is not None:
                    for n in range(chunk.addr, chunk.addr+chunk.size):
                        owners = bitmap[n] = (*bitmap[n], (chunk.x,chunk.z))
                        if len(owners) > 1:
                            duplicate_pages[n] = owners

            for n, chunks in duplicate_pages.items():
                self.track(DuplicatePage(self, n, chunks))

            self._bitmap = bitmap


        return self._bitmap

    def chunk_info(self, x, z):
        idx = chunk_to_index(x,z)
        return self._chunks[idx]

    def set_chunk_info(self, x, z, info):
        self.invalidate()
        idx = chunk_to_index(x,z)
        self._chunks[idx] = info

    #------------------------------------
    # Chunk management
    #------------------------------------
    def parse_chunk_header(self, chunk_info):
        """ Parse the chunk header, returning
            its logical size, suitable decompressor,
            and data to decompress
        """
        *_, mem = chunk_info
        length, compression, data = parse_chunk_header(chunk_info.data)

        if length == 0:
            return 0, None, b''

        if length > 256*PAGE_SIZE:
            # chunk max length is 1MiB
            raise BadChunkError(self, chunk_info)

        if length > len(data):
            # fix missing data
            mem = bytes(data).ljust(length)
            self.track(MissingData(chunk_info))

        try:
            return length, DECOMPRESSOR[compression], data[:length]
        except KeyError:
            raise UnknownCompressionError(self, chunk_info) from None

    def is_valid_chunk(self, chunk_info):
        """ Return true if the chunk header can be
            parsed.
            Exceptions re wrapped in a warning
        """
        try:
            length, *_ = self.parse_chunk_header(chunk_info)
            return length > 0
        except BadChunkError:
            self.track(BadChunkHeader(chunk_info))

    def parse_chunk(self, x, z):
      chunk_info = self.chunk_info(x,z)
      length, decompressor, data = self.parse_chunk_header(chunk_info)
      if length == 0:
          return None

      nbt, *_ = TAG.parse(decompressor(data))

      try:
          lx = nbt.Level.xPos
          lz = nbt.Level.zPos
          if (x,z) != (lx%32,lz%32):
            self.track(InconsistentLocation(self, nbt, chunk_info, (lx,lz)))

      except (AttributeError, KeyError):
          pass

      return nbt

    def write_chunk(self, x, z, nbt, *, compression=ZLIB):
        self.invalidate()

        assert_in_range(x, 0, 32, 'x')
        assert_in_range(z, 0, 32, 'z')

        chunk_info = self.chunk_info(x,z)

        data = io.BytesIO()
        nbt.write_to(data)
        dump = data.getbuffer()
        dump = COMPRESSOR[compression](dump)

        logical_size = len(dump)
        dump = logical_size.to_bytes(4, 'big') + compression + dump

        size = addr = None
        timestamp = int(time())

        idx = z*32+x
        self._chunks[idx] = ChunkInfo(addr, size, timestamp, x, z, dump)

    def get_chunk(self, x, z):
        """ Return the chunk raw data
        """
        return self.chunk_info(x,z).data

    def set_chunk(self, x, z, data, timestamp=None):
        """ Set chunk raw data.
            No validation is performed to check if
            the data are valid.
        """
        self.invalidate()
        timestamp = timestamp or int(time())

        idx = chunk_to_index(x,z)
        self._chunks[idx] = ci = ChunkInfo(None, None, timestamp, x, z, data)
        return ci

    def kill_chunk(self, x, z):
        """ Remove a chunk
        """
        self.set_chunk_info(x,z,EMPTY_CHUNK(x,z))

    def copy_chunk(self, from_x, from_z, to_x, to_z):
        """ Shorthand for set_chunk(...,get_chunk(...))
        """
        self.set_chunk(to_x, to_z, self.get_chunk(from_x, from_z))

    #------------------------------------
    # Chunk iterator & context manager
    #------------------------------------
    def chunk(self, x, z):
        return Chunk(self, x, z)

    def chunks(self, filter=lambda region, info : len(info.data) and region.is_valid_chunk(info)):
        for chunk in self._chunks:
            if filter(self, chunk):
                yield self.chunk(chunk.x, chunk.z)

    #------------------------------------
    # I/O
    #------------------------------------
    def write_to(self, output, *, filter=lambda x,y:True):
        """ Write the current region file to the given output
            Output should support the 'write' operations
        """

        # walk over the chunk list to write the chunk offset and size in the file
        addr = 2
        for chunk in self._chunks:

            size = (len(chunk.data)+PAGE_SIZE-1)//PAGE_SIZE
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

            pad = len(chunk.data)%PAGE_SIZE
            if pad > 0:
                output.write(EMPTY_PAGE[pad:])

    @staticmethod
    def fromFile(path):
      with open(path, 'rb') as f:
        map = f.read() # read into memory since we have issues when
                       # mmap'd backing files are modified
                       # (e.g: by another process of simply by using `save()`)

      result = Region(map, name=path)
      old_version = result._version
      patch(result, withsave(path, open, lambda: result._version > old_version))

      return result
