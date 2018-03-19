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
"""Tests for the instance-groups unmanaged list subcommand."""
import textwrap

from googlecloudsdk.command_lib.compute import completers
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources

import mock

API_VERSION = 'v1'


class UnmanagedInstanceGroupsListTest(test_base.BaseTest,
                                      completer_test_base.CompleterBase):

  def SetUp(self):
    self.SelectApi(API_VERSION)
    def _MockGetZonalResources(service, project, requested_zones,
                               filter_expr, http, batch_url, errors):
      _ = project, requested_zones, filter_expr, http, batch_url, errors
      if service == self.compute.instanceGroupManagers:
        return test_resources.MakeInstanceGroupManagers(API_VERSION)
      if service == self.compute.instanceGroups:
        non_zonal_group = (self.messages.InstanceGroup(
            name='regional-group',
            selfLink=('https://www.googleapis.com/compute/{0}/'
                      'projects/my-project/regions/region-1/'
                      'instanceGroups/group-1'.format(API_VERSION)),
            creationTimestamp='2013-09-06T17:54:10.636-07:00',
            description='Test regional instance group',
            fingerprint='123',
            namedPorts=[],
            size=0,
        ))
        return (test_resources.MakeInstanceGroups(self.messages, API_VERSION)
                + [non_zonal_group])
      return None

    lister_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.lister.GetZonalResources',
        autospec=True)
    self.addCleanup(lister_patcher.stop)
    self.mock_get_zonal_resources = lister_patcher.start()
    self.mock_get_zonal_resources.side_effect = _MockGetZonalResources

    def _MockGetZonalResourcesDicts(*args, **kwargs):
      messages = _MockGetZonalResources(*args, **kwargs)
      return resource_projector.MakeSerializable(messages)

    lister_patcher_dicts = mock.patch(
        'googlecloudsdk.api_lib.compute.lister.GetZonalResourcesDicts',
        autospec=True)
    self.addCleanup(lister_patcher_dicts.stop)
    self.mock_get_zonal_resources_dicts = lister_patcher_dicts.start()
    self.mock_get_zonal_resources_dicts.side_effect = (
        _MockGetZonalResourcesDicts)

  def testTableOutput(self):
    self.Run("""compute instance-groups unmanaged list
      """)
    self.mock_get_zonal_resources_dicts.assert_called_once_with(
        service=self.compute.instanceGroups,
        project='my-project',
        requested_zones=[],
        filter_expr=None,
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.mock_get_zonal_resources.assert_any_call(
        service=self.compute.instanceGroupManagers,
        project='my-project',
        requested_zones=set(['zone-1']),
        filter_expr=None,
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME    ZONE   NETWORK   NETWORK_PROJECT MANAGED INSTANCES
            group-4 zone-1 network-1 my-project      No      1
            """), normalize_space=True)

  def testUriOutputOnly(self):
    self.Run('compute instance-groups unmanaged list --uri')
    self.mock_get_zonal_resources_dicts.assert_called_once_with(
        service=self.compute.instanceGroups,
        project='my-project',
        requested_zones=[],
        filter_expr=None,
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.mock_get_zonal_resources.assert_any_call(
        service=self.compute.instanceGroupManagers,
        project='my-project',
        requested_zones=set(['zone-1']),
        filter_expr=None,
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://www.googleapis.com/compute/{0}/projects/my-project/zones/zone-1/instanceGroups/group-4
            """.format(API_VERSION)), normalize_space=True)

  def testInstanceGroupsCompleter(self):
    self.RunCompleter(
        completers.InstanceGroupsCompleter,
        expected_command=[
            'compute',
            'instance-groups',
            'unmanaged',
            'list',
            '--uri',
            '--quiet',
            '--format=disable',
        ],
        expected_completions=[
            'group-4',
        ],
        cli=self.cli,
    )


if __name__ == '__main__':
  test_case.main()
