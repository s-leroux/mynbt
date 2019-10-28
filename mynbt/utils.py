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


def withsave(obj, writer, path, test=lambda : True):
    """ Make `obj` a context manager with auto-save
        on exit

        `obj` must have a `write_to(output)` method
    """
    class WithSave:
        def save(self):
            with writer(path, 'wb') as output:
                self.write_to(output)

        @property
        def filepath(self):
            return path

        def __enter__(self):
            return self

        def __exit__(self, exc_type, *args):
            if exc_type is None and test():
                self.save()

    cls = obj.__class__
    obj.__class__ = type(cls.__name__, (cls, WithSave), {})
    #
    #

    return obj

