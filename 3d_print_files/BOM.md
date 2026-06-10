# Reachy Mini DIY Build - Bill of Materials

## 3D Printed Parts (17 files)

### Body (4 parts)
| File | Description | Material | Notes |
|------|-------------|----------|-------|
| `body_top_3dprint.stl` | Main body shell (top) | ABS/PETG | Largest part |
| `body_down_3dprint.stl` | Main body shell (bottom) | ABS/PETG | |
| `body_foot_3dprint.stl` | Base/foot | ABS/PETG | |
| `body_turning_3dprint.stl` | Rotating turntable | ABS/PETG | |

### Head (5 parts)
| File | Description | Material | Notes |
|------|-------------|----------|-------|
| `head_front_3dprint.stl` | Head front shell | ABS/PETG | Camera mount |
| `head_back_3dprint.stl` | Head back shell | ABS/PETG | |
| `head_mic_3dprint.stl` | Microphone mount | ABS/PETG | |
| `glasses_dolder_3dprint.stl` | Glasses/eyes holder | ABS/PETG | Lens mount |
| `lens_cap_d40_3dprint.stl` | Lens cap (40mm) | ABS/PETG | Alternative: d30 |

### Antennas (4 parts, some x2)
| File | Description | Qty | Material |
|------|-------------|-----|----------|
| `antenna_body_3dprint.stl` | Antenna main body | 2 | ABS/PETG |
| `antenna_holder_l_3dprint.stl` | Left antenna mount | 1 | ABS/PETG |
| `antenna_holder_r_3dprint.stl` | Right antenna mount | 1 | ABS/PETG |
| `antenna_interface_3dprint.stl` | Antenna motor interface | 2 | ABS/PETG |

### Stewart Platform / Neck (3 parts)
| File | Description | Material | Notes |
|------|-------------|----------|-------|
| `stewart_main_plate_3dprint.stl` | Stewart platform base | ABS/PETG | Motor mounts |
| `stewart_tricap_3dprint.stl` | Stewart platform top cap | ABS/PETG | Head attachment |
| `neck_reference_3dprint.stl` | Neck reference/guide | ABS/PETG | |

---

## Electronics Shopping List

### Motors (Dynamixel)
| Component | Model | Qty | Link | Est. Price |
|-----------|-------|-----|------|------------|
| Base motor | XC330-M288-T | 1 | [Robotis](https://www.robotis.us/dynamixel-xc330-m288-t/) | ~$50 |
| Stewart motors | XL330-M288-T | 6 | [Robotis](https://www.robotis.us/dynamixel-xl330-m288-t/) | ~$180 |
| Antenna motors | XL330-M077-T | 2 | [Robotis](https://www.robotis.us/dynamixel-xl330-m077-t/) | ~$50 |

### Compute
| Component | Model | Qty | Link | Est. Price |
|-----------|-------|-----|------|------------|
| Compute Module | Raspberry Pi CM4104016 | 1 | [RPi](https://www.raspberrypi.com/products/compute-module-4/) | ~$75 |
| IO Board | CM4 IO Board (or custom) | 1 | Various | ~$35 |

### Sensors
| Component | Model | Qty | Link | Est. Price |
|-----------|-------|-----|------|------------|
| Camera | RPi Camera V3 Wide | 1 | [RPi](https://www.raspberrypi.com/products/camera-module-3/) | ~$35 |
| Mic Array | ReSpeaker (XMOS) | 1 | [Seeed](https://www.seeedstudio.com/ReSpeaker-Mic-Array-v2-0.html) | ~$50 |
| Speaker | 5W 4Ohm | 1 | Various | ~$10 |

### Power
| Component | Model | Qty | Notes | Est. Price |
|-----------|-------|-----|-------|------------|
| Battery | LiFePO4 6.4V 2000mAh | 1 | With protection circuit | ~$30 |
| Power Board | Custom/DIY | 1 | 6.8-7.6V regulation | ~$20 |

### Mechanical
| Component | Description | Qty | Notes |
|-----------|-------------|-----|-------|
| Stewart rods | Metal linkages ~20mm | 6 | Ball joints on ends |
| Bearing | 85x110x13mm | 1 | For body rotation |
| Screws | Various M2, M2.5, M3 | Many | Check STL holes |

---

## Estimated Total Cost

| Category | Estimate |
|----------|----------|
| Motors | ~$280 |
| Compute | ~$110 |
| Sensors | ~$95 |
| Power | ~$50 |
| Mechanical | ~$50 |
| Filament | ~$30 |
| **Total** | **~$615** |

---

## Print Settings Recommendations

- **Material:** PETG or ABS (ABS preferred for durability)
- **Layer height:** 0.2mm
- **Infill:** 20-30%
- **Supports:** Yes, for overhangs
- **Bed adhesion:** Brim recommended

---

## Resources

- **SDK Docs:** `docs/source/SDK/`
- **Hardware Specs:** `docs/source/platforms/reachy_mini/hardware.md`
- **Motor Firmware:** `src/reachy_mini/assets/firmware/`
- **Discord:** https://discord.gg/Y7FgMqHsub
