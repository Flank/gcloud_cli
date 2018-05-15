# Copyright 2016 Google Inc. All Rights Reserved.

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
"""Tests for the ML Engine jobs command_lib utils."""
from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.ml_engine import models
from googlecloudsdk.command_lib.ml_engine import models_util
from googlecloudsdk.core import resources
from tests.lib.surface.ml_engine import base


MODEL_URL = ('https://ml.googleapis.com/v1/'
             'projects/other-project/models/other-model')


class ParseModelTest(base.MlBetaPlatformTestBase):

  def testParseModel(self):
    model_ref = models_util.ParseModel('model')
    self.assertEqual(model_ref.projectsId, self.Project())
    self.assertEqual(model_ref.modelsId, 'model')
    self.assertEqual(model_ref.Name(), 'model')
    self.assertEqual(model_ref.RelativeName(),
                     'projects/{}/models/model'.format(self.Project()))

  def testParseModel_Url(self):
    model_ref = models_util.ParseModel(MODEL_URL)
    self.assertEqual(model_ref.projectsId, 'other-project')
    self.assertEqual(model_ref.modelsId, 'other-model')
    self.assertEqual(model_ref.Name(), 'other-model')
    self.assertEqual(model_ref.RelativeName(),
                     'projects/other-project/models/other-model')
    self.assertEqual(model_ref.SelfLink(), MODEL_URL)


class IamPolicyTest(base.MlBetaPlatformTestBase):

  IAM_POLICY_FILE = """\
      {
          "bindings": [
              {
                  "members": [
                      "user:email1@gmail.com"
                  ],
                  "role": "roles/owner"
              }
          ],
          "etag": "BwUjMhCsNvY=",
          "version": 1
      }
  """

  def SetUp(self):
    self.models_client = models.ModelsClient()
    self.model_ref = resources.REGISTRY.Create(models_util.MODELS_COLLECTION,
                                               modelsId='myModel',
                                               projectsId=self.Project())

  def testSetIamPolicy(self):
    policy_file = self.Touch(self.temp_path, 'policy.json',
                             contents=self.IAM_POLICY_FILE)
    policy = self.msgs.GoogleIamV1Policy(
        bindings=[
            self.msgs.GoogleIamV1Binding(
                members=['user:email1@gmail.com'],
                role='roles/owner')],
        etag=b'\x07\x05#2\x10\xac6\xf6',
        version=1)
    set_iam_policy = self.StartObjectPatch(self.models_client, 'SetIamPolicy',
                                           return_value=policy, autospec=True)

    response = models_util.SetIamPolicy(self.models_client, 'myModel',
                                        policy_file)

    self.assertEqual(response, policy)
    set_iam_policy.assert_called_once_with(self.model_ref,
                                           policy,
                                           'bindings,etag,version')
    self.AssertErrContains('Updated IAM policy for model [myModel].')

  def testGetIamPolicy(self):
    policy = self.msgs.GoogleIamV1Policy(etag=b'abcd')
    get_iam_policy = self.StartObjectPatch(self.models_client, 'GetIamPolicy',
                                           return_value=policy, autospec=True)

    response = models_util.GetIamPolicy(self.models_client, 'myModel')

    self.assertEqual(response, policy)
    get_iam_policy.assert_called_once_with(self.model_ref)

  def testAddIamPolicyBinding(self):
    original_policy = self.msgs.GoogleIamV1Policy(
        bindings=[
            self.msgs.GoogleIamV1Binding(
                members=['user:email1@gmail.com'],
                role='roles/owner')],
        etag=b'abcd')
    new_policy = self.msgs.GoogleIamV1Policy(
        bindings=[
            self.msgs.GoogleIamV1Binding(
                members=['user:email1@gmail.com', 'user:user2@gmail.com'],
                role='roles/owner')],
        etag=b'abcd')
    get_iam_policy = self.StartObjectPatch(
        self.models_client, 'GetIamPolicy', return_value=original_policy,
        autospec=True)
    set_iam_policy = self.StartObjectPatch(self.models_client, 'SetIamPolicy',
                                           return_value=new_policy,
                                           autospec=True)

    response = models_util.AddIamPolicyBinding(
        self.models_client, 'myModel', 'user:user2@gmail.com', 'roles/owner')

    self.assertEqual(response, new_policy)
    get_iam_policy.assert_called_once_with(self.model_ref)
    set_iam_policy.assert_called_once_with(self.model_ref, new_policy,
                                           'bindings,etag')

  def testAddIamPolicyBindingNewRole(self):
    original_policy = self.msgs.GoogleIamV1Policy(
        bindings=[],
        etag=b'abcd')
    new_policy = self.msgs.GoogleIamV1Policy(
        bindings=[
            self.msgs.GoogleIamV1Binding(
                members=['user:user2@gmail.com'],
                role='roles/owner')],
        etag=b'abcd')
    get_iam_policy = self.StartObjectPatch(
        self.models_client, 'GetIamPolicy', return_value=original_policy,
        autospec=True)
    set_iam_policy = self.StartObjectPatch(self.models_client, 'SetIamPolicy',
                                           return_value=new_policy,
                                           autospec=True)

    response = models_util.AddIamPolicyBinding(
        self.models_client, 'myModel', 'user:user2@gmail.com', 'roles/owner')

    self.assertEqual(response, new_policy)
    get_iam_policy.assert_called_once_with(self.model_ref)
    set_iam_policy.assert_called_once_with(self.model_ref, new_policy,
                                           'bindings,etag')

  def testRemoveIamPolicyBinding(self):
    original_policy = self.msgs.GoogleIamV1Policy(
        bindings=[
            self.msgs.GoogleIamV1Binding(
                members=['user:email1@gmail.com'],
                role='roles/owner')],
        etag=b'abcd')
    new_policy = self.msgs.GoogleIamV1Policy(bindings=[], etag=b'abcd')
    get_iam_policy = self.StartObjectPatch(
        self.models_client, 'GetIamPolicy', return_value=original_policy,
        autospec=True)
    set_iam_policy = self.StartObjectPatch(self.models_client, 'SetIamPolicy',
                                           return_value=new_policy,
                                           autospec=True)

    response = models_util.RemoveIamPolicyBinding(
        self.models_client, 'myModel', 'user:email1@gmail.com', 'roles/owner')

    self.assertEqual(response, new_policy)
    get_iam_policy.assert_called_once_with(self.model_ref)
    set_iam_policy.assert_called_once_with(self.model_ref, new_policy,
                                           'bindings,etag')
