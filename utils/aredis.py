# -*- coding: UTF-8 -*-
# @Author  ：天泽1344

import redis.asyncio as redis

redis_client = redis.Redis(
	host='120.26.129.134',
	port=8000,
	db=4,
	password='Lzh040127！@#￥%',
	decode_responses=True
)


async def async_set(key, value, expire=None):
	await redis_client.set(key, value, ex=expire)


async def async_get(key):
	return await redis_client.get(key)


async def async_delete(key):
	await redis_client.delete(key)
