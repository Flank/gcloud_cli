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

"""A base class for tests depending on Cloud SDK structural setup."""
from __future__ import absolute_import

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime
import functools
import inspect
import io
import numbers
import os
import socket
import sys
import tempfile
import traceback
import types

import googlecloudsdk
from googlecloudsdk.core import config
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.configurations import named_configs
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.credentials import gce as c_gce
from googlecloudsdk.core.credentials import store as c_store
from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import files as file_utils
from googlecloudsdk.core.util import retry
import tests
from tests.lib import exec_utils
from tests.lib import test_case

from oauth2client import client
from oauth2client.contrib import gce
import six


def _DefaultStatusUpdate(result, unused_status):
  log.warning('Test failure, but will be retried. Exception: {0}'.format(
      ''.join(traceback.format_exception(*result[1]))))


def Retry(f=None, why=None, **kwargs):
  """Decorator wraping retry.RetryOnException with testing-specific defaults."""

  # Wrap a function and retry it up to max_retrials times. It is recommended to
  # retry as little as possible. Don't retry the whole test if just one
  # operation out of ten has a chance of failure.

  if f is None:
    # Return a decorator
    def Decorator(f):
      if f.__name__.startswith('test'):
        raise Exception('Please do not use the Retry decorator on whole tests '
                        'as they are already automatically retried.')
      return Retry(f, why=why, **kwargs)
    return Decorator

  if not isinstance(f, types.FunctionType):
    raise Exception('Retry decorator only works with functions. '
                    'Using it with classes makes the class silently skip.')

  call_kwargs = {'max_retrials': 2,
                 'sleep_ms': 2000,
                 'status_update_func': _DefaultStatusUpdate}

  call_kwargs.update(**kwargs)

  if (call_kwargs['max_retrials'] is not None and
      call_kwargs['max_retrials'] < 1):
    raise ValueError('Retry requires max_retrials >= 1')

  log.warning('Preparing to run {fname} with retries, because: [{why}].'.format(
      fname=f.__name__,
      why=why))

  return retry.RetryOnException(f, **call_kwargs)


class SdkBase(test_case.Base):
  """A base class for tests that use Cloud SDK global state.

  Anything that uses the config directory, properties, or logging, must extend
  this base class.
  """

  def __CleanProperties(self):
    """Make sure properties are set to a clean state between tests.

    This should be called once before and once after the test runs. The
    properties in _clean_properties will be set to whatever value is stored
    there. All other properties will be set to None.
    """
    for section in properties.VALUES:
      for prop in section:
        if (section.name, prop.name) in self._clean_properties:
          prop.Set(self._clean_properties[(section.name, prop.name)])
        else:
          prop.Set(None)

    # Invalidate cache between tests.
    named_configs.ActivePropertiesFile.Invalidate()

  @staticmethod
  def _IsTestClass(clazz):
    return issubclass(clazz, test_case.TestCase)

  @staticmethod
  def _IsTestMethod(func):
    return func.__name__.startswith('test')

  @staticmethod
  def SetDirsSizeLimit(limit):
    """Change the size limit for leftover files in the test directories."""
    if not isinstance(limit, numbers.Number):
      # Was called without a parameter list or with the wrong kind of parameter
      raise Exception('Please specify the new limit in bytes.')

    def Decorator(func_or_cls):
      if inspect.isclass(func_or_cls):
        if not SdkBase._IsTestClass(func_or_cls):
          raise Exception('Directory size limit can only be changed on a test '
                          'class or test method.')

        # Decorating a class. Override __init__ to set the new limit.
        class NewClass(func_or_cls):

          def __init__(self, *args, **kwargs):
            super(NewClass, self).__init__(*args, **kwargs)
            # pylint: disable=protected-access
            self._dirs_size_limit_class = limit

        return NewClass
      else:
        if not SdkBase._IsTestMethod(func_or_cls):
          raise Exception('Directory size limit can only be changed on a test '
                          'class or test method.')

        # Decorating a function. Set the new limit, call original.
        @functools.wraps(func_or_cls)
        def NewFunction(self, *args, **kwargs):
          # pylint: disable=protected-access
          self._dirs_size_limit_method = limit
          return func_or_cls(self, *args, **kwargs)

        return NewFunction

    return Decorator

  def _GetDirSize(self, path):
    # Make os.walk() handle subdir and file names containing unicode chars.
    path = six.text_type(path)
    size = 0
    for root, _, files in os.walk(path):
      for f in files:
        size += os.path.getsize(os.path.join(root, f))
    return size

  def _CloseDirs(self):
    # Just before closing the temporary directory, verify that the test didn't
    # use up too much disk space
    size = self._GetDirSize(self.__root_dir.path)
    if hasattr(self, '_dirs_size_limit_method'):
      size_limit = getattr(self, '_dirs_size_limit_method')
      # Make sure the method limit only applies to the one method
      delattr(self, '_dirs_size_limit_method')
    elif hasattr(self, 'dirs_size_limit_class'):
      size_limit = getattr(self, '_dirs_size_limit_class')
    else:
      size_limit = 2<<20  # 2MB default
    self.assertLess(size, size_limit)

    # Remove the root directory and its contents
    self.__root_dir.Close()
    self.__root_dir = None

  def _GetInstallPropsStats(self):
    props_path = config.Paths().installation_properties_path
    if props_path:
      props_stats = os.stat(props_path)
      # Don't return/compare on all stats, especiall last access time
      return (props_stats.st_mode, props_stats.st_uid, props_stats.st_size,
              props_stats.st_mtime, props_stats.st_ctime)
    else:
      return None

  def _VerifyInstallProps(self):
    self.assertEqual(self.install_props, self._GetInstallPropsStats())

  def SetUp(self):
    self._prev_log_level = log.getLogger().getEffectiveLevel()
    self.__root_dir = file_utils.TemporaryDirectory()
    self.root_path = self.__root_dir.path
    self.temp_path = self.CreateTempDir()
    self.global_config_path = self.CreateTempDir('config')
    encoding.SetEncodedValue(
        os.environ, config.CLOUDSDK_CONFIG, self.global_config_path,
        encoding='utf-8')

    # Redirect home to a temp directory.
    self.home_path = self.CreateTempDir()
    self.StartEnvPatch({'HOME': self.home_path})
    self.mock_get_home_path = self.StartPatch(
        'googlecloudsdk.core.util.platforms.GetHomePath',
        return_value=self.home_path)
    self.mock_expandvars = self.StartPatch(
        'os.path.expandvars', autospec=True, return_value=self.home_path)
    self.addCleanup(self._CloseDirs)
    self.addCleanup(resources.REGISTRY.Clear)

    # Make sure there is nothing in the environment before the tests starts.
    self._clean_properties = {
        # Runtime root should be set back to whatever value it started with
        ('app', 'runtime_root'): properties.VALUES.app.runtime_root.Get(),
        ('core', 'check_gce_metadata'): False,
        ('component_manager', 'disable_update_check'): True,
        ('core', 'disable_usage_reporting'): True,
        ('core', 'should_prompt_to_enable_api'): False,
        ('core', 'allow_py3'): True,
    }
    self.__CleanProperties()
    self.addCleanup(self.__CleanProperties)

    # Turn these off for tests.
    properties.VALUES.GetInvocationStack()[:] = [{}]
    # This is not a real property but behaves like one.
    os.environ.pop('CLOUDSDK_ACTIVE_CONFIG_NAME', None)
    # pylint:disable=protected-access
    named_configs.FLAG_OVERRIDE_STACK._stack[:] = []

    # Make sure certain things are restored between tests
    self.install_props = self._GetInstallPropsStats()
    self.addCleanup(self._VerifyInstallProps)

    properties.VALUES.core.interactive_ux_style.Set(
        properties.VALUES.core.InteractiveUXStyles.TESTING.name)

    # The mocking of stdout and stderr happen in the test_case module whenever
    # a test is using output capture.  We need to reset the logger here to pick
    # up those settings.
    log.Reset()

  def TearDown(self):
    # We need to reset the logger here because it depends on properties and
    # the config directory, so that needs to happen before we unmock that stuff.
    # We have to explicitly pass in the original stdout and stderr streams
    # because when this runs, test_case.WithOutputCapture, will not yet have
    # unmocked these streams.  If we don't then log.Reset here would restore
    # log.out to the mocked sys.stdout and leave it in that state for subsequent
    # tests. This could result in "write to closed stream" exceptions for
    # subsequent log.out writes.
    # pylint:disable=protected-access
    log.Reset(sys.__stdout__, sys.__stderr__)
    self.assertEqual(self._prev_log_level,
                     log.getLogger().getEffectiveLevel(),
                     'The test or the code that is tested has modified the '
                     'logger level/verbosity and did not restore it.')

    self.root_path = None
    self.temp_path = None
    self.global_config_path = None
    os.environ.pop(config.CLOUDSDK_CONFIG, None)

  def CreateTempDir(self, name=None):
    if name:
      path = os.path.join(self.root_path, name)
      file_utils.MakeDir(path)
    else:
      path = tempfile.mkdtemp(dir=self.root_path)
    return path

  @staticmethod
  def Resource(*args):
    """Gets the path to a resource under googlecloudsdk."""
    # Make sure to find parent of tests directory, without assuming it is
    # googlecloudsdk, as tests package can be remapped to different location.
    return os.path.join(
        os.path.dirname(os.path.dirname(
            encoding.Decode(tests.__file__))),
        *args)

  def IsBundled(self):
    """Returns true if we are currently in a built SDK."""
    return Filters._IS_BUNDLED  # pylint: disable=protected-access


def _GetInstalledComponents():
  # pylint:disable=g-import-not-at-top, We can't do this import unless we are
  # in bundled mode.
  from googlecloudsdk.core.updater import update_manager
  return six.iterkeys(
      update_manager.UpdateManager().GetCurrentVersionsInformation())


class Filters(test_case.Filters):
  """Methods for determining when tests run and when they should be skipped."""

  _IS_BUNDLED = config.Paths().sdk_root is not None  # Includes GCE VMs
  _INSTALLED_COMPONENTS = (_GetInstalledComponents() if _IS_BUNDLED else [])
  _IS_ON_GCE = c_gce.Metadata().connected

  _DOCKER_IS_PRESENT = os.path.exists('/var/run/docker.pid')

  @staticmethod
  def RunOnlyInBundle(func):
    """Runs a test only if running as a test bundled into a built SDK."""
    return Filters._CannedSkip(
        Filters._skipUnless, Filters._IS_BUNDLED, func,
        'Test only runs as a bundled test in a built SDK')

  @staticmethod
  def DoNotRunInBundle(func):
    """Runs a test only if not running as a test bundled into a built SDK."""
    return Filters._CannedSkip(
        Filters._skipIf, Filters._IS_BUNDLED, func,
        'Test only runs as a bundled test in a built SDK')

  @staticmethod
  def SkipInBundle(reason, issue):
    """Skip a test if running bundled into a built SDK."""
    return Filters.skipIf(Filters._IS_BUNDLED, reason, issue)

  @staticmethod
  def RunOnlyOnGCE(func):
    """Runs a test only if running as a test on GCE."""
    return Filters._CannedSkip(
        Filters._skipUnless, Filters._IS_ON_GCE, func,
        'Test only runs as a target on GCE')

  @staticmethod
  def DoNotRunOnGCE(func):
    """Runs a test only if not running as a test on GCE."""
    return Filters._CannedSkip(
        Filters._skipIf, Filters._IS_ON_GCE, func,
        'Test does not run as a target on GCE')

  @staticmethod
  def SkipOnGCE(reason, issue):
    """Skips a test when running on GCE."""
    return Filters.skipIf(Filters._IS_ON_GCE, reason, issue)

  @staticmethod
  def DoNotRunOnGCEWhenBundled(func):
    """A decorator that will skip a bundled test if it is being run on GCE."""
    return Filters._CannedSkip(
        Filters._skipIf, Filters._IS_BUNDLED and Filters._IS_ON_GCE, func,
        'Test does not run on GCE when bundled.')

  @staticmethod
  def DoNotRunOnNonGCEWhenBundled(func):
    """Skip a bundled test if it is being run anywhere but GCE."""
    return Filters._CannedSkip(
        Filters._skipIf, Filters._IS_BUNDLED and Filters._IS_ON_GCE, func,
        'Test does not run when bundled outside of GCE.')

  @staticmethod
  def SkipOnGCEWhenBundled(reason, issue):
    """Skip a bundled test if it is being run on GCE."""
    return Filters.skipIf(Filters._IS_BUNDLED and Filters._IS_ON_GCE,
                          reason, issue)

  @staticmethod
  def SkipOnNonGCEWhenBundled(reason, issue):
    """Skip a bundled test if it is being run anywhere but GCE."""
    return Filters.skipIf(Filters._IS_BUNDLED and not Filters._IS_ON_GCE,
                          reason, issue)

  @staticmethod
  def RunOnlyWithDocker(func):
    """A decorator that runs a method only if Docker is present."""
    return Filters._CannedSkip(
        Filters._skipUnless, Filters._DOCKER_IS_PRESENT, func,
        'Test only runs on machines with Docker')

  @staticmethod
  def RequireComponent(*component_ids):
    """A decorator that will skip a test if the component is not installed."""
    def Inner(func):
      if not Filters._IS_BUNDLED:
        # If it's not bundled, all components are available.
        return func
      required = set(*component_ids)
      installed = set(Filters._INSTALLED_COMPONENTS)
      return Filters._skipIf(
          required - installed,
          'Test required component [{0}] but it is not installed.'
          .format(component_ids))(func)
    return Inner


class WithOutputCapture(SdkBase, test_case.WithOutputCapture):
  """A base class for tests that check output/error contents.

  - disables console_io.PromptContinue long line folding
  """

  def SetUp(self):
    log.SetUserOutputEnabled(True)
    # Disable console_io.PromptContinue long line folding.
    self.StartObjectPatch(console_io, '_DoWrap', lambda x: x)


class WithLogCapture(WithOutputCapture):
  """A module for capturing log file contents."""
  LOG = 'log-file'

  def SetUp(self):
    self.logs_dir = self.CreateTempDir()
    log.AddFileLogging(self.logs_dir)

  def _GetLogFileContents(self):
    """Makes sure a single log file was created and returns its contents.

    Raises:
      ValueError: If more than one log directory or file is found.

    Returns:
      str, The contents of the log file.
    """
    sub_dirs = os.listdir(self.logs_dir)
    if len(sub_dirs) != 1:
      raise ValueError('Found more than one log directory')
    sub_dir = os.path.join(self.logs_dir, sub_dirs[0])
    log_files = os.listdir(sub_dir)
    if len(log_files) != 1:
      raise ValueError('Found more than one log file')
    with io.open(os.path.join(sub_dir, log_files[0]), mode='rt',
                 encoding=log.LOG_FILE_ENCODING) as f:
      return f.read()

  def AssertLogContains(self, expected, name=LOG, normalize_space=False,
                        actual_filter=None, success=True):
    return self._AssertContains(expected, self._GetLogFileContents(), name,
                                normalize_space=normalize_space,
                                actual_filter=actual_filter, success=success)

  def AssertLogNotContains(self, expected, name=LOG,
                           normalize_space=False, actual_filter=None,
                           success=False):
    return self._AssertContains(expected, self._GetLogFileContents(), name,
                                normalize_space=normalize_space,
                                actual_filter=actual_filter, success=success)

  def AssertLogEquals(self, expected, name=LOG, normalize_space=False,
                      actual_filter=None, success=True):
    return self._AssertEquals(expected, self._GetLogFileContents(), name,
                              normalize_space=normalize_space,
                              actual_filter=actual_filter, success=success)

  def AssertLogNotEquals(self, expected, name=LOG, normalize_space=False,
                         actual_filter=None, success=False):
    return self._AssertEquals(expected, self._GetLogFileContents(), name,
                              normalize_space=normalize_space,
                              actual_filter=actual_filter, success=success)

  def AssertLogMatches(self, expected, name=LOG, normalize_space=False,
                       actual_filter=None, success=True):
    return self._AssertMatches(expected, self._GetLogFileContents(), name,
                               normalize_space=normalize_space,
                               actual_filter=actual_filter, success=success)

  def AssertLogNotMatches(self, expected, name=LOG,
                          normalize_space=False, actual_filter=None,
                          success=False):
    return self._AssertMatches(expected, self._GetLogFileContents(), name,
                               normalize_space=normalize_space,
                               actual_filter=actual_filter, success=success)


class WithTempCWD(SdkBase):
  """A base class for tests that want to be in a temporary current dir."""

  def SetUp(self):
    self.cwd_path = self.CreateTempDir('temp_cwd')
    try:
      self.__cwd = encoding.Decode(os.getcwd())
    except OSError:
      # Some test runners may bork os.getcwd().
      self.__cwd = self.root_path
      os.chdir(self.__cwd)
    self.addCleanup(self.CleanUp)
    self.EnterDir()

  def CleanUp(self):
    self.ExitDir()

  def EnterDir(self):
    """Changes the CWD to the temp directory this class sets up."""
    cwd = os.getcwd()
    if cwd == self.cwd_path:
      return
    self.__cwd = cwd
    os.chdir(self.cwd_path)

  def ExitDir(self):
    """Changes the CWD back to whatever the test runner started as."""
    os.chdir(self.__cwd)


class WithFakeAuth(SdkBase):
  """A base class that mocks out auth credentials.

  It will allow all code that needs credentials to run as long as it doesn't
  actually make a real API request.
  """

  def FakeAuthAccount(self):
    """Override this method to change the account that is used for credentials.

    Returns:
      str, The account name to use for the credentials object.
    """
    return 'fake_account'

  def FakeAuthAccessToken(self):
    """Override this method to change the access_token used for credentials.

    Returns:
      str, The access_token to use for the credentials object.
    """
    return 'access_token'

  def FakeAuthExpiryTime(self):
    """Override the expiry time of the fake access_token used for credentials.

    Returns:
      datetime.datetime, The expiry time of the access token.
    """
    return datetime.datetime.utcnow() + datetime.timedelta(hours=1)

  def FakeAuthUserAgent(self):
    """Override the user-agent associated with the fake credentials.

    Returns:
      str, The user_agent.
    """
    return 'user_agent'

  def _FakeAuthCredential(self):
    return client.OAuth2Credentials(
        self.FakeAuthAccessToken(), 'client_id', 'client_secret',
        'refresh_token', self.FakeAuthExpiryTime(), 'token_uri',
        self.FakeAuthUserAgent())

  def FakeAuthSetCredentialsPresent(self, present):
    """Set whether there should be active credentials.

    Args:
      present: bool, True to have credentials present, False for no credentials.
    """
    if present:
      self._load_mock.return_value = self._FakeAuthCredential()
    else:
      self._load_mock.side_effect = c_store.NoCredentialsForAccountException(
          self.FakeAuthAccount())

  def SetUp(self):
    def Connect(destpair):
      raise RuntimeError(
          'This test tries to access network at {}'.format(destpair))
    self.socket_connect_mock = self.StartObjectPatch(
        socket.socket, 'connect', side_effect=Connect)
    properties.VALUES.core.account.Set(self.FakeAuthAccount())
    self._load_mock = self.StartObjectPatch(c_store, 'Load')
    self.FakeAuthSetCredentialsPresent(True)
    refresh_mock = self.StartObjectPatch(client.OAuth2Credentials, 'refresh')
    refresh_mock.side_effect = ValueError(
        'TESTING ERROR: You are attempting to refresh a fake credential.  '
        'This probably means you are about to use it, and you should not be.')


class WithFakeComputeAuth(SdkBase):
  """A base class that mocks out compute auth credentials.

  It will allow all code that needs credentials to run as long as it doesn't
  actually make a real API request.
  """

  def FakeAuthAccount(self):
    """Override this method to change the account that is used for credentials.

    Returns:
      str, The account name to use for the credentials object.
    """
    return 'fake_account'

  def FakeAuthAccessToken(self):
    """Override this method to change the access_token used for credentials.

    Returns:
      str, The access_token to use for the credentials object.
    """
    return 'access_token'

  def Project(self):
    """Override the current project.

    Returns:
      str, The current project.
    """
    return 'fake-project'

  def _FakeAuthCredential(self):
    cred = gce.AppAssertionCredentials([])
    cred.access_token = self.FakeAuthAccessToken()
    return cred

  def FakeAuthSetCredentialsPresent(self, present):
    """Set whether there should be active credentials.

    Args:
      present: bool, True to have credentials present, False for no credentials.
    """
    if present:
      self._load_mock.return_value = self._FakeAuthCredential()
    else:
      self._load_mock.side_effect = c_store.NoCredentialsForAccountException(
          self.FakeAuthAccount())

  def SetUp(self):
    properties.VALUES.core.project.Set(self.Project())
    properties.VALUES.core.account.Set(self.FakeAuthAccount())
    self._load_mock = self.StartObjectPatch(c_store, 'Load')
    self.FakeAuthSetCredentialsPresent(True)
    refresh_mock = self.StartObjectPatch(gce.AppAssertionCredentials, 'refresh')
    refresh_mock.side_effect = ValueError(
        'TESTING ERROR: You are attempting to refresh a fake credential.  '
        'This probably means you are about to use it, and you should not be.')


class _BundledLocations(object):
  """A class to encapsulate getting paths to locations within the SDK."""

  def SDKRoot(self, *paths):
    """Compute a directory path relative to the root of the Cloud SDK."""
    root = config.Paths().sdk_root
    if paths:
      for p in paths:
        root = os.path.join(root, p)
    return root

  def BinDir(self, *paths):
    """Compute a directory path relative to the 'bin' directory."""
    return self.SDKRoot('bin', *paths)

  def LibDir(self, *paths):
    """Compute a directory path relative to the 'lib' directory."""
    return self.SDKRoot('lib', *paths)

  def ThirdPartyDir(self, *paths):
    """Compute a directory path relative to the 'third_party' directory."""
    return self.LibDir('third_party', *paths)

  def PlatformDir(self, *paths):
    """Compute a directory path relative to the 'platform' directory."""
    return self.SDKRoot('platform', *paths)

  def DataDir(self, *paths):
    """Compute a directory path relative to the 'data' directory."""
    return self.SDKRoot('data', *paths)


@Filters.RunOnlyInBundle
class BundledBase(SdkBase):
  """A base class for all Cloud SDK test cases that run in a bundled SDK."""

  def SetUp(self):
    # A way to get easy access to common directories in the SDK
    self.locations = _BundledLocations()

  def TearDown(self):
    pass

  def RegisterProcess(self, process):
    """Register a process that was started during a test.

    The process will be killed at the end of the test even when an error occurs

    Args:
      process: the Popen or multiprocess.Process object to kill
    """
    self.addCleanup(self._KillSubprocessIgnoreErrors, (process))

  @staticmethod
  def _AddPythonPathsToEnv(env):
    """Returns a copy of env with Python specific path vars added.

    This preserves any environment specific test runner tweaks.

    Args:
      env: {str: str}, Optional environment variables for the script.

    Returns:
      A copy of env with Python specific path vars added.
    """
    env_with_pythonpaths = dict(env if env else os.environ)
    # sys.path was initialized from PYTHONPATH at startup so we don't have to
    # check PYTHONPATH here. The result will be the original PYTHONPATH dirs
    # plus and dirs inserted/appened by Python startup and test runner
    # initialization.
    encoding.SetEncodedValue(
        env_with_pythonpaths, 'PYTHONPATH', os.pathsep.join(sys.path))
    return env_with_pythonpaths

  def ExecuteScript(self, script_name, args, timeout=None, stdin=None,
                    env=None, add_python_paths=True):
    """Execute the given wrapper script with the given args.

    This wrapper must be a sh script on non-windows, or a .cmd file, without the
    '.cmd' extension (so it has the same script_name as non-windows), on
    windows.

    Args:
      script_name: str, The script to run.
      args: [str], The arguments for the script.
      timeout: int, The number of seconds to wait before killing the process.
      stdin: str, Optional input for the script.
      env: {str: str}, Optional environment variables for the script.
      add_python_paths: bool, Add PYTHONPATH=sys.path to env if True.

    Returns:
      An ExecutionResult object.
    """
    args = exec_utils.GetArgsForScript(script_name, args)
    if add_python_paths:
      env = self._AddPythonPathsToEnv(env)
    # pylint: disable=protected-access
    runner = exec_utils._ProcessRunner(
        args, timeout=timeout, stdin=stdin, env=env)
    runner.Run()
    return runner.result

  def ExecuteLegacyScript(self, script_name, args, interpreter=None,
                          timeout=None, stdin=None, env=None,
                          add_python_paths=True):
    """Execute the given legacy script with the given args.

    Args:
      script_name: str, The script to run.
      args: [str], The arguments for the script.
      interpreter: str, An interpreter to use rather than trying to derive it
        from the extension name.
      timeout: int, The number of seconds to wait before killing the process.
      stdin: str, Optional input for the script.
      env: {str: str}, Optional environment variables for the script.
      add_python_paths: bool, Add PYTHONPATH=sys.path to env if True.

    Returns:
      An ExecutionResult object.
    """
    args = exec_utils.GetArgsForLegacyScript(
        script_name, args, interpreter=interpreter)
    if add_python_paths:
      env = self._AddPythonPathsToEnv(env)
    # pylint: disable=protected-access
    runner = exec_utils._ProcessRunner(
        args, timeout=timeout, stdin=stdin, env=env)
    runner.Run()
    return runner.result

  def ExecuteScriptAsync(self, script_name, args, match_strings=None,
                         timeout=None, stdin=None, env=None,
                         add_python_paths=True):
    """Execute the given script asynchronously in another thread.

    Same as ExecuteScript() except it does not wait for the process to return.
    Instead it returns a context manager that will kill the process once the
    scope exits.  If match_strings is given, the current thread will block until
    the process outputs lines of text that matches the strings in order, then
    the context manager will be returned and the process is kept alive.

    Args:
      script_name: str, The script to run.
      args: [str], The arguments for the script.
      match_strings: [str], A list of strings that must appear in the output in
                   the given order (a single output line may match multiple
                   given strings).
      timeout: int, The number of seconds to wait before killing the process.
      stdin: str, Optional input for the script.
      env: {str: str}, Optional environment variables for the script.
      add_python_paths: bool, Add PYTHONPATH=sys.path to env if True.

    Returns:
      A context manager that will kill the process once the scope exists.
    """
    args = exec_utils.GetArgsForScript(script_name, args)
    if add_python_paths:
      env = self._AddPythonPathsToEnv(env)
    # pylint: disable=protected-access
    runner = exec_utils._ProcessRunner(
        args, timeout=timeout, stdin=stdin, env=env)
    runner.RunAsync(match_strings=match_strings)
    # pylint: disable=protected-access
    return exec_utils._ProcessContext(runner)

  def ExecuteLegacyScriptAsync(self, script_name, args, interpreter=None,
                               match_strings=None, timeout=None, stdin=None,
                               env=None, add_python_paths=True):
    """Execute the given legacy script asynchronously in another thread.

    Same as ExecuteScript() except it does not wait for the process to return.
    Instead it returns a context manager that will kill the process once the
    scope exits.  If match_strings is given, the current thread will block until
    the process outputs lines of text that matches the strings in order, then
    the context manager will be returned and the process is kept alive.

    Args:
      script_name: str, The script to run.
      args: [str], The arguments for the script.
      interpreter: str, An interpreter to use rather than trying to derive it
        from the extension name.
      match_strings: [str], The output strings to match before returning.
      timeout: int, The number of seconds to wait before killing the process.
      stdin: str, Optional input for the script.
      env: {str: str}, Optional environment variables for the script.
      add_python_paths: bool, Add PYTHONPATH=sys.path to env if True.

    Returns:
      A context manager that will kill the process once the scope exists.
    """
    args = exec_utils.GetArgsForLegacyScript(
        script_name, args, interpreter=interpreter)
    if add_python_paths:
      env = self._AddPythonPathsToEnv(env)
    # pylint: disable=protected-access
    runner = exec_utils._ProcessRunner(
        args, timeout=timeout, stdin=stdin, env=env)
    runner.RunAsync(match_strings=match_strings)
    # pylint: disable=protected-access
    return exec_utils._ProcessContext(runner)

  def _KillSubprocessIgnoreErrors(self, process):
    try:
      execution_utils.KillSubprocess(process)
    except RuntimeError:
      # Attempting to kill processes that are no longer running on Windows
      # yields an error which we can safely ignore.
      pass


def main():
  return test_case.main()
