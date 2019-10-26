hexdump_map_hex = tuple( format(i, '02x') for i in range(256) )
hexdump_map_txt = "".join(("."*32, *(chr(i) for i in range(32,127)), "."*129))

def hexdump(data, maxlines=-1, compact=True):
    """ Produce an hex/ascii dump of the data
    """
    def _dumpline(line):
        pass

    data = memoryview(data)
    addr = 0
    previous = ""
    starred = False
    while maxlines != 0:
        if not data:
            if starred:
                yield previous
            break

        line, data = data[:16], data[16:]

        hex = " ".join(hexdump_map_hex[b] for b in line)
        ascii = "".join(hexdump_map_txt[b] for b in line)

        line = "{:06x}    {:50s} |{:8s}|".format(addr, hex, ascii)
        if not compact or maxlines==1:
            yield line
        else:
            if line[6:] == previous[6:]:
                if not starred:
                    starred = True
                    yield '*'
            else:
                if starred and previous:
                    yield previous

                starred = False
                yield line

        previous = line
        maxlines -= 1
        addr += 16

