# SPDX-License-Identifier: Apache-2.0
import time, os

def timed_read(fn,*args,**kwargs):
    t=time.perf_counter(); value=fn(*args,**kwargs); return value,time.perf_counter()-t

def memory_mb(a): return getattr(a,'nbytes',0)/1024**2

def file_size_gb(path): return os.path.getsize(path)/1024**3
