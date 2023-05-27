import os
import sys
import importlib.util


LOCK_FILENAME = 'dumping.lock'

class DumpLock_Basic:
    def __init__(self, lock_dir):
        self.lock_file = os.path.join(lock_dir, LOCK_FILENAME)

    def __enter__(self):
        if os.path.exists(self.lock_file):
            with open(self.lock_file, 'r', encoding='utf-8') as f:
                print(f.read())
            sys.exit("Another instance is already running, quitting...")
        else:
            with open(self.lock_file, 'w', encoding='utf-8') as f:
                f.write(f'PID: {os.getgid()}: Running')
            print("Acquired lock, continuing.")

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.remove(self.lock_file)
        print("Released lock.")

    # decorator
    def __call__(self, func):
        def wrapper(*args, **kwargs):
            with self:
                return func(*args, **kwargs)
        return wrapper


class DumpLock_Fcntl():
    fcntl = None
    try:
        import fcntl
    except ModuleNotFoundError:
        pass

    def __init__(self, lock_dir):
        if self.fcntl is None:
            raise(ModuleNotFoundError("No module named 'fcntl'", name='fcntl'))
        
        self.lock_file = os.path.join(lock_dir, LOCK_FILENAME)
        self.lock_file_fd = None

    def __enter__(self):
        self.lock_file_fd = open(self.lock_file, 'w')
        try:
            self.fcntl.lockf(self.lock_file_fd, self.fcntl.LOCK_EX | self.fcntl.LOCK_NB)
            print("Acquired lock, continuing.")
        except IOError:
            print("Another instance is already running, quitting.")
            sys.exit(-1)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.lock_file_fd is None:
            raise IOError("Lock file not opened.")
        self.fcntl.lockf(self.lock_file_fd, self.fcntl.LOCK_UN)
        self.lock_file_fd.close()
        os.remove(self.lock_file)
        print("Released lock.")

    # decorator
    def __call__(self, func):
        def wrapper(*args, **kwargs):
            with self:
                return func(*args, **kwargs)
        return wrapper

class DumpLock():
    def __new__(cls, lock_dir):
        fcntl_avaivable = importlib.util.find_spec('fcntl')
        if fcntl_avaivable is not None:
            return DumpLock_Fcntl(lock_dir)
        else:
            return DumpLock_Basic(lock_dir)