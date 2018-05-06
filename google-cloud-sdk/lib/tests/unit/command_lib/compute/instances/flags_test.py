# Copyright 2016 Google Inc. All Rights Reserved.
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

"""Unit tests for the intances flags module."""
import argparse

import collections

from apitools.base.py import batch
from googlecloudsdk.api_lib.compute import client_adapter
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.command_lib.compute import scope
from googlecloudsdk.command_lib.compute.instances import flags
from googlecloudsdk.core import log
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.compute import test_base as compute_test_base


class InstanceFlagsTest(test_case.TestCase):

  def SetUp(self):
    self.messages = core_apis.GetMessagesModule('compute', 'v1')

  def testMigrationOptionsMatchApi(self):
    self.assertEqual(sorted(flags.MIGRATION_OPTIONS.keys()), sorted(
        self.messages.Scheduling.OnHostMaintenanceValueValuesEnum
        .to_dict().keys()))

  def testLocalSSdInterfacesMatchApi(self):
    self.assertEqual(flags.LOCAL_SSD_INTERFACES, sorted(
        self.messages.AttachedDisk.InterfaceValueValuesEnum.to_dict().keys()))

  def testWarnForSourceInstanceTemplateLimitationsNoTrigger(self):
    def IsSpecified(name):
      return name not in ['source_instance_template']

    args = argparse.Namespace()
    args.IsSpecified = IsSpecified

    write_mock = self.StartObjectPatch(log.status, 'write')

    flags.WarnForSourceInstanceTemplateLimitations(args)

    write_mock.assert_not_called()

  def testWarnForSourceInstanceTemplateLimitationsNegative(self):

    def IsSpecified(name):
      return name in [
          'source_instance_template', 'machine_type', 'custom_cpu',
          'custom-memory', 'labels'
      ]

    def GetSpecifiedArgNames():
      return [
          '--source-instance-template', '--machine-type', '--custom-cpu',
          '--custom-memory', '--labels'
      ]

    args = argparse.Namespace()
    args.IsSpecified = IsSpecified
    args.GetSpecifiedArgNames = GetSpecifiedArgNames

    write_mock = self.StartObjectPatch(log.status, 'write')

    flags.WarnForSourceInstanceTemplateLimitations(args)

    write_mock.assert_not_called()

  def testWarnForSourceInstanceTemplateLimitationsPositive(self):

    def IsSpecified(name):
      return name in ['source_instance_template', 'unsupperted_flag']

    def GetSpecifiedArgNames():
      return ['--source-instance-template', '--unsupported-flag']

    args = argparse.Namespace()
    args.IsSpecified = IsSpecified
    args.GetSpecifiedArgNames = GetSpecifiedArgNames

    write_mock = self.StartObjectPatch(log.status, 'write', autospec=True)

    flags.WarnForSourceInstanceTemplateLimitations(args)

    write_mock.assert_called()


class InstanceZoneScopeListerTest(compute_test_base.BaseTest):

  def SetUp(self):
    self.client = client_adapter.ClientAdapter('v1', no_http=True)
    self.messages = core_apis.GetMessagesModule('compute', 'v1')
    self.scopes = [scope.ScopeEnum.ZONE]

  def testListMatchingZoneScopes_OneMatch(self):
    aggregate_list_response = [
        self.messages.Instance(name='instance-1', zone='zone-1'),
    ]
    self.make_requests.side_effect = iter([aggregate_list_response])

    self.assertEqual(
        flags.InstanceZoneScopeLister(self.client, None, ['instance-1']),
        {scope.ScopeEnum.ZONE: [self.messages.Zone(name='zone-1')]}
    )

  def testListMatchingZoneScopes_MultipleMatches(self):
    aggregate_list_response = [
        self.messages.Instance(name='my-instance', zone='zone-1'),
        self.messages.Instance(name='my-instance', zone='zone-2'),
    ]
    self.make_requests.side_effect = iter([aggregate_list_response])

    self.assertEqual(
        flags.InstanceZoneScopeLister(self.client, self.scopes,
                                      ['my-instance']),
        {scope.ScopeEnum.ZONE: [self.messages.Zone(name='zone-1'),
                                self.messages.Zone(name='zone-2')]}
    )

  def testAggregateListError(self):
    http_err = http_error.MakeHttpError(code=444)
    payload = collections.namedtuple('Payload',
                                     ['is_error', 'exception', 'response'])
    aggregate_list_response = payload(
        response='response', is_error=True, exception=http_err)
    self.StartObjectPatch(batch.BatchApiRequest, 'Execute',
                          return_value=[aggregate_list_response])
    full_zone_list = [self.messages.Zone(name='zone-.{}'.format(i))
                      for i in range(10)]
    self.StartPatch('googlecloudsdk.api_lib.compute.zones.service.List',
                    return_value=full_zone_list)

    self.assertEqual(
        flags.InstanceZoneScopeLister(self.client, self.scopes,
                                      ['my-instance']),
        {scope.ScopeEnum.ZONE: full_zone_list}
    )


if __name__ == '__main__':
  test_case.main()
