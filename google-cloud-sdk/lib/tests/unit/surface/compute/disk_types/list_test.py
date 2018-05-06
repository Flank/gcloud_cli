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
"""Tests for the disk-types list subcommand."""
import textwrap

from apitools.base.py.testing import mock as apitools_mock
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.compute import completers
from googlecloudsdk.core.resource import resource_projector
from tests.lib import cli_test_base
from tests.lib import completer_test_base
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources
import mock


class DiskTypesListTest(test_base.BaseTest, completer_test_base.CompleterBase):

  def SetUp(self):
    lister_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.lister.GetZonalResourcesDicts',
        autospec=True)
    self.addCleanup(lister_patcher.stop)
    self.mock_get_zonal_resources = lister_patcher.start()
    self.mock_get_zonal_resources.return_value = (
        resource_projector.MakeSerializable(
            test_resources.MakeDiskTypes(self.messages, self.track.prefix)))

  def testTabularOutput(self):
    get_zonal_resources = self.StartObjectPatch(
        lister,
        'GetZonalResourcesDicts',
        return_value=resource_projector.MakeSerializable(
            test_resources.MakeDiskTypes(self.messages, self.track.prefix)),)
    self.Run("""
        compute disk-types list
        """)
    get_zonal_resources.assert_called_once_with(
        service=self.compute.diskTypes,
        project='my-project',
        requested_zones=[],
        filter_expr=None,
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME        ZONE   VALID_DISK_SIZES
            pd-standard zone-1 10GB-10TB
            pd-ssd      zone-1 10GB-1TB
            """), normalize_space=True)


class AlphaBetaDiskTypesListTest(sdk_test_base.WithFakeAuth,
                                 cli_test_base.CliTestBase,
                                 completer_test_base.CompleterBase,
                                 parameterized.TestCase):

  def _SetUpForTrack(self, track):
    self.track = track
    self.mock_client = apitools_mock.Client(
        core_apis.GetClientClass('compute', self._ApiVersion()),
        real_client=core_apis.GetClientInstance(
            'compute', self._ApiVersion(), no_http=True))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)
    self.messages = core_apis.GetMessagesModule('compute', self._ApiVersion())

  def _ApiVersion(self):
    return self.track.prefix or 'v1'

  def _GetDiskTypeAggregatedListResponse(self, scoped_disk_types):
    additional_properties = []
    for scope, disk_types in scoped_disk_types:
      disk_types_scoped_list = self.messages.DiskTypesScopedList(
          diskTypes=disk_types
      )
      additional_property = (
          self.messages.DiskTypeAggregatedList.ItemsValue.AdditionalProperty)(
              key=scope,
              value=disk_types_scoped_list,
          )
      additional_properties.append(additional_property)
    return self.messages.DiskTypeAggregatedList(
        items=self.messages.DiskTypeAggregatedList.ItemsValue(
            additionalProperties=additional_properties,
        ),
    )

  @parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                            calliope_base.ReleaseTrack.BETA)
  def testAggregatedList(self, track):
    self._SetUpForTrack(track)
    expected_request = self.messages.ComputeDiskTypesAggregatedListRequest(
        filter=None,
        maxResults=500,
        project=self.Project(),
    )
    scoped_disk_types = [
        ('zones/arctic-north1-a',
         test_resources.MakeDiskTypes(
             self.messages, self.track.prefix, scope_name='arctic-north1-a')),
        ('regions/arctic-north1',
         test_resources.MakeDiskTypes(
             self.messages, self.track.prefix, scope_type='region',
             scope_name='arctic-north1')),
    ]
    response = self._GetDiskTypeAggregatedListResponse(scoped_disk_types)

    self.mock_client.diskTypes.AggregatedList.Expect(expected_request, response)
    self.Run('compute disk-types list')
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME        LOCATION        SCOPE VALID_DISK_SIZES
            pd-standard arctic-north1-a zone  10GB-10TB
            pd-ssd      arctic-north1-a zone  10GB-1TB
            pd-standard                       10GB-10TB
            pd-ssd                            10GB-1TB
            """), normalize_space=True)

  @parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                            calliope_base.ReleaseTrack.BETA)
  def testZonalList(self, track):
    self._SetUpForTrack(track)
    expected_request = self.messages.ComputeDiskTypesAggregatedListRequest(
        filter='(zone eq arctic-north1-a|antactic-south2-b)',
        maxResults=500,
        project=self.Project(),
    )
    scoped_disk_types = [
        ('zones/arctic-north1-a',
         test_resources.MakeDiskTypes(
             self.messages, self.track.prefix, scope_name='arctic-north1-a')),
        ('zones/antactic-south2-b',
         test_resources.MakeDiskTypes(
             self.messages, self.track.prefix, scope_name='antactic-south2-b')),
    ]
    response = self._GetDiskTypeAggregatedListResponse(scoped_disk_types)

    self.mock_client.diskTypes.AggregatedList.Expect(expected_request, response)
    self.Run("""compute disk-types list
                --zones arctic-north1-a,antactic-south2-b
             """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME        LOCATION          SCOPE VALID_DISK_SIZES
            pd-standard arctic-north1-a   zone  10GB-10TB
            pd-ssd      arctic-north1-a   zone  10GB-1TB
            pd-standard antactic-south2-b zone  10GB-10TB
            pd-ssd      antactic-south2-b zone  10GB-1TB
            """), normalize_space=True)

  @parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                            calliope_base.ReleaseTrack.BETA)
  def testRegionalList(self, track):
    self._SetUpForTrack(track)
    expected_request = self.messages.ComputeDiskTypesAggregatedListRequest(
        filter='(region eq arctic-north1|antactic-south2)',
        maxResults=500,
        project=self.Project(),
    )
    scoped_disk_types = [
        ('regions/arctic-north1',
         test_resources.MakeDiskTypes(
             self.messages, self.track.prefix, scope_type='region',
             scope_name='arctic-north1')),
        ('regions/antactic-south2',
         test_resources.MakeDiskTypes(
             self.messages, self.track.prefix, scope_type='region',
             scope_name='antactic-south2')),
    ]
    response = self._GetDiskTypeAggregatedListResponse(scoped_disk_types)

    self.mock_client.diskTypes.AggregatedList.Expect(expected_request, response)
    self.Run('compute disk-types list --regions arctic-north1,antactic-south2')
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME        LOCATION SCOPE VALID_DISK_SIZES
            pd-standard                10GB-10TB
            pd-ssd                     10GB-1TB
            pd-standard                10GB-10TB
            pd-ssd                     10GB-1TB
            """), normalize_space=True)

  @parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                            calliope_base.ReleaseTrack.BETA)
  def testNamesFilter(self, track):
    self._SetUpForTrack(track)
    expected_request = self.messages.ComputeDiskTypesAggregatedListRequest(
        filter='(name eq pd-standard|pd-ssd)',
        maxResults=500,
        project=self.Project(),
    )
    scoped_disk_types = [
        ('zones/arctic-north1',
         test_resources.MakeDiskTypes(
             self.messages, self.track.prefix, scope_type='region',
             scope_name='arctic-north1')),
        ('zones/antactic-south2',
         test_resources.MakeDiskTypes(
             self.messages, self.track.prefix, scope_type='region',
             scope_name='antactic-south2')),
    ]
    response = self._GetDiskTypeAggregatedListResponse(scoped_disk_types)

    self.mock_client.diskTypes.AggregatedList.Expect(expected_request, response)
    self.Run('compute disk-types list pd-standard pd-ssd')
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME        LOCATION SCOPE VALID_DISK_SIZES
            pd-standard                10GB-10TB
            pd-ssd                     10GB-1TB
            pd-standard                10GB-10TB
            pd-ssd                     10GB-1TB
            """), normalize_space=True)

  @parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                            calliope_base.ReleaseTrack.BETA)
  def testRegexFilter(self, track):
    self._SetUpForTrack(track)
    expected_request = self.messages.ComputeDiskTypesAggregatedListRequest(
        filter='(name eq pd-.*)',
        maxResults=500,
        project=self.Project(),
    )
    scoped_disk_types = [
        ('zones/arctic-north1',
         test_resources.MakeDiskTypes(
             self.messages, self.track.prefix, scope_type='region',
             scope_name='arctic-north1')),
        ('zones/antactic-south2',
         test_resources.MakeDiskTypes(
             self.messages, self.track.prefix, scope_type='region',
             scope_name='antactic-south2')),
    ]
    response = self._GetDiskTypeAggregatedListResponse(scoped_disk_types)

    self.mock_client.diskTypes.AggregatedList.Expect(expected_request, response)
    self.Run('compute disk-types list --regexp pd-.*')
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME        LOCATION SCOPE VALID_DISK_SIZES
            pd-standard                10GB-10TB
            pd-ssd                     10GB-1TB
            pd-standard                10GB-10TB
            pd-ssd                     10GB-1TB
            """), normalize_space=True)

  @parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                            calliope_base.ReleaseTrack.BETA)
  def testMultiFilter(self, track):
    self._SetUpForTrack(track)
    expected_request = self.messages.ComputeDiskTypesAggregatedListRequest(
        filter='(name eq pd-.*)(zone eq oceanina-central3-d)',
        maxResults=500,
        project=self.Project(),
    )
    scoped_disk_types = {}
    response = self._GetDiskTypeAggregatedListResponse(scoped_disk_types)

    self.mock_client.diskTypes.AggregatedList.Expect(expected_request, response)
    self.Run(
        'compute disk-types list --regexp pd-.* --zones oceanina-central3-d')
    self.AssertOutputEquals('')

  def testDiskTypesCompleter(self):
    self._SetUpForTrack(calliope_base.ReleaseTrack.ALPHA)
    expected_request = self.messages.ComputeDiskTypesAggregatedListRequest(
        filter=None,
        maxResults=500,
        project=self.Project(),
    )
    scoped_disk_types = [
        ('zones/arctic-north1-a',
         test_resources.MakeDiskTypes(
             self.messages, self.track.prefix, scope_name='arctic-north1-a')),
        ('regions/arctic-north1',
         test_resources.MakeDiskTypes(
             self.messages, self.track.prefix, scope_type='region',
             scope_name='arctic-north1')),
    ]
    response = self._GetDiskTypeAggregatedListResponse(scoped_disk_types)

    self.mock_client.diskTypes.AggregatedList.Expect(expected_request, response)
    self.mock_client.diskTypes.AggregatedList.Expect(expected_request, response)

    self.RunCompleter(
        completers.DiskTypesCompleter,
        expected_command=[
            [
                'alpha',
                'compute',
                'disk-types',
                'list',
                '--uri',
                '--filter=-zone:*',
                '--quiet',
                '--format=disable',
            ],
            [
                'alpha',
                'compute',
                'disk-types',
                'list',
                '--uri',
                '--filter=zone:*',
                '--quiet',
                '--format=disable',
            ],
        ],
        expected_completions=['pd-ssd', 'pd-standard'],
        args={'project': 'my-project'},
        cli=self.cli,
    )
    self.AssertOutputEquals('')


if __name__ == '__main__':
  test_case.main()
