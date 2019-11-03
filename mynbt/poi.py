from mynbt.anvil import Anvil, ZLIB

class POI(Anvil):
    """ A POI file
    """
    def write_chunk(self, x, z, nbt, *, compression=ZLIB, timestamp=None):
        # adjust POI positions
        try:
            for section in nbt.Data.Sections.values():
                for record in section.Records:
                    ex = record.pos[0] % 32
                    ez = record.pos[2] % 32

                    record.pos[0] = ex + 32*x + 32*32*self._rx
                    record.pos[2] = ez + 32*z + 32*32*self._rz
        except KeyError:
            pass

        return super().write_chunk(x, z, nbt, timestamp=timestamp)

    def set_chunk(self, x, z, ci):
        nbt = self.parse_chunk_info(ci)
        return self.write_chunk(x, z, nbt, timestamp=ci.timestamp)


