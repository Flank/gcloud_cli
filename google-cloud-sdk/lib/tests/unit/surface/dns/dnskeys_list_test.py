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
#
"""Tests that exercise the 'gcloud dns dnskeys list' command."""

from tests.lib import test_case
from tests.lib.surface.dns import base


class DnskeysListBetaTest(base.DnsMockBetaTest):

  def testZeroKeysList(self):
    messages = self.messages_beta
    self.mocked_dns_client.dnsKeys.List.Expect(
        messages.DnsDnsKeysListRequest(project=self.Project(),
                                       maxResults=100,
                                       managedZone=u'my-zone'),
        messages.DnsKeysListResponse(dnsKeys=[]))
    self.Run('dns dnskeys list --zone my-zone')
    self.AssertErrContains('Listed 0 items.')

  def testMultipleKeysList(self):
    messages = self.messages_beta
    self.mocked_dns_client.dnsKeys.List.Expect(
        messages.DnsDnsKeysListRequest(project=self.Project(),
                                       maxResults=100,
                                       managedZone=u'my-zone'),
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
    self.Run('dns dnskeys list --zone my-zone')
    self.AssertOutputContains("""\
ID  KEY_TAG  TYPE          IS_ACTIVE  DESCRIPTION
1   1234     keySigning   True
5   567890   zoneSigning  True       My awesome ZSK!
""", normalize_space=True)


if __name__ == '__main__':
  test_case.main()
