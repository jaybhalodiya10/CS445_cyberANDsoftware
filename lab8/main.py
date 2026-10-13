# CS445 - Lab 8: Hash Functions Performance Comparison
# Comparing cryptographic and non-cryptographic hash functions

import hashlib
import time
import struct
import mmh3

# Input configuration
input_string = "jay" * 500
NUM_READINGS = 10

# Constants for 64-bit non-cryptographic hash algorithms
K1 = 0xb492b66fbe98f273
K2 = 0x9ae16a3b2f90404f


def rotate_right(value, shift):
    """Rotate 64-bit integer to the right."""
    value &= 0xFFFFFFFFFFFFFFFF
    return ((value >> shift) | (value << (64 - shift))) & 0xFFFFFFFFFFFFFFFF


def read_uint64(data, offset):
    """Read a 64-bit little-endian unsigned integer from bytes."""
    return struct.unpack('<Q', data[offset:offset + 8])[0]


def mix16(u, v, multiplier):
    """Mix two 64-bit integers with a multiplier."""
    a = (u ^ v) * multiplier & 0xFFFFFFFFFFFFFFFF
    a ^= (a >> 47)
    b = (v ^ a) * multiplier & 0xFFFFFFFFFFFFFFFF
    b ^= (b >> 47)
    return b * multiplier & 0xFFFFFFFFFFFFFFFF


def cityhash64(data):
    """CityHash64 implementation in Python."""
    if isinstance(data, str):
        data = data.encode('utf-8')
    n = len(data)

    if n < 64:
        multiplier = K2 + n * 2
        a = read_uint64(data, 0) * K1 & 0xFFFFFFFFFFFFFFFF
        b = read_uint64(data, 8)
        c = read_uint64(data, n - 8) * multiplier & 0xFFFFFFFFFFFFFFFF
        d = read_uint64(data, n - 16) * K2 & 0xFFFFFFFFFFFFFFFF
        return mix16(
            (rotate_right(a + b, 43) + rotate_right(c, 30) + d) & 0xFFFFFFFFFFFFFFFF,
            (a + rotate_right(b + K2, 18) + c) & 0xFFFFFFFFFFFFFFFF,
            multiplier
        )

    x = read_uint64(data, 0)
    y = read_uint64(data, n - 16) ^ K1
    z = read_uint64(data, n - 56) ^ K2
    v0 = rotate_right(y - x, 49) * K1 & 0xFFFFFFFFFFFFFFFF
    v1 = rotate_right(x, 35) * K1 & 0xFFFFFFFFFFFFFFFF
    w0 = rotate_right(v0 + z, 38) * K1 & 0xFFFFFFFFFFFFFFFF
    w1 = rotate_right(v1 + y, 28) * K1 & 0xFFFFFFFFFFFFFFFF

    pos = 0
    while pos + 64 <= n:
        x = rotate_right(x + y + v0 + read_uint64(data, pos + 8), 37) * K1 & 0xFFFFFFFFFFFFFFFF
        y = rotate_right(y + v1 + read_uint64(data, pos + 48), 42) * K1 & 0xFFFFFFFFFFFFFFFF
        x ^= w1
        y = (y + v0 + read_uint64(data, pos + 40)) & 0xFFFFFFFFFFFFFFFF
        z = rotate_right(z + w0, 33) * K1 & 0xFFFFFFFFFFFFFFFF
        v0 = (read_uint64(data, pos) + v1 * K1) & 0xFFFFFFFFFFFFFFFF
        v1 = (read_uint64(data, pos + 16) + x + w0) & 0xFFFFFFFFFFFFFFFF
        w0 = (z + read_uint64(data, pos + 32)) & 0xFFFFFFFFFFFFFFFF
        w1 = (x + read_uint64(data, pos + 56)) & 0xFFFFFFFFFFFFFFFF
        x, z = z, x
        pos += 64

    return mix16(
        (v0 + w1) & 0xFFFFFFFFFFFFFFFF,
        (w0 + y) & 0xFFFFFFFFFFFFFFFF,
        K1 + ((z & 0xFF) << 1)
    )


def farmhash64(data):
    """FarmHash64 implementation in Python."""
    if isinstance(data, str):
        data = data.encode('utf-8')
    n = len(data)
    seed = 81
    x = seed
    y = (seed * K2 + 113) & 0xFFFFFFFFFFFFFFFF
    z = (y * K2) & 0xFFFFFFFFFFFFFFFF

    pos = 0
    while pos + 32 <= n:
        a = read_uint64(data, pos)
        b = read_uint64(data, pos + 8)
        c = read_uint64(data, pos + 16)
        d = read_uint64(data, pos + 24)
        x = rotate_right(x + a + b, 37) * K1 & 0xFFFFFFFFFFFFFFFF
        y = rotate_right(y + c + d, 42) * K1 & 0xFFFFFFFFFFFFFFFF
        x ^= d
        y = (y + a + b) & 0xFFFFFFFFFFFFFFFF
        z = rotate_right(z ^ c, 33) * K1 & 0xFFFFFFFFFFFFFFFF
        pos += 32

    return mix16((x + z) & 0xFFFFFFFFFFFFFFFF, y, K1 + ((z & 0xFF) << 1))


# Whirlpool S-Box lookup table
WHIRLPOOL_SBOX = [
    0x18, 0x23, 0xC6, 0xE8, 0x87, 0xB8, 0x01, 0x4F, 0x36, 0xA6, 0xD2, 0xF5, 0x79, 0x6F, 0x91, 0x52,
    0x60, 0xBC, 0x9B, 0x8E, 0xA3, 0x0C, 0x7B, 0x35, 0x1D, 0xE0, 0xD7, 0xC2, 0x2E, 0x4B, 0xFE, 0x57,
    0x15, 0x77, 0x37, 0xE5, 0x9F, 0xF0, 0x4A, 0xDA, 0x58, 0xC9, 0x29, 0x0A, 0xB1, 0xA0, 0x6B, 0x85,
    0xBD, 0x5D, 0x10, 0xF4, 0xCB, 0x3E, 0x05, 0x67, 0xE4, 0x27, 0x41, 0x8B, 0xA7, 0x7D, 0x95, 0xD8,
    0xFB, 0xEE, 0x7C, 0x66, 0xDD, 0x17, 0x47, 0x9E, 0xCA, 0x2D, 0xBF, 0x07, 0xAD, 0x5A, 0x83, 0x33,
    0x63, 0x02, 0xAA, 0x71, 0xC8, 0x19, 0x49, 0xD9, 0xF2, 0xE3, 0x5B, 0x88, 0x9A, 0x26, 0x32, 0xB0,
    0xE9, 0x0F, 0xD5, 0x80, 0xBE, 0xCD, 0x34, 0x48, 0xFF, 0x7A, 0x90, 0x5F, 0x20, 0x68, 0x1A, 0xAE,
    0xB4, 0x54, 0x93, 0x22, 0x64, 0xF1, 0x73, 0x12, 0x40, 0x08, 0xC3, 0xEC, 0xDB, 0xA1, 0x8D, 0x3D,
    0x97, 0x00, 0xCF, 0x2B, 0x76, 0x82, 0xD6, 0x1B, 0xB5, 0xAF, 0x6A, 0x50, 0x45, 0xF3, 0x30, 0xEF,
    0x3F, 0x55, 0xA2, 0xEA, 0x65, 0xBA, 0x2F, 0xC0, 0xDE, 0x1C, 0xFD, 0x4D, 0x92, 0x75, 0x06, 0x8A,
    0xB2, 0xE6, 0x0E, 0x1F, 0x62, 0xD4, 0xA8, 0x96, 0xF9, 0xC5, 0x25, 0x59, 0x84, 0x72, 0x39, 0x4C,
    0x5E, 0x78, 0x38, 0x8C, 0xD1, 0xA5, 0xE2, 0x61, 0xB3, 0x21, 0x9C, 0x1E, 0x43, 0xC7, 0xFC, 0x04,
    0x51, 0x99, 0x6D, 0x0D, 0xFA, 0xDF, 0x7E, 0x24, 0x3B, 0xAB, 0xCE, 0x11, 0x8F, 0x4E, 0xB7, 0xEB,
    0x3C, 0x81, 0x94, 0xF7, 0xB9, 0x13, 0x2C, 0xD3, 0xE7, 0x6E, 0xC4, 0x03, 0x56, 0x44, 0x7F, 0xA9,
    0x2A, 0xBB, 0xC1, 0x53, 0xDC, 0x0B, 0x9D, 0x6C, 0x31, 0x74, 0xF6, 0x46, 0xAC, 0x89, 0x14, 0xE1,
    0x16, 0x3A, 0x69, 0x09, 0x70, 0xB6, 0xD0, 0xED, 0xCC, 0x42, 0x98, 0xA4, 0x28, 0x5C, 0xF8, 0x86,
]


def build_whirlpool_tables():
    """Generate round transformation tables for Whirlpool."""
    tables = [[0] * 256 for _ in range(8)]
    for x in range(256):
        v = WHIRLPOOL_SBOX[x]
        v2 = ((v << 1) ^ (0x11D if v & 0x80 else 0)) & 0xFF
        v4 = ((v2 << 1) ^ (0x11D if v2 & 0x80 else 0)) & 0xFF
        v8 = ((v4 << 1) ^ (0x11D if v4 & 0x80 else 0)) & 0xFF
        row = (v << 56) | (v << 48) | (v4 << 40) | (v << 32) | (v8 << 24) | ((v4 ^ v) << 16) | (v2 << 8) | (v8 ^ v)
        tables[0][x] = row
        for t in range(1, 8):
            tables[t][x] = ((row >> (8 * t)) | (row << (64 - 8 * t))) & 0xFFFFFFFFFFFFFFFF
    return tables


C_TABLE = build_whirlpool_tables()


def build_whirlpool_round_constants():
    """Generate 10 round constants for Whirlpool."""
    round_constants = []
    for r in range(10):
        val = 0
        for j in range(8):
            val ^= (C_TABLE[j][8 * r + j] & (0xFF << (56 - 8 * j)))
        round_constants.append(val)
    return round_constants


RC_TABLE = build_whirlpool_round_constants()


def whirlpool_hash(data):
    """Whirlpool hash function (512-bit output)."""
    if isinstance(data, str):
        data = data.encode('utf-8')
    bit_len = len(data) * 8
    buffer = bytearray(data)
    buffer.append(0x80)

    while len(buffer) % 64 != 32:
        buffer.append(0x00)

    buffer += b'\x00' * 24 + struct.pack('>Q', bit_len)
    data_bytes = bytes(buffer)

    state = [0] * 8
    for block_start in range(0, len(data_bytes), 64):
        block = data_bytes[block_start:block_start + 64]
        round_key = list(state)
        block_state = [struct.unpack('>Q', block[i * 8:(i + 1) * 8])[0] ^ round_key[i] for i in range(8)]

        for r in range(10):
            # Key schedule
            next_key = [0] * 8
            for i in range(8):
                val = 0
                for t in range(8):
                    val ^= C_TABLE[t][(round_key[(i - t) % 8] >> (56 - 8 * t)) & 0xFF]
                next_key[i] = val & 0xFFFFFFFFFFFFFFFF
            next_key[0] ^= RC_TABLE[r]
            round_key = next_key

            # State transformation
            next_state = [0] * 8
            for i in range(8):
                val = 0
                for t in range(8):
                    val ^= C_TABLE[t][(block_state[(i - t) % 8] >> (56 - 8 * t)) & 0xFF]
                next_state[i] = (val ^ round_key[i]) & 0xFFFFFFFFFFFFFFFF
            block_state = next_state

        for i in range(8):
            state[i] ^= block_state[i]

    return b''.join(struct.pack('>Q', v) for v in state).hex()


# Wrapper functions for each hash algorithm
def hash_md5(data):
    return hashlib.md5(data).hexdigest()

def hash_sha1(data):
    return hashlib.sha1(data).hexdigest()

def hash_sha256(data):
    return hashlib.sha256(data).hexdigest()

def hash_sha512(data):
    return hashlib.sha512(data).hexdigest()

def hash_murmur3(data):
    return mmh3.hash128(data)

def hash_cityhash(data):
    return cityhash64(data)

def hash_farmhash(data):
    return farmhash64(data)

def hash_whirlpool(data):
    return whirlpool_hash(data)

def hash_blake2s(data):
    return hashlib.blake2s(data).hexdigest()


def main():
    data_bytes = input_string.encode('utf-8')
    input_bits = len(data_bytes) * 8

    # List of hash algorithms to evaluate: (Algorithm Name, Hash Function, Output Bits)
    hash_list = [
        ("MD5", hash_md5, 128),
        ("SHA-1", hash_sha1, 160),
        ("SHA-256", hash_sha256, 256),
        ("SHA-512", hash_sha512, 512),
        ("MurmurHash3", hash_murmur3, 128),
        ("CityHash", hash_cityhash, 64),
        ("FarmHash", hash_farmhash, 64),
        ("Whirlpool", hash_whirlpool, 512),
        ("BLAKE2s", hash_blake2s, 256),
    ]

    benchmark_data = []

    # Run benchmark trials
    for name, func, out_bits in hash_list:
        trials = []
        for _ in range(NUM_READINGS):
            start_time = time.perf_counter()
            func(data_bytes)
            end_time = time.perf_counter()
            trials.append(end_time - start_time)

        avg_time = sum(trials) / len(trials)
        benchmark_data.append({
            "name": name,
            "input_bits": input_bits,
            "output_bits": out_bits,
            "avg_time": avg_time
        })

    # Rank algorithms based on average execution time (faster = higher priority)
    ranked_by_speed = sorted(benchmark_data, key=lambda item: item["avg_time"])
    for rank, item in enumerate(ranked_by_speed, start=1):
        item["priority"] = rank

    # Display comparison table
    print(f"{'Sr.':<5} {'Hash Function':<15} {'Language':<10} {'Input (bits)':<14} {'Output (bits)':<15} {'Avg Time (sec)':<18} {'Priority'}")
    for sr_no, item in enumerate(benchmark_data, start=1):
        print(f"{sr_no:<5} {item['name']:<15} {'Python':<10} {item['input_bits']:<14} {item['output_bits']:<15} {item['avg_time']:<18.10f} {item['priority']}")

    # Efficiency analysis
    print("\nAnalysis:")
    print(f"Most efficient (Priority 1): {ranked_by_speed[0]['name']}")
    print(f"Least efficient (Priority 9): {ranked_by_speed[-1]['name']}")


if __name__ == "__main__":
    main()