# Copyright 2014 Google Inc. All Rights Reserved.
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

"""Base for Deployment Manager V2 unit tests."""

from __future__ import absolute_import
from __future__ import unicode_literals
import time

from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from six.moves import range  # pylint: disable=redefined-builtin


_TEST_DATA_DIR = ['tests', 'lib', 'surface', 'deployment_manager', 'test_data']


class DmV2UnitTestBase(
    sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase):
  """Base class for Deployment manager unit tests."""

  OPERATION_NAME = 'op-123'

  def SetUp(self):
    properties.VALUES.core.project.Set(self.Project())

    self.TargetingV2Api()

    # Mock out time.sleep calls in operation polling
    self.time_mock = self.StartObjectPatch(time, 'time')
    self.sleep_mock = self.StartObjectPatch(time, 'sleep')

  def GetTestFilePath(self, *path):
    return self.Resource(*(_TEST_DATA_DIR
                           + [self.FinalTestDataDir()]
                           + list(path)))

  def FinalTestDataDir(self):
    raise NotImplementedError('Give me the last part of your test data path!')

  def TargetingAlphaApi(self):
    self._TargetApiVersion('alpha')

  def TargetingV2BetaApi(self):
    self._TargetApiVersion('v2beta')

  def TargetingV2Api(self):
    self._TargetApiVersion('v2')

  def _TargetApiVersion(self, version):
    self.mocked_client = mock.Client(
        apis.GetClientClass('deploymentmanager', version),
        real_client=apis.GetClientInstance('deploymentmanager', version))
    self.mocked_client.Mock()
    self.addCleanup(self.mocked_client.Unmock)

    self.messages = apis.GetMessagesModule('deploymentmanager', version)

  def TargetingAlphaCommandTrack(self):
    self.track = base.ReleaseTrack.ALPHA

  def TargetingBetaCommandTrack(self):
    self.track = base.ReleaseTrack.BETA

  def WithOperationPolling(self,
                           operation_type,
                           poll_attempts=2,
                           error=None,
                           require_final_poll=True):
    operation_name = self.OPERATION_NAME

    for _ in range(poll_attempts):
      # Operation is pending for a while
      self.mocked_client.operations.Get.Expect(
          request=self.messages
          .DeploymentmanagerOperationsGetRequest(
              project=self.Project(),
              operation=operation_name,
          ),
          response=self.messages.Operation(
              name=operation_name,
              status='PENDING',
          )
      )
    # Polling is finished, so respond with completion failure or success
    if error:
      self.mocked_client.operations.Get.Expect(
          request=self.messages
          .DeploymentmanagerOperationsGetRequest(
              project=self.Project(),
              operation=operation_name,
          ),
          response=self.messages.Operation(
              name=operation_name,
              operationType=operation_type,
              status='DONE',
              error=error
          )
      )
    elif require_final_poll:
      self.mocked_client.operations.Get.Expect(
          request=self.messages
          .DeploymentmanagerOperationsGetRequest(
              project=self.Project(),
              operation=operation_name,
          ),
          response=self.messages.Operation(
              name=operation_name,
              operationType=operation_type,
              status='DONE',
          )
      )

  def OperationErrorFor(self, message):
    return self.messages.Operation.ErrorValue(
        errors=[
            self.messages.Operation.ErrorValue.ErrorsValueListEntry(
                code='400',
                location='quux',
                message=message
            )
        ]
    )


class CompositeTypesUnitTestBase(DmV2UnitTestBase):

  def GetExpectedSimpleTemplate(self):
    imports = {}
    for import_path in ['simple.jinja', 'simple.jinja.schema', 'helper.jinja']:
      full_import_path = self.GetTestFilePath(import_path)
      with open(full_import_path, 'r') as import_file:
        imports[import_path] = import_file.read()

    expected_template = self.messages.TemplateContents(
        imports=[self.messages.ImportFile(
            name='helper.jinja',
            content=imports['helper.jinja']
        )],
        schema=imports['simple.jinja.schema'],
        template=imports['simple.jinja'],
        interpreter='JINJA'
    )
    return expected_template
