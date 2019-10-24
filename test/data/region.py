import itertools

PAGE_SIZE=4096
EMPTY_PAGE=bytes(PAGE_SIZE)
EMPTY_HEADER=bytes(2*PAGE_SIZE)

def CHUNK(x, z, *, pageaddr, pagecount=None, timestamp=0, data):
    # pageaddr in page, not bytes!

    if pagecount is None:
        pagecount = (len(data)+PAGE_SIZE-1)//PAGE_SIZE

    idx = z*32+x

    # data = data.ljust(pagecount*PAGE_SIZE, b"\x00")

    return {
        idx*4: (pageaddr<<8|pagecount).to_bytes(4, 'big'),
        idx*4+PAGE_SIZE: timestamp.to_bytes(4, 'big'),
        pageaddr*PAGE_SIZE: data
    }

def CHUNK_DATA(data, *, length=None, compression=0):
    assert compression==0
    if length is None:
        length = len(data)

    return b"".join((
      length.to_bytes(4, 'big'),
      compression.to_bytes(1, 'big'),
      data,
    ))

def REGION(size_in_bytes, *chunks):
    region = bytearray(size_in_bytes)

    for offset, data in itertools.chain(*(chunk.items() for chunk in chunks)):
        end = offset+len(data)
        region[offset:end] = data

    assert len(region) == size_in_bytes
    return bytes(region)

EMPTY_REGION = REGION(2*PAGE_SIZE)



