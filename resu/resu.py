#!/usr/bin/env python
# coding: utf-8

import base64
import gzip
import pickle
import signal
import sys
import time
from pathlib import Path
from typing import Any, Callable, Iterable, Optional, Union

from tqdm import tqdm

try:
    import py7zr  # optional
except ImportError:
    py7zr = False


class Checkpoint:

    def __init__(self,
                 input_data: Optional[Union[Iterable, str]] = None,
                 ckpt_file: Optional[str] = None):
        self.input_data = input_data
        self.ckpt_file = ckpt_file
        self.progress = []

    def insert(self, input_data):
        self.input_data = input_data

    def resume(self, ckpt_file):
        self.ckpt_file = ckpt_file

    def ckpt_io(self, mode='read'):
        if mode == 'write':
            with gzip.open(self.ckpt_file, 'wb') as j:
                pickle.dump(self.progress, j)
        elif mode == 'read':
            with gzip.open(self.ckpt_file, 'rb') as j:
                data = pickle.load(j)
            return data

    def keyboard_interrupt_handler(self, sig: int, _) -> None:
        print(f'KeyboardInterrupt (id: {sig}) has been caught...')
        print(f'Saving progress to checkpoint file `{self.ckpt_file}` before '
              'terminating the program gracefully...')
        self.ckpt_io(mode='write')
        sys.exit(1)

    def read_data(self) -> Iterable:
        suffix = Path(self.input_data).suffix.lower()
        if suffix in ['.7z', '.7zip']:
            if not py7zr:
                raise ImportError(
                    'py7zr is not installed! Install with: `pip install py7zr`'
                )
            with py7zr.SevenZipFile(self.input_data, 'r') as z:
                for j in z.readall().values():
                    return pickle.load(j)

        elif suffix == '.json':
            with open(self.input_data) as j:
                return pickle.load(j)

        elif suffix in ['.gz', '.gzip']:
            with gzip.open(self.ckpt_file, 'rb') as j:
                return pickle.load(j)

        else:
            raise NotImplementedError(
                'Input file format is not supported! Pass an iterable object '
                'instead.\nSupported file formats for reading directly from '
                'a file: (.json, .7zip|.7z, .gzip|.gz)')

    @staticmethod
    def _encode(x: Any) -> bytes:
        return base64.b64encode(pickle.dumps(x))

    def check_progress(self) -> list:
        if not self.ckpt_file:
            self.ckpt_file = f'{int(time.time())}.ckpt'
            Path(self.ckpt_file).touch()
        else:
            if Path(self.ckpt_file).exists():
                data = self.ckpt_io(mode='read')
                for x in data:
                    self.progress.append(self._encode(x))
                print(f'Resuming from `{self.ckpt_file}`... '
                      f'Skipped {len(data)} completed entries.')
            else:
                raise FileNotFoundError(
                    'The path to the checkpoint file does not exist!')

        if isinstance(self.input_data, str):
            data = self.read_data()
        else:
            data = self.input_data

        data = [x for x in data if self._encode(x) not in self.progress]
        return data

    def record(self,
               func: Callable,
               checkpoint_every: int = 100,
               show_progress: bool = True,
               *args,
               **kwargs) -> list:
        data = self.check_progress()
        if not data:
            print('The progress is at 100%. Nothing to update.')
            return

        signal.signal(signal.SIGINT, self.keyboard_interrupt_handler)

        results = []

        if show_progress:
            iterable = enumerate(tqdm(data))
        else:
            iterable = enumerate(data)

        for n, item in iterable:
            results.append(func(item, *args, **kwargs))
            self.progress.append(self._encode(item))
            n += 1

            if n == checkpoint_every:
                print('Saving progress to checkpoint file: '
                      f'`{self.ckpt_file}`...')
                self.ckpt_io(mode='write')
                checkpoint_every += checkpoint_every

        self.ckpt_io(mode='write')
        return results
