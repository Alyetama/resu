#!/usr/bin/env python
# coding: utf-8

import base64
import gzip
import json
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
    """Checkpoint is a class that helps you to resume your progress from where
    you left off in case of a keyboard interrupt (Ctrl+C) or a system crash.

    Parameters
    ----------
    input_data : Optional[Union[Iterable, str]]
        An iterable object or a path to a file containing the data to be
        processed.
    ckpt_file : Optional[str]
        Path to the checkpoint file. If not provided, a checkpoint file will be
        created automatically.

    Attributes
    ----------
    input_data : Optional[Union[Iterable, str]]
        An iterable object or a path to a file containing the data to be
        processed.
    ckpt_file : Optional[str]
        Path to the checkpoint file. If not provided, a checkpoint file will be
        created automatically.
    progress : list
        A list of completed entries.

    Methods
    -------
    insert(input_data)
        Inserts the input data.
    resume(ckpt_file)
        Resumes the progress from the checkpoint file.
    ckpt_io(mode='read')
        Reads or writes the progress to the checkpoint file.
    keyboard_interrupt_handler(sig: int, _)
        Handles the keyboard interrupt.
    read_data() -> Iterable
        Reads the input data from a file.
    _encode(x: Any) -> bytes
        Encodes the input data.
    check_progress() -> list
        Checks the progress.
    record(func: Callable, checkpoint_every: int = 100, \
        show_progress: bool = True, *args, **kwargs) -> list
        Records the progress.
    """

    def __init__(self,
                 input_data: Optional[Union[Iterable, str]] = None,
                 ckpt_file: Optional[str] = None) -> None:
        self.input_data = input_data
        self.ckpt_file = ckpt_file
        self.progress = []

    def insert(self, input_data) -> None:
        """Inserts the input data."""
        self.input_data = input_data

    def resume(self, ckpt_file) -> None:
        """Loads the progress from the checkpoint file."""
        self.ckpt_file = ckpt_file

    def ckpt_io(self, mode='read') -> Optional[list]:
        """Reads or writes the progress to the checkpoint file."""
        if mode == 'write':
            with gzip.open(self.ckpt_file, 'wb') as j:
                pickle.dump(self.progress, j)
        elif mode == 'read':
            with gzip.open(self.ckpt_file, 'rb') as j:
                data = pickle.load(j)
            return data

    def keyboard_interrupt_handler(self, sig: int, _) -> None:
        """Handles the keyboard interrupt."""
        print(f'KeyboardInterrupt (id: {sig}) has been caught...')
        print(f'Saving progress to checkpoint file `{self.ckpt_file}` before '
              'terminating the program gracefully...')
        self.ckpt_io(mode='write')
        sys.exit(1)

    def read_data(self) -> Iterable:
        """Reads the input data from a file."""
        suffix = Path(self.input_data).suffix.lower()
        if suffix in ['.7z', '.7zip']:
            if not py7zr:
                raise ImportError(
                    'py7zr is not installed! Install with: `pip install py7zr`'
                )
            with py7zr.SevenZipFile(self.input_data, 'r') as z:
                for j in z.readall().values():
                    return json.load(j)

        elif suffix == '.json':
            with open(self.input_data) as j:
                return json.load(j)

        elif suffix in ['.gz', '.gzip']:
            with gzip.open(self.input_data, 'rb') as j:
                return json.load(j)

        else:
            raise NotImplementedError(
                'Input file format is not supported! Pass an iterable object '
                'instead.\nSupported file formats for reading directly from '
                'a file: (.json, .7zip|.7z, .gzip|.gz)')

    @staticmethod
    def _encode(x: Any) -> bytes:
        return base64.b64encode(pickle.dumps(x))

    def check_progress(self) -> list:
        """Checks progress and returns remaining data.

        This method checks the progress of the task and returns the remaining
        data items that need to be processed. It also updates the progress
        information based on the data that has already been processed.

        Returns:
            list: A list of data items that need to be processed.
        Raises:
            FileNotFoundError: If the checkpoint file does not exist.
        """
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
        """Records progress of processing data using a given function.

        This method records the progress of processing data using the specified
        function. It iterates over the data, applies the function to each item,
        and records the progress. Checkpoints are saved at specified intervals.

        Args:
            func (Callable): The function to apply to each data item.
            checkpoint_every (int, optional): Interval for saving checkpoints.
                Defaults to 100.
            show_progress (bool, optional): Whether to display progress bars.
                Defaults to True.
            *args: Additional positional arguments to pass to the function.
            **kwargs: Additional keyword arguments to pass to the function.

        Returns:
            list: A list of results from applying the function to the data.
        """
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
