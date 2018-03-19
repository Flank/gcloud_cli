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

"""Unit tests for service-management enable command."""

from googlecloudsdk.api_lib.services import exceptions
from googlecloudsdk.api_lib.util import exceptions as api_lib_exceptions
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.services import unit_test_base


class ServicesEnableTest(unit_test_base.SV1UnitTestBase):
  """Unit tests for services enable command."""

  def testServicesEnable(self):
    operation_name = 'operation-12345-67890'

    self.mocked_client.services.Enable.Expect(
        request=self.services_messages.ServicemanagementServicesEnableRequest(
            serviceName=self.DEFAULT_SERVICE_NAME,
            enableServiceRequest=self.services_messages.EnableServiceRequest(
                consumerId='project:' + self.PROJECT_NAME
            )
        ),
        response=self.services_messages.Operation(
            name=operation_name,
            done=False,
        )
    )

    self.MockOperationWait(operation_name)

    self.WriteInput('y\n')
    self.Run('services enable %s' % self.DEFAULT_SERVICE_NAME)
    self.AssertErrContains(operation_name)
    self.AssertErrContains('Operation finished successfully.')

  def testServicesMultiEnable(self):
    num_services = 3
    service_names = ['service-name%d.googleapis.com' % i
                     for i in range(num_services)]
    operation_names = ['operation-12345-%d' % i for i in range(num_services)]

    messages = self.services_messages
    for service_name, operation_name in zip(service_names, operation_names):
      self.mocked_client.services.Enable.Expect(
          request=messages.ServicemanagementServicesEnableRequest(
              serviceName=service_name,
              enableServiceRequest=messages.EnableServiceRequest(
                  consumerId='project:' + self.PROJECT_NAME
              )
          ),
          response=messages.Operation(
              name=operation_name,
              done=False,
          )
      )
      self.MockOperationWait(operation_name)

    self.WriteInput('y\n')
    self.Run('services enable %s' % ' '.join(service_names))
    for operation_name in operation_names:
      self.AssertErrContains(operation_name)
    self.AssertErrContains('Operation finished successfully.')

  def testServicesEnableAsync(self):
    operation_name = 'operation-12345-67890'

    self.mocked_client.services.Enable.Expect(
        request=self.services_messages.ServicemanagementServicesEnableRequest(
            serviceName=self.DEFAULT_SERVICE_NAME,
            enableServiceRequest=self.services_messages.EnableServiceRequest(
                consumerId='project:' + self.PROJECT_NAME
            )
        ),
        response=self.services_messages.Operation(
            name=operation_name,
            done=False,
        )
    )

    self.WriteInput('y\n')
    self.Run('services enable %s --async' % (self.DEFAULT_SERVICE_NAME))
    self.AssertErrContains(operation_name)
    self.AssertErrContains('Asynchronous operation is in progress.')

  def testServicesEnableConsumer(self):
    operation_name = 'operation-12345-67890'
    consumer_project = 'another-consumer-project'

    self.mocked_client.services.Enable.Expect(
        request=self.services_messages.ServicemanagementServicesEnableRequest(
            serviceName=self.DEFAULT_SERVICE_NAME,
            enableServiceRequest=self.services_messages.EnableServiceRequest(
                consumerId='project:' + consumer_project
            )
        ),
        response=self.services_messages.Operation(
            name=operation_name,
            done=False,
        )
    )

    self.MockOperationWait(operation_name)

    self.WriteInput('y\n')
    self.Run('services enable %s '
             '--project %s' % (self.DEFAULT_SERVICE_NAME, consumer_project))
    self.AssertErrContains(operation_name)
    self.AssertErrContains('Operation finished successfully.')

  def _ExpectEnableServiceCall_Error(self, consumer_project, server_error):
    self.mocked_client.services.Enable.Expect(
        request=self.services_messages.ServicemanagementServicesEnableRequest(
            serviceName=self.DEFAULT_SERVICE_NAME,
            enableServiceRequest=self.services_messages.EnableServiceRequest(
                consumerId='project:' + consumer_project
            )
        ),
        exception=server_error
    )

  def testServicesEnableConsumer_PermissionsError(self):
    consumer_project = 'another-consumer-project'
    server_error = http_error.MakeDetailedHttpError(code=403, message='Error.')
    self._ExpectEnableServiceCall_Error(consumer_project, server_error)
    self.WriteInput('y\n')
    with self.assertRaises(
        exceptions.EnableServicePermissionDeniedException):
      self.Run('services enable %s '
               '--project %s' % (self.DEFAULT_SERVICE_NAME, consumer_project))

  def testServicesEnableConsumer_GenericError(self):
    consumer_project = 'another-consumer-project'
    server_error = http_error.MakeDetailedHttpError(code=400, message='Error.')
    self._ExpectEnableServiceCall_Error(consumer_project, server_error)
    self.WriteInput('y\n')
    with self.assertRaises(api_lib_exceptions.HttpException):
      self.Run('services enable %s '
               '--project %s' % (self.DEFAULT_SERVICE_NAME, consumer_project))


if __name__ == '__main__':
  test_case.main()
