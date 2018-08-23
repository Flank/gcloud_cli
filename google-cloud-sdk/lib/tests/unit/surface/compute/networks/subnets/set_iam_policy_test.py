# -*- coding: utf-8 -*- #
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
"""Tests for the networks subnets set-iam-policy subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from apitools.base.py import encoding

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import exceptions
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources

messages = core_apis.GetMessagesModule('compute', 'beta')


class SetIamPolicyTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('beta')
    self.track = calliope_base.ReleaseTrack.BETA
    json = encoding.MessageToJson(
        test_resources.IamPolicyWithOneBindingAndDifferentEtag(self.messages))
    self.temp_file = self.Touch(self.temp_path, 'good.json', contents=json)

  def testSetIamPolicy(self):

    policy = test_resources.IamPolicyWithOneBindingAndDifferentEtag(
        self.messages)

    self.make_requests.side_effect = iter([
        iter([policy]),
    ])

    self.Run("""
        compute networks subnets set-iam-policy resource --region region-1 {0}
        """.format(self.temp_file))

    self.CheckRequests(
        [(self.compute.subnetworks,
          'SetIamPolicy',
          messages.ComputeSubnetworksSetIamPolicyRequest(
              resource='resource',
              project='my-project',
              region='region-1',
              regionSetPolicyRequest=messages.RegionSetPolicyRequest(
                  bindings=policy.bindings,
                  etag=policy.etag)))],
    )
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            bindings:
            - members:
              - user:testuser@google.com
              role: owner
            etag: ZXRhZ1R3bw==
            """))

  def testBadJsonOrYamlSetIamPolicyProject(self):
    temp_file = self.Touch(self.temp_path, 'bad', contents='bad')

    with self.assertRaises(exceptions.Error):
      self.Run("""
          compute networks subnets set-iam-policy resource --region region-1 {0}
          """.format(temp_file))

  def testBadJsonSetIamPolicyProject(self):
    temp_file = '/some/bad/path/doesnotexist'
    with self.assertRaises(exceptions.Error):
      self.Run("""
          compute networks subnets set-iam-policy resource --region region-1 {0}
          """.format(temp_file))

  def testNotFound(self):
    def MakeRequests(*_, **kwargs):
      if False:  # pylint: disable=using-constant-test
        yield
      kwargs['errors'].append((404, 'Not Found'))
    self.make_requests.side_effect = MakeRequests

    with self.AssertRaisesToolExceptionRegexp(textwrap.dedent("""\
        Could not fetch resource:
         - Not Found
        """)):
      self.Run("""
          compute networks subnets set-iam-policy my-resource {0}
          --region region-1
          """.format(self.temp_file))


class SetIamPolicyGaTest(test_base.BaseTest):

  def testNotInGA(self):
    with self.AssertRaisesArgumentErrorRegexp(
        'Invalid choice:'):
      self.Run("""
          compute networks subnets set-iam-policy my-resource
          --region region-1
          """)


if __name__ == '__main__':
  test_case.main()
