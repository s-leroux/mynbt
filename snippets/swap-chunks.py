""" This snippet demonstrate how to swap two chunks
    in a region
"""

import os.path
from mynbt.world import World

WORLD_NAME="My World"
REGION=(0,0)
A_CHUNK=(1,2)
B_CHUNK=(-1,-2)


with World.fromStandardSaveFolder(WORLD_NAME).region(*REGION) as region:
    # Pythonic swap:
    # >>> a,b = b,a
    region.chunk[*A_CHUNK], region.chunk[*B_CHUNK] = region.chunk[*B_CHUNK], region.chunk[*A_CHUNK]
