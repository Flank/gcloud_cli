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
"""Module for test base classes."""

import logging
import os
import tempfile

from apitools.base.py import exceptions
from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
import httplib2


class BaseTest(sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase):
  """Base class for gcloud iam.tests.unit."""

  def Project(self):
    """The project to use for this test."""
    return 'test-project'

  def SetUp(self):
    self.msgs = apis.GetMessagesModule('iam', 'v1')
    self._file_write_mocks = {}
    self._files_to_delete = []
    self.addCleanup(self._HandleFileMocks)

    self.sample_unique_id = '123456789876543212345'

    properties.VALUES.core.project.Set(self.Project())
    self.client = mock.Client(client_class=apis.GetClientClass('iam', 'v1'))
    self.client.Mock()
    self.addCleanup(self.client.Unmock)
    log.SetVerbosity(logging.INFO)
    self.PostSetUp()

  def PostSetUp(self):
    pass

  def _GetMockFile(self):
    """Returns a temporary filename to use for mocking.

    Additionally, keeps track of it to be deleted after the test suite is
    finished.

    Returns:
      A temporary filename that doesn't yet exist.
    """
    file_obj = tempfile.NamedTemporaryFile()
    filename = file_obj.name
    # Windows platforms give permission denied errors if you try to use this
    # filename without closing the file object. Python doesn't have a way to
    # just generate a tempname. It's gnarly, but hey, it works.
    file_obj.close()
    self._files_to_delete.append(filename)
    return filename

  def MockFileRead(self, contents):
    """Mocks a file to be used as input to the test.

    Args:
      contents: The result of reading this file.

    Returns:
      The filename of the input file.
    """
    tmp_file = self._GetMockFile()
    with open(tmp_file, 'wb') as handle:
      handle.write(contents)
    return tmp_file

  def MockFileWrite(self, expected):
    """Mocks a file that should be written during a test.

    When the test concludes, the contents in this file will be automatically
    checked against the expected value.

    Args:
      expected: The result expected to be written into this file during the
      test's run.

    Returns:
      The filename of the output file.
    """
    tmp_file = self._GetMockFile()
    self._file_write_mocks[tmp_file] = expected
    return tmp_file

  def _HandleFileMocks(self):
    """Cleanup function to deal with file mocking.

    When run, this function ensures all MockFileWrite objects have the correct
    written value. Afterwards, it will delete every temp file created by
    MockFileWrite or MockFileRead.

    Raises:
      AssertionError: The MockFileWrite wasn't written with the correct data.
    """
    for tmp_file, expected in self._file_write_mocks.items():
      with open(tmp_file, 'rb') as handle:
        actual = handle.read()
        if expected != actual:
          raise AssertionError(
              'Expected file managed by MockFileWrite to have `{0}` written, '
              'actually got `{1}`'.format(expected, actual))

    for tmp_file in self._files_to_delete:
      os.remove(tmp_file)

  def MockHttpError(self, status, reason, body=None, url=None):
    """Creates a mock HTTP error.

    Useful to mock client interactions with missing resources.

    Args:
      status: The HTTP status.
      reason: Why the error occurred.
      body: The body of the response.
      url: The URL this error occurred at.

    Returns:
      An HttpError object.
    """
    if body is None:
      body = ''
    response = httplib2.Response({'status': status, 'reason': reason})
    return exceptions.HttpError(response, body, url)
