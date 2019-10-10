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

"""Unit tests for api_lib.compute.images.policy module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.resource_manager import org_policies
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.compute.images import policy
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.apitools import http_error


def _BuildSampleImages(resource_registry):
  return [
      {
          'selfLink':
              resource_registry.Parse(
                  None,
                  params={'project': 'project-1',
                          'image': 'image-1'},
                  collection='compute.images').SelfLink(),
          'status':
              'READY'
      },
      {
          'selfLink':
              resource_registry.Parse(
                  None,
                  params={'project': 'project-2',
                          'image': 'image-1'},
                  collection='compute.images').SelfLink(),
          'status':
              'READY'
      },
      {
          'selfLink':
              resource_registry.Parse(
                  None,
                  params={'project': 'project-3',
                          'image': 'image-1'},
                  collection='compute.images').SelfLink(),
          'status':
              'NOT READY'
      },
  ]


class AugmentImagesStatusTests(test_case.WithOutputCapture):

  def SetUp(self):
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'v1')
    self.images = _BuildSampleImages(self.resources)
    self.messages = org_policies.OrgPoliciesMessages()

  def testAllowAll(self):
    org_policy = self.messages.ListPolicy()
    org_policy.allValues = (
        self.messages.ListPolicy.AllValuesValueValuesEnum.ALLOW)
    self.StartPatch(
        'googlecloudsdk.command_lib.compute.images.policy._GetPolicyNoThrow',
        return_value=org_policy)

    images = list(
        policy.AugmentImagesStatus(self.resources, 'project-x', self.images))
    self.assertListEqual(self.images, images)

  def testDenyAll(self):
    org_policy = self.messages.ListPolicy()
    org_policy.allValues = (
        self.messages.ListPolicy.AllValuesValueValuesEnum.DENY)
    self.StartPatch(
        'googlecloudsdk.command_lib.compute.images.policy._GetPolicyNoThrow',
        return_value=org_policy)

    images = policy.AugmentImagesStatus(self.resources, 'project-x',
                                        self.images)
    self.assertListEqual([image['status'] for image in images], [
        'BLOCKED_BY_POLICY',
        'BLOCKED_BY_POLICY',
        'NOT READY',
    ])

  def testError(self):

    def GetPolicyWrapped(project_id, errors_to_propagate):
      del project_id
      errors_to_propagate.append(Exception('Some error'))

      org_policy = self.messages.ListPolicy()
      org_policy.allValues = (
          self.messages.ListPolicy.AllValuesValueValuesEnum.ALLOW)
      return org_policy

    self.StartPatch(
        'googlecloudsdk.command_lib.compute.images.policy._GetPolicyNoThrow',
        side_effect=GetPolicyWrapped)

    images = []
    for image in policy.AugmentImagesStatus(self.resources, 'project-x',
                                            self.images):
      images.append(image)

    self.assertListEqual(self.images, images)


class GetPolicyTests(cli_test_base.CliTestBase, sdk_test_base.WithFakeAuth):

  def SetUp(self):
    self.mocked_client = mock.Client(
        apis.GetClientClass('cloudresourcemanager',
                            org_policies.ORG_POLICIES_API_VERSION))
    self.mocked_client.Mock()
    self.addCleanup(self.mocked_client.Unmock)

    self.messages = org_policies.OrgPoliciesMessages()

  def testSimple(self):
    list_policy = self.messages.ListPolicy()
    self.mocked_client.projects.GetEffectiveOrgPolicy.Expect(
        request=self.messages.
        CloudresourcemanagerProjectsGetEffectiveOrgPolicyRequest(
            projectsId='project-x',
            getEffectiveOrgPolicyRequest=self.messages.
            GetEffectiveOrgPolicyRequest(
                constraint=org_policies.FormatConstraint(
                    'compute.trustedImageProjects'))),
        response=self.messages.OrgPolicy(listPolicy=list_policy))

    self.assertIs(list_policy, policy._GetPolicy('project-x'))


class GetPolicyWrappedTests(test_case.TestCase):

  def testSuccess(self):
    org_policy = object()

    patch = self.StartPatch(
        'googlecloudsdk.command_lib.compute.images.policy._GetPolicy',
        return_value=org_policy)

    errors = []
    self.assertIs(org_policy,
                  policy._GetPolicyNoThrow('project-x', errors))
    self.assertListEqual(errors, [])
    patch.assert_called_once_with('project-x')

  def testError(self):
    exception = http_error.MakeHttpError()

    patch = self.StartPatch(
        'googlecloudsdk.command_lib.compute.images.policy._GetPolicy',
        side_effect=exception)

    errors = []
    org_policy = policy._GetPolicyNoThrow('project-x', errors)

    self.assertIsNone(org_policy)
    self.assertListEqual(errors, [exception])
    patch.assert_called_once_with('project-x')


class IsAllowedTests(test_case.TestCase):

  def SetUp(self):
    self.messages = org_policies.OrgPoliciesMessages()
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'v1')

  def MakePolicy(self, allowed_values, denied_values):
    org_policy = self.messages.ListPolicy()
    org_policy.allValues = (
        self.messages.ListPolicy.AllValuesValueValuesEnum.ALL_VALUES_UNSPECIFIED
    )
    org_policy.allowedValues = allowed_values
    org_policy.deniedValues = denied_values
    return org_policy

  def testAllowAll(self):
    org_policy = self.messages.ListPolicy()
    org_policy.allValues = (
        self.messages.ListPolicy.AllValuesValueValuesEnum.ALLOW)

    errors = []
    self.assertTrue(
        policy._IsAllowed(self.resources, 'project-1', org_policy, errors))
    self.assertListEqual(errors, [])
    self.assertTrue(
        policy._IsAllowed(self.resources, 'project-2', org_policy, errors))
    self.assertListEqual(errors, [])
    self.assertTrue(
        policy._IsAllowed(self.resources, 'project-3', org_policy, errors))
    self.assertListEqual(errors, [])

  def testDenyAll(self):
    org_policy = self.messages.ListPolicy()
    org_policy.allValues = (
        self.messages.ListPolicy.AllValuesValueValuesEnum.DENY)

    errors = []
    self.assertFalse(
        policy._IsAllowed(self.resources, 'project-1', org_policy, errors))
    self.assertListEqual(errors, [])
    self.assertFalse(
        policy._IsAllowed(self.resources, 'project-2', org_policy, errors))
    self.assertListEqual(errors, [])
    self.assertFalse(
        policy._IsAllowed(self.resources, 'project-3', org_policy, errors))
    self.assertListEqual(errors, [])

  def testAllowed(self):
    allowed_values = ['projects/project-1', 'projects/project-2']
    denied_values = []

    errors = []
    org_policy = self.MakePolicy(allowed_values, denied_values)

    self.assertTrue(
        policy._IsAllowed(self.resources, 'project-1', org_policy, errors))
    self.assertListEqual(errors, [])
    self.assertTrue(
        policy._IsAllowed(self.resources, 'project-2', org_policy, errors))
    self.assertListEqual(errors, [])
    self.assertFalse(
        policy._IsAllowed(self.resources, 'project-3', org_policy, errors))
    self.assertListEqual(errors, [])

  def testDenied(self):
    allowed_values = []
    denied_values = ['projects/project-2']

    errors = []
    org_policy = self.MakePolicy(allowed_values, denied_values)

    self.assertTrue(
        policy._IsAllowed(self.resources, 'project-1', org_policy, errors))
    self.assertListEqual(errors, [])
    self.assertFalse(
        policy._IsAllowed(self.resources, 'project-2', org_policy, errors))
    self.assertListEqual(errors, [])
    self.assertTrue(
        policy._IsAllowed(self.resources, 'project-3', org_policy, errors))
    self.assertListEqual(errors, [])

  def testComplex(self):
    allowed_values = ['projects/project-1', 'projects/project-2']
    denied_values = ['projects/project-2']

    errors = []
    org_policy = self.MakePolicy(allowed_values, denied_values)

    self.assertTrue(
        policy._IsAllowed(self.resources, 'project-1', org_policy, errors))
    self.assertListEqual(errors, [])
    self.assertFalse(
        policy._IsAllowed(self.resources, 'project-2', org_policy, errors))
    self.assertListEqual(errors, [])
    self.assertFalse(
        policy._IsAllowed(self.resources, 'project-3', org_policy, errors))
    self.assertListEqual(errors, [])

  def testMalformedRecord(self):
    allowed_values = ['projects/project-1', 'projectss/project-2']
    denied_values = ['projects/project-2']

    errors = []
    org_policy = self.MakePolicy(allowed_values, denied_values)

    self.assertTrue(
        policy._IsAllowed(self.resources, 'project-3', org_policy, errors))
    self.assertEqual(1, len(errors))
    self.assertEqual(
        str(errors[0]), 'could not parse resource [projectss/project-2]: '
        'It is not in compute.projects collection as it does not match '
        'path template projects/(.*)$')

if __name__ == '__main__':
  test_case.main()
