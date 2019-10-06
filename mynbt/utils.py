def rslice(base, start, stop):
    return Slice(base, start, stop)

class Slice:
    def __init__(self, base, start, stop):
        if start is None:
            start = 0
        elif start < 0:
            start += len(base)
        if stop is None:
            stop = len(base)
        elif stop < 0:
            stop += len(base)

        if stop > len(base):
            stop = len(base)

        if start > stop:
            start = stop

        self.base = base
        self.start = start
        self.stop = stop

    def __repr__(self):
        return "Slice({base},{start},{stop})".format(**self.__dict__)

    def __len__(self):
        return self.stop-self.start

    def __eq__(self,other):
        if type(other) is Slice:
            other = [*other]

        if type(other) is list:
            return [*self] == other

        return super().__eq__(other)

    def __getitem__(self,idx):
        if type(idx) is int:
            idx += self.start if idx >= 0 else self.stop
            if idx >= self.stop or idx < self.start:
                raise IndexError
            
            return self.base[idx]
        elif type(idx) is slice:
            if idx.step is not None:
                raise TypeError("step slices are not supported")
            istart = 0 if idx.start is None else idx.start
            istop = self.stop if idx.stop is None else idx.stop
            return Slice(self.base,
                    istart + (self.start if istart >= 0 else self.stop),
                    istop + (self.start if istop >= 0 else self.stop))
                        

