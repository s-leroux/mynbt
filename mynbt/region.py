from mynbt.anvil import Anvil

class Region(Anvil):
    """ A Region file
    """
    def __init__(self, rx, rz, data=b"", *, name=None):
        super().__init__(data, name=name)
        self._rx = rx
        self._rz = rz

    @classmethod
    def fromFile(cls, rx, rz, path):
        return super().fromFile(path, factory=lambda *args, **kwargs : Region(rx,rz,*args,**kwargs))

    def set_chunk(self, ci):
        nbt = self.parse_chunk_info(ci)

        data_rx, data_cx = divmod(nbt.xPos, 32)
        data_rz, data_cz = divmod(nbt.zPos, 32)

        nbt.xPos = 32*self._rx+ci.x
        nbt.zPos = 32*self._rz+ci.z

        return self.write_chunk(ci.x, ci.z, nbt, timestamp=ci.timestamp)

