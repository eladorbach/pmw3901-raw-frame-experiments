# PMW3901 raw image capture

35 × 35 grayscale image capture from the PMW3901 on the Crazyflie 2.x Flow Deck V2.

## Hardware

- Crazyflie 2.x with Flow Deck V2
- USB connection to Jetson AGX Xavier

## Firmware

The changes to [Bitcraze crazyflie-firmware](https://github.com/bitcraze/crazyflie-firmware) are in `firmware.patch`. They add raw pixel acquisition and frame transfer over the USB app channel.

**Bench use only. Remove propellers. Do not fly with this firmware.** Restore standard firmware and power-cycle before flight.

## Capture

```bash
python3 flow_pixels_native.py --capture --frames 5 --timeout 45 --outdir captures
python3 flow_pixels_native.py --capture --frames 0 --timeout 45 --show --outdir live
```

`frame_protocol.py` handles frame reassembly and integrity checks.

## Measurements

| Parameter | Value |
| --- | --- |
| Image size | 35 × 35 pixels |
| Capture time | 3.27 s per frame |
| Frame rate | 0.31 FPS |
| Valid frames in timing test | 5/5 |

A missing USB fragment currently terminates the capture process. The viewer was run with a systemd restart policy during testing.

## Images

- [Capture 1](images/capture-01.png): vertical bright band
- [Capture 2](images/capture-02.png): horizontal bright band

The bright regions are saturated. No lens calibration has been applied.
