# -*- coding: UTF-8 -*-
# @Author  ：天泽1344
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError,AuthenticationFailed
from rest_framework_simplejwt.exceptions import InvalidToken


def custom_exception_handler(exc, context):
	response = exception_handler(exc, context)
	# 捕获序列化器验证错误
	if isinstance(exc, ValidationError):
		detail = exc.detail
		message = "参数错误"
		code = 1001
		if isinstance(detail, dict):
			key = next(iter(detail))
			val = detail[key]
			if isinstance(val, list):
				first_error = val[0]
				message = str(first_error)
				if hasattr(first_error, 'code'):
					code = first_error.code
			else:
				message = str(val)
		elif isinstance(exc, list):
			first_error = detail[0]
			message = str(first_error)
			if hasattr(first_error, 'code'):
				code = first_error.code
		else:
			message = str(detail)
			if hasattr(detail, 'code'):
				code = detail.code
		data = {
			'code': code,
			'message': message,
		}
		return Response(data, status=200)
	# 捕获jwt验证失败
	if isinstance(exc, InvalidToken):
		data = {
			'code': 1003,
			'message': 'token过期'
		}
		return Response(data, status=200)

	if isinstance(exc, AuthenticationFailed):
		data = {
			'code': 1003,
			'message': exc.detail
		}
		return Response(data, status=200)

	# 未捕获的错误，直接返回
	return response
