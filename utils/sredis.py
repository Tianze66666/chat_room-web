# -*- coding: UTF-8 -*-
# @Author  ：天泽1344

import redis
from django.conf import settings
from djangoProject.configer import USER_TOKEN_KEY

redis_client = redis.Redis(
    host=settings.REDIS_CACHE_CONFIG['host'],
    port=settings.REDIS_CACHE_CONFIG['port'],
    db=settings.REDIS_CACHE_CONFIG['db'],
    password=settings.REDIS_CACHE_CONFIG['password'],
    decode_responses=settings.REDIS_CACHE_CONFIG['decode_responses'],
)

class ChangeTokenStatusMixin:
    def __init__(self):
        self.ex_access = int(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds())
        self.ex_refresh = int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds())
        self.key = USER_TOKEN_KEY
        self.mode_dic = {
            0:self.set_token,
            1:self.delete_token,
        }
    #self,user_id, refresh_jti=None, access_jti=None,type=0


    def change_user_token(self,user_id, refresh_jti=None, access_jti=None,type=0):
        try:
            self.mode_dic.get(type)(user_id, refresh_jti, access_jti)
        except Exception as e:
            print(e)

    def set_token(self,user_id, refresh_jti=None, access_jti=None):
        pipe = redis_client.pipeline()
        if refresh_jti:
            pipe.set(self.key.format('refresh', user_id, ), refresh_jti, ex=self.ex_refresh)
        if access_jti:
            pipe.set(self.key.format('access', user_id, ), access_jti, ex=self.ex_access)
        pipe.execute()
        return

    def delete_token(self,user_id,*args,**kwargs):
        pipe = redis_client.pipeline()
        pipe.delete(self.key.format('refresh', user_id, ))
        pipe.delete(self.key.format('access', user_id, ))
        pipe.execute()
        return
