import os
import os.path
import glob

from mynbt.region import Region
from mynbt.section import Section
from mynbt.poi import POI
from mynbt.nbt import parse_file

# ====================================================================
# Constants
# ====================================================================
SAVES_FOLDER="saves"

# XXX The MINECRAFT_HOME default value should be platform dependent XXX
MINECRAFT_HOME=os.getenv("MINECRAFT_HOME") or os.path.join(os.path.expanduser("~"), ".minecraft")

# ====================================================================
# Locator
# ====================================================================
def Locator(dirname):
    return type('',(),dict(
        level=lambda : os.path.join(dirname, 'level.dat'),
        raids=lambda : os.path.join(dirname, 'data', 'raids.dat'),
        region=lambda rx, rz : os.path.join(dirname, 'region', 'r.{}.{}.mca'.format(rx,rz)),
        poi=lambda rx, rz : os.path.join(dirname, 'poi', 'r.{}.{}.mca'.format(rx,rz)),
        players=lambda : glob.glob(os.path.join(dirname, '*.dat'))
    ))

# ====================================================================
# Utilities
# ====================================================================
def partition(xrange, yrange, zrange):
    """ Split the given x/y/z ranges expressed in world coordinate system
        in region/chunk/section/range-in-section
    """
    x = _partition(xrange)
    y = _partition(yrange)
    z = _partition(zrange)

    result={}
    for rx,vx in x.items():
        for rz,vz in z.items():
            result[rx,rz] = chunks = {}
            for (cx, x_span) in vx:
                for (cz, z_span) in vz:
                    chunks[cx, cz] = [(cy, x_span,y_span,z_span) for ry,vy in y.items() for (cy, y_span) in vy]

    return result

def _partition(xrange):
    result = {}

    lx = xrange.stop-xrange.start
    if lx <= 0:
        return result

    cx, ix = divmod(xrange.start, 16)
    rx, cx = divmod(cx, 32)

    l = None

    while lx > 0:
        if l is None:
            l = result.setdefault(rx, [])
        l.append((cx, range(ix, min(ix+lx, 16))))
        lx -= 16-ix
        ix = 0
        if cx == 31:
            cx = 0
            rx += 1
            l = None
        else:
            cx += 1

    return result


# ====================================================================
# ChangeSet
# ====================================================================
class ChangeSet:
    """ Cache region so region files are not written after every
        single changes
    """

    def __init__(self, world):
        self._world = world
        self._cache = {}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        for region in self._cache.values():
            region.__exit__(*args)

    def region(self, rx, rz):
        try:
            result = self._cache[rx,rz]
        except KeyError:
            result = self._cache[rx,rz] = self._world.region(rx,rz, factory=Region.withCache())

        return result

    #------------------------------------
    # World modifications
    #------------------------------------
    def apply(self, fct, xrange, yrange, zrange, *args, **kwargs):
        """ Apply a function to an area of the world
        """
        for (rx, ry), chunks in partition(xrange, yrange, zrange).items():
            with self.region(rx, ry) as region:
                for (cx, cz), sections in chunks.items():
                    with region.chunk[cx,cz].parse() as nbt:
                        for cy, *span in sections:
                            section = nbt.section[cy]
                            fct(section, *span, *args, **kwargs)

    def fill(self, xrange, yrange, zrange, **block):
        """ Fill an area of the world
        """
        self.apply(Section.fill, xrange, yrange, zrange, **block)

# ====================================================================
# World
# ====================================================================
class World:
    def __init__(self, dirname):
        """ Handle the Minecraft world located at dirname
        """
        self._dirname = dirname
        self._locator = Locator(dirname)

    @staticmethod
    def fromSaveFolder(minecrafthome, worldname):
        """ Factory method to open a world from the `saves`
            folder of the given MC directory
        """
        return World(os.path.join(minecrafthome, SAVES_FOLDER, worldname))

    @staticmethod
    def fromStandardSaveFolder(worldname):
        """ Factory method to open a world from the `saves`
            folder of the Minecraft directory at the standard
            location
        """
        return World.fromSaveFolder(MINECRAFT_HOME, worldname)

    def region(self, rx, rz, factory=None):
        return Region.fromFile(rx, rz, self._locator.region(rx,rz), factory=factory)

    def poi(self, rx, rz):
        return POI.fromFile(rx, rz, self._locator.region(rx,rz))

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

        return self.region(rx,rz).chunk[cx,cz]

    def chunks(self, cx_range, cz_range):
        """ Iterator over the chunks in the range

            Region are kept in cache during iteration
        """

        raise NotImplementedError

    def block(self, x,y,z):
        """ Get the block at (x,y,z) in the world coordinate system.

            This is awfully inefficient if you need to retrieve many
            blocks.
        """
        cx, x = divmod(x, 16)
        cy, y = divmod(y, 16)
        cz, z = divmod(z, 16)

        return self.chunk(cx, cz).parse().section[cy].block(x,y,z)

    @property
    def editor(self):
        return ChangeSet(self)

    def players(self):
        """ Itertor over the player's data
        """
        for player in self._locator.players():
            with parse_file(player) as p:
                yield p

