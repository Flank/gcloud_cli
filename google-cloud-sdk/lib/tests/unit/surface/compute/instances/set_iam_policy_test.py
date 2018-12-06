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
"""Tests for the instances set-iam-policy subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from apitools.base.py import encoding

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import exceptions
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources


@parameterized.parameters(
    (calliope_base.ReleaseTrack.ALPHA, 'alpha'),
    (calliope_base.ReleaseTrack.BETA, 'beta'))
class SetIamPolicyTest(test_base.BaseTest,
                       test_case.WithOutputCapture,
                       parameterized.TestCase):

  def _SetUp(self, track, api_version):
    self.SelectApi(api_version)
    self.track = track
    json = encoding.MessageToJson(
        test_resources.IamPolicyWithOneBindingAndDifferentEtag(self.messages))
    self.temp_file = self.Touch(self.temp_path, 'good.json', contents=json)

  def testSetIamPolicy(self, track, api_version):
    self._SetUp(track, api_version)

    self.make_requests.side_effect = iter([
        iter([test_resources.IamPolicyWithOneBindingAndDifferentEtag(
            self.messages)]),
    ])

    self.Run("""
        compute instances set-iam-policy resource --zone zone-1 {0}
        """.format(self.temp_file))

    policy = test_resources.IamPolicyWithOneBindingAndDifferentEtag(
        self.messages)
    self.CheckRequests(
        [(self.compute.instances, 'SetIamPolicy',
          self.messages.ComputeInstancesSetIamPolicyRequest(
              resource='resource',
              project='my-project',
              zone='zone-1',
              zoneSetPolicyRequest=self.messages.ZoneSetPolicyRequest(
                  policy=policy)))],)
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            bindings:
            - members:
              - user:testuser@google.com
              role: owner
            etag: ZXRhZ1R3bw==
            """))
    self.AssertErrContains(
        'instance [projects/my-project/zones/zone-1/instances/resource]')

  def testBadJsonOrYamlSetIamPolicyProject(self, track, api_version):
    self._SetUp(track, api_version)
    temp_file = self.Touch(self.temp_path, 'bad', contents='bad')

    with self.assertRaises(exceptions.Error):
      self.Run("""
          compute instances set-iam-policy resource --zone zone-1 {0}
          """.format(temp_file))

  def testBadJsonSetIamPolicyProject(self, track, api_version):
    self._SetUp(track, api_version)
    temp_file = '/some/bad/path/doesnotexist'
    with self.assertRaises(exceptions.Error):
      self.Run("""
          compute instances set-iam-policy resource --zone zone-1 {0}
          """.format(temp_file))

  def testNotFound(self, track, api_version):
    self._SetUp(track, api_version)
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
          compute instances set-iam-policy my-resource {0} --zone zone-1
          """.format(self.temp_file))


if __name__ == '__main__':
  test_case.main()
