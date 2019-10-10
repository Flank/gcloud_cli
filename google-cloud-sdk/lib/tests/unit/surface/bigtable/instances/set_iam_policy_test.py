# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Tests for bigtable instances set-iam-policy command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import re

from apitools.base.py import encoding
from googlecloudsdk.api_lib.bigtable import util
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import exceptions
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib.surface.bigtable import base


# TODO(b/117336602) Stop using parameterized for track parameterization.
@parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                          calliope_base.ReleaseTrack.BETA,
                          calliope_base.ReleaseTrack.GA)
class SetIamPolicyTest(base.BigtableV2TestBase,
                       sdk_test_base.WithOutputCapture):

  def SetUp(self):
    self.policy = self.msgs.Policy(
        bindings=[
            self.msgs.Binding(
                role='roles/bigtable.admin', members=['domain:foo.com']),
            self.msgs.Binding(
                role='roles/bigtable.viewer', members=['user:admin@foo.com'])
        ],
        etag='someUniqueEtag'.encode(),
        version=1)
    self.instance_ref = util.GetInstanceRef('my-instance')
    json = encoding.MessageToJson(self.policy)
    self.temp_file = self.Touch(self.temp_path, contents=json)

  def testSetIamPolicy(self, track):
    self.track = track
    set_request = self.msgs.SetIamPolicyRequest(policy=self.policy)
    self.client.projects_instances.SetIamPolicy.Expect(
        request=self.msgs.BigtableadminProjectsInstancesSetIamPolicyRequest(
            resource=self.instance_ref.RelativeName(),
            setIamPolicyRequest=set_request),
        response=self.policy)
    set_policy_request = self.Run("""
        bigtable instances set-iam-policy my-instance {0}
        """.format(self.temp_file))
    self.assertEqual(set_policy_request, self.policy)
    self.AssertErrContains('Updated IAM policy for instance [my-instance].')

  def testBadJsonOrYamlSetIamPolicyProject(self, track):
    self.track = track
    temp_file = self.Touch(self.temp_path, 'bad', contents='bad')

    with self.AssertRaisesExceptionRegexp(
        exceptions.Error, 'not a properly formatted YAML or JSON policy file'):
      self.Run("""
          bigtable instances set-iam-policy my-instance {0}
          """.format(temp_file))

  def testBadJsonSetIamPolicyProject(self, track):
    self.track = track
    temp_file = os.path.join(self.temp_path, 'doesnotexist')

    with self.AssertRaisesExceptionRegexp(
        exceptions.Error, r'Failed to load YAML from \[{}\]'.format(
            re.escape(temp_file))):
      self.Run("""
          bigtable instances set-iam-policy my-instance {0}
          """.format(temp_file))
