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
"""Tests for the public advertised prefix create subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class PublicAdvertisedPrefixesCreateTest(test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi('alpha')

  def _ExpectCreate(self, public_advertised_prefix, project=None):
    request = self.messages.ComputePublicAdvertisedPrefixesInsertRequest(
        project=project or self.Project(),
        publicAdvertisedPrefix=public_advertised_prefix)
    self.make_requests.side_effect = [[public_advertised_prefix]]
    return request

  def testCreate_Default(self):
    public_advertised_prefix = self.messages.PublicAdvertisedPrefix(
        name='my-pap',
        ipCidrRange='1.2.3.0/24',
        dnsVerificationIp='1.2.3.4',
        description='example-pap')
    request = self._ExpectCreate(public_advertised_prefix)

    result = self.Run('compute public-advertised-prefixes create my-pap '
                      '--range 1.2.3.0/24 --dns-verification-ip 1.2.3.4 '
                      '--description example-pap')

    self.CheckRequests([(self.compute.publicAdvertisedPrefixes, 'Insert',
                         request)])
    self.assertEqual(result, public_advertised_prefix)
    self.AssertErrContains('Created public advertised prefix [my-pap]')


if __name__ == '__main__':
  test_case.main()
