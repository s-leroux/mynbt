
# ==================================================================== 
# Useful macros & constants
# ====================================================================
NAME=lambda s: (len(s).to_bytes(2, 'big') + s.encode('utf8')).hex()
STRING=NAME

END = lambda : "00"
BYTE = lambda n: n.to_bytes(1, 'big').hex()
SHORT = lambda n: n.to_bytes(2, 'big').hex()
INT = lambda n: n.to_bytes(4, 'big').hex()
LONG = lambda n: n.to_bytes(8, 'big').hex()
FLOAT = lambda : ""
DOUBLE = lambda : ""
BYTE_ARRAY = lambda : ""
STRING = NAME
LIST = lambda : ""
COMPOUND = lambda : ""
INT_ARRAY = lambda : ""
LONG_ARRAY = lambda : ""

(
    END.ID,
    BYTE.ID,
    SHORT.ID,
    INT.ID,
    LONG.ID,
    FLOAT.ID,
    DOUBLE.ID,
    BYTE_ARRAY.ID,
    STRING.ID,
    LIST.ID,
    COMPOUND.ID,
    INT_ARRAY.ID,
    LONG_ARRAY.ID,
  ) = ("{:02x}".format(n) for n in range(13))

class FRAME:
  def __init__(self, *content):
      self.HEX = " ".join(str(c) for c in content)
      self.BYTES = bytes.fromhex(self.HEX)

  def __str__(self):
      return self.HEX

""" Small helper to avoid passing the frame name as a named parmeter
    after the value(s) which ws somewhat counter-intuitive
    
    Usage:
    WITH_NAME("Hello", STRING_FRAME)("World")

    equivalent to
    STRING_FRAME("World", name="Hello")
"""
def WITH_NAME(name, frame):
    return lambda *args : frame(*args, name=name)

# ==================================================================== 
# Atomic values
# ====================================================================
SOME_BYTE = FRAME(
  BYTE.ID,
  NAME("byteTest"),
  "7F"
)

BYTE_FRAME = lambda v, name="byteTest" : FRAME(
  BYTE.ID,
  NAME(name),
    BYTE(v)
)

SHORT_FRAME = lambda v, name="shortTest" : FRAME(
  SHORT.ID,
  NAME(name),
    SHORT(v)
)

INT_FRAME = lambda v, name = "intTest" : FRAME(
  INT.ID,
  NAME(name),
    INT(v)
)

LONG_FRAME = lambda v, name = "longTest" : FRAME(
  LONG.ID,
  NAME(name),
    LONG(v)
)

STRING_FRAME = lambda v, name = "stringTest" : FRAME(
  STRING.ID,
  NAME(name),
    STRING(v)
)

SOME_SHORT = SHORT_FRAME(32767)

# ==================================================================== 
# Compounds
# ====================================================================

COMPOUND_FRAME = lambda *frames, name="compoundTest" : FRAME(
  COMPOUND.ID,
  NAME(name),
    *frames,
  END()
)

SOME_COMPOUND = WITH_NAME("Comp", COMPOUND_FRAME)( 
  SOME_SHORT, SOME_BYTE,
)

SOME_NESTED_COMPOUND = WITH_NAME("Data", COMPOUND_FRAME)(
  SOME_SHORT, SOME_COMPOUND,
)

EMPTY_COMPOUND = WITH_NAME("Empty", COMPOUND_FRAME)()

# ==================================================================== 
# Arrays
# ====================================================================
BYTE_ARRAY_FRAME = lambda v, name = "byteArrayTest" : FRAME(
  BYTE_ARRAY.ID,
  NAME(name),
    INT(len(v)),
    *(BYTE(n) for n in v)
)

# There is currently no TAG_ShortArray
# SHORT_ARRAY_FRAME = lambda v, name = "shortArrayTest" : FRAME(
#   SHORT_ARRAY.ID,
#   NAME(name),
#     INT(len(v)),
#     *(SHORT(n) for n in v)
# )

INT_ARRAY_FRAME = lambda v, name = "intArrayTest" : FRAME(
  INT_ARRAY.ID,
  NAME(name),
    INT(len(v)),
    *(INT(n) for n in v)
)

LONG_ARRAY_FRAME = lambda v, name = "longArrayTest" : FRAME(
  LONG_ARRAY.ID,
  NAME(name),
    INT(len(v)),
    *(LONG(n) for n in v)
)

SOME_BYTE_ARRAY = BYTE_ARRAY_FRAME([1,2,3,4])

# ==================================================================== 
# Lists
# ====================================================================
LIST_FRAME = lambda t, data, name = "listTest" : FRAME(
  LIST.ID,
  NAME(name),
    t.ID,
    INT(len(data)),
    *(t(v) for v in data)
)
SOME_LIST = WITH_NAME("List", LIST_FRAME)(
    SHORT, [0,1,2,3]
)

