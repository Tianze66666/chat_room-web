# -*- coding: UTF-8 -*-
# @Author  ：天泽1344
from rest_framework.response import Response
from rest_framework import status as http_status


class UserResponse:
	@staticmethod
	def success(code=1000, data=None, message="success", status=http_status.HTTP_200_OK):
		res = {
			"code": code,
			"message": message,
			"data": data
		}
		if not data:
			res.pop('data')
		return Response(res, status=status)

	@staticmethod
	def fail(code=1001, data=None, message="fail", status=http_status.HTTP_200_OK):
		res = {
			"code": code,
			"message": message,
			"data": data
		}
		if not data:
			res.pop('data')
		return Response(res, status=status)
