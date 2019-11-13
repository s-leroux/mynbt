from mynbt.anvil import Anvil, ZLIB

from mynbt.utils import patch
from mynbt.section import Section

#------------------------------------
# Region
#------------------------------------
class Region(Anvil):
    """ A Region file
    """
    def parse_chunk_info(self, chunk_info):
        nbt = super().parse_chunk_info(chunk_info)

        return nbt

    def write_chunk(self, x, z, nbt, *, compression=ZLIB, timestamp=None):
        data_rx, data_cx = divmod(nbt.Level.xPos, 32)
        data_rz, data_cz = divmod(nbt.Level.zPos, 32)

        # adjust region pos
        nbt.Level.xPos = 32*self._rx+x
        nbt.Level.zPos = 32*self._rz+z

        # adjust entity positions
        try:
            for entity in nbt.Level.Entities:
                ex = entity.Pos[0] % 16
                ez = entity.Pos[2] % 16

                entity.Pos[0] = ex + 16*x + 16*32*self._rx
                entity.Pos[2] = ez + 16*z + 16*32*self._rz
        except KeyError:
            pass

        # adjust tile entity positions
        try:
            for entity in nbt.Level.TileEntities:
                ex = entity.x % 16
                ez = entity.z % 16

                entity.x = ex + 16*x + 16*32*self._rx
                entity.z = ez + 16*z + 16*32*self._rz
        except KeyError:
            pass

        return super().write_chunk(x, z, nbt, timestamp=timestamp)

    def set_chunk(self, x, z, ci):
        nbt = self.parse_chunk_info(ci)
        return self.write_chunk(x, z, nbt, timestamp=ci.timestamp)

    @classmethod
    def withCache(cls):
        cache = {}
        class WithCache(cls):
            def parse_chunk_info(self, chunk_info):
                key = chunk_info.x, chunk_info.z
                try:
                    nbt, version = cache[key]

                    if nbt._version == version:
                        return nbt
                except KeyError:
                    pass

                nbt = super().parse_chunk_info(chunk_info)
                cache[key] = (nbt, nbt._version)

                return nbt

            def write_chunk(self, x, z, nbt, *, compression=ZLIB, timestamp=None):
                cache[x,z] = (nbt, nbt._version)
                return super().write_chunk(x,z,nbt,compression=compression, timestamp=timestamp)


        return WithCache

    class Chunk(Anvil.Chunk):
        def sections(self, filter=lambda section : True):
            level = self.nbt['Level']
            for section in level['Sections']:
                if filter(section):
                    yield Section.fromNBT(level.xPos, level.zPos, section)

        def section(self, y):
            try:
                return next(self.sections(filter=lambda section : section.Y == y))
            except StopIteration:
                return Section.new(self.nbt.Level.xPos, idx, self.nbt.Level.zPos)
