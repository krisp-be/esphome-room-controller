"""Turn off core dumps for this process.

pcbnew sometimes segfaults. Under WSL every crash is written as a 1-3 GB dump to the Windows
disk, and several of those in a row (make-board.sh retries) froze the whole PC. A process that
is not "dumpable" is skipped by the kernel, so no dump is written. Import this before pcbnew.
"""
import ctypes
import sys

if sys.platform.startswith("linux"):
    try:
        ctypes.CDLL(None).prctl(4, 0, 0, 0, 0)   # PR_SET_DUMPABLE = 0
    except (OSError, AttributeError):
        pass
