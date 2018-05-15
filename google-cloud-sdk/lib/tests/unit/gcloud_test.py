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

"""Tests for gcloud entry point."""

from __future__ import absolute_import
from __future__ import unicode_literals

import errno
import signal
import sys

import gcloud
from googlecloudsdk.calliope import command_loading
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib import crash_handling
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import store
from tests.lib import sdk_test_base

import mock
import six


class GcloudTest(sdk_test_base.WithOutputCapture):

  def SetUp(self):
    self.cli = self.StartObjectPatch(
        parser_extensions.ArgumentParser, 'parse_args')
    self.old_int_handler = signal.getsignal(signal.SIGINT)
    self.report_error_mock = self.StartObjectPatch(
        crash_handling, 'ReportError')
    properties.VALUES.core.allow_py3.Set(True)

  def TearDown(self):
    signal.signal(signal.SIGINT, self.old_int_handler)

  def testKeyboardInterrupt(self):
    """Ensures that an exception caused by a keyboard interrupt passes through.

    This is important so that proper clean-up happens.
    """
    self.cli.side_effect = KeyboardInterrupt
    self.assertRaises(KeyboardInterrupt, gcloud.main)

  def testException(self):
    """Ensures that unhandled exceptions direct the user to 'gcloud feedback'.

    gcloud should exit with a non-zero exit code.
    """
    msg = 'Example exception message text'
    exception = Exception(msg)
    self.cli.side_effect = exception
    self.assertRaises(SystemExit, gcloud.main)
    self.report_error_mock.assert_called_once_with(exception, is_crash=True)

  def testKnownError(self):
    # We want to suggest reinstall here
    msg = 'Example exception message text'
    exception = exceptions.Error(msg)
    self.cli.side_effect = exception
    self.assertRaises(SystemExit, gcloud.main)
    self.report_error_mock.assert_called_once_with(exception, is_crash=False)

  def testIOErrorEPIPE(self):
    msg = 'Example exception message text'
    exception = IOError(errno.EPIPE, msg)
    self.cli.side_effect = exception
    self.assertRaises(SystemExit, gcloud.main)
    self.report_error_mock.assert_not_called()

  def testExceptionWithTraceback(self):
    properties.VALUES.core.print_unhandled_tracebacks.Set(True)
    msg = 'Example exception message text'
    exception = Exception(msg)
    self.cli.side_effect = exception
    self.assertRaisesRegex(Exception, msg, gcloud.main)
    self.report_error_mock.assert_called_once_with(exception, is_crash=True)

  def testExceptionImportErrorRunCommand(self):
    crash_handling_mock = self.StartObjectPatch(crash_handling,
                                                'HandleGcloudCrash')
    # We want to suggest reinstall here
    msg = 'Example exception message text'
    exception = command_loading.CommandLoadFailure('gcloud version',
                                                   ImportError(msg))
    self.cli.side_effect = exception
    self.assertRaises(SystemExit, gcloud.main)
    crash_handling_mock.assert_called_once_with(exception)

  def testNormalExit(self):
    devshell_mock = self.StartObjectPatch(
        store.DevShellCredentialProvider, 'Register')
    gce_mock = self.StartObjectPatch(
        store.GceCredentialProvider, 'Register')
    devshell_unregister_mock = self.StartObjectPatch(
        store.DevShellCredentialProvider, 'UnRegister')
    gce_unregister_mock = self.StartObjectPatch(
        store.GceCredentialProvider, 'UnRegister')
    with self.assertRaises(SystemExit) as cm:
      gcloud.main()
    self.assertIsNone(cm.exception.code)
    self.report_error_mock.assert_not_called()
    devshell_mock.assert_called_once()
    devshell_unregister_mock.assert_called_once()
    gce_mock.assert_called_once()
    gce_unregister_mock.assert_called_once()
    self.assertMultiLineEqual('', self.GetErr())
    self.assertMultiLineEqual('', self.GetOutput())

  def testExceptionImportErrorImportingGcloudMain(self):
    # If there's an error importing gcloud_main from gcloud, don't suggest
    # reinstall
    module_path = '.'.join(['googlecloudsdk', 'gcloud_main'])
    with mock.patch.dict('sys.modules', {module_path: None}):
      with self.assertRaises(SystemExit) as cm:
        gcloud.main()
      self.assertEqual(1, cm.exception.code)
      self.report_error_mock.assert_not_called()
    error = (
        'No module named gcloud_main' if six.PY2 else
        "import of 'gcloud_main' halted; None in sys.modules")
    self.assertMultiLineEqual("""\
ERROR: gcloud failed to load: {0}
    gcloud_main = _import_gcloud_main()
    import {1}

This usually indicates corruption in your gcloud installation or problems with \
your Python interpreter.

Please verify that the following is the path to a working Python 2.7 executable:
    {2}

If it is not, please set the CLOUDSDK_PYTHON environment variable to point to \
a working Python 2.7 executable.

If you are still experiencing problems, please reinstall the Cloud SDK using \
the instructions here:
    https://cloud.google.com/sdk/
""".format(error, module_path, sys.executable), self.GetErr())
    self.assertMultiLineEqual('', self.GetOutput())

  def testExceptionOtherErrorImportingGcloudMain(self):
    # If there's an error importing gcloud_main from gcloud, don't suggest
    # reinstall
    self.StartObjectPatch(gcloud, '_import_gcloud_main',
                          side_effect=Exception('Exception message'))
    with self.assertRaises(SystemExit) as cm:
      gcloud.main()
    self.assertEqual(1, cm.exception.code)
    self.report_error_mock.assert_not_called()
    self.maxDiff = None
    self.assertMultiLineEqual("""\
ERROR: gcloud failed to load: Exception message
    gcloud_main = _import_gcloud_main()
    return _mock_self._mock_call(*args, **kwargs)
    raise effect

This usually indicates corruption in your gcloud installation or problems with \
your Python interpreter.

Please verify that the following is the path to a working Python 2.7 executable:
    {0}

If it is not, please set the CLOUDSDK_PYTHON environment variable to point to \
a working Python 2.7 executable.

If you are still experiencing problems, please reinstall the Cloud SDK using \
the instructions here:
    https://cloud.google.com/sdk/
""".format(sys.executable), self.GetErr())
    self.assertMultiLineEqual('', self.GetOutput())


if __name__ == '__main__':
  sdk_test_base.main()
