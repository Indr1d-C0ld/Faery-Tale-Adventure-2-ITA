// Minimal stand-ins for the ScummVM types used by saga2/shorten.cpp (Melchior tool).
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cstdint>
#include <cmath>
#include <cstdarg>
#include <vector>
typedef uint8_t byte; typedef uint8_t uint8; typedef int8_t int8; typedef uint16_t uint16; typedef int16_t int16;
typedef uint32_t uint32; typedef int32_t int32; typedef unsigned int uint;
template<class T> T MIN(T a, T b) { return a < b ? a : b; }
template<class T> T MAX(T a, T b) { return a > b ? a : b; }
template<class T> T ABS(T a) { return a < 0 ? -a : a; }
static void warning(const char *f, ...) { va_list v; va_start(v, f); vfprintf(stderr, f, v); fputc('\n', stderr); va_end(v); }
static void error(const char *f, ...) { va_list v; va_start(v, f); vfprintf(stderr, f, v); fputc('\n', stderr); va_end(v); exit(1); }
namespace Common {
struct ReadStream {
	const byte *d; size_t n, p = 0;
	ReadStream(const byte *d_, size_t n_) : d(d_), n(n_) {}
	byte readByte() { return p < n ? d[p++] : 0; }
	uint32 readUint32BE() { uint32 v = 0; for (int i = 0; i < 4; i++) v = (v << 8) | readByte(); return v; }
	uint32 read(void *b, uint32 k) { uint32 m = (uint32)MIN<size_t>(k, n - p); memcpy(b, d + p, m); p += m; return m; }
};
typedef ReadStream SeekableReadStream;
}
namespace Audio { enum { FLAG_UNSIGNED = 1, FLAG_16BITS = 2, FLAG_LITTLE_ENDIAN = 4, FLAG_STEREO = 8 }; }
