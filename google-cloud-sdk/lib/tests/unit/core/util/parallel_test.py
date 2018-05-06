# encoding: utf-8
# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Unit tests for googlecloudsdk.core.util.parallel."""
from __future__ import absolute_import
from __future__ import unicode_literals
import contextlib
import sys
import traceback

from googlecloudsdk.core.util import parallel
from tests.lib import test_case
import six
from six.moves import range  # pylint: disable=redefined-builtin
from six.moves import zip  # pylint: disable=redefined-builtin


_UNICODE_TEST_STRING = 'いろはにほへとちりぬるを'


class MyException(Exception):

  def __eq__(self, other):
    return (isinstance(other, MyException)
            and six.text_type(self) == six.text_type(other))

  def __hash__(self):
    return hash(self)


class UnpickleableError(Exception):

  def __init__(self, msg):
    self.obj = lambda: None  # non-module-level functions are not pickleable
    super(UnpickleableError, self).__init__(msg)

  def __eq__(self, other):
    return (isinstance(other, UnpickleableError) and
            six.text_type(self) == six.text_type(other))


def _PlusOne(num):
  """Adds 1 to num (dummy function for testing)."""
  return num + 1


def _ReturnNone(_):
  """Returns None (dummy function for testing)."""
  return None


def _RaiseError(_):
  raise MyException(_UNICODE_TEST_STRING)


def _ReturnUnpickleableObject(_):
  return lambda: None  # non-module-level functions are not pickleable


def _RaiseUnpickleableError(_):
  raise UnpickleableError(_UNICODE_TEST_STRING)


try:
  _RaiseError(None)
except MyException:
  _REFERENCE_EXC_INFO = sys.exc_info()


try:
  _RaiseUnpickleableError(None)
except UnpickleableError:
  _REFERENCE_UNPICKLEABLE_EXC_INFO = sys.exc_info()


class MultiErrorTest(test_case.TestCase):

  def testMultiErrorStr(self):
    err = parallel.MultiError([MyException(':('), MyException(':(')])
    self.assertEqual(str(err),
                     'One or more errors occurred:\n'
                     ':(\n\n'
                     ':(')

  def testMultiErrorUnicode(self):
    err = parallel.MultiError([
        MyException(_UNICODE_TEST_STRING), MyException(_UNICODE_TEST_STRING)])
    self.assertEqual(six.text_type(err),
                     'One or more errors occurred:\n'
                     'いろはにほへとちりぬるを\n\n'
                     'いろはにほへとちりぬるを')


class PoolTestBase(object):

  def testApply_InvalidState(self):
    with self.assertRaises(parallel.InvalidStateException):
      self.pool.Apply(_PlusOne, (1,))

  def testApplyAsync_InvalidState(self):
    with self.assertRaises(parallel.InvalidStateException):
      self.pool.ApplyAsync(_PlusOne, (1,))

  def testMap_InvalidState(self):
    with self.assertRaises(parallel.InvalidStateException):
      self.pool.Map(_PlusOne, list(range(10)))

  def testMapAsync_InvalidState(self):
    with self.assertRaises(parallel.InvalidStateException):
      self.pool.Map(_PlusOne, list(range(10)))

  def testStart_StartedTwice(self):
    self.pool.Start()
    self.addCleanup(self.pool.Join)
    with self.assertRaises(parallel.InvalidStateException):
      self.pool.Start()()

  def testJoin_InvalidState(self):
    with self.assertRaises(parallel.InvalidStateException):
      self.pool.Join()

  @contextlib.contextmanager
  def _AssertRaisesSimilarTraceback(self, expected_exc_info):
    """Assert that the given function invocation raises."""
    expected_exc_type, expected_exc_value, expected_exc_tb = expected_exc_info
    try:
      yield
    except expected_exc_type:
      _, exc_value, exc_tb = sys.exc_info()
      self.assertEqual(exc_value, expected_exc_value)
      self.assertEqual(traceback.format_tb(exc_tb)[-1],
                       traceback.format_tb(expected_exc_tb)[-1])
    except:  # pylint: disable=bare-except
      exc_type = sys.exc_info()[0]
      self.fail('Expected [{0}] but got [{1}].'.format(expected_exc_info,
                                                       exc_type))
    else:
      self.fail('Expected [{0}] but no exception found.'.format(
          expected_exc_info))

  @contextlib.contextmanager
  def _AssertRaisesMultiError(self, expected_errors):
    try:
      yield
    except parallel.MultiError as multi_err:
      for actual_err, expected_err in zip(multi_err.errors, expected_errors):
        if isinstance(expected_err, type):
          self.assertTrue(isinstance(actual_err, expected_err))
        elif isinstance(expected_err, tuple):
          expected_exc_type, expected_exc_value, expected_exc_tb = expected_err
          exc_type, exc_value, exc_tb = sys.exc_info()
          self.assertEqual(exc_type, expected_exc_type)
          self.assertEqual(exc_value, expected_exc_value)
          self.assertEqual(traceback.format_tb(exc_tb)[-1],
                           traceback.format_tb(expected_exc_tb)[-1])
        else:
          self.assertEqual(actual_err, expected_err)
    except:  # pylint: disable=bare-except
      exc_type = sys.exc_info()[0]
      self.fail('Expected MultiError of {0} but got [{1}]'.format(
          expected_errors, exc_type))
    else:
      self.fail('Expected MultiError of {0} but no execption found.'.format(
          expected_errors))

  def testApply(self):
    with self.pool:
      for arg, expected in zip(range(100), range(1, 101)):
        self.assertEqual(self.pool.Apply(_PlusOne, (arg,)), expected)

  def testApplyAsync(self):
    with self.pool:
      for arg, expected in zip(range(100), range(1, 101)):
        self.assertEqual(self.pool.ApplyAsync(_PlusOne, (arg,)).Get(), expected)

  def testMap(self):
    with self.pool:
      self.assertEqual(self.pool.Map(_PlusOne, list(range(100))),
                       list(range(1, 101)))

  def testMapAsync(self):
    with self.pool:
      self.assertEqual(self.pool.MapAsync(_PlusOne, list(range(100))).Get(),
                       list(range(1, 101)))

  def testApply_None(self):
    with self.pool:
      for arg in range(100):
        self.assertEqual(self.pool.Apply(_ReturnNone, (arg,)), None)

  def testApplyAsync_None(self):
    with self.pool:
      for arg, expected in zip(range(100), range(1, 101)):
        self.assertEqual(self.pool.ApplyAsync(_PlusOne, (arg,)).Get(), expected)

  def testMap_None(self):
    with self.pool:
      self.assertEqual(self.pool.Map(_PlusOne, list(range(100))),
                       list(range(1, 101)))

  def testMapAsync_None(self):
    with self.pool:
      self.assertEqual(self.pool.MapAsync(_PlusOne, list(range(100))).Get(),
                       list(range(1, 101)))

  def testApply_Error(self):
    with self.pool:
      with self._AssertRaisesSimilarTraceback(_REFERENCE_EXC_INFO):
        self.pool.Apply(_RaiseError, (None,))

  def testApply_UnpickleableResult(self):
    with self.pool:
      self.assertIs(
          type(self.pool.Apply(_ReturnUnpickleableObject, (None,))),
          type(lambda: None))

  def testApply_UnpickleableError(self):
    with self.pool:
      with self._AssertRaisesSimilarTraceback(_REFERENCE_UNPICKLEABLE_EXC_INFO):
        self.pool.Apply(_RaiseUnpickleableError, (None,))

  def testMap_Error(self):
    with self.pool:
      with self._AssertRaisesMultiError([MyException(_UNICODE_TEST_STRING),
                                         MyException(_UNICODE_TEST_STRING)]):
        self.pool.Map(_RaiseError, [None, None])

  def testMap_UnpickleableResult(self):
    with self.pool:
      for result in self.pool.Map(_ReturnUnpickleableObject, [None, None]):
        self.assertIs(type(result), type(lambda: None))

  def testMap_UnpickleableError(self):
    with self.pool:
      with self._AssertRaisesMultiError([
          UnpickleableError(_UNICODE_TEST_STRING),
          UnpickleableError(_UNICODE_TEST_STRING)]):
        self.pool.Map(_RaiseUnpickleableError, [None, None])


class DummyPoolTest(test_case.TestCase, PoolTestBase):

  def SetUp(self):
    self.pool = parallel.DummyPool()


class ThreadPoolTest(test_case.TestCase, PoolTestBase):

  def SetUp(self):
    self.pool = parallel.ThreadPool(2)


class GetPoolTest(test_case.TestCase):

  def testGetPool_DummyPool(self):
    pool = parallel.GetPool(1)
    self.assertTrue(isinstance(pool, parallel.DummyPool))

  def testGetPool_ThreadPool(self):
    pool = parallel.GetPool(8)
    self.assertTrue(isinstance(pool, parallel.ThreadPool))
    self.assertEqual(pool.num_threads, 8)

if __name__ == '__main__':
  test_case.main()
