# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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


"""Unit tests for 'types update' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.api_lib.deployment_manager import exceptions
from tests.lib import test_case
from tests.lib.surface.deployment_manager import unit_test_base


CT_NAME = 'tp1'
DESCRIPTOR_URL = 'foobar.com'
DESCRIPTION = 'foo bar'
STATUS = 'EXPERIMENTAL'


class TypesUpdateTest(unit_test_base.CompositeTypesUnitTestBase):
  """Unit tests for 'types update' command.

  We only test a few scenarios here, because most of the functionality is
  covered by the DeploymentManagerWriteCommand.
  """

  def SetUp(self):
    self.TargetingV2BetaApi()
    self.TargetingBetaCommandTrack()
    self.withExpectedGet()
    self.withExpectedUpdate()

  def FinalTestDataDir(self):
    return 'simple_configs'

  def testUpdateOneCompositeTypeSuccess(self):
    self.WithOperationPolling(operation_type='update')
    self.Run(self.updateComand())
    self.AssertOutputEquals('')
    self.AssertErrContains('Waiting for update [op-123]')
    self.AssertErrContains('Updated composite_type [tp1].')

  def testAsync(self):
    self.Run(self.updateComand() + ' --async')
    self.AssertOutputEquals('Operation [op-123] running....\n')
    self.AssertErrContains('Update in progress for composite_type [tp1].\n')

  def testOperationFailed(self):
    self.WithOperationPolling(poll_attempts=0,
                              error=self.OperationErrorFor('something bad'),
                              operation_type='update')
    with self.assertRaisesRegex(exceptions.Error,
                                re.compile(r'.*something bad.*')):
      self.Run(self.updateComand())

  def updateComand(self):
    return ('deployment-manager types update {0} --description "{1}" '
            '--status {2} --update-labels {3} --remove-labels {4}'.format(
                CT_NAME,
                DESCRIPTION,
                STATUS,
                'foo=baz',
                'baz'))

  def withExpectedGet(self):
    composite_type = self.messages.CompositeType(
        name=CT_NAME,
        description=DESCRIPTION,
        status=STATUS,
        templateContents=self.GetExpectedSimpleTemplate(),
        labels=[self.messages.CompositeTypeLabelEntry(key='baz', value='quux'),
                self.messages.CompositeTypeLabelEntry(key='foo', value='bar')])
    self.mocked_client.compositeTypes.Get.Expect(
        request=self.messages.DeploymentmanagerCompositeTypesGetRequest(
            project=self.Project(),
            compositeType=CT_NAME),
        response=composite_type
    )

  def withExpectedUpdate(self):
    composite_type = self.messages.CompositeType(
        name=CT_NAME,
        description=DESCRIPTION,
        status=STATUS,
        templateContents=self.GetExpectedSimpleTemplate(),
        labels=[self.messages.CompositeTypeLabelEntry(key='foo', value='baz')])
    self.mocked_client.compositeTypes.Update.Expect(
        request=self.messages.DeploymentmanagerCompositeTypesUpdateRequest(
            project=self.Project(),
            compositeType=CT_NAME,
            compositeTypeResource=composite_type),
        response=self.messages.Operation(
            name=self.OPERATION_NAME,
            operationType='update',
            status='PENDING',
        )
    )


if __name__ == '__main__':
  test_case.main()


