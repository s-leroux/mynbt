from mynbt.anvil import Anvil, ZLIB

class Region(Anvil):
    """ A Region file
    """
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

