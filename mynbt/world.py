import os.path
import glob

from mynbt.region import Region
from mynbt.nbt import TAG

# ====================================================================
# Locator
# ====================================================================
def Locator(dirname):
    return type('',(),dict(
        level=lambda : os.path.join(dirname, 'level.dat'),
        raids=lambda : os.path.join(dirname, 'data', 'raids.dat'),
        region=lambda rx, rz : os.path.join(dirname, 'region', 'r.{}.{}.mca'.format(rx,rz)),
        players=lambda : glob.glob(os.path.join(dirname, '*.dat'))
    ))

# ====================================================================
# World
# ====================================================================
class World:
    def __init__(self, dirname):
        """ Handle the Minecraft world located at dirname
        """
        self._dirname = dirname
        self._locator = Locator(dirname)

    def region(self, rx, rz):
        return Region.fromFile(self._locator.region(rx,rz))

    def chunk(self, cx, cz):
        """ Get a chunk

            cx and cy are the chunk position in the world coordinate system

            This method makes no assumption regarding a possible modification
            of the region file, so the region is re-opened at each invocation.
            For efficiency, World.region() should be prefered when retrieving
            several chunks from the same region
        """
        rx,cx = divmod(cx,32)
        rz,cz = divmod(cz,32)

        return self.region(rx,rz).chunk(cx,cz)

    def chunks(self, cx_range, cz_range):
        """ Iterator over the chunks in the range

            Region are kept in cache during iteration
        """

        raise NotImplementedError

    def players(self):
        """ Itertor over the player's data
        """
        for player in self._locator.players():
            with TAG.parse_file(player) as p:
                yield p
