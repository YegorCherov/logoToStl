<img src="example.png" width="800" alt="3D Logo Preview" />

# Image to 3D STL Generator

This Python script converts a 2D image logo into a single, perfectly scaled, 3D printable STL file. It bakes your desired dimensions directly into the mesh, ensuring it imports into OrcaSlicer, Bambu Studio, or Cura at the exact physical size specified.

## Features

* Single file output containing both the baseplate and the logo details.
* Automatic nozzle filtering to erase lines and details too thin for your printer nozzle.
* Exact millimeter scaling to prevent sizing errors in slicing software.
* Raised mode to place the logo details on top of the baseplate.
* Etched mode to carve the logo details into the plate while leaving a solid floor underneath.
* Clean vertical walls with adjustable edge smoothing to minimize printer vibrations.

## Prerequisites

You need Python and the following libraries installed:

```bash
pip install numpy numpy-stl opencv-python
```

## Quick Start

1. Save the Python script to your computer.
2. Open the script and set your image input and STL output paths at the bottom.
3. Run the script:

```bash
python generator.py
```

## Configuration Parameters

You can control all physical dimensions directly inside the script call:

* `target_width_mm`: The exact width of the final 3D model in millimeters when imported into your slicer.
* `backplate_thickness_mm`: The total thickness of your base plate in millimeters.
* `logo_height_mm`: The height of the raised logo details, or the depth of the etched carving.
* `nozzle_diameter_mm`: Your printer nozzle diameter. Any details smaller than this are automatically deleted to prevent unprintable paths.
* `inverse`: Set to False to etch the logo into the plate, or True to raise the logo on top of the plate.
* `invert_logo`: Set to True if your source image has a dark logo on a light background.
* `resolution_limit`: Controls the density of the 3D mesh. A value of 450 keeps detail high while maintaining a small file size.
