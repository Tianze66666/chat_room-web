# -*- coding: UTF-8 -*-
# @Author  ：天泽1344

import time
import threading


class SnowflakeGenerator:
	def __init__(self, worker_id=1, datacenter_id=1):
		self.worker_id = worker_id & 0x1F  # 5 bit max 31
		self.datacenter_id = datacenter_id & 0x1F  # 5 bit max 31
		self.sequence = 0
		self.last_timestamp = -1
		self.lock = threading.Lock()

	def _time_gen(self):
		return int(time.time() * 1000)

	def _til_next_millis(self, last_timestamp):
		timestamp = self._time_gen()
		while timestamp <= last_timestamp:
			timestamp = self._time_gen()
		return timestamp

	def generate(self):
		with self.lock:
			timestamp = self._time_gen()

			if timestamp < self.last_timestamp:
				raise Exception("Clock moved backwards")

			if timestamp == self.last_timestamp:
				self.sequence = (self.sequence + 1) & 0xFFF  # 12 bit
				if self.sequence == 0:
					timestamp = self._til_next_millis(self.last_timestamp)
			else:
				self.sequence = 0

			self.last_timestamp = timestamp

			id = ((timestamp - 1288834974657) << 22) | (self.datacenter_id << 17) | (
						self.worker_id << 12) | self.sequence
			return id


snowflake = SnowflakeGenerator()


def get_snowflake_id():
	return snowflake.generate()
