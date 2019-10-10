# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
#
"""Tests that exercise the 'gcloud dns dns-keys list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.dns import base


@parameterized.named_parameters(
    ('Beta', calliope_base.ReleaseTrack.BETA, 'v1beta2'),
    ('GA', calliope_base.ReleaseTrack.GA, 'v1'),
)
class DnskeysListTest(base.DnsMockMultiTrackTest):

  def testZeroKeysList(self, track, api_version):
    self.SetUpForTrack(track, api_version)
    messages = self.messages
    self.client.dnsKeys.List.Expect(
        messages.DnsDnsKeysListRequest(project=self.Project(),
                                       maxResults=100,
                                       managedZone='my-zone'),
        messages.DnsKeysListResponse(dnsKeys=[]))
    self.Run('dns dns-keys list --zone my-zone')
    self.AssertErrContains('Listed 0 items.')

  def testMultipleKeysList(self, track, api_version):
    self.SetUpForTrack(track, api_version)
    messages = self.messages
    self.client.dnsKeys.List.Expect(
        messages.DnsDnsKeysListRequest(project=self.Project(),
                                       maxResults=100,
                                       managedZone='my-zone'),
        messages.DnsKeysListResponse(dnsKeys=[
            messages.DnsKey(id='1',
                            keyTag=1234,
                            isActive=True,
                            type=messages.DnsKey.TypeValueValuesEnum(
                                'keySigning'),),
            messages.DnsKey(id='5',
                            keyTag=567890,
                            isActive=True,
                            type=messages.DnsKey.TypeValueValuesEnum(
                                'zoneSigning'),
                            description='My awesome ZSK!',),
        ]))
    self.Run('dns dns-keys list --zone my-zone')
    self.AssertOutputContains("""\
ID  KEY_TAG  TYPE          IS_ACTIVE  DESCRIPTION
1   1234     keySigning   True
5   567890   zoneSigning  True       My awesome ZSK!
""", normalize_space=True)

  def testMultipleKeysList_DsRecord(self, track, api_version):
    self.SetUpForTrack(track, api_version)
    messages = self.messages
    self.client.dnsKeys.List.Expect(
        messages.DnsDnsKeysListRequest(project=self.Project(),
                                       maxResults=100,
                                       managedZone='my-zone'),
        messages.DnsKeysListResponse(dnsKeys=[
            messages.DnsKey(
                id='1',
                keyTag=1234,
                isActive=True,
                algorithm=messages.DnsKey.AlgorithmValueValuesEnum('rsasha256'),
                digests=[messages.DnsKeyDigest(
                    digest=('13E4DFF745E9FAE91B5448CC9C83C729'
                            '6F9FB68276D04526B4551268271DCDC5'),
                    type=messages.DnsKeyDigest.TypeValueValuesEnum('sha256')
                )],
                type=messages.DnsKey.TypeValueValuesEnum('keySigning')),
            messages.DnsKey(id='5',
                            keyTag=567890,
                            isActive=True,
                            type=messages.DnsKey.TypeValueValuesEnum(
                                'zoneSigning'),
                            description='My awesome ZSK!',),
        ]))
    self.Run('dns dns-keys list '
             '    --zone my-zone '
             '    --format "table(id, ds_record())" '
             '    --filter "type=keySigning"')
    self.AssertOutputEquals("""\
ID  DS_RECORD
1   1234 8 2 13E4DFF745E9FAE91B5448CC9C83C7296F9FB68276D04526B4551268271DCDC5
""", normalize_space=True)

if __name__ == '__main__':
  test_case.main()
