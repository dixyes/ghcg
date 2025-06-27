# Github contributions 3D model generator

## Prepare

1. install pypi dependencies

```bash
pip install -r requirements.txt
```

2. install [OpenSCAD Nightly](https://www.openscad.org/downloads.html) (choose Development Snapshots for manifold backend)

3. install [Inkscape](https://inkscape.org/)

## Usage

```bash
python generate.py <username> [year]
```

fill will be generated in `output/<user>-<year>/object.scad`

## Example and slicing advice

Using SANLU white and black PLA filament and Bambu "Bambu green" filament, 0.2mm layer height, 0.4mm nozzle

The model is sliced upside down for better surface.

![Example](assets/example.png)

Key slicing settings:

- Upside down to get better surface
- Wall Generator: Arachne
- Wall loops: 1

Remember to check if small features for text are generated in the first layer, if not, you may need to adjust Wall generator paramaters

## TODOs

- [ ] dark mode
- [ ] other styles like gitlab
- [ ] github skyline ??
- [ ] github city ??
- [ ] support slicers color recognition

## License

Copyright (c) 2025 Yun Dou <dixyes@gmail.com>

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details
