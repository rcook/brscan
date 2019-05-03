#!/usr/bin/env python
from __future__ import print_function
import argparse
import string
import struct
import sys

DUMP_COLUMN_WIDTH = 16
HEADER_SIZE = 48
HEADER_PREFIX = "BOSS BR0 Format "
HEADER_SUFFIX = "Ver1.00BR-900" + (" " * 10)

class DiskInfoParser(object):
    def parse(self, file_type, i):
        song_count0 = int(fetch_str(4, i))
        song_count1 = fetch_16u(i)
        if song_count1 != song_count0 + 1:
            raise FormatError("Inconsistent song counts in DISKINFO {} vs {}".format(song_count0, song_count1))
        if fetch_byte(i) != 0 or fetch_byte(i) != 0:
            raise FormatError("Unexpected trailing bytes in DISKINFO")
        assert_at_end(i)
        return DiskInfo(song_count0)

class SongInfoParser(object):
    def parse(self, file_type, i):
        song_name = ""
        while True:
            c = next(i)
            if c == "\0": break
            song_name += c
        return SongInfo(song_name)

class DummyParser(object):
    def parse(self, file_type, i):
        return Dummy(file_type)

PARSERS = {
    "DISKINFO": DiskInfoParser,
    "SONGINFO2": SongInfoParser
}
DUMMIES = [
    "ARRANGE",
    "DRUMKIT",
    "EFFECTS",
    "TAKE_EVT",
    "PATTERN",
    "PITCHMAP"
]
for d in DUMMIES:
    PARSERS[d] = DummyParser

class FormatError(Exception):
    pass

class Header(object):
    def __init__(self, file_type, parser):
        self.__file_type = file_type
        self.__parser = parser

    @property
    def file_type(self): return self.__file_type

    def parse(self, i):
        return self.__parser().parse(self.__file_type, i)

class DiskInfo(object):
    def __init__(self, song_count):
        self.__song_count = song_count

    def dump(self):
        print("DISKINFO: song_count={}".format(self.__song_count))

class SongInfo(object):
    def __init__(self, song_name):
        self.__song_name = song_name

    def dump(self):
        print("SONGINFO: song_name={}".format(self.__song_name))

class Dummy(object):
    def __init__(self, file_type):
        self.__file_type = file_type

    def dump(self):
        print("{}: (unimplemented)".format(self.__file_type))

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
    header_str = fetch_str(HEADER_SIZE, i)
    if not header_str.startswith(HEADER_PREFIX) or not header_str.endswith(HEADER_SUFFIX):
        raise FormatError("Invalid header")

    file_type = header_str[len(HEADER_PREFIX) : HEADER_SIZE - len(HEADER_SUFFIX)].rstrip()
    parser = PARSERS.get(file_type)
    if parser is None:
        raise FormatError("Unsupported file type {}".format(file_type))
    return Header(file_type, parser)

def read(path):
    with open(path, "rb") as f:
        data = f.read()

    n = len(data)
    if n == 0:
        raise FormatError("File is empty")
    if ord(data[0]) == 0x3f:
        raise FormatError("File is audio data")

    i = iter(data)

    h = fetch_header(i)
    print("File type: {}".format(h.file_type))
    h.parse(i).dump()

def handle_dump(args):
    try:
        read(args.file_name)
    except FormatError as e:
        sys.stderr.write("File {} is in invalid format ({})\n".format(args.file_name, e.message))
        exit(1)
    except StopIteration:
        sys.stderr.write("Failed to read from {}\n".format(args.file_name))
        exit(2)

def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    dump_parser = subparsers.add_parser("dump", help="dump file contents")
    dump_parser.set_defaults(func=handle_dump)
    dump_parser.add_argument("file_name", metavar="FILE_NAME", type=str, help="File to parse")
    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
