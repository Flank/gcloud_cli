# -*- coding: utf-8 -*- #
# Copyright 2015 Google Inc. All Rights Reserved.
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

"""Test assertions for the sdk_test_base test assertions. We must dig deeper."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.core import config
import googlecloudsdk.core.util.files as file_utils
from tests.lib import sdk_test_base

import six


class TestRetryDecorator(sdk_test_base.WithOutputCapture):
  counter = 0

  def SetUp(self):
    TestRetryDecorator.counter = 0

  # Raises exceptions ValueError(s, 1), ValueError(s,2), ...
  def ThrowValueErrorsThenReturn(self, s, max_exceptions=None):
    TestRetryDecorator.counter += 1
    if (max_exceptions is not None and
        TestRetryDecorator.counter >= max_exceptions):
      return TestRetryDecorator.counter
    error_id = (s, TestRetryDecorator.counter)
    raise ValueError(error_id)

  @sdk_test_base.Retry
  def RetryDefaultThrowValueError(self, x):
    self.ThrowValueErrorsThenReturn(x)

  @sdk_test_base.Retry(max_retrials=4, sleep_ms=0)
  def RetryThrowValueErrorFiveTimes(self, x):
    self.ThrowValueErrorsThenReturn(x)

  @sdk_test_base.Retry
  def testRetryThrowValueErrorsThenSucceed(self):
    self.ThrowValueErrorsThenReturn('a', max_exceptions=2)

  def testRetryDefaultThrowValueError(self):
    with self.assertRaisesRegex(ValueError, '\'a\', 3'):
      self.RetryDefaultThrowValueError(b'a' if six.PY2 else 'a')

    self.AssertErrContains('WARNING: Test failure, but will be retried.')
    self.AssertErrContains('ValueError: (\'a\', 1)')
    self.AssertErrContains('ValueError: (\'a\', 2)')
    self.AssertErrContains('ValueError: (\'a\', 3)')
    self.AssertErrNotContains('ValueError: (\'a\', 4)')

  def testRetryThrowValueErrorFiveTimes(self):
    with self.assertRaisesRegex(ValueError, '\'a\', 5'):
      self.RetryThrowValueErrorFiveTimes('a')

  def testWhy(self):
    explanation = 'because I said so.'

    @sdk_test_base.Retry(why=explanation)
    def foo():
      return 42

    foo()
    self.AssertErrContains(explanation)

  def testNoDecorateWithZeroTimes(self):
    with self.assertRaisesRegex(ValueError,
                                r'Retry requires max_retrials >= 1'):
      @sdk_test_base.Retry(max_retrials=0)
      def unused_foo(x):
        return x


class InstallPropsTest(sdk_test_base.SdkBase):

  def PreSetUp(self):
    temp_path = file_utils.TemporaryDirectory()
    self.addCleanup(temp_path.Close)

    self.props_path = os.path.join(temp_path.path, 'props')

    with open(self.props_path, 'w') as props_file:
      props_file.write('[core]\ndisable_usage_reporting = True\n')

    self.props_patch = self.StartObjectPatch(
        config.Paths, 'installation_properties_path', new=self.props_path)

  def testVerifyStatsFails(self):
    with open(self.props_path, 'w') as props_file:
      props_file.write('[compute]\n')

    with self.assertRaises(AssertionError):
      self._VerifyInstallProps()

    # Change this so that the test won't fail later
    self.install_props = self._GetInstallPropsStats()


class TestSizeLimitDecorator(sdk_test_base.WithOutputCapture):

  def FakeCloseDirs(self, obj):
    if hasattr(obj, '_dirs_size_limit_method'):
      size_limit = getattr(obj, '_dirs_size_limit_method')
      delattr(obj, '_dirs_size_limit_method')
    else:
      size_limit = getattr(obj, '_dirs_size_limit_class', None)
    return size_limit

  def AssertSizeLimit(self, obj, func_name, size_limit):
    getattr(obj, func_name)()
    self.assertEqual(size_limit, self.FakeCloseDirs(obj))

  def SetUp(self):
    self.testclass = self.StartObjectPatch(
        sdk_test_base.SdkBase, '_IsTestClass')
    self.testclass.return_value = True

  def testApplyToFunction(self):
    class FooTest(object):

      @sdk_test_base.SdkBase.SetDirsSizeLimit(42)
      def test1(self):
        pass

      def test2(self):
        pass

    foo = FooTest()
    self.AssertSizeLimit(foo, 'test2', None)
    self.AssertSizeLimit(foo, 'test1', 42)
    self.AssertSizeLimit(foo, 'test2', None)

  def testApplyToClass(self):
    @sdk_test_base.SdkBase.SetDirsSizeLimit(42)
    class FooTest(object):

      def test1(self):
        pass

      def test2(self):
        pass

    foo = FooTest()
    self.AssertSizeLimit(foo, 'test1', 42)
    self.AssertSizeLimit(foo, 'test2', 42)

  def testFunctionOverridesClass(self):
    @sdk_test_base.SdkBase.SetDirsSizeLimit(42)
    class FooTest(object):

      @sdk_test_base.SdkBase.SetDirsSizeLimit(1337)
      def test1(self):
        pass

      def test2(self):
        pass

    foo = FooTest()
    self.AssertSizeLimit(foo, 'test2', 42)
    self.AssertSizeLimit(foo, 'test1', 1337)
    self.AssertSizeLimit(foo, 'test2', 42)

  def testNoDecorator(self):
    class FooTest(object):

      def test(self):
        pass

    foo = FooTest()
    self.AssertSizeLimit(foo, 'test', None)

  def testBadDecoratorBadArg(self):
    with self.assertRaises(Exception):

      @sdk_test_base.SdkBase.SetDirsSizeLimit('1MB')
      class _(object):
        pass

  def testBadDecoratorNoArg(self):
    with self.assertRaises(Exception):

      @sdk_test_base.SdkBase.SetDirsSizeLimit
      class _(object):
        pass

  def testBadDecoratorWrongClass(self):
    self.testclass.return_value = False
    with self.assertRaises(Exception):

      @sdk_test_base.SdkBase.SetDirsSizeLimit
      class _(object):
        pass

  def testBadDecoratorWrongFunction(self):
    with self.assertRaises(Exception):

      class _(object):

        @sdk_test_base.SdkBase.SetDirsSizeLimit(1)
        def _(self):
          pass


if __name__ == '__main__':
  sdk_test_base.main()
