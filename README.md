# Watchl
A small command-line utility, made with the intent to combine elements of `watch` and `less`, periodically executing a shell command and providing a scrollable output, with the scrolling position kept between updates of the command's output. Watchl uses the standard Python curses module to maintain it's display, and has no external dependencies.

Watchl's Viewer class can also be imported into a Python script that utilizes Watchl's updating interface.

## Usage

```
./watchl.py "ls ~"
```
This will provide a scrollable, live-updated list of the files in your home directory.

```
./watchl.py ./pyview.sh ./watchl.py
```
`pyview.sh` is a small script to get a summary of any Python source files in the arguments.  Using it with watchl will make that list scrollable and responsive to changes.

```
from watchl import Viewer
from time import sleep

viewer = Viewer()
viewer.start()

x = 0
while viewer.is_alive():
	x+=1
	viewer.set([str(y)+": "+str(x+y) for y in range(100)])
	sleep(0.5)
```
Watchl's Viewer class can be used to quickly and simply provide it's updatable interface to Python scripts, such as this one.
