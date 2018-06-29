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

"""Base class for all Functions commands tests."""

from __future__ import absolute_import
from __future__ import unicode_literals
from apitools.base.py.testing import mock as apitools_mock

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.util import gcloudignore
from googlecloudsdk.core.util import archive
from googlecloudsdk.core.util import files as file_utils
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import sdk_test_base

import mock

NO_PROJECT_REGEXP = r'The required property \[project\] is not currently set'
NO_PROJECT_RESOURCE_ARG_REGEXP = r'Failed to find attribute \[project\]'
NO_AUTH_REGEXP = (r'Your current active account \[.*\] does not have any valid '
                  'credentials')
OP_FAILED_REGEXP = r'OperationError: code=13, message=Operation has failed.'


class FunctionsTestBase(sdk_test_base.WithFakeAuth,
                        cli_test_base.CliTestBase,
                        parameterized.TestCase):
  """Base class for tests in functions package. Project is not set here."""

  def SetUp(self):
    # TODO(b/36553351): Untangle tests.
    self.mock_client = apitools_mock.Client(
        core_apis.GetClientClass('cloudfunctions', 'v1'),
        real_client=core_apis.GetClientInstance('cloudfunctions', 'v1',
                                                no_http=True))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)
    self.messages = core_apis.GetMessagesModule('cloudfunctions', 'v1')
    self.track = calliope_base.ReleaseTrack.GA
    self._region = 'us-central1'
    self.StartPatch('time.sleep')

  def ReturnUnderMaxSize(self, *unused_args, **unused_kwargs):
    return 50 * 2**20 + 1

  def ReturnLargeFileSize(self, *unused_args, **unused_kwargs):
    return 512 * 2**20 + 1

  def MockUnpackedSourcesDirSize(self):
    self.StartObjectPatch(
        file_utils, 'GetTreeSizeBytes', self.ReturnUnderMaxSize)

  def MockChooserAndMakeZipFromFileList(self):
    mock_chooser = mock.MagicMock(gcloudignore.FileChooser)
    mock_chooser.GetIncludedFiles.return_value = []
    self.StartObjectPatch(
        gcloudignore, 'GetFileChooserForDir', return_value=mock_chooser)
    self.StartObjectPatch(archive, 'MakeZipFromDir')

  def GetRegion(self):
    return self._region

  def SetRegion(self, region):
    self._region = region

  def _GenerateFailedStatus(self):
    failed_status = self.messages.Status()
    failed_status.code = 13
    failed_status.message = 'Operation has failed.'
    return failed_status

  def _GenerateActiveOperation(self, name):
    operation = self.messages.Operation()
    operation.name = name
    return operation

  def _GenerateFailedOperation(self, name):
    operation = self.messages.Operation()
    operation.name = name
    operation.done = True
    operation.error = self._GenerateFailedStatus()
    return operation

  def _GenerateSuccessfulOperation(self, name):
    operation = self.messages.Operation()
    operation.name = name
    operation.done = True
    return operation
