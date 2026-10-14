"""Reuse installed CUDA libraries on Windows without changing the system PATH."""

import os
from pathlib import Path
import sys

_directories = []


def configure_cuda():
    if sys.platform != 'win32' or _directories:
        return
    candidates = [Path(value) for value in os.environ.get('SPEECH_CUDA_DLL_DIRS', '').split(os.pathsep) if value]
    candidates.append(Path(sys.base_prefix) / 'Lib/site-packages/torch/lib')
    for root in (Path.home() / '.cache/lm-studio', Path.home() / '.lmstudio'):
        vendor = root / 'extensions/backends/vendor'
        if vendor.is_dir():
            candidates.extend(p for p in vendor.iterdir() if p.is_dir() and (p / 'cublas64_12.dll').is_file())
    for directory in candidates:
        if directory.is_dir():
            _directories.append(os.add_dll_directory(str(directory)))
            os.environ['PATH'] = str(directory) + os.pathsep + os.environ['PATH']
