#!/usr/bin/python3

import curses
import sys
import builtins
import os
from argparse import ArgumentParser
from subprocess import Popen, PIPE, STDOUT
import time
from io import StringIO
from threading import Thread, Lock
from locked import Locked
from queue import Queue

# TODO : establish consistent capitalization/underscoring naming pattern
# TODO : turn into usable Python module, where the user may supply their own display buffer update hook
# TODO : add search feature to viewer
# TODO : view scrolling position at bottom of viewer
# TODO : execution rate/interval argument
# TODO : is color piping possible?
# TODO: if scrolled to the bottom and lines are added, stay at the bottom
# TODO : turn functions into Thread methods


def deinit_curses(screen):
	curses.nocbreak()
	screen.keypad(0)
	curses.echo()
	curses.endwin()

def refreshBuffer(cmd, lineBuffer, lineBufferUpdated, EXECUTE_RATE=0.5):
	""" To be ran in its own thread. Periodically issues a system call and updates a buffer with the output of the command's stdout and stderr.
		
		Arguments:
			cmd - The command to periodically run

			lineBuffer - a Locked object, whose value are a list of strings, each a line to be displayed by `def viewer()`

			lineBufferUpdated - a Locked object, containing a boolean, denoting to the viewer that `lineBuffer` has been updated, signalling to update its internal buffer.

			EXECUTE_RATE - how many times the command should be executed, per second
	"""

	cmdBuffer = None
	last_executed = 0

	# Buffer update loop
	while True:
		# Restrict update rate
		t = time.time()
		if t - last_executed < 1/EXECUTE_RATE:
			continue


		# Execute command
		cmdBuffer = Popen(
			cmd, shell=1,
			stderr=STDOUT, stdout=PIPE,
			env=os.environ.copy()
		)

		cmdBuffer.wait()
		last_executed = time.time()

		# Write results to lineBuffer
		with lineBuffer:
			lineBuffer.value = cmdBuffer.stdout\
					.read().decode().split("\n")

		# Flag that lineBuffer has been updated
		with lineBufferUpdated:
			lineBufferUpdated.value = True

def viewer(lineBuffer, lineBufferUpdated, DISPLAY_RATE=5):
	""" To be ran in it's own thread.  Handles user display and keyboard interaction via curses.
		Arguments:
			lineBuffer - Locked object, containing a list of strings, to be copied to a buffer in viewer()'s namespace, with each string each to be displayed on it's own line. 

			lineBufferUpdated - Locked object containing a boolean denoting that lineBuffer has been updated, and therefore should be copied to viewer()'s internal display buffer.

			DISPLAY_RATE - how many times, per second, the display should be updated
	"""

	# Init curses screen
	screen = curses.initscr()
	curses.cbreak()
	curses.noecho()
	curses.halfdelay(5)
	screen.keypad(1)

	# Encapsulate subroutine in try block to deinit curses upon exception
	try:
		line_num = 0
		last_refreshed = 0
		lineBufferCurrent = None
		
		# Wait until lineBuffer is populated for the first time, then
		# update display
		while True:
			with lineBuffer:
				if lineBuffer.value is not None:
					lineBufferCurrent = lineBuffer.value.copy()
					break
			time.sleep(0.1)
		
		# Display loop
		while True:
			# Limit display rate
			t = time.time()
			if t - last_refreshed >= 1/DISPLAY_RATE:
				last_refreshed = t
				continue
			last_refreshed = t

			screen.clear()
			screen.border(0)
			height, width = screen.getmaxyx()
			
			# If the lineBuffer has been updated, copy it to the
			# internal buffer
			with lineBufferUpdated as u:
				if u.value:
					with lineBuffer as lb:
						lineBufferCurrent = lb.value.copy()
					u.value = False

			# Update screen with value from internal display buffer,
			# but only the lines between the top of the scrolled display
			# and the rest forward which can fit on the screen
			# screen.addstr(0, 1, str(len(lineBufferCurrent)))
			BORDER = 2
			for d, line in enumerate(lineBufferCurrent[line_num:line_num+height-BORDER]):
				i = d + line_num
				if i-line_num >= height - BORDER:
					break
				screen.addstr(i-line_num+1, 1, line[:width-BORDER])
			char = screen.getch()

			# input switch
			if char == ord('q'):
				break  # quit
			elif char in (curses.KEY_UP, ord('k')):
				# scroll up
				if line_num > 0:
					line_num -= 1
			elif char in (curses.KEY_DOWN, ord('j')):
				# scroll down
				if line_num + height + 1 <= len(lineBufferCurrent):
					line_num += 1
			elif char == ord('g'):
				# scroll to top
				line_num = 0
			elif char == ord('G'):
				# scroll to bottom
				line_num = len(lineBufferCurrent) - height
			screen.refresh()
	finally:
		deinit_curses(screen)

def main():
	""" Parses CLI arguments and initializes some threads to maintain a buffer of output from a supplied system command and update them to a scrollable CLI interface.
	"""

	# Parse CLI args
	parser = ArgumentParser(description="")
	parser.add_argument(
		'-f', '--file',
		help="The file to be read from."
	)
	parser.add_argument(
		'--interval', default=2, type=int
	)
	parser.add_argument(
		'evaluate', nargs="+",
		help="Command to be executed"
	)
	parser.add_argument(
		'--env', type=str,
		help="Environment script location"
	)

	parsed = parser.parse_args()
	cmd = " ".join(parsed.evaluate)

	# Threads
	lineBuffer = Locked()
	lineBufferUpdated = Locked(False)

	t_viewer = Thread(
		target=viewer,
		args=[lineBuffer, lineBufferUpdated]
	)

	t_refresh_buffer = Thread(
		target=refreshBuffer,
		args=(cmd, lineBuffer, lineBufferUpdated)
	)
	# TODO : daemon mode potentially dangerous. Consider implementing exit flag
	t_refresh_buffer.daemon = True

	t_viewer.start()
	t_refresh_buffer.start()

if __name__=="__main__":
	main()
