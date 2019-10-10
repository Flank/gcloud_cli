# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Set of utilities used in e2e tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime
import logging
import random
import string
import sys
import threading
import time
import traceback

from six.moves import range  # pylint: disable=redefined-builtin


# Use system random to avoid multiple tests that both generate the same
# resource name. System random is really random even on concurrent requests.
_sys_rng = random.SystemRandom()


# This needs to be in a format that allows lexographic sorting of the timestamps
TIMESTAMP_FORMAT = '%Y%m%d-%H%M%S'


def GetResourceNameGenerator(prefix='', suffix='', sequence_start=None,
                             sequence_step=1, count=None, hash_len=4,
                             delimiter='-', timestamp_format=TIMESTAMP_FORMAT):
  """Generates resources names as 'prefix-YYYYMMDD-HHMMSS-XXXX-HASH-suffix'.

  Args:
    prefix: str, every name produced will have this prefix.
    suffix: str, every name produced will have this suffix.
    sequence_start: int, starting sequence number, if None
                    sequence will not appear in the name.
    sequence_step: int, if sequence_start is specified each subsequent name
                   will have sequence number incremented by this amount.
    count: int, total number of names to produce in this generator,
           None for infinity.
    hash_len: int, number of random characters to generate.
    delimiter: str, delimeter to use to separate parts of the name.
    timestamp_format: str, the format to use for timestamp. If None or empty,
                      names will not have timestamp.
  Yields:
    formatted name with above specified attributes.
  """

  items = {}
  template = []

  if prefix:
    items['prefix'] = prefix
    template.append('{prefix}')

  if timestamp_format:
    timestamp_format = delimiter.join(timestamp_format.split('-'))
    items['timestamp'] = datetime.datetime.utcnow().strftime(timestamp_format)
    template.append('{timestamp}')

  sequence = sequence_start or 0
  if sequence_start is not None:
    items['sequence'] = sequence
    items['width'] = (len(str(sequence_start + sequence_step * count))
                      if count else 2)
    template.append('{sequence:0{width}d}')

  if hash_len:
    template.append('{hash}')

  if suffix:
    items['suffix'] = suffix
    template.append('{suffix}')

  while count is None or count > 0:
    if sequence is not None:
      items['sequence'] = sequence
      sequence += sequence_step

    if hash_len:
      items['hash'] = ''.join(
          [_sys_rng.choice(string.ascii_lowercase + string.digits)
           for _ in range(hash_len)])
    yield delimiter.join(template).format(**items)
    if count:
      count -= 1


def PrintAllThreadStacks(out=None):
  """Prints traces for all running threads to "out", a file-like object.

  This function intentionally does not use the normal logging library, because
  one use case it needs to support is debugging hanging tests. In particular,
  some test frameworks capture logging output, such that output from hung tests
  is never actually flushed to a console or file. This function can write to
  a local file, for example, to circumvent log capturing.

  Args:
    out: file, the file-like object to print to.
  """
  if out is None:
    out = sys.stderr

  # pylint:disable=protected-access, There does not appear to be another way
  # to collect the stacktraces for all running threads.
  for thread_id, stack in sys._current_frames().items():
    out.write('Traceback for thread 0x{0:x}:\n'.format(thread_id))

    for filename, line_number, name, text in traceback.extract_stack(stack):
      out.write('  File "{0}", line {1}, in {2}\n'.format(
          filename, line_number, name))
      out.write('    {0}\n'.format(text))


class WatchDog(threading.Thread):
  """A thread that runs a callback if not poked periodically."""

  def __init__(self, timeout_secs=60, timeout_cb=None, timer=time):
    """Constructs a WatchDog.

    Args:
      timeout_secs: int, maximum time allowed to elapse between calls to
          Alive() for timeout_cb not to be called.
      timeout_cb: callable, the callback to call when a timeout is encountered.
          If None, defaults to PrintAllThreadStacks.
      timer: obj, either the "time" module, or an object that has time() and
          sleep() methods, used for all such calls internally.
    """
    super(WatchDog, self).__init__()
    self._timeout_secs = timeout_secs
    self._timeout_cb = timeout_cb
    self._timer = timer
    self._last_alive_time_secs = 0
    self._stopping = False

    if self._timeout_cb is None:
      self._timeout_cb = PrintAllThreadStacks

  def Alive(self):
    """Resets the current timeout for this WatchDog."""
    self._last_alive_time_secs = self._timer.time()

  def Stop(self):
    """Stops this WatchDog, if running. A call to join() should follow."""
    if not self._stopping:
      logging.info('Stopping WatchDog [0x%x]', id(self))
      self._stopping = True

  # Override
  def run(self):
    logging.info('Starting WatchDog [0x%x]', id(self))
    self._last_alive_time_secs = self._timer.time()

    while not self._stopping:
      if self._timer.time() >= self._last_alive_time_secs + self._timeout_secs:
        logging.info('WatchDog firing! [0x%x]', id(self))
        self._timeout_cb()
        break
      self._timer.sleep(0.1)
