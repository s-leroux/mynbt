import os.path
from pprint import pprint

from mynbt.region import Region

REGION_X=0
REGION_Z=0
REGION_FILE=os.path.join("test","data","region-r.{}.{}.mca".format(REGION_X, REGION_Z))
region=Region.fromFile(REGION_X, REGION_Z, REGION_FILE)

""" Print all entities (id and position) foud in the region file
"""
for chunk in region.chunks():
    with chunk.parse() as nbt:
        for entity in nbt.Level.Entities:
            print(entity.id, entity.Pos)    
