#!/usr/bin/python3

import curses
import os
from argparse import ArgumentParser
from subprocess import Popen, PIPE, STDOUT
import time
from threading import Thread, Lock
from locked import Locked

# TODO : establish consistent capitalization/underscoring naming pattern
# TODO : add search feature to viewer
# TODO : view scrolling position at bottom of viewer
# TODO : execution rate/interval argument
# TODO : is color piping possible?
# TODO : if scrolled to the bottom and lines are added, stay at the bottom
# TODO : space, page_up, and page_down in the viewer


def _deinit_curses(screen):
	curses.nocbreak()
	screen.keypad(0)
	curses.echo()
	curses.endwin()

class CommandBufferRefresh(Thread):
	def __init__(self, cmd, lineBuffer, lineBufferUpdated, execute_rate=0.5):
		""" Periodically issues a system command and updates a buffer (stored in a Locked object containing a list of lines) with the output of the command's stdout and stderr.
			
			Arguments:
				cmd - The command to periodically run

				lineBuffer - a Locked object, whose value are a list of strings, each a line to be displayed by `def viewer()`

				lineBufferUpdated - a Locked object, containing a boolean, denoting to the viewer that `lineBuffer` has been updated, signalling to update its internal buffer.

				execute_rate - how many times the command should be executed, per second
		"""
		# TODO : daemon mode potentially dangerous. Consider implementing exit flag
		Thread.__init__(self, daemon=True)
		self.cmd = cmd
		self.lineBuffer = lineBuffer
		self.lineBufferUpdated = lineBufferUpdated
		self.execute_rate = execute_rate

	def run(self):
		cmdBuffer = None
		last_executed = 0

		# Buffer update loop
		while True:
			# Restrict update rate
			t = time.time()
			if t - last_executed < 1/self.execute_rate:
				continue


			# Execute command
			cmdBuffer = Popen(
				self.cmd, shell=1,
				stderr=STDOUT, stdout=PIPE,
				env=os.environ.copy()
			)

			cmdBuffer.wait()
			last_executed = time.time()

			# Write results to self.lineBuffer
			with self.lineBuffer:
				self.lineBuffer.value = cmdBuffer.stdout\
						.read().decode().split("\n")

			self.lineBufferUpdated.set(True)


class Viewer(Thread):
	def __init__(self, refresh_buffer=None, refresh_update=None, display_rate=5):
		""" Handles user display and keyboard interaction via curses.
			Arguments:
				refresh_buffer - Locked object, containing a list of strings, to be copied to a buffer in viewer()'s namespace, with each string each to be displayed on it's own line. 

				refresh_update - Locked object containing a boolean denoting that lineBuffer has been updated, and therefore should be copied to viewer()'s internal display buffer.

				self.display_rate - how many times, per second, the display should be updated
		"""
		Thread.__init__(self)
		self.refresh_buffer = Locked(list()) if refresh_buffer is None else refresh_buffer
		self.refresh_update = Locked(False)  if refresh_update is None else refresh_update
		self.display_buffer = list()
		self.display_rate = display_rate

	def set(self, val):
		""" Sets the content in viewer to val, where val is a list of strings """
		self.refresh_buffer.set(val)
		self.refresh_update.set(True)

	def getBuffer(self):
		""" Returns a tuple of two Locked objects, the first containing a list of strings which points to the viewer's content, and the second containing a boolean which, when set to true, tells the viewer that the content has been refreshed. """
		return self.refresh_buffer, self.refresh_update

	def run(self):
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
			self.display_buffer = None
			
			# Wait until self.refresh_buffer is populated for the first time, then
			# update display
			while True:
				with self.refresh_buffer:
					if self.refresh_buffer.value is not None:
						self.display_buffer = self.refresh_buffer.value.copy()
						break
				time.sleep(0.1)
			
			# Display loop
			while True:

				# Limit display rate
				t = time.time()
				if t - last_refreshed >= 1/self.display_rate:
					last_refreshed = t
					continue
				last_refreshed = t

				screen.clear()
				screen.border(0)
				height, width = screen.getmaxyx()
				
				# If the self.refresh_buffer has been updated, copy it to the
				# internal buffer
				with self.refresh_update as u:
					if u.value:
						with self.refresh_buffer as lb:
							self.display_buffer = lb.value.copy()
						u.value = False

				# Update screen with value from internal display buffer,
				# but only the lines between the top of the scrolled display
				# and the rest forward which can fit on the screen
				# screen.addstr(0, 1, str(len(self.display_buffer)))
				BORDER = 2
				for d, line in enumerate(self.display_buffer[line_num:line_num+height-BORDER]):
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
					if line_num + height + 1 <= len(self.display_buffer):
						line_num += 1
				elif char == ord('g'):
					# scroll to top
					line_num = 0
				elif char == ord('G'):
					# scroll to bottom
					line_num = len(self.display_buffer) - height
				screen.refresh()
		except Exception as e:
			_deinit_curses(screen)
			raise e
		finally:
			_deinit_curses(screen)

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
	viewer = Viewer()
	buffer, bufferUpdated = viewer.getBuffer()

	refresh = CommandBufferRefresh(cmd, buffer, bufferUpdated)

	viewer.start()
	refresh.start()

if __name__=="__main__":
	main()
