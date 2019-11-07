import os.path
from pprint import pprint

from mynbt.region import Region

REGION_X=-0
REGION_Z=-0
REGION_FILE=os.path.join("test","data","region-r.{}.{}.mca".format(REGION_X, REGION_Z))
region=Region.fromFile(REGION_X, REGION_Z, REGION_FILE)

# Get the first non-empty chunk in the region
for chunk in region.chunks():
    print("Chunk {},{} from {}:".format(chunk.x, chunk.z, REGION_FILE))
    pprint(chunk.parse().export())
