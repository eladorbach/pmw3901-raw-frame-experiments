"""35x35 PMW3901 PX v1 packet decoder. No device access."""
import binascii
import struct

WIDTH, HEIGHT = 35, 35
PIXELS = WIDTH * HEIGHT
CHUNK = 25
CHUNKS = (PIXELS + CHUNK - 1) // CHUNK
MAGIC = b'PX'

class FrameAssembler:
    def __init__(self):
        self.active_id = None
        self.chunks = {}
        self.completed = 0
        self.error = None

    def reset(self):
        self.active_id = None
        self.chunks.clear()
        self.error = None

    def accept(self, packet):
        packet = bytes(packet)
        if len(packet) < 5 or packet[:2] != MAGIC:
            return None
        fid, index, count = packet[2], packet[3], packet[4]
        if self.active_id != fid:
            self.active_id = fid
            self.chunks.clear()
            self.error = None
        if index == 255:
            if len(packet) not in (9, 17, 25):
                self.error = 'bad trailer length'
                return None
            if count != 0:
                self.error = 'sensor capture failed (status %d)' % count
                return None
            if len(self.chunks) != CHUNKS:
                self.error = 'missing %d of %d image fragments' % (CHUNKS - len(self.chunks), CHUNKS)
                return None
            pixels = b''.join(self.chunks[i] for i in range(CHUNKS))
            if len(pixels) != PIXELS:
                self.error = 'incorrect image length'
                return None
            received_crc, = struct.unpack_from('<I', packet, 5)
            if received_crc != (binascii.crc32(pixels) & 0xffffffff):
                self.error = 'CRC32 mismatch'
                return None
            self.last_timing = (struct.unpack_from('<II', packet, 9) + struct.unpack_from('<HHHH', packet, 17)) if len(packet) == 25 else (struct.unpack_from('<II', packet, 9) if len(packet) == 17 else None)
            self.completed += 1
            self.reset()
            return fid, pixels
        if count != CHUNKS or index >= CHUNKS:
            self.error = 'invalid frame packet index/count'
            return None
        expected_len = min(CHUNK, PIXELS - index * CHUNK)
        if len(packet) != 5 + expected_len:
            self.error = 'bad packet length'
            return None
        data = packet[5:]
        if index in self.chunks and self.chunks[index] != data:
            self.error = 'conflicting duplicate packet'
            return None
        self.chunks[index] = data
        return None

def write_pgm(path, pixels):
    if len(pixels) != PIXELS:
        raise ValueError('wrong image dimensions')
    with open(path, 'wb') as out:
        out.write(b'P5\n35 35\n255\n')
        out.write(pixels)
