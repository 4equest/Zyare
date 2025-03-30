from concurrent.futures import ThreadPoolExecutor
from functools import wraps
import threading

# スレッドプールを作成（最大4スレッド）
thread_pool = ThreadPoolExecutor(max_workers=4)

def run_in_background(app):
    """バックグラウンドで関数を実行するデコレータ"""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            def task():
                with app.app_context():
                    f(*args, **kwargs)
            
            thread = threading.Thread(target=task)
            thread.daemon = True  # デーモンスレッドとして設定
            thread.start()
            return thread
        return wrapped
    return decorator

def run_in_thread_pool(app, f):
    """スレッドプールで関数を実行"""
    def task():
        with app.app_context():
            f()
    
    thread_pool.submit(task) 