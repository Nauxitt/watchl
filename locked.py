from threading import Lock

class Locked(object):
	def __init__(self, value=None):
		self.value = value
		self._lock = Lock()

	def release(self):
		self._lock.release()

	def acquire(self):
		self._lock.acquire()

	def locked(self):
		return self._lock.locked()

	def __enter__(self):
		self._lock.acquire()
		return self

	def __exit__(self, type, value, traceback):
		self._lock.release()
	
	def set(self, val):
		self.value = val
	
	def get(self):
		return self.value

	def __add__(self, val):
		return self.value + val

	def __sub__(self, val):
		return self.value - val

	def __mul__(self, val):
		return self.value * val

	def __div__(self, val):
		return self.value / val

	def __iadd__(self, val):
		self.value += val
		return self

	def __isub__(self, val):
		self.value -= val
		return self

	def __imul__(self, val):
		self.value *= val
		return self

	def __idiv__(self, val):
		self.value /= val
		return self

if __name__ == "__main__":
	from threading import Thread
	from time import sleep
	
	def t_a(locked):
		for n in range(20):
			with locked as x:
				x += 1
				print(x.value)
			sleep(1/4)

	def t_b(locked):
		for n in range(5):
			with locked as x:
				x *= 2
				print(x.value)
			sleep(7/3)

	x = Locked(1)
	Thread(target=t_a, args=[x]).start()
	Thread(target=t_b, args=[x]).start()
