#!/usr/bin/env python
from __future__ import print_function
import string
import struct

DUMP_COLUMN_WIDTH = 16
HEADER_SIZE = 48
SUPPORTED_VERSION = "Ver1.00BR-900"
SUPPORTED_FILE_TYPES = ["DISKINFO"]

class FormatError(Exception):
    pass

class Header(object):
    def __init__(self, file_type):
        self.__file_type = file_type

    @property
    def file_type(self): return self.__file_type

class DISKINFO(object):
    def __init__(self, song_count):
        self.__song_count = song_count

    @property
    def song_count(self): return self.__song_count

def dump_line(n, idx, data):
    print("{0:08x}  ".format(idx), end="")
    s = ""
    for j in xrange(DUMP_COLUMN_WIDTH):
        i = idx + j
        if i >= n:
            print("   ", end="")
        else:
            c = data[i]
            print("{0:02x} ".format(ord(c)), end="")
            if c in string.printable:
                s += c
            else:
                s += "."
    print(" |{}|".format(s))

def dump(label, data):
    print("===== BEGIN {}".format(label))
    n = len(data)
    idx = 0
    for i in xrange(n // DUMP_COLUMN_WIDTH):
        dump_line(n, idx, data)
        idx += DUMP_COLUMN_WIDTH
    if n % DUMP_COLUMN_WIDTH > 0:
        dump_line(n, idx, data)
    print("===== END {}".format(label))

def assert_at_end(i):
    try:
        next(i)
        raise FormatError("Expected end of file")
    except StopIteration:
        pass

def fetch_byte(i):
    return struct.unpack("<B", next(i))[0]

def fetch_16u(i):
    b0 = fetch_byte(i)
    b1 = fetch_byte(i)
    return (b0 << 8) + b1

def fetch_byte_string(n, i):
    return [ next(i) for _ in xrange(n) ]

def fetch_str(n, i):
    return "".join(fetch_byte_string(n, i))

def fetch_header(i):
    tags = fetch_str(HEADER_SIZE, i).strip().split(" ")
    if len(tags) != 5:
        raise FormatError("Invalid header")
    tag0, tag1, tag2, tag3, tag4 = tags
    if tag0 != "BOSS" or tag1 != "BR0" or tag2 != "Format":
        raise FormatError("Invalid header")
    if tag4 != SUPPORTED_VERSION:
        raise FormatError("Unsupported version {}".format(tag4))
    if tag3 not in SUPPORTED_FILE_TYPES:
        raise FormatError("Unsupported file type {}".format(tag3))
    return Header(tag3)

def fetch_DISKINFO(i):
    n0 = int(fetch_str(4, i))
    n1 = fetch_16u(i)
    if n1 != n0 + 1:
        raise FormatError("Inconsistent song counts in DISKINFO {} vs {}".format(n0, n1))
    if fetch_byte(i) != 0 or fetch_byte(i) != 0:
        raise FormatError("Unexpected trailing bytes in DISKINFO")
    assert_at_end(i)
    return DISKINFO(n0)

def read(path):
    with open(path, "rb") as f:
        data = f.read()

    i = iter(data)

    h = fetch_header(i)
    if h.file_type == "DISKINFO":
        disk_info = fetch_DISKINFO(i)
        print("DISKINFO: song_count={}".format(disk_info.song_count))
    else:
        raise RuntimeError("Not implemented")

def main():
    read("DISKINF2.BR0")

if __name__ == "__main__":
    main()
