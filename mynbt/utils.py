hexdump_map = "".join(("."*32, *(chr(i) for i in range(32,127)), "."*129))

def hexdump(data):
    """ Produce a canonical hex/ascii dump of the data
    """
    def _dumpline(line):
        pass

    data = memoryview(data)
    addr = 0
    while True:
        if not data:
            break

        line, data = data[:16], data[16:]

        h = line.hex()
        hex = " ".join(a+b for a,b in zip(h[::2],h[1::2]))
        ascii = "".join(hexdump_map[b] for b in line)

        yield "{:06x}    {:50s} |{:8s}|".format(addr, hex, ascii)
        addr += 16


for line in hexdump(bytes(range(256))):
    print(line)
