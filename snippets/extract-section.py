import os.path
from pprint import pprint

from mynbt.region import Region

REGION_X=0
REGION_Z=0
REGION_FILE=os.path.join("test","data","simplechunk-r.{}.{}.mca".format(REGION_X, REGION_Z))
region=Region.fromFile(REGION_X, REGION_Z, REGION_FILE)

# Get the first non-empty chunk in the region
chunk = next(region.chunks())
nbt = chunk.parse()
for section in nbt.Level.Sections:
    if section.Y == 5:
        section = section.export()
        d = {k: section[k] for k in ('Palette', 'BlockStates', 'Y')}
        pprint(d)

