# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Tests for Spanner instances set-iam-policy command."""

import os
import re

from apitools.base.py import encoding
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import resources
from tests.lib import parameterized
from tests.lib.surface.spanner import base


@parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                          calliope_base.ReleaseTrack.BETA,
                          calliope_base.ReleaseTrack.GA)
class SetIamPolicyTest(base.SpannerTestBase):

  def SetUp(self):
    self.instance_ref = resources.REGISTRY.Parse(
        'insId',
        params={'projectsId': self.Project()},
        collection='spanner.projects.instances')
    self.policy = self.msgs.Policy(
        bindings=[
            self.msgs.Binding(
                role=u'roles/spanner.databaseAdmin',
                members=[u'domain:foo.com']), self.msgs.Binding(
                    role=u'roles/spanner.viewer',
                    members=[u'user:admin@foo.com'])
        ],
        etag='someUniqueEtag',
        version=1)
    json = encoding.MessageToJson(self.policy)
    self.temp_file = self.Touch(self.temp_path, contents=json)

  def testSetIamPolicy(self, track):
    self.track = track
    set_request = self.msgs.SetIamPolicyRequest(
        policy=self.policy, updateMask='bindings,etag,version')
    self.client.projects_instances.SetIamPolicy.Expect(
        request=self.msgs.SpannerProjectsInstancesSetIamPolicyRequest(
            resource=self.instance_ref.RelativeName(),
            setIamPolicyRequest=set_request),
        response=self.policy)
    set_policy_request = self.Run("""
        spanner instances set-iam-policy insId {0}
        """.format(self.temp_file))
    self.assertEqual(set_policy_request, self.policy)
    self.AssertErrContains('Updated IAM policy for instance [insId].')

  def testBadJsonOrYamlSetIamPolicyProject(self, track):
    self.track = track
    temp_file = self.Touch(self.temp_path, 'bad', contents='bad')

    with self.AssertRaisesExceptionRegexp(
        exceptions.Error, 'not a properly formatted YAML or JSON policy file'):
      self.Run("""
          spanner instances set-iam-policy insId {0}
          """.format(temp_file))

  def testBadJsonSetIamPolicyProject(self, track):
    self.track = track
    temp_file = os.path.join(self.temp_path, 'doesnotexist')

    with self.AssertRaisesExceptionRegexp(
        exceptions.Error,
        r'Failed to load YAML from \[{}\]'.format(re.escape(temp_file))):
      self.Run("""
          spanner instances set-iam-policy insId {0}
          """.format(temp_file))
