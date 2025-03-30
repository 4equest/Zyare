from concurrent.futures import ThreadPoolExecutor
from functools import wraps
import threading
from typing import Callable, Any

# スレッドプールの作成
executor = ThreadPoolExecutor(max_workers=4)

def run_in_background(func: Callable) -> Callable:
    """関数をバックグラウンドで実行するデコレータ"""
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> None:
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.daemon = True  # メインスレッドが終了したら、このスレッドも終了
        thread.start()
    return wrapper

def run_in_thread_pool(func: Callable) -> Any:
    """関数をスレッドプールで実行する"""
    return executor.submit(func).result() 