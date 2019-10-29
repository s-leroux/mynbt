""" This snippet demonstrate how to swap two chunks
    in a region
"""
import sys
import os.path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))

from mynbt.world import World

WORLD_NAME="Demo"
REGION=(0,0)
A_CHUNK=(0,0)
B_CHUNK=(1,2)


with World.fromStandardSaveFolder(WORLD_NAME).region(*REGION) as region:
    # Pythonic swap:
    # >>> a,b = b,a
    region.chunk[A_CHUNK], region.chunk[B_CHUNK] = region.chunk[B_CHUNK], region.chunk[A_CHUNK]
