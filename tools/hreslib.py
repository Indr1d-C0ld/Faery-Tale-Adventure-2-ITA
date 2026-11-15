"""Libreria comune per gli archivi HRES di FTA2 (motore SAGA2)."""
import struct

class Group:
    def __init__(self, f, tag, entries):
        self.f, self.tag, self.entries = f, tag, entries   # entries: lista di (id, off, size)
    def index_of(self, idb):
        for i, (t, o, s) in enumerate(self.entries):
            if t == idb: return i
        raise KeyError(idb)
    def read_index(self, i):
        _, o, s = self.entries[i]
        self.f.seek(o); return self.f.read(s)
    def read(self, idb):
        return self.read_index(self.index_of(idb))

class HRes:
    def __init__(self, path):
        self.path = path
        self.f = open(path, 'rb')
        self.data_cache = None
        magic, self.dir_off, self.dir_size = struct.unpack('<4sII', self.f.read(12))
        assert magic == b'HRES', path
        self.groups = {}
        for tag, o, s in self._entries(self.dir_off, self.dir_size):
            self.groups[tag] = Group(self.f, tag, list(self._entries(o, s)))
    def _entries(self, off, size):
        self.f.seek(off); d = self.f.read(size)
        for i in range(0, size - size % 12, 12):
            yield struct.unpack_from('<4sII', d, i)
    def group(self, tag):
        return self.groups[tag.encode() if isinstance(tag, str) else tag]

def tagstr(b):
    return ''.join(chr(c) if 32 < c < 127 else '\\x%02x' % c for c in b)
