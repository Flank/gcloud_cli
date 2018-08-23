# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Tests that exercise IAM-related `binauthz policy` commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.container.binauthz import base


class PolicyGetIamTest(base.BinauthzMockedBetaPolicyClientUnitTest):

  def SetUp(self):
    self.proj = self.Project()
    self.resource = 'projects/{}/policy'.format(self.proj)

  def testGet(self):
    self.client.projects_policy.GetIamPolicy.Expect(
        self.messages.
        BinaryauthorizationProjectsPolicyGetIamPolicyRequest(
            resource=self.resource),
        self.messages.IamPolicy(etag=b'foo'))

    self.RunBinauthz('policy get-iam-policy')
    self.AssertOutputContains('etag: Zm9v')  # "foo" in b64

  def testListCommandFilter(self):
    self.client.projects_policy.GetIamPolicy.Expect(
        self.messages.BinaryauthorizationProjectsPolicyGetIamPolicyRequest(
            resource=self.resource),
        self.messages.IamPolicy(etag=b'foo'))

    self.RunBinauthz(
        'policy get-iam-policy '
        '    --filter=etag:Zm9v'
        '    --format=table[no-heading](etag:sort=1)')
    self.AssertOutputEquals('Zm9v\n')


class PolicyModifyIamTest(sdk_test_base.WithTempCWD,
                          base.BinauthzMockedBetaPolicyClientUnitTest):

  def SetUp(self):
    self.proj = self.Project()
    self.resource = 'projects/{}/policy'.format(self.proj)

  def testSetBindings(self):
    policy = self.messages.IamPolicy(
        etag=b'foo',
        bindings=[
            self.messages.Binding(members=['people'], role='roles/owner')
        ])
    policy_filename = self.Touch(
        name='foo.json',
        directory=self.cwd_path,
        contents=textwrap.dedent("""
        {
          "etag": "Zm9v",
          "bindings": [ { "members": ["people"], "role": "roles/owner" } ]
        }
        """))

    self.client.projects_policy.SetIamPolicy.Expect(
        self.messages.BinaryauthorizationProjectsPolicySetIamPolicyRequest(
            resource=self.resource,
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=policy)),
        response=policy)

    self.RunBinauthz('policy set-iam-policy {}'.format(policy_filename))
    self.AssertOutputContains(textwrap.dedent("""
        bindings:
        - members:
          - people
          role: roles/owner
        etag: Zm9v
    """).lstrip())
    self.AssertErrContains('Updated IAM policy for policy [{}].'.format(
        self.proj))

  def testAddBinding(self):
    self.client.projects_policy.GetIamPolicy.Expect(
        self.messages.
        BinaryauthorizationProjectsPolicyGetIamPolicyRequest(
            resource=self.resource),
        self.messages.IamPolicy(etag=b'foo'))

    policy = self.messages.IamPolicy(
        etag=b'foo',
        bindings=[
            self.messages.Binding(members=['people'], role='roles/owner')
        ])
    self.client.projects_policy.SetIamPolicy.Expect(
        self.messages.BinaryauthorizationProjectsPolicySetIamPolicyRequest(
            resource=self.resource,
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=policy)),
        response=policy)

    self.RunBinauthz(
        'policy add-iam-policy-binding '
        '    --member people'
        '    --role roles/owner')
    self.AssertOutputContains(textwrap.dedent("""
        bindings:
        - members:
          - people
          role: roles/owner
        etag: Zm9v
    """).lstrip())

  def testRemoveBinding(self):
    policy_before = self.messages.IamPolicy(
        etag=b'foo',
        bindings=[
            self.messages.Binding(members=['people'], role='roles/owner')
        ])
    policy_after = self.messages.IamPolicy(etag=b'foo', bindings=[])

    self.client.projects_policy.GetIamPolicy.Expect(
        self.messages.BinaryauthorizationProjectsPolicyGetIamPolicyRequest(
            resource=self.resource),
        response=policy_before)

    self.client.projects_policy.SetIamPolicy.Expect(
        self.messages.BinaryauthorizationProjectsPolicySetIamPolicyRequest(
            resource=self.resource,
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=policy_after)),
        response=policy_after)

    self.RunBinauthz(
        'policy remove-iam-policy-binding '
        '    --member people'
        '    --role roles/owner')
    self.AssertOutputContains('etag: Zm9v')


if __name__ == '__main__':
  test_case.main()
