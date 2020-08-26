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
"""Tests for the public delegated prefixes describe subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute.public_prefixes import test_resources


class PublicDelegatedPrefixesDescribeTest(test_base.BaseTest,
                                          test_case.WithOutputCapture):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi('alpha')
    self.region = 'us-central1'

  def testDescribe_global(self):
    self.make_requests.side_effect = iter([
        [test_resources.PUBLIC_DELEGATED_PREFIXES_ALPHA[0]],
    ])

    self.Run('compute public-delegated-prefixes describe my-pdp1 --global')

    self.CheckRequests([
        (self.compute.globalPublicDelegatedPrefixes, 'Get',
         self.messages.ComputeGlobalPublicDelegatedPrefixesGetRequest(
             publicDelegatedPrefix='my-pdp1', project='my-project'))
    ])
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            description: My global PDP 1
            fingerprint: MTIzNA==
            ipCidrRange: 1.2.3.128/25
            kind: compute#globalPublicDelegatedPrefix
            name: my-pdp1
            parentPrefix: {uri}/projects/my-project/global/publicAdvertisedPrefixes/my-pap1
            selfLink: {uri}/projects/my-project/global/publicDelegatedPrefixes/my-pdp1
            """.format(uri=self.compute_uri)))

  def testDescribe_regional(self):
    self.make_requests.side_effect = iter([
        [test_resources.PUBLIC_DELEGATED_PREFIXES_ALPHA[1]],
    ])

    self.Run(
        'compute public-delegated-prefixes describe my-pdp1 --region {}'.format(
            self.region))

    self.CheckRequests([(self.compute.publicDelegatedPrefixes, 'Get',
                         self.messages.ComputePublicDelegatedPrefixesGetRequest(
                             publicDelegatedPrefix='my-pdp1',
                             project='my-project',
                             region=self.region))])
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            description: My PDP 2
            fingerprint: MTIzNDU=
            ipCidrRange: 1.2.3.12/30
            kind: compute#publicDelegatedPrefix
            name: my-pdp2
            parentPrefix: {uri}/projects/my-project/global/publicAdvertisedPrefixes/my-pap1
            selfLink: {uri}/projects/my-project/regions/{region}/publicDelegatedPrefixes/my-pdp2
            """.format(uri=self.compute_uri, region=self.region)))


if __name__ == '__main__':
  test_case.main()
