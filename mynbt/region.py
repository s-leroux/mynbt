from mynbt.anvil import Anvil, ZLIB

class Region(Anvil):
    """ A Region file
    """
    def write_chunk(self, x, z, nbt, *, compression=ZLIB, timestamp=None):
        data_rx, data_cx = divmod(nbt.xPos, 32)
        data_rz, data_cz = divmod(nbt.zPos, 32)

        nbt.xPos = 32*self._rx+x
        nbt.zPos = 32*self._rz+z

        try:
            for entity in nbt.Level.Entities:
                ex = entity.Pos[0] % 32
                ez = entity.Pos[2] % 32

                entity.Pos[0] = ex + 32*x + 32*32*self._rx
                entity.Pos[2] = ez + 32*z + 32*32*self._rz
        except KeyError:
            pass

        return super().write_chunk(x, z, nbt, timestamp=timestamp)

    def set_chunk(self, x, z, ci):
        nbt = self.parse_chunk_info(ci)
        return self.write_chunk(x, z, nbt, timestamp=ci.timestamp)

