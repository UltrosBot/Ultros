__author__ = 'Sean'

def decode_varint(data, pos=0):
    first = ord(data[pos])
    if (first & 0x80) == 0x00:
        return (first & 0x7F), 1
    elif (first & 0xC0) == 0x80:
        return (first & 0x4F) << 8 | ord(data[pos + 1]), 2
    elif (first & 0xF0) == 0xF0:
        if (first & 0xFC) == 0xF0:
            return (ord(data[pos + 1]) << 24 | ord(data[pos + 2]) << 16 | ord(
                data[pos + 3]) << 8 | ord(data[pos + 4]), 5)
        elif (first & 0xFC) == 0xF4:
            return (ord(data[pos + 1]) << 56 | ord(data[pos + 2]) << 48 | ord(
                    data[pos + 3]) << 40 | ord(data[pos + 4]) << 32 | ord(
                    data[pos + 5]) << 24 | ord(data[pos + 6]) << 16 | ord(
                    data[pos + 7]) << 8 | ord(data[pos + 8]), 9)
        elif (first & 0xFC) == 0xF8:
            result, length = decode_varint(data, pos + 1)
            return -result, length + 1
        elif (first & 0xFC) == 0xFC:
            return -(first & 0x03), 1
        else:
            raise ValueError("Invalid VarInt data")
    elif (first & 0xF0) == 0xE0:
        return (
        (first & 0x0F) << 24 | ord(data[pos + 1]) << 16 | ord(data[pos + 2]) << 8 | ord(
            data[pos + 3]), 4)
    elif (first & 0xE0) == 0xC0:
        return (first & 0x1F) << 16 | ord(data[pos + 1]) << 8 | ord(data[pos + 2]), 3
    else:
        raise ValueError("Invalid VarInt data")
