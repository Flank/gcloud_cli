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

"""Test of the 'operations' command."""
from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.container import util
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core import yaml
from googlecloudsdk.core.console import console_io
from surface.container.operations import cancel
from tests.lib import test_case
from tests.lib.surface.container import base


class OperationsTestGA(base.TestBaseV1,
                       base.GATestBase,
                       base.OperationsTestBase,
                       test_case.WithOutputCapture):
  """gcloud GA track using container v1 API."""

  def AssertOutputIsPendingCreateOp(self):
    # output should be valid yaml
    out = yaml.load(self.GetOutput())
    self.assertIsNotNone(out)
    self.assertEqual(out['operationType'], str(self.op_create))
    self.assertEqual(out['status'], str(self.op_pending))
    self.assertEqual(out['zone'], self.ZONE)

  def testDescribe(self):
    properties.VALUES.compute.zone.Set('default-zone')
    self.ExpectGetOperation(self._MakeOperation())
    self.Run(self.operations_command_base + ' --zone={0} describe {1}'.format(
        self.ZONE, self.MOCK_OPERATION_ID))
    self.AssertOutputIsPendingCreateOp()

  def testDescribeDefaults(self):
    properties.VALUES.compute.zone.Set(self.ZONE)
    self.ExpectGetOperation(self._MakeOperation())
    self.Run(self.operations_command_base + ' describe {0}'.format(
        self.MOCK_OPERATION_ID))
    self.AssertOutputIsPendingCreateOp()

  def testDescribeMissingZone(self):
    with self.assertRaises(exceptions.MinimumArgumentException):
      self.Run(self.operations_command_base + ' describe {0}'.format(
          self.MOCK_OPERATION_ID))

  def testDescribeMissingProject(self):
    properties.VALUES.core.project.Set(None)
    with self.assertRaises(properties.RequiredPropertyError):
      self.Run(self.operations_command_base + ' --zone={0} describe {1}'.format(
          self.ZONE, self.MOCK_OPERATION_ID))

  def testListOneZone(self):
    operations = [
        self._MakeOperation(),
    ]
    resp = self.msgs.ListOperationsResponse(operations=operations)
    self.ExpectListOperation(zone=self.ZONE, response=resp)
    self.Run(self.operations_command_base + ' --zone={0} list'.format(
        self.ZONE))
    self.AssertOutputContains('CREATE_CLUSTER')

  def testListOneRegion(self):
    kwargs = {'zone': self.REGION}
    operations = [
        self._MakeOperation(**kwargs),
    ]
    resp = self.msgs.ListOperationsResponse(operations=operations)
    self.ExpectListOperation(zone=self.REGION, response=resp)
    self.Run(self.operations_command_base + ' --region={0} list'.format(
        self.REGION))
    self.AssertOutputContains('CREATE_CLUSTER')

  def testListGlobal(self):
    properties.VALUES.compute.zone.Set('ignored-default-zone')
    delete = self.msgs.Operation.OperationTypeValueValuesEnum.DELETE_CLUSTER
    operations = [
        self._MakeOperation(),
        self._MakeOperation(
            operationType=delete,
            zone='some-other-zone')
    ]
    resp = self.msgs.ListOperationsResponse(operations=operations)
    self.ExpectListOperation(zone='-', response=resp)
    self.Run(self.operations_command_base + ' list')
    self.AssertOutputContains('CREATE_CLUSTER')
    self.AssertOutputContains('DELETE_CLUSTER')
    self.AssertOutputContains(self.ZONE)
    self.AssertOutputContains('some-other-zone')

  def testWaitSuccess(self):
    properties.VALUES.compute.zone.Set('default-zone')
    # Return pending a few times then success
    self.ExpectGetOperation(self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation(
        status=self.msgs.Operation.StatusValueValuesEnum.DONE))
    self.Run(self.operations_command_base + ' --zone={0} wait {1}'.format(
        self.ZONE, self.MOCK_OPERATION_ID))
    self.AssertErrContains(
        'Waiting for {0} to complete'.format(self.MOCK_OPERATION_ID))
    out = yaml.load(self.GetOutput())
    self.assertIsNotNone(out)
    self.assertEqual(out['operationType'], 'CREATE_CLUSTER')
    self.assertEqual(out['status'], 'DONE')
    self.assertEqual(out['zone'], self.ZONE)

  def testWaitFailure(self):
    properties.VALUES.compute.zone.Set('default-zone')
    # Return pending a few times then failure
    self.ExpectGetOperation(self._MakeOperation())
    self.ExpectGetOperation(self._MakeOperation())
    op = self._MakeOperation(
        status=self.msgs.Operation.StatusValueValuesEnum.DONE,
        errorMessage='something went wrong')
    self.ExpectGetOperation(op)
    with self.assertRaises(util.Error):
      self.Run(self.operations_command_base + ' --zone={0} wait {1}'.format(
          self.ZONE, self.MOCK_OPERATION_ID))
    self.AssertErrContains(
        'Operation [{0}] finished with error: something went wrong'.format(
            str(op)))

  def testWaitUnauthorized(self):
    properties.VALUES.compute.zone.Set('default-zone')
    self.ExpectGetOperation(self._MakeOperation(),
                            exception=base.UNAUTHORIZED_ERROR)
    with self.assertRaises(exceptions.HttpException):
      self.Run(self.operations_command_base + ' --zone={0} wait {1}'.format(
          self.ZONE, self.MOCK_OPERATION_ID))
    self.AssertErrContains('code=403, message=unauthorized')

  def _testCancel(self):
    properties.VALUES.compute.zone.Set('default-zone')
    op = self._MakeOperation()
    self.ExpectGetOperation(op)
    self.WriteInput('y')
    self.ExpectCancelOperation(op)
    self.ExpectGetOperation(op)
    self.Run(self.operations_command_base + ' --zone={0} cancel {1}'.format(
        self.ZONE, op.name))
    self.AssertErrContains(cancel.CANCEL_OPERATION_MESSAGE.
                           format(op.name, op.name))

  def _testCancelCancel(self):
    properties.VALUES.compute.zone.Set('default-zone')
    self.ExpectGetOperation(self._MakeOperation())
    self.WriteInput('n')
    self.ClearOutput()
    self.ClearErr()
    with self.assertRaises(console_io.OperationCancelledError):
      self.Run(self.operations_command_base + ' --zone={0} cancel {1}'.format(
          self.ZONE, self.MOCK_OPERATION_ID))
    self.AssertErrContains('Aborted by user.')


# TODO(b/64575339): switch to use parameterized testing.
# Mixin class must come in first to have the correct multi-inheritance behavior.
class OperationsTestBetaV1API(base.BetaTestBase, OperationsTestGA):
  """gcloud Beta track using container v1 API."""

  def SetUp(self):
    properties.VALUES.container.use_v1_api.Set(True)


# Mixin class must come in first to have the correct multi-inheritance behavior.
class OperationsTestBetaV1Beta1API(
    base.TestBaseV1Beta1, OperationsTestBetaV1API):
  """gcloud Beta track using container v1beta1 API."""

  def SetUp(self):
    properties.VALUES.container.use_v1_api.Set(False)


# Mixin class must come in first to have the correct multi-inheritance behavior.
class OperationsTestAlphaV1API(base.AlphaTestBase, OperationsTestBetaV1API):
  """gcloud Alpha track using container v1 API."""

  def SetUp(self):
    properties.VALUES.container.use_v1_api.Set(True)

  def testCancel(self):
    self._testCancel()

  def testCancelCancel(self):
    self._testCancelCancel()


# Mixin class must come in first to have the correct multi-inheritance behavior.
class OperationsTestAlphaV1Alpha1API(
    base.TestBaseV1Alpha1,
    OperationsTestAlphaV1API,
    OperationsTestBetaV1Beta1API):
  """gcloud Alpha track using container v1alpha1 API."""

  def SetUp(self):
    properties.VALUES.container.use_v1_api.Set(False)


if __name__ == '__main__':
  test_case.main()
