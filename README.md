# Watchl
A small command-line utility, made with the intent to combine elements of `watch` and `less`, periodically executing a shell command and providing a scrollable output, with the scrolling position kept between updates of the command's output.

## Usage

```
./watchl.py "ls ~"
```
This will provide a scrollable, live-updated list of the files in your home directory.

```
./watchl.py ./pyview.sh ./watchl.py
```
`pyview.sh` is a small script to get a summary of any Python source files in the arguments.  Using it with watchl will make that list scrollable and responsive to changes.
