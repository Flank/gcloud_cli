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
"""Tests for the public advertised prefixes describe subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute.public_prefixes import test_resources


class PublicAdvertisedPrefixesDescribeGaTest(test_base.BaseTest,
                                             test_case.WithOutputCapture):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi('alpha')

  def testSimpleCase(self):
    self.make_requests.side_effect = iter([
        [test_resources.PUBLIC_ADVERTISED_PREFIXES_ALPHA[0]],
    ])

    self.Run('compute public-advertised-prefixes describe my-pap1')

    self.CheckRequests([
        (self.compute.publicAdvertisedPrefixes, 'Get',
         self.messages.ComputePublicAdvertisedPrefixesGetRequest(
             publicAdvertisedPrefix='my-pap1', project='my-project'))
    ])
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            description: My PAP 1
            dnsVerificationIp: 1.2.3.4
            ipCidrRange: 1.2.3.0/24
            kind: compute#publicAdvertisedPrefix
            name: my-pap1
            selfLink: {uri}/projects/my-project/publicAdvertisedPrefixes/my-pap1
            sharedSecret: vader is luke's father
            status: VALIDATED
            """.format(uri=self.compute_uri)))


if __name__ == '__main__':
  test_case.main()
