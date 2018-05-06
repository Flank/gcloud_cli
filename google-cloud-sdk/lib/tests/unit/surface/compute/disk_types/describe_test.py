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
"""Tests for the disk-types describe subcommand."""
import textwrap

from googlecloudsdk.calliope import base
from tests.lib import completer_test_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources


class DiskTypesDescribeTest(test_base.BaseTest,
                            completer_test_base.CompleterBase,
                            test_case.WithOutputCapture,
                            parameterized.TestCase):

  def testSimpleCase(self):
    self.make_requests.side_effect = iter([
        [test_resources.DISK_TYPES[0]],
    ])

    self.Run("""
        compute disk-types describe pd-standard --zone zone-1
        """)

    self.CheckRequests(
        [(self.compute.diskTypes,
          'Get',
          self.messages.ComputeDiskTypesGetRequest(
              diskType='pd-standard',
              project='my-project',
              zone='zone-1'))],
    )
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            name: pd-standard
            selfLink: https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1/diskTypes/pd-standard
            validDiskSize: 10GB-10TB
            zone: https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1
            """))

  @parameterized.parameters((base.ReleaseTrack.ALPHA, 'alpha'),
                            (base.ReleaseTrack.BETA, 'beta'))
  def testSimpleRegionalCase(self, track, api_version):
    self.track = track
    self.SelectApi(api_version)
    mock = object()
    self.make_requests.side_effect = [
        [mock],
    ]

    result = self.Run("""
        compute disk-types describe pd-standard
        --region region-1
        --format=disable
        """)

    self.CheckRequests(
        [(self.compute.regionDiskTypes,
          'Get',
          self.messages.ComputeRegionDiskTypesGetRequest(
              diskType='pd-standard',
              project='my-project',
              region='region-1'))],
    )
    self.assertIs(result, mock)

  def testUriRegionalCase(self):
    self.track = base.ReleaseTrack.ALPHA
    self.SelectApi('alpha')
    mock = object()
    self.make_requests.side_effect = [
        [mock],
    ]

    result = self.Run("""
        compute disk-types describe {}/projects/my-project/regions/region-1/diskTypes/pd-standard
        --format=disable
        """.format(self.compute_uri))

    self.CheckRequests(
        [(self.compute.regionDiskTypes,
          'Get',
          self.messages.ComputeRegionDiskTypesGetRequest(
              diskType='pd-standard',
              project='my-project',
              region='region-1'))],
    )
    self.assertIs(result, mock)

  @parameterized.parameters((base.ReleaseTrack.ALPHA, 'alpha'),
                            (base.ReleaseTrack.BETA, 'beta'))
  def testPromptRegionalCase(self, track, api_version):
    self.track = track
    self.SelectApi(api_version)
    mock = object()
    self.make_requests.side_effect = [
        [mock],
    ]

    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)

    self.StartPatch(
        'googlecloudsdk.api_lib.compute.zones.service.List',
        return_value=[])
    self.StartPatch(
        'googlecloudsdk.api_lib.compute.regions.service.List',
        return_value=[self.messages.Region(name='region-1')])

    result = self.Run("""
        compute disk-types describe pd-standard
        --format=disable
        """)

    self.CheckRequests(
        [(self.compute.regionDiskTypes,
          'Get',
          self.messages.ComputeRegionDiskTypesGetRequest(
              diskType='pd-standard',
              project='my-project',
              region='region-1'))],
    )
    self.assertIs(result, mock)

  def testDescribeCompleter(self):
    self.AssertCommandArgCompleter(
        command='compute disk-types describe',
        arg='DISK_TYPE',
        module_path='command_lib.compute.completers.DiskTypesCompleter')


if __name__ == '__main__':
  test_case.main()
