hexdump_map_hex = tuple( format(i, '02x') for i in range(256) )
hexdump_map_txt = "".join(("."*32, *(chr(i) for i in range(32,127)), "."*129))

def hexdump(data):
    """ Produce an hex/ascii dump of the data
    """
    def _dumpline(line):
        pass

    data = memoryview(data)
    addr = 0
    while True:
        if not data:
            break

        line, data = data[:16], data[16:]

        hex = " ".join(hexdump_map_hex[b] for b in line)
        ascii = "".join(hexdump_map_txt[b] for b in line)

        yield "{:06x}    {:50s} |{:8s}|".format(addr, hex, ascii)
        addr += 16

