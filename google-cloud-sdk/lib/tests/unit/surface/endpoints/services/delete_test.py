# Copyright 2017 Google Inc. All Rights Reserved.
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

"""Unit tests for endpoints services delete command."""

from googlecloudsdk.core.console import console_io

from tests.lib import test_case
from tests.lib.surface.endpoints import unit_test_base


class EndpointsDeleteTest(unit_test_base.EV1UnitTestBase):
  """Unit tests for endpoints services delete command."""

  def testServicesDelete(self):
    operation_name = 'operation-12345-67890'
    self.mocked_client.services.Delete.Expect(
        request=self.services_messages.ServicemanagementServicesDeleteRequest(
            serviceName=self.DEFAULT_SERVICE_NAME
        ),
        response=self.services_messages.Operation(
            name=operation_name,
            done=True,
        )
    )

    self.MockOperationWait(operation_name)

    self.WriteInput('y\n')
    self.Run('endpoints services delete ' + self.DEFAULT_SERVICE_NAME)
    self.AssertErrContains(operation_name)
    self.AssertErrContains('Operation finished successfully.')

  def testServicesDeleteAsync(self):
    operation_name = 'operation-12345-67890'
    self.mocked_client.services.Delete.Expect(
        request=self.services_messages.ServicemanagementServicesDeleteRequest(
            serviceName=self.DEFAULT_SERVICE_NAME
        ),
        response=self.services_messages.Operation(
            name=operation_name,
            done=False,
        )
    )

    self.WriteInput('y\n')
    self.Run('endpoints services delete --async {0}'.format(
        self.DEFAULT_SERVICE_NAME))
    self.AssertErrContains(operation_name)
    self.AssertErrContains('Asynchronous operation is in progress')

  def testServicesDeleteCancelled(self):
    self.WriteInput('n\n')
    with self.assertRaisesRegex(console_io.OperationCancelledError,
                                'Aborted by user.'):
      self.Run('endpoints services delete ' + self.DEFAULT_SERVICE_NAME)

  def testServicesDeleteForced(self):
    operation_name = 'operation-12345-67890'
    self.mocked_client.services.Delete.Expect(
        request=self.services_messages.ServicemanagementServicesDeleteRequest(
            serviceName=self.DEFAULT_SERVICE_NAME
        ),
        response=self.services_messages.Operation(
            name=operation_name,
            done=False,
        )
    )

    self.MockOperationWait(operation_name)

    self.Run(
        'endpoints services delete --quiet %s' % self.DEFAULT_SERVICE_NAME)
    self.AssertErrContains(operation_name)
    self.AssertErrContains('Operation finished successfully.')


if __name__ == '__main__':
  test_case.main()
