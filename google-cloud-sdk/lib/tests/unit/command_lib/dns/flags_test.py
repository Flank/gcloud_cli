# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""Unit tests for cpanner flags module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.dns import flags
from tests.lib import completer_test_base
from tests.lib.surface.dns import base


class CompletionTest(base.DnsMockTest, completer_test_base.CompleterBase):

  def testKeyCompleter(self):
    messages = self.messages
    self.mocked_dns_v1.dnsKeys.List.Expect(
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

    self.RunCompleter(
        flags.KeyCompleter,
        expected_command=[
            'dns',
            'dns-keys',
            'list',
            '--format=value(keyTag)',
            '--quiet',
            '--zone=my-zone',
        ],
        expected_completions=['1234', '567890'],
        args={'--zone': 'my-zone'},
        cli=self.cli,
    )


class BetaCompletionTest(base.DnsMockBetaTest,
                         completer_test_base.CompleterBase):

  def testKeyCompleter(self):
    messages = self.messages_beta
    self.mocked_dns_client.dnsKeys.List.Expect(
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

    self.RunCompleter(
        flags.BetaKeyCompleter,
        expected_command=[
            'beta',
            'dns',
            'dns-keys',
            'list',
            '--format=value(keyTag)',
            '--quiet',
            '--zone=my-zone',
        ],
        expected_completions=['1234', '567890'],
        args={'--zone': 'my-zone'},
        cli=self.cli,
    )


if __name__ == '__main__':
  completer_test_base.main()

