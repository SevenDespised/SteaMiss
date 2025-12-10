import sys
import os
from pathlib import Path


def ensure_single_instance(app_name="SteaMiss"):
    """确保只有一个实例运行，使用文件锁机制。"""
    import tempfile
    import atexit
    
    # 使用临时目录创建锁文件
    lock_file = Path(tempfile.gettempdir()) / f"{app_name}.lock"
    
    try:
        # 尝试以独占方式打开文件
        if sys.platform == "win32":
            import msvcrt
            lock_fd = os.open(str(lock_file), os.O_CREAT | os.O_EXCL | os.O_RDWR)
            
            def cleanup():
                try:
                    os.close(lock_fd)
                    lock_file.unlink(missing_ok=True)
                except:
                    pass
            
            atexit.register(cleanup)
            return True
        else:
            # Linux/Mac 使用 fcntl
            import fcntl
            lock_fd = open(str(lock_file), 'w')
            fcntl.lockf(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            
            def cleanup():
                try:
                    lock_fd.close()
                    lock_file.unlink(missing_ok=True)
                except:
                    pass
            
            atexit.register(cleanup)
            return True
            
    except (OSError, IOError):
        # 文件已被锁定，说明另一个实例正在运行
        return False
