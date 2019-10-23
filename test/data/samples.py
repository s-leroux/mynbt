
# ==================================================================== 
# Useful macros & constants
# ====================================================================
NAME=lambda s: (len(s).to_bytes(2, 'big') + s.encode('utf8')).hex()
STRING=NAME
BYTE = lambda n: n.to_bytes(1, 'big').hex()
SHORT = lambda n: n.to_bytes(2, 'big').hex()
INT = lambda n: n.to_bytes(4, 'big').hex()
LONG = lambda n: n.to_bytes(8, 'big').hex()

class FRAME:
  def __init__(self, *content):
      self.HEX = " ".join(str(c) for c in content)
      self.BYTES = bytes.fromhex(self.HEX)

  def __str__(self):
      return self.HEX

class ID: (
    END,
    BYTE,
    SHORT,
    INT,
    LONG,
    FLOAT,
    DOUBLE,
    BYTE_ARRAY,
    STRING,
    LIST,
    COMPOUND,
    INT_ARRAY,
    LONG_ARRAY,
  ) = ("{:02x}".format(n) for n in range(13))

END=ID.END

# ==================================================================== 
# Atomic values
# ====================================================================
SOME_BYTE = FRAME(
  ID.BYTE,
  NAME("byteTest"),
  "7F"
)

BYTE_FRAME = lambda v, name="byteTest" : FRAME(
  ID.BYTE,
  NAME(name),
    BYTE(v)
)

SHORT_FRAME = lambda v, name="shortTest" : FRAME(
  ID.SHORT,
  NAME(name),
    SHORT(v)
)

INT_FRAME = lambda v, name = "intTest" : FRAME(
  ID.INT,
  NAME(name),
    INT(v)
)

LONG_FRAME = lambda v, name = "longTest" : FRAME(
  ID.LONG,
  NAME(name),
    LONG(v)
)

STRING_FRAME = lambda v, name = "stringTest" : FRAME(
  ID.STRING,
  NAME(name),
    STRING(v)
)

SOME_SHORT = SHORT_FRAME(32767)

# ==================================================================== 
# Compounds
# ====================================================================
SOME_COMPOUND = FRAME(
  ID.COMPOUND,
  NAME("Comp"),
    # payload
    SOME_SHORT,
    SOME_BYTE,
  END
)
SOME_NESTED_COMPOUND = FRAME(
  ID.COMPOUND,
  NAME("Data"),
    # payload
    SOME_SHORT,
    SOME_COMPOUND,
  END
)
EMPTY_COMPOUND = FRAME(
  ID.COMPOUND,
  NAME("Empty"),
  END
)

# ==================================================================== 
# Arrays
# ====================================================================
BYTE_ARRAY_FRAME = lambda v, name = "byteArrayTest" : FRAME(
  ID.BYTE_ARRAY,
  NAME(name),
    INT(len(v)),
    *(BYTE(n) for n in v)
)

# There is currently no TAG_ShortArray
# SHORT_ARRAY_FRAME = lambda v, name = "shortArrayTest" : FRAME(
#   ID.SHORT_ARRAY,
#   NAME(name),
#     INT(len(v)),
#     *(SHORT(n) for n in v)
# )

INT_ARRAY_FRAME = lambda v, name = "intArrayTest" : FRAME(
  ID.INT_ARRAY,
  NAME(name),
    INT(len(v)),
    *(INT(n) for n in v)
)

LONG_ARRAY_FRAME = lambda v, name = "longArrayTest" : FRAME(
  ID.LONG_ARRAY,
  NAME(name),
    INT(len(v)),
    *(LONG(n) for n in v)
)

SOME_BYTE_ARRAY = BYTE_ARRAY_FRAME([1,2,3,4])

# ==================================================================== 
# Lists
# ====================================================================
SOME_LIST = FRAME(
  ID.LIST,
  NAME("List"),
    ID.SHORT,                     # paylod tag id
    INT(4), # count
    SHORT(0),
    SHORT(1),
    SHORT(2),
    SHORT(3),
)

