import os.path
from pprint import pprint

from mynbt.world import World
from mynbt.region import Region

REGION_X=0
REGION_Z=0
#REGION_FILE=os.path.join("test","data","region-r.{}.{}.mca".format(REGION_X, REGION_Z))
#region=Region.fromFile(REGION_X, REGION_Z, REGION_FILE)
WORLD_NAME="Demo"
REGION=(0,0)

region = World.fromStandardSaveFolder(WORLD_NAME).region(*REGION)
""" Print all entities (id and position) foud in the region file
"""
for chunk in region.chunks():
    with chunk.parse() as nbt:
        print(nbt.Level.xPos, nbt.Level.zPos)
        for entity in nbt.Level.Entities:
            print(entity.id, entity.Pos)
            pprint(entity.export())
