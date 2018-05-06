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
"""Tests that exercise the 'gcloud dns dns-keys describe' command."""

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.dns import base


@parameterized.named_parameters(
    ('Beta', calliope_base.ReleaseTrack.BETA, 'v1beta2'),
    ('GA', calliope_base.ReleaseTrack.GA, 'v1'),
)
class DnskeysDescribeTest(base.DnsMockMultiTrackTest):

  def _GetZsk(self):
    m = self.messages
    return m.DnsKey(
        algorithm=m.DnsKey.AlgorithmValueValuesEnum('rsasha256'),
        creationTime='2015-10-22T18:46:48.654Z',
        id='3',
        isActive=True,
        keyLength=2048,
        keyTag=18898,
        publicKey=(
            'AwEAAbj4dDv7tNbTV4P5cvAaqZxlozE5Khdae33SkrBlh+G+LmDDffi+Kv'
            '9lSlj0qsK9Gh6kZsI6GIl4UgSw5Pcz5lo4WXnlfOExkGKxoxDMpGS5vOh36NqcqnIf'
            'oyJ5xo7J5KfNK+Z5tyDXAfkPRt7gH5+MnltQ0B6GvijIXzOCo9j8mpFPXGduz3Pi7f'
            'DjsEubBsgWPcDxOQqjY1RRJHDGje6T4QhN/czWbN7usnwINtDdejVUn0NVDyrSqJGk'
            'hyAH/cOWE7//CmvhU7OHmKDJA407iIo4w7LljlU38wVcjf7RB5YhJw8znktCdv0Nze'
            'P9EN1Zbx0xlzUIRP5eIE/Ce6U='),
        type=m.DnsKey.TypeValueValuesEnum('zoneSigning'),
    )

  def _GetKsk(self):
    m = self.messages
    return m.DnsKey(
        algorithm=m.DnsKey.AlgorithmValueValuesEnum('rsasha256'),
        creationTime='2015-10-22T18:46:48.654Z',
        digests=[m.DnsKeyDigest(
            digest=(
                '13E4DFF745E9FAE91B5448CC9C83C7296F9FB68276D04526B4551268271'
                'DCDC5'),
            type=m.DnsKeyDigest.TypeValueValuesEnum('sha256'),
        )],
        id='3',
        isActive=True,
        keyLength=2048,
        keyTag=18898,
        publicKey=(
            'AwEAAbj4dDv7tNbTV4P5cvAaqZxlozE5Khdae33SkrBlh+G+LmDDffi+Kv'
            '9lSlj0qsK9Gh6kZsI6GIl4UgSw5Pcz5lo4WXnlfOExkGKxoxDMpGS5vOh36NqcqnIf'
            'oyJ5xo7J5KfNK+Z5tyDXAfkPRt7gH5+MnltQ0B6GvijIXzOCo9j8mpFPXGduz3Pi7f'
            'DjsEubBsgWPcDxOQqjY1RRJHDGje6T4QhN/czWbN7usnwINtDdejVUn0NVDyrSqJGk'
            'hyAH/cOWE7//CmvhU7OHmKDJA407iIo4w7LljlU38wVcjf7RB5YhJw8znktCdv0Nze'
            'P9EN1Zbx0xlzUIRP5eIE/Ce6U='),
        type=m.DnsKey.TypeValueValuesEnum('keySigning'),
    )

  def testDescribeZSK(self, track, api_version):
    self.SetUpForTrack(track, api_version)
    m = self.messages
    expected_key = self._GetZsk()

    self.client.dnsKeys.Get.Expect(
        m.DnsDnsKeysGetRequest(
            managedZone='my-zone',
            project=self.Project(),
            dnsKeyId=expected_key.id),
        expected_key)

    self.Run('dns dns-keys describe --zone my-zone {0}'.format(expected_key.id))

    # pylint: disable=line-too-long
    expected_output = """\
algorithm: rsasha256
creationTime: '2015-10-22T18:46:48.654Z'
id: '3'
isActive: true
keyLength: 2048
keyTag: 18898
publicKey: AwEAAbj4dDv7tNbTV4P5cvAaqZxlozE5Khdae33SkrBlh+G+LmDDffi+Kv9lSlj0qsK9Gh6kZsI6GIl4UgSw5Pcz5lo4WXnlfOExkGKxoxDMpGS5vOh36NqcqnIfoyJ5xo7J5KfNK+Z5tyDXAfkPRt7gH5+MnltQ0B6GvijIXzOCo9j8mpFPXGduz3Pi7fDjsEubBsgWPcDxOQqjY1RRJHDGje6T4QhN/czWbN7usnwINtDdejVUn0NVDyrSqJGkhyAH/cOWE7//CmvhU7OHmKDJA407iIo4w7LljlU38wVcjf7RB5YhJw8znktCdv0NzeP9EN1Zbx0xlzUIRP5eIE/Ce6U=
type: zoneSigning
"""
    # pylint: enable=line-too-long

    self.AssertOutputContains(expected_output, normalize_space=True)

  def testDescribeKSK(self, track, api_version):
    self.SetUpForTrack(track, api_version)
    m = self.messages
    expected_key = self._GetKsk()

    self.client.dnsKeys.Get.Expect(
        m.DnsDnsKeysGetRequest(
            managedZone='my-zone',
            project=self.Project(),
            dnsKeyId=expected_key.id),
        expected_key)

    self.Run('dns dns-keys describe --zone my-zone {0}'.format(expected_key.id))

    # pylint: disable=line-too-long
    expected_output = """\
algorithm: rsasha256
creationTime: '2015-10-22T18:46:48.654Z'
digests:
- digest: 13E4DFF745E9FAE91B5448CC9C83C7296F9FB68276D04526B4551268271DCDC5
  type: sha256
id: '3'
isActive: true
keyLength: 2048
keyTag: 18898
publicKey: AwEAAbj4dDv7tNbTV4P5cvAaqZxlozE5Khdae33SkrBlh+G+LmDDffi+Kv9lSlj0qsK9Gh6kZsI6GIl4UgSw5Pcz5lo4WXnlfOExkGKxoxDMpGS5vOh36NqcqnIfoyJ5xo7J5KfNK+Z5tyDXAfkPRt7gH5+MnltQ0B6GvijIXzOCo9j8mpFPXGduz3Pi7fDjsEubBsgWPcDxOQqjY1RRJHDGje6T4QhN/czWbN7usnwINtDdejVUn0NVDyrSqJGkhyAH/cOWE7//CmvhU7OHmKDJA407iIo4w7LljlU38wVcjf7RB5YhJw8znktCdv0NzeP9EN1Zbx0xlzUIRP5eIE/Ce6U=
type: keySigning
"""
    # pylint: enable=line-too-long

    self.AssertOutputContains(expected_output, normalize_space=True)

  def testDescribeKSK_DSRecord(self, track, api_version):
    self.SetUpForTrack(track, api_version)
    m = self.messages
    expected_key = self._GetKsk()

    self.client.dnsKeys.Get.Expect(
        m.DnsDnsKeysGetRequest(
            managedZone='my-zone',
            project=self.Project(),
            dnsKeyId=expected_key.id),
        expected_key)

    self.Run(
        'dns dns-keys describe --zone my-zone --format "value(ds_record())" 3')

    expected_output = (
        '18898 8 2 '
        '13E4DFF745E9FAE91B5448CC9C83C7296F9FB68276D04526B4551268271DCDC5')
    self.AssertOutputContains(expected_output, normalize_space=True)


if __name__ == '__main__':
  test_case.main()
