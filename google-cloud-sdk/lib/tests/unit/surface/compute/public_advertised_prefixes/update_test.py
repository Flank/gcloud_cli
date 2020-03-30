# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Tests for the public advertised prefixes update subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.api_lib.util import waiter as waiter_test_base


class PublicAdvertisedPrefixesUpdateTest(sdk_test_base.WithFakeAuth,
                                         cli_test_base.CliTestBase,
                                         waiter_test_base.Base):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.client = mock.Client(core_apis.GetClientClass('compute', 'alpha'))
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'alpha')
    self.client.Mock()
    self.addCleanup(self.client.Unmock)
    self.messages = self.client.MESSAGES_MODULE
    self.compute_uri = (
        'https://www.googleapis.com/compute/{0}'.format('alpha'))
    self.pap_name = 'my-pap'
    self.operation_status_enum = self.messages.Operation.StatusValueValuesEnum
    self.status_enum = self.messages.PublicAdvertisedPrefix.StatusValueValuesEnum

  def _GetOperationMessage(self, operation_name, status, resource_uri=None):
    return self.messages.Operation(
        name=operation_name,
        status=status,
        selfLink='{0}/projects/{1}/global/operations/{2}'.format(
            self.compute_uri, self.Project(), operation_name),
        targetLink=resource_uri)

  def _ExpectGet(self, resource):
    self.client.publicAdvertisedPrefixes.Get.Expect(
        self.messages.ComputePublicAdvertisedPrefixesGetRequest(
            publicAdvertisedPrefix=self.pap_name, project=self.Project()),
        resource)

  def _ExpectPatch(self, status, fingerprint):
    self.client.publicAdvertisedPrefixes.Patch.Expect(
        self.messages.ComputePublicAdvertisedPrefixesPatchRequest(
            publicAdvertisedPrefix=self.pap_name,
            project=self.Project(),
            publicAdvertisedPrefixResource=self.messages.PublicAdvertisedPrefix(
                status=status, fingerprint=fingerprint)),
        self._GetOperationMessage('operation-covfefe',
                                  self.operation_status_enum.PENDING))

  def _ExpectPoll(self):
    pap_uri = (
        self.compute_uri + '/projects/{0}/global/'
        'publicAdvertisedPrefixes/{1}'.format(self.Project(), self.pap_name))
    self.client.globalOperations.Wait.Expect(
        self.messages.ComputeGlobalOperationsWaitRequest(
            operation='operation-covfefe', project=self.Project()),
        self._GetOperationMessage(
            'operation-covfefe',
            self.messages.Operation.StatusValueValuesEnum.DONE, pap_uri))

  def testUpdate_setStatus(self):
    old_pap = self.messages.PublicAdvertisedPrefix(
        name=self.pap_name, status=self.status_enum.INITIAL, fingerprint=b'old')
    new_pap = self.messages.PublicAdvertisedPrefix(
        name=self.pap_name,
        status=self.status_enum.PTR_CONFIGURED,
        fingerprint=b'new')
    self._ExpectGet(old_pap)
    self._ExpectPatch(self.status_enum.PTR_CONFIGURED, b'old')
    self._ExpectPoll()
    self._ExpectGet(new_pap)
    result = self.Run('compute public-advertised-prefixes update {} '
                      '--status=ptr-configured'.format(self.pap_name))
    self.assertEqual(new_pap, result)
    self.AssertErrContains('Updating public advertised prefix [{}].'.format(
        self.pap_name))


if __name__ == '__main__':
  test_case.main()
