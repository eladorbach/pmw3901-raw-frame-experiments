# PMW3901 raw-frame experiments

35 × 35 grayscale frame capture from a PMW3901 optical-flow sensor on a Crazyflie 2.x Flow Deck V2.

**Bench-only firmware. Remove propellers. Do not fly with these modifications.** Raw-frame acquisition changes normal sensor operation. Power-cycle before returning to flight firmware.

## Contents

- `firmware.patch`: modifications to Bitcraze Crazyflie firmware (including SPI polling, frame capture, and USB app-channel transport).
- `flow_pixels_native.py`: USB capture and live image viewer.
- `frame_protocol.py`: packet assembly and frame integrity checks.
- `images/`: two screenshots of the live viewer on a Jetson AGX Xavier.

The screenshots show saturated vertical and horizontal bright bands. They document the initial optical setup; they are **not** lens-calibration results.

## Performance

Five verified 35 × 35 frames captured in approximately 3.27 seconds each (0.31 FPS). The current USB viewer can stop on a missing image fragment; a systemd restart policy was used during testing.

## Firmware

Apply the patch against a compatible Bitcraze crazyflie-firmware checkout and build with the ARM embedded toolchain. The patch is provided as a research snapshot rather than a flight-ready release.

## Status

Work in progress. Lens calibration and higher frame-rate readout have not been validated.

## Attribution

Based on the open-source [Bitcraze crazyflie-firmware](https://github.com/bitcraze/crazyflie-firmware). See its license and the original PMW3901 driver.
