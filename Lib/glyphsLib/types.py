#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#	 http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.



__all__ = [
	'transform', 'point'
]

import re, datetime, traceback, math

class baseType(object):
	default = None
	def __init__(self, value = None):
		if value:
			self.value = self.read(value)
		else:
			self.value = self.default
	
	def __repr__(self):
		return "<%s %s>" % (self.__class__.__name__, self.plistValue())
	
	def read(self, src):
		"""Return a typed value representing the structured glyphs strings."""
		raise NotImplementedError('%s read' % type(self).__name__)

	def plistValue(self):
		"""Return structured glyphs strings representing the typed value."""
		raise NotImplementedError('%s write' % type(self).__name__)


class point(object):
	"""Read/write a vector in curly braces."""
	dimension = 2
	default = [1, 0]
	regex = re.compile('{%s}' % ', '.join(['([-.e\d]+)'] * dimension))
	def __init__(self, value = None):
		if value:
			self.value = [float(i) for i in self.regex.match(value).groups()]
		else:
			self.value = self.default
	def plistValue(self):
		assert isinstance(self.value, list) and len(self.value) == self.dimension
		return '"{%s}"' % (', '.join(floatToString(v, 3) for v in self.value))

	def __getitem__(self, key):
		return self.value[key]
#		if type(key) is int and key < self.dimension:
#			return self.value[key]
#			if key < len(self.value):
#				return self.value[key]
#			else:
#				return 0
#		else:
#			raise KeyError

	def __setitem__(self, key, value):
		if type(key) is int and key < self.dimension:
			while self.dimension > len(self.value):
				self.value.append(0)
			self.value[key] = value
		else:
			raise KeyError
	def __len__(self):
		return self.dimension

class transform(point):
	"""Read/write a six-element vector."""
	dimension = 6
	default = [1, 0, 0, 1, 0, 0]
	regex = re.compile('{%s}' % ', '.join(['([-.e\d]+)'] * dimension))
	def plistValue(self):
		assert isinstance(self.value, list) and len(self.value) == self.dimension
		return '"{%s}"' % (', '.join(floatToString(v, 5) for v in self.value))	

class glyphs_datetime(baseType):
	"""Read/write a datetime.  Doesn't maintain time zone offset."""
	
	def read(self, src):
		"""Parse a datetime object from a string."""
		# parse timezone ourselves, since %z is not always supported
		# see: http://bugs.python.org/issue6641
		string, tz = src.rsplit(' ', 1)
		datetime_obj = datetime.datetime.strptime(string, '%Y-%m-%d %H:%M:%S')
		offset = datetime.timedelta(hours=int(tz[:3]), minutes=int(tz[0] + tz[3:]))
		return datetime_obj + offset

	def plistValue(self):
		return "\"%s +0000\"" % self.value

	def strftime(self, val):
		try:
			return self.value.strftime(val)
		except:
			return None
			
class color(baseType):

	def read(self, src = None):
		if src == None:
			return None
		elif src[0] == "(":
			src = src[1:-1]
			color = src.split(",")
			color = tuple([int(c) for c in color])
		else:
			color = int(src)
		return color

	def __repr__(self):
		return self.value.__repr__()
	
	def plistValue(self):
		if self.value is not None:
			return str(self.value)
		return None
	

# mutate list in place
def _mutate_list(fn, l):
	assert isinstance(l, list)
	for i in range(len(l)):
		l[i] = fn(l[i])
	return l

def readIntlist(src):
	return _mutate_list(int, src)

def writeIntlist(val):
	return _mutate_list(str, val)


def actualPrecition(Float):
	ActualPrecition = 5
	Integer = round(Float * 100000.0)
	while ActualPrecition >= 0:
		if Integer != round(Integer / 10.0) * 10:
			return ActualPrecition
		
		Integer = round(Integer / 10.0)
		ActualPrecition -= 1
	
	if ActualPrecition < 0:
		ActualPrecition = 0
	return ActualPrecition


def floatToString(Float, precision = 3):
	try:
		ActualPrecition = actualPrecition(Float)
		precision = min(precision, ActualPrecition)
		fractional = math.modf(math.fabs(Float))[0]
		if precision >= 5 and fractional >= 0.00001 and fractional <= 0.99999:
			return "%.5f" % Float
		elif precision >= 4 and fractional >= 0.0001 and fractional <= 0.9999:
			return "%.4f" % Float
		elif precision >= 3 and fractional >= 0.001 and fractional <= 0.999:
			return "%.3f" % Float
		elif precision >= 2 and fractional >= 0.01 and fractional <= 0.99:
			return "%.2f" % Float
		elif precision >= 1 and fractional >= 0.1 and fractional <= 0.9:
			return "%.1f" % Float
		else:
			return "%.0f" % Float
	except:
		print(traceback.format_exc())
		
NSPropertyListNameSet = (
	False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, # 0
	False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, # 16
	False, False, False, False, True, False, False, False, False, False, False, False, False, False, True, True, # 32
	True, True, True, True, True, True, True, True, True, True, False, False, False, False, False, False, # 48
	False, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, # 64
	True, True, True, True, True, True, True, True, True, True, True, False, False, False, False, True, # 80
	False, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, # 96
	True, True, True, True, True, True, True, True, True, True, True, False, False, False, False, False
	)
def needsQuotes(string):
	needsQuotes = False
	if not isinstance(string, (str, unicode)):
		return False
	for c in string:
		d = ord(c)
		if d >= 128 or not NSPropertyListNameSet[d]:
			needsQuotes = True
	if not needsQuotes:
		i = None
		try:
			i = int(string)
		except:
			pass
		if i is not None:
			needsQuotes = True
	return needsQuotes
def feature_syntax_encode(value):
	if isinstance(value, (str, unicode)) and needsQuotes(value):
		
		value = value.replace("\"", "\\\"")
		value = value.replace("\n", "\\012")
		value = '"%s"' % value
	return value