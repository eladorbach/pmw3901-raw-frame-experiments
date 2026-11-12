#!/usr/bin/env python3
"""Flow Deck V2 PMW3901 pixel viewer. Local USB, NO firmware flashing.

Stock Crazyflie firmware does not implement PXV/PX?; --probe fails closed
until reviewed bench firmware is installed. Never fly with bench firmware.
"""
import argparse
import datetime
import itertools
import sys
import time
from pathlib import Path

from frame_protocol import FrameAssembler, write_pgm
from cf_flow_usb_stdlib import NativeUsb, packet, unpack_packet

PORT_APP, CHANNEL_APP = 13, 2
VERSION_REQUEST = b'PXV'
VERSION_REPLY = b'PX!\x01'
FRAME_REQUEST = b'PX?'

class PixelCameraError(RuntimeError):
    pass

def receive_app(usb, timeout_ms):
    raw = usb.receive(max(1, min(200, int(timeout_ms))))
    if not raw:
        return None
    msg = unpack_packet(raw)
    if msg and msg[0] == PORT_APP and msg[1] == CHANNEL_APP:
        return msg[2]
    return None

def probe_bench_firmware(usb, timeout=2.5):
    """Read-only capability handshake. Does NOT switch sensor mode."""
    usb.send(packet(PORT_APP, CHANNEL_APP, VERSION_REQUEST))
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        got = receive_app(usb, min(100, max(1, int((end-time.monotonic())*1000))))
        if got == VERSION_REPLY:
            return True
    raise PixelCameraError('PXV handshake absent: stock/incompatible firmware; no capture requested')

def capture_one(usb, timeout=15):
    receiver = FrameAssembler()
    usb.send(packet(PORT_APP, CHANNEL_APP, FRAME_REQUEST))
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        got = receive_app(usb, min(100, max(1, int((end-time.monotonic())*1000))))
        if got is None:
            continue
        complete = receiver.accept(got)
        if complete is not None:
            if receiver.last_timing:
                us, polls = receiver.last_timing[:2]
                print('SENSOR_TIMING capture_ms=%.1f pixel_ready_reads=%d avg_reads_per_pixel=%.2f quarter_ms=%s' % (us/1000., polls, polls/1225., receiver.last_timing[2:]), flush=True)
            return complete
        if receiver.error:
            raise PixelCameraError(receiver.error)
    raise PixelCameraError('timed out waiting for complete 35x35 frame: %d/49 chunks' % len(receiver.chunks))

def main():
    ap = argparse.ArgumentParser(description='PMW3901 raw pixels over Crazyflie native USB')
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument('--probe', action='store_true')
    group.add_argument('--capture', action='store_true')
    ap.add_argument('--frames', type=int, default=1)
    ap.add_argument('--timeout', type=float, default=15)
    ap.add_argument('--show', action='store_true', help='show 700x700 grayscale image on AGX screen')
    ap.add_argument('--outdir', default='frames')
    args = ap.parse_args()
    if not 0 <= args.frames <= 1000000 or not 3 <= args.timeout <= 60:
        ap.error('--frames 0 (continuous) or 1..1000000, --timeout 3..60')
    if args.show and not args.capture:
        ap.error('--show requires --capture')
    cv2 = np = None
    if args.show:
        try:
            import cv2
            import numpy as np
        except ImportError as exc:
            ap.error('OpenCV + numpy must already exist: %s' % exc)
    with NativeUsb() as usb:
        print('Crazyflie USB connected (0483:5740).', flush=True)
        usb.begin_crtp()
        probe_bench_firmware(usb)
        print('Bench firmware PX v1 detected.', flush=True)
        if args.probe:
            print('Read-only probe complete. No sensor-mode change.', flush=True)
            return
        target = Path(args.outdir)
        target.mkdir(parents=True, exist_ok=True)
        print('BENCH MODE: propellers OFF; power-cycle before flight.', flush=True)
        last_frame_at = None
        fps_ema = None
        try:
            for i in (itertools.count() if args.frames == 0 else range(args.frames)):
                frame_id, pixels = capture_one(usb, args.timeout)
                now = time.monotonic()
                if last_frame_at is not None:
                    instantaneous_fps = 1.0 / max(now - last_frame_at, 1e-6)
                    fps_ema = instantaneous_fps if fps_ema is None else 0.25 * instantaneous_fps + 0.75 * fps_ema
                last_frame_at = now
                date = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                dest = target / ('pmw3901_%s_%03d_id%03d.pgm' % (date, i, frame_id))
                write_pgm(dest, pixels)
                print('Frame %d: %d valid grayscale pixels saved to %s' % (i+1, len(pixels), dest), flush=True)
                if args.show:
                    raw = np.frombuffer(pixels, dtype=np.uint8).reshape(35, 35)
                    img = cv2.resize(raw, (700, 700), interpolation=cv2.INTER_NEAREST)
                    fps_text = 'FPS: --' if fps_ema is None else 'FPS: %.2f' % fps_ema
                    cv2.rectangle(img, (8, 8), (230, 53), (0,), -1)
                    cv2.putText(img, fps_text, (17, 39), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (255,), 2, cv2.LINE_AA)
                    cv2.imshow('PMW3901 raw (700x700)', img)
                    if cv2.waitKey(50) & 255 == 27:
                        break
        finally:
            if args.show:
                cv2.destroyAllWindows()
            print('Bench capture mode remains until Crazyflie power-cycle. Do NOT fly.', flush=True)

if __name__ == '__main__':
    try:
        main()
    except (PixelCameraError, OSError) as exc:
        print('ERROR:', exc, file=sys.stderr)
        sys.exit(2)
