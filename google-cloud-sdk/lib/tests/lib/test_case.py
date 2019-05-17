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

"""A base class for all testing in the Cloud SDK."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib
import inspect
import io
import logging
import mimetypes
import os
import pkgutil
import re
import sys
import threading
import time
import traceback
import unittest
import uuid
import warnings

if 'google' in sys.modules:
  # By this time 'google' should NOT be in sys.modules, but some releases of
  # protobuf preload google package via .pth file setting its __path__. This
  # prevents loading of other packages in the same namespace.
  # Below add our vendored 'google' packages to its path if this is the case.
  google_paths = getattr(sys.modules['google'], '__path__', [])
  # pylint:disable=g-import-not-at-top
  import googlecloudsdk
  gcloud_root_dir = os.path.dirname(os.path.dirname(googlecloudsdk.__file__))
  vendored_google_path = os.path.join(gcloud_root_dir, 'third_party', 'google')
  if vendored_google_path not in google_paths:
    google_paths.append(vendored_google_path)

# pylint:disable=g-import-not-at-top
from googlecloudsdk.core import exceptions
from googlecloudsdk.core.console import console_attr
from googlecloudsdk.core.util import encoding as enc
from googlecloudsdk.core.util import files as files_util
# TODO(b/121133803): This needs to be imported before any test starts because
# we mock out Thread in the base test case here and if the import happens after
# the mock, things don't work.
from googlecloudsdk.core.util import parallel  # pylint: disable=unused-import
from googlecloudsdk.core.util import pkg_resources
from googlecloudsdk.core.util import platforms

import mock
import portpicker
import six

try:
  # Assign import to a variable so it can be mocked consistently.
  pytest = __import__('pytest')
except ImportError:
  pytest = None


class Error(BaseException):
  """A base exception for this module."""
  pass


class InvalidTestClassError(Error):
  """An exception for when the structure of a test class is invalid."""
  pass


def main():
  unittest.main()


def _IsBinaryMediaPath(path):
  """Returns True if path/url has a binary media extension.

  Args:
    path: str, A path or url to check. Only the name is checked. The
      corresponding file/resource does not need to exist.

  Returns:
    True if path/url has a binary media extension.
  """
  source_extensions = ['.bash', '.html', '.js', '.md', '.py', '.sh']
  # Check easy source extensions first. These cover source files that might
  # have mime type application/* instead of or in addition to text/* below.
  if os.path.splitext(path)[1].lower() in source_extensions:
    return False
  # Fall back to mime types.
  media_type_subtype, _ = mimetypes.guess_type(path)
  if not media_type_subtype:
    return False
  media_type = media_type_subtype.split('/')[0]
  return media_type in ('application', 'audio', 'image', 'video')


class ThreadCleanupError(Error):
  """An exception indicating that not all created threads were cleaned up."""
  pass


class _ThreadInfo(object):

  def __init__(self, thread, creation_stack_trace):
    self.thread = thread
    self.creation_stack_trace = creation_stack_trace


class FakeStd(io.BytesIO):
  """A class to use for mocking sys.stdout, sys.stderr, and sys.stdin.

  In this class, we attempt to mimick the behavior of the streams on both Python
  2 and 3 so they behave the same under test.

  On Python 3, read() and write() take text and the buffer attribute is used to
  read and write raw bytes. On Python 2, read() and write() takes bytes
  (although text is accepted and sometimes works).

  Under the covers we always store the data as bytes so we can support binary
  reading and writing. On Python 3 we encode and decode automatically so it
  works with reading and writing text.
  """

  def __init__(self, *args, **kwargs):
    super(FakeStd, self).__init__(*args, **kwargs)
    self.errors = None
    self.encoding = 'ascii'

  @property
  def buffer(self):
    # Buffer always contains the byte string (available on python 3 only). Here
    # We just return the byte stream itself (since it's already bytes).
    return super(FakeStd, self)

  def read(self, *args, **kwargs):
    # Get raw data from the buffer.
    data = self.buffer.read(*args, **kwargs)
    if not six.PY2:
      # Only Python 3, return text strings.
      data = console_attr.Decode(data)
    # On Python 2, return byte strings.
    return data

  def readline(self, *args, **kwargs):
    # Get raw data from the buffer.
    data = self.buffer.readline(*args, **kwargs)
    if not six.PY2:
      # Only Python 3, return text strings.
      data = console_attr.Decode(data)
    # On Python 2, return byte strings.
    return data

  def readlines(self, *args, **kwargs):
    # Get raw data from the buffer.
    # pylint:disable=g-builtin-op, We need to pass args so can't use the default
    # iterator.
    for line in self.buffer.readlines(*args, **kwargs):
      if not six.PY2:
        # Only Python 3, return text strings.
        yield console_attr.Decode(line)
      else:
        # On Python 2, return byte strings.
        yield line

  def __iter__(self):
    return self.readlines()

  def write(self, s):
    # Unknown object type.
    if not isinstance(s, six.string_types):
      raise TypeError('expected a string or other character buffer object')

    encoding = console_attr.GetConsoleAttr().GetEncoding()

    if six.PY2:
      # TODO(b/72815887): Make this an error
      # On Py2, we should be getting bytes here, but we don't enforce it because
      # stdout is flexible about that and can take both. If we get unicode,
      # encode using ascii because that's what happens by default. Eventually
      # we should remove this so we can catch everyone that should be using
      # unicode but isn't
      if not isinstance(s, six.binary_type):
        s = s.encode(encoding)
    else:
      if not isinstance(s, six.text_type):
        raise TypeError('expected a text string')
      s = s.encode(encoding)

    return self.buffer.write(s)


class TestCase(unittest.TestCase, object):
  """A base class for all Cloud SDK tests.

  It handles the chaining of set up and tear down methods (since pyunit does
  not actually do this on its own).  This let's us maintain the set up and
  tear down behavior when using test base classes as mix-ins.
  """
  _BAD_METHODS = [
      ('setUp', 'SetUp'),
      ('tearDown', 'TearDown'),
      ('setUpClass', 'SetUpClass'),
      ('tearDownClass', 'TearDownClass')
  ]

  _WHITELISTED_ENV_VARS = set([
      '_ARGCOMPLETE_COMP_WORDBREAKS',
      'PYTEST_CURRENT_TEST',
  ])

  def __init__(self, *args, **kwargs):
    # Do checking of structure of all classes in the hierarchy.
    for clazz in self.__Subclasses():
      for method, alt in TestCase._BAD_METHODS:
        if method in clazz.__dict__:
          raise InvalidTestClassError(
              'Class [{clazz}] defines a [{method}] method.  To get proper '
              'method chaining, implement [{alt}] instead.'
              .format(clazz=clazz.__name__, method=method + '()',
                      alt=alt + '()'))
    super(TestCase, self).__init__(*args, **kwargs)

    if six.PY2:
      # Using this assertRaisesRegex in py2 shuts up the py3 assertRaisesRegexp
      # deprecation warning.
      self.assertRaisesRegex = self._assertRaisesRegex  # pylint: disable=invalid-name

      # Using this assertRegex in py2 shuts up the py3 assertRegexp
      # deprecation warning.
      self.assertRegex = self._assertRegex  # pylint: disable=invalid-name

      # Backporting assertCountEqual to py2 to get python2 tests to pass.
      self.assertCountEqual = self._assertCountEqual  # pylint: disable=invalid-name
    else:
      # assertRegexpMatches works but we need ...
      self.assertNotRegexpMatches = self.assertNotRegex  # pylint: disable=invalid-name

  def _assertRaisesRegex(self, *args, **kwargs):  # pylint: disable=invalid-name
    """python3 really hates that trailing p."""
    return six.assertRaisesRegex(self, *args, **kwargs)

  def _assertRegex(self, *args, **kwargs):  # pylint: disable=invalid-name
    """python3 really hates that trailing p."""
    return six.assertRegex(self, *args, **kwargs)

  def _assertCountEqual(self, *args, **kwargs):  # pylint: disable=invalid-name
    """Accounts for the removal of assertItemsEqual in Python 3."""
    return six.assertCountEqual(self, *args, **kwargs)

  @classmethod
  def __Subclasses(cls):
    for clazz in cls.__mro__:
      if clazz == TestCase:
        # Stop checking once we get to up to this class.
        break
      if not issubclass(clazz, TestCase):
        # Do not process random classes in the hierarchy that are not rooted
        # in TestCase.
        continue
      yield clazz
    return

  @classmethod
  def setUpClass(cls):
    for cls in reversed(list(cls.__Subclasses())):
      if 'SetUpClass' in cls.__dict__:
        cls.SetUpClass()

  @classmethod
  def tearDownClass(cls):
    for cls in cls.__Subclasses():
      if 'TearDownClass' in cls.__dict__:
        cls.TearDownClass()

  def setUp(self):
    # TODO(b/77644889): Figure out what's going on and remove this warning skip.
    # This gets reset by unittest after each test case so it needs to be done
    # here in setUp().
    if not six.PY2:
      warnings.filterwarnings(
          action='ignore',
          message='unclosed <ssl.SSLSocket',
          # This only exists in Python 3.
          category=ResourceWarning)  # pylint:disable=undefined-variable
    # Make sure certain things are restored between tests
    self._originals = {
        'working directory': os.getcwd(),
        'environment': enc.EncodeEnv(dict(os.environ)),
        'system paths': list(sys.path),
        'stdout': sys.stdout,
        'stderr': sys.stderr,
        'stdin': sys.stdin
    }

    # This is done separately to make sure _originals is included in the state
    self._originals['state'] = set(dir(self))

    self.addCleanup(self._CleanupTestState)
    self._CatchThreadCreation()
    self._CatchCustomSignalHandling()
    console_attr.GetConsoleAttr(encoding='ascii')

    for cls in reversed(list(self.__Subclasses())):
      if 'PreSetUp' in cls.__dict__:
        cls.PreSetUp(self)
    for cls in reversed(list(self.__Subclasses())):
      if 'SetUp' in cls.__dict__:
        cls.SetUp(self)

  def tearDown(self):
    # stdout and stderr get logged only in the base class's TearDown method,
    # so we need to let that get executed
    exception_context = None
    for cls in self.__Subclasses():
      if 'TearDown' in cls.__dict__:
        try:
          cls.TearDown(self)
        # pylint:disable=broad-except, we will be reraising one of these
        # exceptions anyway
        except Exception as e:
          exception_context = exceptions.ExceptionContext(e)
    if exception_context:
      exception_context.Reraise()

  @contextlib.contextmanager
  def _VerifyTestCleanup(self, name, target):
    self.maxDiff = None  # pylint: disable=invalid-name
    self.assertEqual(self._originals[name], target,
                     '{name} was left in an altered state'.format(name=name))
    yield

  def _CleanupTestState(self):
    for attr in set(dir(self)) - self._originals['state']:
      delattr(self, attr)

    with self._VerifyTestCleanup('stdout', sys.stdout):
      sys.stdout = self._originals['stdout']

    with self._VerifyTestCleanup('stderr', sys.stderr):
      sys.stderr = self._originals['stderr']

    with self._VerifyTestCleanup('stdin', sys.stdin):
      sys.stdin = self._originals['stdin']

    with self._VerifyTestCleanup('working directory', os.getcwd()):
      os.chdir(self._originals['working directory'])

    with self._VerifyTestCleanup('system paths', sys.path):
      sys.path[:] = self._originals['system paths']

    with self._VerifyTestCleanup(
        'environment',
        self._GrabEnvironment(self._originals['environment'])):
      os.environ.clear()
      os.environ.update(self._originals['environment'])

    self._originals.clear()

  def _GrabEnvironment(self, ref_environ=None):
    ref_environ = ref_environ or {}
    env = {}
    for k, v in six.iteritems(os.environ):
      # Ignore environment changes due to property settings.
      if k.startswith('CLOUDSDK_') or k in self._WHITELISTED_ENV_VARS:
        # Derive whitelisted from reference environment.
        if k in ref_environ:
          env[k] = ref_environ[k]
      else:
        env[k] = v
    # In case whitelisted env var got deleted during test, restore it.
    for k, v in six.iteritems(ref_environ):
      if k not in os.environ and (k.startswith('CLOUDSDK_') or
                                  k in self._WHITELISTED_ENV_VARS):
        env[k] = v

    return env

  def _CatchCustomSignalHandling(self):
    # Whenever a signal handler is registered, catch it and make it only handle
    # arbiter signals.
    self._registered_signal_handlers = {}

    # Mock signal.signal to put the signal handlers in our own list.
    def _StoreSignalHandler(*args, **unused_kwargs):
      signal_type, signal_handler = args[:2]  # pylint: disable=unbalanced-tuple-unpacking
      old_handler = self._registered_signal_handlers.get(signal_type)
      if not signal_handler:
        self._registered_signal_handlers.pop(signal_type, None)
      else:
        self._registered_signal_handlers[signal_type] = signal_handler
      return old_handler
    self.StartPatch('signal.signal').side_effect = _StoreSignalHandler

    # Mock signal.getsignal to return None or the handler we have on file.
    def _GetSignalHandler(*args, **unused_kwargs):
      signal_type = args[0]
      return self._registered_signal_handlers.get(signal_type, None)
    self.StartPatch('signal.getsignal').side_effect = _GetSignalHandler

    # Mock os.kill to manually call the handler we have mocked.
    backup_kill = os.kill
    def _PropagateSignal(*args, **kwargs):
      pid, sig = args[:2]  # pylint: disable=unbalanced-tuple-unpacking
      if pid != os.getpid():
        # Behave normally if it's not for us. Just in case.
        return backup_kill(*args, **kwargs)
      self.assertIn(sig, six.iterkeys(self._registered_signal_handlers),
                    'Signal sent does not have a handler registered!')
      return self._registered_signal_handlers[sig](sig, None)
    self.StartPatch('os.kill').side_effect = _PropagateSignal

    # Check that at the end of the tests we have all our signal handlers
    # cleaned up.
    def _CheckSignalHandler():
      self.assertEqual(
          0, len(self._registered_signal_handlers),
          'Test registers signal handler without restoring the old handler '
          'before test ends. Registered signal handlers for following signals: '
          + six.text_type(list(six.iterkeys(self._registered_signal_handlers))))
    self.addCleanup(_CheckSignalHandler)

  def _CatchThreadCreation(self):
    # Whenever a thread is created, hold on to a reference so that we can block
    # on its completion.
    backup_thread = threading.Thread
    self._created_threads = []
    def StoreCreatedThread(*args, **kwargs):
      current_stack = [enc.Decode(s) for s in traceback.format_stack()]
      # Skip the last few entries to get to the Thread creation call
      # (1) Mock: `__call__` (2) Mock: `_mock_call` (3) StoreCreatedThread
      current_stack = current_stack[:-3]
      thread_info = _ThreadInfo(backup_thread(*args, **kwargs),
                                ''.join(current_stack))
      self._created_threads.append(thread_info)
      return thread_info.thread
    self.StartPatch('threading.Thread').side_effect = StoreCreatedThread

    # Check that all threads are dead before a test ends.
    def _CheckThreadsAreDead():
      num_retrials = 3
      while True:
        alive_threads = [info for info in self._created_threads
                         if info.thread.isAlive()]
        if not alive_threads:
          break
        if num_retrials:
          time.sleep(0.1)  # Give some time for threads to shutdown.
          num_retrials -= 1
        else:
          raise ThreadCleanupError(
              'Some threads created by the test are not cleaned up!\n\n' +
              '\n\n'.join(info.creation_stack_trace for info in alive_threads))

    self.addCleanup(_CheckThreadsAreDead)

  def JoinAllThreads(self, timeout=10):
    """Call Thread.join for all threads created in the test.

    Args:
      timeout: float, a timeout for joining each thread

    Raises:
      ThreadCleanupError: if not all threads finished running in the given time
    """
    for thread_info in self._created_threads:
      thread_info.thread.join(timeout)

  def IsOnWindows(self):
    """Returns true if we are running on Windows."""
    return Filters._IS_ON_WINDOWS  # pylint: disable=protected-access

  def IsOnLinux(self):
    """Returns true if we are running on Linux."""
    return Filters._IS_ON_LINUX  # pylint: disable=protected-access

  def IsOnMac(self):
    """Returns true if we are running on Mac."""
    return Filters._IS_ON_MAC  # pylint: disable=protected-access

  @staticmethod
  def IsInDeb():
    """Returns true if we are running from within a Debian package."""
    return Filters._IS_IN_DEB

  @staticmethod
  def IsInRpm():
    """Returns true if we are running from within an RPM package."""
    return Filters._IS_IN_RPM

  def StartPatch(self, *args, **kwargs):
    """Runs mock.patch with the given args, and returns the mock object.

    This starts the patcher, returns the mock object, and registers the patcher
    to stop on test teardown.

    Args:
      *args: The args to pass to mock.patch()
      **kwargs: The kwargs to pass to mock.patch()

    Returns:
      Mock, The result of starting the patcher.
    """
    patcher = mock.patch(*args, **kwargs)
    self.addCleanup(patcher.stop)
    return patcher.start()

  def StartDictPatch(self, *args, **kwargs):
    """Runs mock.dict.patch with the given args, and returns the mock object.

    This starts the patcher, returns the mock object, and registers the patcher
    to stop on test teardown.

    Args:
      *args: The args to pass to mock.patch.dict()
      **kwargs: The kwargs to pass to mock.patch.dict()

    Returns:
      Mock, The result of starting the patcher.
    """
    patcher = mock.patch.dict(*args, **kwargs)
    self.addCleanup(patcher.stop)
    return patcher.start()

  def StartEnvPatch(self, env_vars, clear=False):
    """Same as StartDictPatch but specifically for os.environ.

    It automatically handles the encoding of environment variable keys and
    values.

    Args:
      env_vars: {str: str}, The key value pairs to put in the environment.
      clear: bool, True to clear the environment before setting new values.

    Returns:
      Mock, The result of starting the patcher.
    """
    self.StartDictPatch(os.environ, clear=clear)
    for key, value in six.iteritems(env_vars):
      enc.SetEncodedValue(os.environ, key, value)

  def StartObjectPatch(self, *args, **kwargs):
    """Runs mock.patch.object with the given args, and returns the mock object.

    This starts the patcher, returns the mock object, and registers the patcher
    to stop on test teardown.

    Args:
      *args: The args to pass to mock.patch.object()
      **kwargs: The kwargs to pass to mock.patch.object()

    Returns:
      Mock, The result of starting the patcher.
    """
    patcher = mock.patch.object(*args, **kwargs)
    self.addCleanup(patcher.stop)
    return patcher.start()

  def StartPropertyPatch(self, *args, **kwargs):
    """Runs mock.patch.object with the given args, and returns the mock object.

    This uses new_callable=mock.PropertyMock to correctly mock a property.
    This starts the patcher, returns the mock object, and registers the patcher
    to stop on test teardown.

    Args:
      *args: The args to pass to mock.patch.object()
      **kwargs: The kwargs to pass to mock.patch.object()

    Returns:
      Mock, The result of starting the patcher.
    """
    return self.StartObjectPatch(
        *args, new_callable=mock.PropertyMock, **kwargs)

  def StartModulePatch(self, name, module_mock):
    """Patches an entire module out with a mock of that module.

    This should not generally need to be used, but sometimes an entire module
    needs to be replaced.  This patches the sys.modules dict, and
    also patches every loaded module to replace named references to the module.

    Args:
      name: str, The name of the module that is being patched
      module_mock: The replacement module

    Returns:
      module_mock
    """
    # Patch the module dictionary for the module itself.
    patcher = mock.patch.dict(sys.modules, [(name, module_mock)])
    self.addCleanup(patcher.stop)
    patcher.start()

    # Change all loaded references to the module.
    # Create a copy because the dict can change as we are patching it.
    modules = dict(sys.modules)
    for n, mod in six.iteritems(modules):
      if n == name:
        continue
      if hasattr(mod, name):
        self.StartObjectPatch(mod, name, module_mock)

    return module_mock

  def RmTree(self, path):
    if os.path.exists(path):
      files_util.RmTree(path)

  def SkipTest(self, message=None):
    """Call this from SetUp to skip running the test itself."""
    if message:
      logging.info(message)
    else:
      logging.info('Skipping test.')
    raise unittest.SkipTest

  @contextlib.contextmanager
  def SkipTestIfRaises(self, exception_type, message=None):
    """Context manager to skip a test if some setup code raises an exception."""
    try:
      yield
    except exception_type:
      if message:
        logging.info(message)
      else:
        logging.info('Expected exception [%s] raised. Skipping test.',
                     exception_type.__name__)
      raise unittest.SkipTest


class WithContentAssertions(TestCase):
  """A helper class with content assertions."""

  def SetUp(self):
    self._show_contents_on_failure = True

  def _CompareFail(self, reason, expected, actual):
    """Calls self.fail() showing the reason and expected and actual values.

    Args:
      reason: string, The reason for the assrtion failure.
      expected: string, The expected value.
      actual: string, The actual value.
    """
    if '\n' in expected.rstrip('\n') or '\n' in actual.rstrip('\n'):
      # A mismatch on an expected or actual value containing an embedded
      # newline yields a readable failure message that is easy to scrape.
      msg = ('{reason}:\n<<<EXPECTED>>>\n{expected}\n'
             '<<<ACTUAL>>>\n{actual}\n<<<END>>>'.format(
                 reason=reason, expected=expected, actual=actual))
    else:
      msg = ('{reason} [{expected}]: [{actual}]'.format(
          reason=reason, expected=expected, actual=actual))

    # TODO(b/73656229): We should not need to encode here, but
    # assertRaisesRegexp() doesn't handle unicode correctly.
    self.fail(console_attr.SafeText(msg))

  def _AssertCompare(self, expected, actual, name, normalize_space=False,
                     actual_filter=None, compare=None, success=None,
                     description=None, golden=False):
    r"""Assert comparison of expected and actual stdout or stderr contents.

    Args:
      expected: string, The the expected comparison value.
      actual: string, The actual comparison value.
      name: The contents name.
      normalize_space: bool or str, True to normalize ' \t\v' characters,
        otherwise a set of characters to normalize. Sequences of the normalize
        are collapsed into a single space character. Leading and trailing
        characters to be normalized are stripped from each line. " a \nb\t c "
        normalizes to "a\nb c".
      actual_filter: str f(actual), A function that filters the actual value
        before compare(expected, actual) is applied.
      compare: f(expected, actual), A comparison function that returns True
        on success and False on failure.
      success: bool, The successful compare(expected, actual) return value.
      description: str, A word or phrase describing "compare", used in
        self.fail().
      golden: bool, The expected value is from a golden file that can be updated
        by update-regressions.sh.
    """

    if os.linesep != '\n' and '\n' in expected:
      actual = actual.replace(os.linesep, '\n')
      expected = expected.replace(os.linesep, '\n')
    if normalize_space:
      expected = NormalizeSpace(normalize_space, expected)
      actual = NormalizeSpace(normalize_space, actual)
    if actual_filter:
      actual = actual_filter(actual)
    if bool(compare(expected, actual)) == success:
      return

    self._show_contents_on_failure = False
    expected, actual = _StripLongestCommonSpaceSuffix(expected, actual)
    reason = '{name} {word} not {description} the expected {value}'.format(
        name=name if os.path.sep == '/' else name.replace(os.path.sep, '/'),
        word='does' if success else 'should',
        description=description,
        value='pattern' if description == 'match' else 'value')
    if golden:
      reason += ('\n(see update-regressions.sh --help)')

    try:
      self._CompareFail(reason, expected, actual)
    except UnicodeError:
      # Output encoding mismatch, most likely invalid ASCII characters.
      # Try again with invalid ASCII characters encoded as \uXXXX unicode
      # escapes for valid unicode characters or \xXX for invalid bytes.
      # We don't do the encoding right away because we don't know if the output
      # can handle unicode or utf8 encoding, and we don't know if the input
      # was unicode, iso 8 bit exteneded, or some other encoding.
      reason = console_attr.SafeText(reason)
      expected = console_attr.SafeText(expected)
      actual = console_attr.SafeText(actual)
      # It shouldn't fail this time. If it does we'll want to see the execption
      # and trace anyway.
      self._CompareFail(reason, expected, actual)

  def _AssertContains(self, expected, actual, name, normalize_space=False,
                      actual_filter=None, success=True, golden=False):
    self._AssertCompare(
        expected, actual, name, normalize_space=normalize_space,
        actual_filter=actual_filter,
        compare=lambda expected, actual: expected in actual,
        description='contain', success=success, golden=golden)

  def _AssertEquals(self, expected, actual, name, normalize_space=False,
                    actual_filter=None, success=True):
    self._AssertCompare(
        expected, actual, name, normalize_space=normalize_space,
        actual_filter=actual_filter,
        compare=lambda expected, actual: expected == actual,
        description='equal', success=success)

  def _AssertMatches(self, expected, actual, name, normalize_space=False,
                     actual_filter=None, success=True):
    self._AssertCompare(
        expected, actual, name, normalize_space=normalize_space,
        actual_filter=actual_filter,
        compare=lambda expected, actual: re.search(expected, actual, re.M|re.S),
        description='match', success=success)


class Base(WithContentAssertions):
  """A base class for tests that use filesystem."""

  def SetUp(self):
    # This makes pyunit apply any custom failure messages to the original
    # generated message.
    self.longMessage = True  # pylint: disable=invalid-name

    # Normalize newline endings on Windows for multi-line string asserts.
    if self.IsOnWindows():
      old_assert = Base.assertMultiLineEqual

      def MyAssert(base_self, expected, actual, *args, **kwargs):
        # Matches newlines without a preceding carriage return.
        regex = re.compile(r'(^|[^\r])\n', flags=re.MULTILINE)
        replacement = r'\1\r\n'
        expected = regex.sub(replacement, expected)
        actual = regex.sub(replacement, actual)
        old_assert(base_self, expected, actual, *args, **kwargs)
      self.StartObjectPatch(Base, 'assertMultiLineEqual', MyAssert)

  def Touch(self, directory, name=None, contents='', makedirs=False):
    """Creates a file with the given contents.

    Args:
      directory: str, A directory to create the file in.
      name: str, An optional name for the file.  If None, a random name will be
        used.
      contents: str, The contents to write to the file.
      makedirs: bool, If true makes any directories necessary for the specified
        directory to exist.

    Returns:
      str, The full path of the file that was created.
    """
    if name:
      # Make sure name does not have any path parts, so that makedirs can
      # create dirs if needed.
      full_path = os.path.join(directory, name)
      directory = os.path.dirname(full_path)
      name = os.path.basename(full_path)
    else:
      name = self.RandomFileName()
    if makedirs and not os.path.exists(directory):
      os.makedirs(directory)

    # TODO(b/73165575): Don't do this once we update all the tests to use text
    # strings by default.
    path = os.path.join(directory, name)
    if isinstance(contents, six.text_type):
      files_util.WriteFileContents(path, contents)
    else:
      files_util.WriteBinaryFileContents(path, contents)

    return path

  def RandomFileName(self):
    return uuid.uuid4().hex

  def AssertDirectoryExists(self, *path_parts):
    """Asserts that the given directory exists.

    Args:
      *path_parts: str, The pieces of the path to combine to get the path to the
        directory.
    """
    path = os.path.join(*path_parts)
    if not os.path.isdir(path):
      self.fail('Expected directory [{0}] does not exist.'.format(path))

  def AssertFileExists(self, *path_parts):
    """Asserts that the given file exists."""
    path = os.path.join(*path_parts)
    if not os.path.isfile(path):
      self.fail('Expected file [{0}] does not exist.'.format(path))

  def AssertFileNotExists(self, *path_parts):
    """Asserts that the given file does not exist."""
    path = os.path.join(*path_parts)
    if os.path.isfile(path):
      self.fail('File [{0}] exists but was not expected to.'.format(path))

  def AssertFileExistsWithContents(self, expected_contents, *path_parts,
                                   **kwargs):
    """Asserts that the given file exists and has the expected contents.

    Args:
      expected_contents: str, The contents that should be in the file.
      *path_parts: str, The pieces of the path to combine to get the path to the
        file.
      **kwargs: _AssertContains kwargs.
    """
    self.AssertFileExists(*path_parts)
    path = os.path.join(*path_parts)
    self.AssertFileEquals(expected_contents, path, **kwargs)

  def AssertFileContains(self, expected, path, normalize_space=False,
                         actual_filter=None, success=True):
    self._AssertContains(expected, files_util.ReadFileContents(path), path,
                         normalize_space=normalize_space,
                         actual_filter=actual_filter, success=success)

  def AssertFileNotContains(self, expected, path, normalize_space=False,
                            actual_filter=None, success=False):
    self._AssertContains(expected, files_util.ReadFileContents(path), path,
                         normalize_space=normalize_space,
                         actual_filter=actual_filter, success=success)

  def AssertFileEquals(self, expected, path, normalize_space=False,
                       actual_filter=None, success=True):
    self._AssertEquals(expected, files_util.ReadFileContents(path), path,
                       normalize_space=normalize_space,
                       actual_filter=actual_filter, success=success)

  def AssertBinaryFileEquals(self, expected, path, success=True):
    with io.open(path, mode='rb') as f:
      contents = f.read()
    self._AssertEquals(
        expected, contents, path, normalize_space=False, success=success)

  def AssertFileNotEquals(self, expected, path, normalize_space=False,
                          actual_filter=None, success=False):
    self._AssertEquals(expected, files_util.ReadFileContents(path), path,
                       normalize_space=normalize_space,
                       actual_filter=actual_filter, success=success)

  def AssertFileMatches(self, expected, path, normalize_space=False,
                        actual_filter=None, success=True):
    self._AssertMatches(expected, files_util.ReadFileContents(path), path,
                        normalize_space=normalize_space,
                        actual_filter=actual_filter, success=success)

  def AssertFileNotMatches(self, expected, path, normalize_space=False,
                           actual_filter=None, success=False):
    self._AssertMatches(expected, files_util.ReadFileContents(path), path,
                        normalize_space=normalize_space,
                        actual_filter=actual_filter, success=success)

  @staticmethod
  def GetPort():
    """Gets a valid port to use for the test.

    Returns:
      A valid port not used by another test.
    """
    return six.text_type(portpicker.PickUnusedPort())


class InvalidFilterError(Exception):
  pass


def _ModulePresent(module_path):
  try:
    return bool(pkgutil.find_loader(module_path))
  except ImportError:
    return False


class Filters(object):
  """Methods for determining when tests run and when they should be skipped."""

  _IS_ON_WINDOWS = (platforms.OperatingSystem.Current() ==
                    platforms.OperatingSystem.WINDOWS)
  _IS_ON_LINUX = (platforms.OperatingSystem.Current() ==
                  platforms.OperatingSystem.LINUX)
  _IS_ON_MAC = (platforms.OperatingSystem.Current() ==
                platforms.OperatingSystem.MACOSX)
  _IS_IN_DEB = os.environ.get('CLOUDSDK_TEST_PLATFORM', '') == 'deb'
  _IS_IN_RPM = os.environ.get('CLOUDSDK_TEST_PLATFORM', '') == 'rpm'
  _IS_IN_KOKORO = 'KOKORO_JOB_NAME' in os.environ

  @staticmethod
  def IsOnWindows():
    """Returns true if we are running on Windows."""
    return Filters._IS_ON_WINDOWS

  @staticmethod
  def IsOnLinux():
    """Returns true if we are running on Linux."""
    return Filters._IS_ON_LINUX

  @staticmethod
  def IsOnMac():
    """Returns true if we are running on Mac."""
    return Filters._IS_ON_MAC

  @staticmethod
  def IsInDeb():
    """Returns true if we are running from within a Debian package."""
    return Filters._IS_IN_DEB

  @staticmethod
  def IsInRpm():
    """Returns true if we are running from within an RPM package."""
    return Filters._IS_IN_RPM

  @staticmethod
  def _ShouldDecorate(thing):
    """Returns whether or not thing is something to decorate."""
    return (thing is None or inspect.isclass(thing) or
            inspect.ismethod(thing) or inspect.isfunction(thing))

  # Do not call these directly
  _skip = staticmethod(unittest.skip)
  _skipIf = staticmethod(unittest.skipIf)  # pylint: disable=invalid-name
  _skipUnless = staticmethod(unittest.skipUnless)  # pylint: disable=invalid-name

  @staticmethod
  def _GetSkipString(reason, issue):
    return '{why} ({bug})'.format(why=reason, bug=issue)

  @staticmethod
  def _Skip(skip_type, reason, issue, **kwargs):
    """A base skip function that enforces certain usage patterns.

    Args:
      skip_type: One of the unittest skip functions to call
      reason: Why this test was skipped. Cannot be blank.
      issue: An issue number tied to this skip. Cannot be blank.
      **kwargs: Other arguments to pass to the skip_type function.

    Returns:
      The decorator returned by skip_type

    Raises:
      InvalidFilterError: If the skip violates the desired usage patterns.
    """
    if Filters._ShouldDecorate(reason):
      raise InvalidFilterError('A reason must be given')

    if issue:
      if isinstance(issue, six.string_types) and issue.startswith('b/'):
        reason = Filters._GetSkipString(reason, issue)
      else:
        raise InvalidFilterError('Invalid issue number given')
    else:
      raise InvalidFilterError('An issue number must be given')

    return skip_type(reason=reason, **kwargs)

  @staticmethod
  def _CannedSkip(skip_type, skip_condition,
                  reason_or_function, default_reason):
    """Allows for skips with both default and optional explanations.

    This is a factory function for skip decorators that do not require a reason
    or issue number. These are meant to be used in cases where running the test
    does not make sense, such as running a symlink test on Windows. This
    function should not be called directly.

    Args:
      skip_type: A conditional skip function to be wrapped.
      skip_condition: A condition to pass to skip_type.
      reason_or_function: If called without an arguments list, this will be the
        function to decorate; otherwise, this will be the reason given for the
        skip.
      default_reason: The default reason to report if no more specific reason
        is given.

    Returns:
      The wrapped skip decorator or the decorated function.
    """
    if Filters._ShouldDecorate(reason_or_function):  # Use default on these
      return skip_type(skip_condition, default_reason)(reason_or_function)
    else:  # Return a decorator with the given reason otherwise
      return skip_type(skip_condition, reason_or_function)

  @staticmethod
  def _RunSkippedTests():
    return bool(
        pytest and Filters._IsEnvSet('CLOUDSDK_RUN_SKIPPED_TESTS'))

  @staticmethod
  def _Silence(reason=None, condition=True):
    """A silenced test will run, but will be skipped if it fails.

    Support for silencing tests requires the pytest_silencer_plugin in
    googlecloudsdk/tests/lib/pytest_silencer_plugin.py.

    Args:
      reason: A textual description of why the test is silenced.
      condition: A boolean indicating whether or not to silence the test.
    Returns:
      A decorator to silence a test.
    """
    def _SilenceDecorator(func):
      if not condition:
        return func
      silence_marker = pytest.mark.silence(reason=reason)
      try:
        # Parameterized tests are an iterable of tests.
        return [silence_marker(f) for f in func]
      except TypeError:
        return silence_marker(func)
    return _SilenceDecorator

  @staticmethod
  def _SilenceUnless(reason=None, condition=False):
    return Filters._Silence(reason=reason, condition=not condition)

  @staticmethod
  def skip(reason, issue):  # pylint: disable=invalid-name
    """Unconditionally skips a test.

    Note: The skip decorators are for tests that are skipped due to a bug or
      similar issue. If a test is skipped because it tests (e.g.) some OS
      specific code, use the DoNotRun... or RunOnly... decorators instead.
      Skipped tests will be run in periodic jobs to see if they are still
      failing. To prevent a skipped test from being run, use skipAlways.

    Args:
      reason: A textual description of why the test is skipped.
      issue: A bug number tied to this skip. Must be in the format 'b/####...'

    Returns:
      A decorator that will skip a test.
    """
    if Filters._RunSkippedTests():
      skip_type = Filters._Silence
    else:
      skip_type = Filters._skip
    return Filters._Skip(skip_type, reason, issue)

  @staticmethod
  def skipAlways(reason, issue):  # pylint: disable=invalid-name
    """Unconditionally skips a test. Will not be run until unskipped.

    Note: The skip decorators are for tests that are skipped due to a bug or
      similar issue. If a test is skipped because it tests (e.g.) some OS
      specific code, use the DoNotRun... or RunOnly... decorators instead.
      Tests with this decorator will NOT be run automatically to determine if
      they are still failing.

    Args:
      reason: A textual description of why the test is skipped.
      issue: A bug number tied to this skip. Must be in the format 'b/####...'

    Returns:
      A decorator that will skip a test.
    """
    return Filters._Skip(Filters._skip, reason, issue)

  @staticmethod
  # pylint: disable=invalid-name
  def skipIf(condition, reason, issue):
    """Skips a test under a given condition.

    Note: The skip decorators are for tests that are skipped due to a bug or
      similar issue. If a test is skipped because it tests (e.g.) some OS
      specific code, use the DoNotRun... or RunOnly... decorators instead.

    Args:
      condition: A boolean indicating whether or not to skip the test
      reason: A textual description of why the test is skipped.
      issue: A bug number tied to this skip. Must be in the format 'b/####...'

    Returns:
      A decorator that will skip a test under the given condition.
    """
    if Filters._RunSkippedTests():
      skip_type = Filters._Silence
    else:
      skip_type = Filters._skipIf
    return Filters._Skip(skip_type, reason, issue, condition=condition)

  @staticmethod
  # pylint: disable=invalid-name
  def skipUnless(condition, reason, issue):
    """Skips a test outside of a given condition.

    Note: The skip decorators are for tests that are skipped due to a bug or
      similar issue. If a test is skipped because it tests (e.g.) some OS
      specific code, use the DoNotRun... or RunOnly... decorators instead.

    Args:
      condition: A boolean indicating whether or not to run the test
      reason: A textual description of why the test is skipped.
      issue: A bug number tied to this skip. Must be in the format 'b/####...'

    Returns:
      A decorator that will skip a test outside of the given condition.
    """
    if Filters._RunSkippedTests():
      skip_type = Filters._SilenceUnless
    else:
      skip_type = Filters._skipUnless
    return Filters._Skip(skip_type, reason, issue, condition=condition)

  @staticmethod
  def DoNotRunIf(condition, reason):
    """A generic DoNotRun. More specific decorators should be preferred.

    Note: The DoNotRun... decorators are for tests that are not meant to be run
      under the given condition (e.g. a symlink test on Windows). If the test
      should run under the given condition, but is skipped due to a bug, use the
      skip decorators instead.

    Args:
      condition: A boolean indicating whether or not to run this test
      reason: A textual description of why this test does not run under the
        given condition

    Returns:
      A decorator that will skip a test under the given condition.
    """
    return Filters._CannedSkip(Filters._skipIf, condition, reason, None)

  @staticmethod
  def RunOnlyIf(condition, reason):
    """A generic RunOnly. More specific decorators should be preferred.

    Note: The RunOnly... decorators are for tests that are meant to be run only
      under the given condition. If the test should run outside the given
      condition, but is skipped due to a bug, use the skip decorators instead.

    Args:
      condition: A boolean indicating whether or not to run this test
      reason: A textual description of why this test does not run outside the
        given condition

    Returns:
      A decorator that will skip a test outside the given condition.
    """
    return Filters._CannedSkip(Filters._skipUnless, condition, reason, None)

  @staticmethod
  def RunOnlyOnPy2(reason_or_function):
    """A decorator for tests designed to only run on Python 2.

    Note: The RunOnly... decorators are for tests that are meant to be run only
      under the given condition. If the test should run outside the given
      condition, but is skipped due to a bug, use the skip decorators instead.

    Args:
      reason_or_function: If called without an arguments list, this will be the
        function to decorate; otherwise, this will be the reason given for the
        skip.

    Returns:
      A decorator that will skip a test outside of Python 2.
    """
    return Filters._CannedSkip(
        Filters._skipUnless, six.PY2, reason_or_function,
        'This test requires features only available on Python 2.')

  @staticmethod
  def SkipOnPy3(reason, issue):
    """A decorator that skips a test if running under Python 3.

    Note: The skip decorators are for tests that are skipped due to a bug or
      similar issue. If a test is skipped because it tests (e.g.) some OS
      specific code, use the DoNotRun... or RunOnly... decorators instead.

    Args:
      reason: A textual description of why the test is skipped.
      issue: A bug number tied to this skip. Must be in the format 'b/####...'

    Returns:
      A decorator that will skip a test if running under Python 3.
    """
    return Filters.skipIf(six.PY3, reason, issue)

  @staticmethod
  def SkipOnPy3Always(reason, issue):
    """A decorator that always skips a test if running under Python 3.

    Note: The skip decorators are for tests that are skipped due to a bug or
      similar issue. If a test is skipped because it tests (e.g.) some OS
      specific code, use the DoNotRun... or RunOnly... decorators instead.

    Args:
      reason: A textual description of why the test is skipped.
      issue: A bug number tied to this skip. Must be in the format 'b/####...'

    Returns:
      A decorator that will always skip a test if running under Python 3.
    """
    return Filters._Skip(Filters._skipIf, reason, issue, condition=six.PY3)

  @staticmethod
  def DoNotRunOnPy3(reason_or_function):
    """A decorator that doesn't run a test if running under Python 3.

    Note: The DoNotRun... decorators are for tests that are not meant to be run
      under the given condition (e.g. a symlink test on Windows). If the test
      should run under the given condition, but is skipped due to a bug, use the
      skip decorators instead.

    Args:
      reason_or_function: If called without an arguments list, this will be the
        function to decorate; otherwise, this will be the reason given for the
        skip.

    Returns:
      A decorator that will not run a test in Python 3.
    """
    return Filters._CannedSkip(
        Filters._skipIf, six.PY3, reason_or_function,
        'This test will not be upgraded to run on Python 3.')

  @staticmethod
  def DoNotRunOnPy2(reason_or_function):
    """A decorator that doesn't run a test if running under Python 2.

    Note: The DoNotRun... decorators are for tests that are not meant to be run
      under the given condition (e.g. a symlink test on Windows). If the test
      should run under the given condition, but is skipped due to a bug, use the
      skip decorators instead.

    Args:
      reason_or_function: If called without an arguments list, this will be the
        function to decorate; otherwise, this will be the reason given for the
        skip.

    Returns:
      A decorator that will not run a test in Python 2.
    """
    return Filters._CannedSkip(
        Filters._skipIf, six.PY2, reason_or_function,
        'This test will not be upgraded to run on Python 2.')

  @staticmethod
  def SkipOnWindows(reason, issue):
    """A decorator that skips a method if on Windows.

    Note: The skip decorators are for tests that are skipped due to a bug or
      similar issue. If a test is skipped because it tests (e.g.) some OS
      specific code, use the DoNotRun... or RunOnly... decorators instead.

    Args:
      reason: A textual description of why the test is skipped.
      issue: A bug number tied to this skip. Must be in the format 'b/####...'

    Returns:
      A decorator that will skip a test in Windows.
    """
    return Filters.skipIf(Filters._IS_ON_WINDOWS, reason, issue)

  @staticmethod
  def DoNotRunOnWindows(reason_or_function):
    """Decorator for tests that require features not available on Windows.

    Note: The DoNotRun... decorators are for tests that are not meant to be run
      under the given condition (e.g. a symlink test on Windows). If the test
      should run under the given condition, but is skipped due to a bug, use the
      skip decorators instead.

    Args:
      reason_or_function: If called without an arguments list, this will be the
        function to decorate; otherwise, this will be the reason given for the
        skip.

    Returns:
      A decorator that will skip a test in Windows.
    """
    return Filters._CannedSkip(
        Filters._skipIf, Filters._IS_ON_WINDOWS, reason_or_function,
        'This test requires features not available on Windows.')

  @staticmethod
  def RunOnlyOnWindows(reason_or_function):
    """A decorator for tests designed to only run on Windows.

    Note: The RunOnly... decorators are for tests that are meant to be run only
      under the given condition. If the test should run outside the given
      condition, but is skipped due to a bug, use the skip decorators instead.

    Args:
      reason_or_function: If called without an arguments list, this will be the
        function to decorate; otherwise, this will be the reason given for the
        skip.

    Returns:
      A decorator that will skip a test outside of Windows.
    """
    return Filters._CannedSkip(
        Filters._skipUnless, Filters._IS_ON_WINDOWS, reason_or_function,
        'This test requires features only available on Windows.')

  @staticmethod
  def SkipOnLinux(reason, issue):
    """A decorator that skips a method if on Linux.

    Note: The skip decorators are for tests that are skipped due to a bug or
      similar issue. If a test is skipped because it tests (e.g.) some OS
      specific code, use the DoNotRun... or RunOnly... decorators instead.

    Args:
      reason: A textual description of why the test is skipped.
      issue: A bug number tied to this skip. Must be in the format 'b/####...'

    Returns:
      A decorator that will skip a test in Linux.
    """
    return Filters.skipIf(Filters._IS_ON_LINUX, reason, issue)

  @staticmethod
  def DoNotRunOnLinux(reason_or_function):
    """Decorator for tests that require features not available on Linux.

    Note: The DoNotRun... decorators are for tests that are not meant to be run
      under the given condition (e.g. a symlink test on Windows). If the test
      should run under the given condition, but is skipped due to a bug, use the
      skip decorators instead.

    Args:
      reason_or_function: If called without an arguments list, this will be the
        function to decorate; otherwise, this will be the reason given for the
        skip.

    Returns:
      A decorator that will skip a test in Linux.
    """
    return Filters._CannedSkip(
        Filters._skipIf, Filters._IS_ON_LINUX, reason_or_function,
        'This test requires features not available on Linux.')

  @staticmethod
  def RunOnlyOnLinux(reason_or_function):
    """A decorator for tests designed to only run on Linux.

    Note: The RunOnly... decorators are for tests that are meant to be run only
      under the given condition. If the test should run outside the given
      condition, but is skipped due to a bug, use the skip decorators instead.

    Args:
      reason_or_function: If called without an arguments list, this will be the
        function to decorate; otherwise, this will be the reason given for the
        skip.

    Returns:
      A decorator that will skip a test outside of Linux.
    """
    return Filters._CannedSkip(
        Filters._skipUnless, Filters._IS_ON_LINUX, reason_or_function,
        'This test requires features only available on Linux.')

  @staticmethod
  def SkipOnMac(reason, issue):
    """A decorator that skips a method if on Mac.

    Note: The skip decorators are for tests that are skipped due to a bug or
      similar issue. If a test is skipped because it tests (e.g.) some OS
      specific code, use the DoNotRun... or RunOnly... decorators instead.

    Args:
      reason: A textual description of why the test is skipped.
      issue: A bug number tied to this skip. Must be in the format 'b/####...'

    Returns:
      A decorator that will skip a test on Mac.
    """
    return Filters.skipIf(Filters._IS_ON_MAC, reason, issue)

  @staticmethod
  def DoNotRunOnMac(reason_or_function):
    """Decorator for tests that require features not available on Mac.

    Note: The DoNotRun... decorators are for tests that are not meant to be run
      under the given condition (e.g. a symlink test on Windows). If the test
      should run under the given condition, but is skipped due to a bug, use the
      skip decorators instead.

    Args:
      reason_or_function: If called without an arguments list, this will be the
        function to decorate; otherwise, this will be the reason given for the
        skip.

    Returns:
      A decorator that will skip a test on Mac.
    """
    return Filters._CannedSkip(
        Filters._skipIf, Filters._IS_ON_MAC, reason_or_function,
        'This test requires features not available on Mac.')

  @staticmethod
  def RunOnlyOnMac(reason_or_function):
    """A decorator for tests designed to only run on Mac.

    Note: The RunOnly... decorators are for tests that are meant to be run only
      under the given condition. If the test should run outside the given
      condition, but is skipped due to a bug, use the skip decorators instead.

    Args:
      reason_or_function: If called without an arguments list, this will be the
        function to decorate; otherwise, this will be the reason given for the
        skip.

    Returns:
      A decorator that will skip a test outside of Mac.
    """
    return Filters._CannedSkip(
        Filters._skipUnless, Filters._IS_ON_MAC, reason_or_function,
        'This test requires features only available on MAC.')

  @staticmethod
  def _IsEnvSet(variable):
    """Checks if an environment variable is considered set."""
    env = os.getenv(variable, False)
    # Jenkins (underlying Kokoro) sets ENV_VAR to the string 'false' rather than
    # not setting it at all, hence the following string comparison.
    return env and env != 'false'

  @staticmethod
  def SkipInKokoro(reason, issue):
    """A decorator that skips a method if running in Kokoro.

    Note: The skip decorators are for tests that are skipped due to a bug or
      similar issue. If a test is skipped because it tests (e.g.) some OS
      specific code, use the DoNotRun... or RunOnly... decorators instead.

    Args:
      reason: A textual description of why the test is skipped.
      issue: A bug number tied to this skip. Must be in the format 'b/####...'

    Returns:
      A decorator that will skip a test in a Kokoro job.
    """
    return Filters.skipIf(Filters._IS_IN_KOKORO, reason, issue)

  @staticmethod
  def DoNotRunInKokoro(reason_or_function):
    """Decorator for tests that should not run in Kokoro jobs.

    Note: The DoNotRun... decorators are for tests that are not meant to be run
      under the given condition (e.g. a symlink test on Windows). If the test
      should run under the given condition, but is skipped due to a bug, use the
      skip decorators instead.

    Args:
      reason_or_function: If called without an arguments list, this will be the
        function to decorate; otherwise, this will be the reason given for the
        skip.

    Returns:
      A decorator that will skip a test when running in a Kokoro job.
    """
    return Filters._CannedSkip(
        Filters._skipIf, Filters._IS_IN_KOKORO, reason_or_function,
        'This test does not run in Kokoro.')

  @staticmethod
  def RunOnlyInKokoro(reason_or_function):
    """A decorator for tests designed to only run Kokoro jobs.

    Note: The RunOnly... decorators are for tests that are meant to be run only
      under the given condition. If the test should run outside the given
      condition, but is skipped due to a bug, use the skip decorators instead.

    Args:
      reason_or_function: If called without an arguments list, this will be the
        function to decorate; otherwise, this will be the reason given for the
        skip.

    Returns:
      A decorator that will skip a test when not running in a Kokoro job.
    """
    return Filters._CannedSkip(
        Filters._skipUnless, Filters._IS_IN_KOKORO, reason_or_function,
        'This test only runs in Kokoro.')

  @staticmethod
  def SkipInDebPackage(reason, issue):
    """A decorator that skips a method if installed via a Deb package.

    Note: The skip decorators are for tests that are skipped due to a bug or
      similar issue. If a test is skipped because it tests (e.g.) some OS
      specific code, use the DoNotRun... or RunOnly... decorators instead.

    Args:
      reason: A textual description of why the test is skipped.
      issue: A bug number tied to this skip. Must be in the format 'b/####...'

    Returns:
      A decorator that will skip a test in a Deb package.
    """
    return Filters.skipIf(Filters._IS_IN_DEB, reason, issue)

  @staticmethod
  def DoNotRunInDebPackage(reason_or_function):
    """Decorator for tests that require features not available in Deb packages.

    Note: The DoNotRun... decorators are for tests that are not meant to be run
      under the given condition (e.g. a symlink test on Windows). If the test
      should run under the given condition, but is skipped due to a bug, use the
      skip decorators instead.

    Args:
      reason_or_function: If called without an arguments list, this will be the
        function to decorate; otherwise, this will be the reason given for the
        skip.

    Returns:
      A decorator that will skip a test in a Deb package installation.
    """
    return Filters._CannedSkip(
        Filters._skipIf, Filters._IS_IN_DEB, reason_or_function,
        'This test requires features not available on Mac.')

  @staticmethod
  def RunOnlyInDebPackage(reason_or_function):
    """A decorator for tests designed to only run in Deb packages.

    Note: The RunOnly... decorators are for tests that are meant to be run only
      under the given condition. If the test should run outside the given
      condition, but is skipped due to a bug, use the skip decorators instead.

    Args:
      reason_or_function: If called without an arguments list, this will be the
        function to decorate; otherwise, this will be the reason given for the
        skip.

    Returns:
      A decorator that will skip a test outside of a Deb package installatio.
    """
    return Filters._CannedSkip(
        Filters._skipUnless, Filters._IS_IN_DEB, reason_or_function,
        'This test requires features only available on MAC.')

  @staticmethod
  def SkipInRpmPackage(reason, issue):
    """A decorator that skips a method if installed via a RPM package.

    Note: The skip decorators are for tests that are skipped due to a bug or
      similar issue. If a test is skipped because it tests (e.g.) some OS
      specific code, use the DoNotRun... or RunOnly... decorators instead.

    Args:
      reason: A textual description of why the test is skipped.
      issue: A bug number tied to this skip. Must be in the format 'b/####...'

    Returns:
      A decorator that will skip a test in a RPM package.
    """
    return Filters.skipIf(Filters._IS_IN_RPM, reason, issue)

  @staticmethod
  def DoNotRunInRpmPackage(reason_or_function):
    """Decorator for tests that require features not available in RPM packages.

    Note: The DoNotRun... decorators are for tests that are not meant to be run
      under the given condition (e.g. a symlink test on Windows). If the test
      should run under the given condition, but is skipped due to a bug, use the
      skip decorators instead.

    Args:
      reason_or_function: If called without an arguments list, this will be the
        function to decorate; otherwise, this will be the reason given for the
        skip.

    Returns:
      A decorator that will skip a test in a RPM package installation.
    """
    return Filters._CannedSkip(
        Filters._skipIf, Filters._IS_IN_RPM, reason_or_function,
        'This test requires features not available on Mac.')

  @staticmethod
  def RunOnlyInRpmPackage(reason_or_function):
    """A decorator for tests designed to only run in RPM packages.

    Note: The RunOnly... decorators are for tests that are meant to be run only
      under the given condition. If the test should run outside the given
      condition, but is skipped due to a bug, use the skip decorators instead.

    Args:
      reason_or_function: If called without an arguments list, this will be the
        function to decorate; otherwise, this will be the reason given for the
        skip.

    Returns:
      A decorator that will skip a test outside of a RPM package installatio.
    """
    return Filters._CannedSkip(
        Filters._skipUnless, Filters._IS_IN_RPM, reason_or_function,
        'This test requires features only available on MAC.')

  @staticmethod
  def RunOnlyWithEnv(variable, reason=None):
    """Runs a method only if an environmental variable is true.

    Note: The RunOnly... decorators are for tests that are meant to be run only
      under the given condition. If the test should run outside the given
      condition, but is skipped due to a bug, use the skip decorators instead.

    Args:
      variable: The environmental variable name to check.
      reason: An optional reason for this skip.

    Returns:
      A decorator that will skip a test if the environmental variable is false
        or not set.
    """
    if not reason:
      reason = ('This test only runs in certain environments: {0}'
                .format(variable))
    return Filters._skipUnless(Filters._IsEnvSet(variable), reason)

  @staticmethod
  def RunOnlyIfExecutablePresent(executable_name, reason=None):
    """Runs a method only if the executable is on the path.

    Note: The RunOnly... decorators are for tests that are meant to be run only
      under the given condition. If the test should run outside the given
      condition, but is skipped due to a bug, use the skip decorators instead.

    Args:
      executable_name: The executable name to check. Must be just the name with
        no directory or extension.
      reason: An optional reason for this skip.

    Returns:
      A decorator that will skip a test if the executable is not on the path.
    """
    if not reason:
      reason = ('This test requires the [{0}] executable to be on the '
                'path.'.format(executable_name))
    return Filters._skipUnless(
        files_util.FindExecutableOnPath(executable_name), reason)

  @staticmethod
  def RunOnlyIfModulePresent(module, reason=None):
    """Runs a method only if the given module is present and importable.

    Note: The RunOnly... decorators are for tests that are meant to be run only
      under the given condition. If the test should run outside the given
      condition, but is skipped due to a bug, use the skip decorators instead.

    Args:
      module: str, the (dot-separated) module name to check.
      reason: An optional reason for this skip.

    Returns:
      A decorator that will skip a test if the module available.
    """
    if not reason:
      reason = 'Module [{}] is required'.format(module)
    return Filters._skipUnless(_ModulePresent(module), reason)

  @staticmethod
  def RunOnlyIfLongrunning(reason_or_function=None):
    """Runs a method only if invoked as longrunning (off by default).

    This requires that the environment variable ENABLE_LONGRUNNING_TESTS
    is set.

    Note: The RunOnly... decorators are for tests that are meant to be run only
      under the given condition. If the test should run outside the given
      condition, but is skipped due to a bug, use the skip decorators instead.

    Args:
      reason_or_function: If called without an arguments list, this will be the
        function to decorate; otherwise, this will be the reason given for the
        skip.

    Returns:
      A decorator that will skip a test unless the environment variable is set.
    """
    return Filters._CannedSkip(
        Filters._skipUnless,
        Filters._IsEnvSet('ENABLE_LONGRUNNING_TESTS'),
        reason_or_function,
        'This test is marked as longrunning and is not run by default.')


class WithInput(Base):
  """A base class for tests that need to write to stdin."""

  def MockStdinFileNo(self):
    return 0

  def SetUp(self):
    """Redirects stdin to a buffer so we can write to it."""
    self.stdin = FakeStd()
    self.stdin.fileno = self.MockStdinFileNo
    self.StartPatch('sys.stdin', new=self.stdin)

  def TearDown(self):
    """Restores stdin its original file descriptors."""
    self.stdin.close()

  def WriteInput(self, *lines):
    """Writes the given lines into the stdin buffer for consumption.

    Args:
      *lines: str, A tuple of lines to write to standard in.

    """
    current_pos = self.stdin.tell()
    self.stdin.seek(0, os.SEEK_END)
    for line in lines:
      # TODO(b/72815887): We are making this string binary for now so that it
      # doesn't coerce 'line' into unicode when it isn't already. When we are
      # done, we want everything to be unicode strings all the time.
      self.stdin.write(
          line + (b'\n' if isinstance(line, six.binary_type) else '\n'))
    self.stdin.seek(current_pos)

  def WriteBinaryInput(self, contents):
    """Writes the given contents into the stdin buffer for consumption.

    Args:
      contents: str, Binary data to write to standard in.

    Raises:
      ValueError: If the contents are not bytes.
    """
    if not isinstance(contents, six.binary_type):
      raise ValueError('expected a byte string')
    current_pos = self.stdin.tell()
    self.stdin.seek(0, os.SEEK_END)
    self.stdin.buffer.write(contents)
    self.stdin.seek(current_pos)


def NormalizeSpace(norm, original_string):
  r"""Returns a copy of original_string with norm chars normalized.

  Strings are normalized by:
    * Deleting all norm chars at the beginning of each line.
    * Deleting all norm chars at the end of each line.
    * Collapsing all norm char sequences to a single space character.

  Args:
    norm: The string of characters to normalize into one space character or
      True for ' \t\v'.
    original_string: The string to normalize.

  Returns:
    A copy of original_string with norm chars normalized
  """
  space = norm if isinstance(norm, six.string_types) else ' \t\v'
  # Python 2.6 re.sub() does not support the flags kwarg, but re.compile() does.
  re_beg = re.compile('^[' + space + ']+', flags=re.MULTILINE)
  normalized_beg = re_beg.sub('', original_string)
  re_end = re.compile('[' + space + ']+$', flags=re.MULTILINE)
  normalized_end = re_end.sub('', normalized_beg)
  return re.sub('[' + space + ']+', ' ', normalized_end)


def _StripLongestCommonSpaceSuffix(str_a, str_b):
  """Strips the longest common isspace() suffix from str_a and str_b.

  Args:
    str_a: The first string to strip.
    str_b: The second string to strip.

  Returns:
    (str_a_stripped, str_b_stripped)
      str_a_stripped: str_a with longest common isspace() suffix stripped.
      str_b_stripped: str_b with longest common isspace() suffix stripped.
  """
  i = 0
  while True:
    try:
      end_a = str_a[i - 1]
      end_b = str_b[i - 1]
    except IndexError:
      break
    if end_a != end_b or not end_a.isspace():
      break
    i -= 1
  if not i:
    return str_a, str_b
  return str_a[:i], str_b[:i]


class WithOutputCapture(WithContentAssertions):
  """A base class for tests that need to capture stdout and stderr."""
  ERR = 'stderr'
  OUT = 'stdout'
  OUTPUT_MSG = 'Captured {name} {fp}: <<<{output}>>>\n'

  def MockStdoutFileNo(self):
    return 1

  def MockStderrFileNo(self):
    return 2

  def SetUp(self):
    """Redirects stdout and stderr to a buffer so we can capture it."""
    self.stdout = FakeStd()
    self.stderr = FakeStd()
    self.stdout.fileno = self.MockStdoutFileNo
    self.stderr.fileno = self.MockStderrFileNo
    self.StartPatch('sys.stdout', new=self.stdout)
    self.StartPatch('sys.stderr', new=self.stderr)
    self._show_test_output = os.getenv('CLOUDSDK_SHOW_TEST_OUTPUT', '0') == '1'
    self._encoding_was_set = False
    # Python 3 does not have this method, but handles exception scope as if it
    # is always used.
    if six.PY2:
      sys.exc_clear()

  def ShowTestOutput(self):
    """Call this from a test's SetUp to force that test's output to display."""
    self._show_test_output = True

  def TearDown(self):
    """Restores stdout and stderr to their original file descriptors."""
    if self._show_contents_on_failure:
      if sys.exc_info()[0] is not None or self._show_test_output:
        # Print what we captured in full, if error for debugging.
        # Use the environmental variable to print for tests with no error

        # The format command fails if the captured stdout/stderr is not composed
        # of all ASCII characters. Decode, then re-encode in order to avoid
        # this (these characters will be replaced with '?').
        stdout = self.stdout.getvalue()
        if stdout:
          try:
            sys.__stdout__.write(WithOutputCapture.OUTPUT_MSG.format(
                name=self.id(), fp='stdout', output=stdout))
          except UnicodeError:
            stdout = console_attr.SafeText(stdout)
            sys.__stdout__.write(WithOutputCapture.OUTPUT_MSG.format(
                name=self.id(), fp='stdout', output=stdout))
        stderr = self.stderr.getvalue()
        if stderr:
          try:
            sys.__stderr__.write(WithOutputCapture.OUTPUT_MSG.format(
                name=self.id(), fp='stderr', output=stderr))
          except UnicodeError:
            stderr = console_attr.SafeText(stderr)
            sys.__stderr__.write(WithOutputCapture.OUTPUT_MSG.format(
                name=self.id(), fp='stderr', output=stderr))
    self.stdout.close()
    self.stderr.close()

  def SetEncoding(self, encoding=None):
    br"""Sets the captured output stream encoding.

    At this point self.stdout and self.stderr are the mocked stdout and stderr.
    This method sets the encoding on those streams. At test assertion execution
    time the GetOutput() and GetErr() methods reap and convert the encoded data
    to unicode. This tests the encoding => decoding path on the output streams.
    It also allows test assertion expected values to be specified as utf-8
    u'...' strings using glyphs rather than \uxxxx codes. This makes the tests
    much easier to read and maintain.

    Args:
      encoding: The mocked output stream encoding name.
    """
    if not encoding:
      current_os = platforms.OperatingSystem.Current()
      if current_os == platforms.OperatingSystem.WINDOWS:
        encoding = 'cp437'
      else:
        encoding = 'utf-8'
    console_attr.GetConsoleAttr(encoding=encoding, reset=True)

  def GetOutput(self):
    """Get the text that was printed to stdout."""
    return console_attr.Decode(self.GetOutputBytes())

  def GetOutputBytes(self):
    return self.stdout.getvalue()

  def GetErr(self):
    """Get the text that was printed to stderr."""
    return console_attr.Decode(self.GetErrBytes())

  def GetErrBytes(self):
    return self.stderr.getvalue()

  def ClearOutput(self):
    """Resets the standard output capture."""
    self.stdout.truncate(0)
    self.stdout.seek(0)

  def ClearErr(self):
    """Resets the standard error capture."""
    self.stderr.truncate(0)
    self.stderr.seek(0)

  def AssertOutputContains(self, expected, name=OUT, normalize_space=False,
                           actual_filter=None, success=True):
    self._AssertContains(expected, self.GetOutput(), name,
                         normalize_space=normalize_space,
                         actual_filter=actual_filter, success=success)

  def AssertOutputNotContains(self, expected, name=OUT, normalize_space=False,
                              actual_filter=None, success=False):
    self._AssertContains(expected, self.GetOutput(), name,
                         normalize_space=normalize_space,
                         actual_filter=actual_filter, success=success)

  def AssertOutputEquals(self, expected, name=OUT, normalize_space=False,
                         actual_filter=None, success=True):
    self._AssertEquals(expected, self.GetOutput(), name,
                       normalize_space=normalize_space,
                       actual_filter=actual_filter, success=success)

  def AssertOutputNotEquals(self, expected, name=OUT, normalize_space=False,
                            actual_filter=None, success=False):
    self._AssertEquals(expected, self.GetOutput(), name,
                       normalize_space=normalize_space,
                       actual_filter=actual_filter, success=success)

  def AssertOutputMatches(self, expected, name=OUT, normalize_space=False,
                          actual_filter=None, success=True):
    output = self.GetOutput()
    self._AssertMatches(
        expected,
        output,
        name,
        normalize_space=normalize_space,
        actual_filter=actual_filter,
        success=success)

  def AssertOutputNotMatches(self, expected, name=OUT, normalize_space=False,
                             actual_filter=None, success=False):
    self._AssertMatches(expected, self.GetOutput(), name,
                        normalize_space=normalize_space,
                        actual_filter=actual_filter, success=success)

  def AssertOutputContainsFile(self, golden_path, normalize_space=False,
                               actual_filter=None, success=True):
    package_path = self.GetTestdataPackagePath(golden_path)
    expected = console_attr.Decode(
        pkg_resources.GetResourceFromFile(golden_path))
    self._AssertContains(expected, self.GetOutput(), package_path,
                         normalize_space=normalize_space,
                         actual_filter=actual_filter, success=success,
                         golden=True)

  def AssertOutputBytesEquals(self,
                              expected,
                              name=OUT,
                              normalize_space=False,
                              actual_filter=None,
                              success=True):
    self._AssertEquals(
        expected,
        self.GetOutputBytes(),
        name,
        normalize_space=normalize_space,
        actual_filter=actual_filter,
        success=success)

  def AssertErrContains(self, expected, name=ERR, normalize_space=False,
                        actual_filter=None, success=True):
    self._AssertContains(expected, self.GetErr(), name,
                         normalize_space=normalize_space,
                         actual_filter=actual_filter, success=success)

  def AssertErrNotContains(self, expected, name=ERR, normalize_space=False,
                           actual_filter=None, success=False):
    self._AssertContains(expected, self.GetErr(), name,
                         normalize_space=normalize_space,
                         actual_filter=actual_filter, success=success)

  def AssertErrEquals(self, expected, name=ERR, normalize_space=False,
                      actual_filter=None, success=True):
    self._AssertEquals(expected, self.GetErr(), name,
                       normalize_space=normalize_space,
                       actual_filter=actual_filter, success=success)

  def AssertErrNotEquals(self, expected, name=ERR, normalize_space=False,
                         actual_filter=None, success=False):
    self._AssertEquals(expected, self.GetErr(), name,
                       normalize_space=normalize_space,
                       actual_filter=actual_filter, success=success)

  def AssertErrMatches(self, expected, name=ERR, normalize_space=False,
                       actual_filter=None, success=True):
    self._AssertMatches(expected, self.GetErr(), name,
                        normalize_space=normalize_space,
                        actual_filter=actual_filter, success=success)

  def AssertErrNotMatches(self, expected, name=ERR, normalize_space=False,
                          actual_filter=None, success=False):
    self._AssertMatches(expected, self.GetErr(), name,
                        normalize_space=normalize_space,
                        actual_filter=actual_filter, success=success)

  def _GetStdTestRunDir(self):
    """Returns the directory from which all standard tests are run."""
    parts = __file__.split(os.path.sep)
    # This module is tests.lib.test_case
    return os.path.sep.join(parts[:-3]) + os.path.sep

  def GetTestdataPath(self, caller_path, *args):
    """Returns the absolute path for the file caller_path+*args.

    For example, this gets the absolute path for the markdown subtest file
    'gcloud.md'
      absolute_path = self.GetTestdataPath(__file__, 'markdown', 'gcloud.md')

    Args:
      caller_path: The absolute path of the calling module, usually __file__.
      *args: The golden file subdirs and base name.

    Returns:
      Returns the absolute path for the file caller_path+*args.
    """
    directory = os.path.dirname(caller_path)
    return os.path.join(directory, 'testdata', *args)

  def GetTestdataPackagePath(self, path):
    """Returns the pkg_resources package path for path.

    The package path is relative to the package root. It is used in
    Assert*IsGolden() error messages to show the golden files that have
    regressions.

    Args:
      path: An absolute path.

    Returns:
      Returns the pkg_resources package path for path.
    """
    std_test_run_dir = self._GetStdTestRunDir()
    return path[len(std_test_run_dir):]

  def AssertOutputIsGolden(self, caller_path, *args, **kwargs):
    """Call AssertOutputContainsFile() on golden file.

    Use this to record large/complex test output in a golden file. When the
    test fails use update-regressions.sh to update the golden files.

    Args:
      caller_path: The absolute path of the calling module, usually __file__.
      *args: The golden file subdirs and base name.
      **kwargs: _AssertContains kwargs.
    """
    golden_path = self.GetTestdataPath(caller_path, *args)
    self.AssertOutputContainsFile(golden_path, **kwargs)

  def AssertFileIsGolden(self, path, caller_path, *args, **kwargs):
    """Compares the content of path against a data file.

    Args:
      path: The path name to be tested.
      caller_path: The absolute path of the calling module, usually __file__.
      *args: The golden file subdirs and base name.
      **kwargs: _AssertContains kwargs.
    """
    golden_path = self.GetTestdataPath(caller_path, *args)
    package_path = self.GetTestdataPackagePath(golden_path)
    expected = console_attr.Decode(
        pkg_resources.GetResourceFromFile(golden_path))
    with io.open(path, 'rt') as f:
      self._AssertContains(
          expected, f.read(), package_path, golden=True, **kwargs)

  def AssertDirectoryIsGolden(self, directory, caller_path, *args, **kwargs):
    """Compares the sorted directory <size,name> list against a data file.

    File sizes are listed 0-filled width 5.

    Args:
      directory: The directory path name.
      caller_path: The absolute path of the calling module, usually __file__.
      *args: The golden file subdirs and base name.
      **kwargs: _AssertContains kwargs.
    """
    buf = io.StringIO()
    buf.write('<<<DIRECTORY {directory}>>>\n'.format(
        directory=os.path.basename(directory)))
    for dirpath, _, files in sorted(os.walk(directory)):
      for name in sorted(files):
        path = os.path.join(dirpath, name)
        if _IsBinaryMediaPath(path):
          # Binary -- avoid '\n' <=> '\r\n' morphing on some systems.
          text_size = os.stat(path).st_size
        else:
          with io.open(path, 'rt') as f:
            text_size = sum(len(line) for line in f)
        relative_path = os.path.relpath(path, directory)
        if os.path.sep != '/':
          relative_path = relative_path.replace(os.path.sep, '/')
        buf.write('{size:05} {path}\n'.format(size=text_size,
                                              path=relative_path))
    buf.write('<<</DIRECTORY>>>\n')
    golden_path = self.GetTestdataPath(caller_path, *args)
    package_path = self.GetTestdataPackagePath(golden_path)
    expected = console_attr.Decode(
        pkg_resources.GetResourceFromFile(golden_path))
    self._AssertContains(
        expected, buf.getvalue(), package_path, golden=True, **kwargs)
