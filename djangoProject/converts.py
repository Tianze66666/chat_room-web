# -*- coding: UTF-8 -*-
# @Author  ：天泽1344
from django.urls.converters import StringConverter


class EmailConverter(StringConverter):
	regex = r'[\w.%+-]+@[\w.-]+\.[a-zA-Z]{2,}'

	def to_python(self, value):
		return value

	def to_url(self, value):
		return value