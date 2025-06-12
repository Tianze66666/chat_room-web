# -*- coding: UTF-8 -*-
# @Author  ：天泽1344
from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError
from rest_framework import status
from rest_framework.response import Response

# def custom_exception_handler(exc, context):
#     # 调用默认的异常处理器获得标准错误响应
#     response = exception_handler(exc, context)
#     if response is not None:
#         if isinstance(exc, ValidationError):
#             # 修改返回格式
#             customized_response = {
#                 "code": 400,
#                 "message": "参数校验错误",
#                 "errors": response.data  # 包含具体字段错误信息
#             }
#             return Response(customized_response, status=status.HTTP_400_BAD_REQUEST)
#     return response

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        # 统一格式包装错误响应
        custom_response = {
            "code": response.status_code,
            "message": "",
            "data": None,
        }
        if isinstance(response.data, dict):
            # DRF 默认的错误信息
            if "detail" in response.data:
                custom_response["message"] = response.data["detail"]
            else:
                # 错误字段具体信息
                custom_response["message"] = "请求参数错误"
                custom_response["data"] = response.data
        else:
            custom_response["message"] = str(response.data)
        return Response(custom_response, status=response.status_code)
    # 对于未捕获的异常，返回500及统一格式
    # return Response({
    #     "code": 500,
    #     "message": "服务器异常，请稍后重试",
    #     "data": None
    # }, status=500)