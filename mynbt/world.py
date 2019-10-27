import os.path

# ====================================================================
# Locator
# ====================================================================
def Locator(dirname):
    STANDARD_FILES=dict(
        level='level.dat',
        poi='poi.dat',
    )

    T = type('',(),{})
    for name, file in STANDARD_FILES.items():
        setattr(T, name, (lambda d, f : property(lambda self : os.path.join(d, f)))(dirname, file))

    return T()
