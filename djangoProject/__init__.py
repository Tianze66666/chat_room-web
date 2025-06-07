from .celery import app as celery_app


from concurrent.futures import ThreadPoolExecutor

# 最多开 10 个线程（你可以根据服务器性能调大）
thread_pool = ThreadPoolExecutor(max_workers=10)


def submit_task(func, *args, **kwargs):
	thread_pool.submit(func, *args, **kwargs)

__all__ = ('celery_app',submit_task)
