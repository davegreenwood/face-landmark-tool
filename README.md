# Face Landmark Tool

A simple application for labelling facial landmarks. Although this may grow, the
key features are:

* Open an image
* Load landmarks
* Display landmarks over image
* Edit landmark position
* Save Landmarks

## Installation

From the project directory, type `pip install -e .` to install an entry point to
the system. The application requires PyQt5.

## Usage

Start the app by typing `flt` , the app then opens in it's own window.

Load an image using the File menu.
A landmark model is provided that can be adjusted by dragging points or sections.
The drag item highlights red to indicate what will move...

Custom landmark models can be loaded. again with the file menu.
Landmarks can be saved to file or can be printed to stdout with `Ctrl + P`.
It is possible to pipe the output to file, eg:

    flt >> lm.txt

this provides a compact workflow that puts the image file name and the
point positions into a single line in a text file.

## Hotkeys

* The view can be zoomed using `Ctrl + =` and `Ctrl + -` or the scroll wheel.
* The model can be selected as a whole with `Ctrl + A`, and deslected with `Ctrl + D` .
* Individual model sections can be added to the current selection with `Ctrl` click.
* The model can be scaled as a whole up or down with `Alt + A`, and `Alt + D` .
* The display line width can be set with `Ctrl + 1`, `Ctrl + 2`, `Ctrl + 3`.
