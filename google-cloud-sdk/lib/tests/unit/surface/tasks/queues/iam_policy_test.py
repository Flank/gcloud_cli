# -*- coding: utf-8 -*- #
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

"""IAM tests for `gcloud tasks queues`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from tests.lib import test_case
from tests.lib.surface.tasks import test_base


class GetIamPolicyTest(test_base.CloudTasksTestBase):

  def SetUp(self):
    self.queue_name = (
        'projects/other-project/locations/us-central1/queues/my-queue')
    self.admin_role = 'roles/cloudtasks.queueAdmin'

  def testGetIamPolicy(self):
    expected_policy = self.messages.Policy(
        bindings=[self.messages.Binding(
            role=self.admin_role, members=['user:test-user@google.com'])],
        etag=b'etag')
    self.queues_service.GetIamPolicy.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesGetIamPolicyRequest(
            resource=self.queue_name),
        response=expected_policy)

    actual_policy = self.Run(
        'tasks queues get-iam-policy {}'.format(self.queue_name))

    self.assertEqual(actual_policy, expected_policy)

  def testGetIamPolicy_Location(self):
    queue_id = 'my-queue'
    queue_name = (
        'projects/fake-project/locations/us-central2/queues/{}'.format(
            queue_id))
    expected_policy = self.messages.Policy(
        bindings=[self.messages.Binding(
            role=self.admin_role, members=['user:test-user@google.com'])],
        etag=b'etag')
    self.queues_service.GetIamPolicy.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesGetIamPolicyRequest(
            resource=queue_name),
        response=expected_policy)

    actual_policy = self.Run(
        'tasks queues get-iam-policy {} --location=us-central2'.format(
            queue_id))

    self.assertEqual(actual_policy, expected_policy)


class SetIamPolicyTest(test_base.CloudTasksTestBase):

  def SetUp(self):
    self.queue_name = (
        'projects/other-project/locations/us-central1/queues/my-queue')
    self.admin_role = 'roles/cloudtasks.queueAdmin'

  def testSetIamPolicy(self):
    expected_policy = self.messages.Policy(
        bindings=[self.messages.Binding(
            role=self.admin_role, members=['user:test-user@google.com'])])
    policy_file = self.Touch(self.temp_path, 'policy.yaml',
                             contents=encoding.MessageToJson(expected_policy))
    self.queues_service.SetIamPolicy.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesSetIamPolicyRequest(
            resource=self.queue_name,
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=expected_policy)),
        response=expected_policy)

    actual_policy = self.Run(
        'tasks queues set-iam-policy {} {}'.format(self.queue_name,
                                                   policy_file))

    self.assertEqual(actual_policy, expected_policy)

  def testSetIamPolicy_Location(self):
    queue_id = 'my-queue'
    queue_name = (
        'projects/fake-project/locations/us-central2/queues/{}'.format(
            queue_id))
    expected_policy = self.messages.Policy(
        bindings=[self.messages.Binding(
            role=self.admin_role, members=['user:test-user@google.com'])])
    policy_file = self.Touch(self.temp_path, 'policy.yaml',
                             contents=encoding.MessageToJson(expected_policy))
    self.queues_service.SetIamPolicy.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesSetIamPolicyRequest(
            resource=queue_name,
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=expected_policy)),
        response=expected_policy)

    actual_policy = self.Run(
        'tasks queues set-iam-policy {} {} --location=us-central2'.format(
            queue_id, policy_file))

    self.assertEqual(actual_policy, expected_policy)


if __name__ == '__main__':
  test_case.main()
