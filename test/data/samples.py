SOME_BYTE = "".join((
  "01",                     # tag
  "00 08", b"byteTest".hex(),   # name
  "7F"                      # value
))
SOME_SHORT = "".join((
  "02",                     # tag
  "00 09", b"shortTest".hex(),   # name
  "7F FF"                   # value
))
SOME_COMPOUND = "".join((
  "0A",                     # tag
  "00 04", b"Comp".hex(),   # name

  # payload
  SOME_SHORT,
  SOME_BYTE,
  "00"                      #end
))
SOME_NESTED_COMPOUND = "".join((
  "0A",                     # tag
  "00 04", b"Data".hex(),   # name

  # payload
  SOME_SHORT,
  SOME_COMPOUND,
  "00"                      #end
))
EMPTY_COMPOUND = "".join((
  "0A",                     # tag
  "00 05", b"Empty".hex(),  # name
  "00"                      #end
))
SOME_LIST = "".join((
  "09"
  "00 04", b"List".hex(),
  "02",                     # paylod tag id
  "00 00 00 04"             # count
  "00 00",
  "00 01",
  "00 02",
  "00 03",
))

