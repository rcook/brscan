#!/usr/bin/env python
from __future__ import print_function
import string

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

def fetch(n, i):
    return [ next(i) for _ in xrange(n) ]

def fetch_str(n, i):
    return "".join(fetch(n, i))

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

def read(path):
    with open(path, "rb") as f:
        data = f.read()

    i = iter(data)

    h = fetch_header(i)
    print("file type: {}".format(h.file_type))

def main():
    read("DISKINF2.BR0")

if __name__ == "__main__":
    main()
