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
"""Tests for the ML Models library."""
from __future__ import absolute_import
from __future__ import unicode_literals
from apitools.base.py import encoding

from googlecloudsdk.api_lib.ml_engine import models
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.surface.ml_engine import base


class ModelsClientTest(base.MlGaPlatformTestBase):

  def _MakeCreateRequest(self, parent, model):
    return self.msgs.MlProjectsModelsCreateRequest(
        parent=parent,
        googleCloudMlV1Model=model)

  def _MakePatchRequest(self, model_ref, model, update_mask):
    return self.msgs.MlProjectsModelsPatchRequest(
        name=model_ref.RelativeName(),
        googleCloudMlV1Model=model,
        updateMask=','.join(update_mask))

  def SetUp(self):
    self.models_client = models.ModelsClient()

  def testCreate(self):
    model = self.short_msgs.Model(
        name='myModel', onlinePredictionLogging=False)
    self.client.projects_models.Create.Expect(
        self._MakeCreateRequest(
            parent='projects/{}'.format(self.Project()),
            model=model),
        model)
    self.assertEqual(model, self.models_client.Create('myModel', None))

  def testCreateEnableLogging(self):
    model = self.short_msgs.Model(
        name='myModel', onlinePredictionLogging=True)
    self.client.projects_models.Create.Expect(
        self._MakeCreateRequest(
            parent='projects/{}'.format(self.Project()),
            model=model),
        model)
    self.assertEqual(model, self.models_client.Create('myModel', None, True))

  def testCreateDescription(self):
    model = self.short_msgs.Model(
        name='myModel', description='My Model', onlinePredictionLogging=False)
    self.client.projects_models.Create.Expect(
        self._MakeCreateRequest(
            parent='projects/{}'.format(self.Project()),
            model=model),
        model)
    self.assertEqual(model, self.models_client.Create('myModel', None,
                                                      description='My Model'))

  def testCreateWithSingleRegion(self):
    model = self.short_msgs.Model(
        name='myModel', regions=['us-central1'], onlinePredictionLogging=False)
    self.client.projects_models.Create.Expect(
        self._MakeCreateRequest(
            parent='projects/{}'.format(self.Project()),
            model=model),
        model)
    self.assertEqual(model,
                     self.models_client.Create('myModel', ['us-central1']))

  def testCreateWithMultipleRegion(self):
    model = self.short_msgs.Model(
        name='myModel',
        regions=['us-central1', 'us-east1'],
        onlinePredictionLogging=False)
    self.client.projects_models.Create.Expect(
        self._MakeCreateRequest(
            parent='projects/{}'.format(self.Project()),
            model=model),
        model)
    self.assertEqual(model,
                     self.models_client.Create('myModel',
                                               ['us-central1', 'us-east1']))

  def testDelete(self):
    op = self.msgs.GoogleLongrunningOperation(name='opId')
    self.client.projects_models.Delete.Expect(
        request=self.msgs.MlProjectsModelsDeleteRequest(
            name='projects/{}/models/myModel'.format(self.Project())),
        response=op)
    self.assertEqual(op, self.models_client.Delete('myModel'))

  def testGet(self):
    model = self.short_msgs.Model(name='myModel')
    self.client.projects_models.Get.Expect(
        self.msgs.MlProjectsModelsGetRequest(
            name='projects/{}/models/myModel'.format(self.Project())),
        model)
    self.assertEqual(model, self.models_client.Get('myModel'))

  def testList(self):
    response_items = [
        self.short_msgs.Model(name='modelName1'),
        self.short_msgs.Model(name='modelName2')
    ]
    project_ref = resources.REGISTRY.Parse(self.Project(),
                                           collection='ml.projects')
    self.client.projects_models.List.Expect(
        request=self.msgs.MlProjectsModelsListRequest(
            parent='projects/{}'.format(self.Project()),
            pageSize=100),
        response=self.short_msgs.ListModelsResponse(
            models=response_items))
    self.assertEqual(response_items,
                     list(self.models_client.List(project_ref)))

  def testGetIamPolicy(self):
    policy = self.msgs.GoogleIamV1Policy()
    model_ref = resources.REGISTRY.Parse(
        'myModel', params={'projectsId': self.Project()},
        collection='ml.projects.models')
    self.client.projects_models.GetIamPolicy.Expect(
        request=self.msgs.MlProjectsModelsGetIamPolicyRequest(
            resource='projects/{}/models/myModel'.format(self.Project())),
        response=policy)

    self.assertIs(policy, self.models_client.GetIamPolicy(model_ref))

  def testSetIamPolicy(self):
    request_policy = self.msgs.GoogleIamV1Policy(etag=b'abcd')
    response_policy = self.msgs.GoogleIamV1Policy(etag=b'efgh')
    model_ref = resources.REGISTRY.Parse(
        'myModel', params={'projectsId': self.Project()},
        collection='ml.projects.models')

    request = self.msgs.GoogleIamV1SetIamPolicyRequest(
        policy=request_policy,
        updateMask='etag,bindings')
    self.client.projects_models.SetIamPolicy.Expect(
        request=self.msgs.MlProjectsModelsSetIamPolicyRequest(
            googleIamV1SetIamPolicyRequest=request,
            resource='projects/{}/models/myModel'.format(self.Project())),
        response=response_policy)

    self.assertIs(response_policy,
                  self.models_client.SetIamPolicy(model_ref, request_policy,
                                                  'etag,bindings'))

  def testPatchLabels(self):
    labels = {'foo': 'bar', 'fizz': 'buzz'}
    labels_field = encoding.DictToAdditionalPropertyMessage(
        labels, self.short_msgs.Model.LabelsValue, True)
    model_ref = resources.REGISTRY.Parse('myModel',
                                         params={'projectsId': self.Project()},
                                         collection='ml.projects.models')
    model = self.short_msgs.Model(labels=labels_field)
    self.client.projects_models.Patch.Expect(
        self._MakePatchRequest(model_ref=model_ref, model=model,
                               update_mask=['labels']), model)

    label_update = labels_util.UpdateResult(True, labels_field)
    self.assertEqual(model, self.models_client.Patch(model_ref, label_update))

  def testPatchDescription(self):
    updated_description = 'My New Description'
    model_ref = resources.REGISTRY.Parse('myModel',
                                         params={'projectsId': self.Project()},
                                         collection='ml.projects.models')
    model = self.short_msgs.Model(description=updated_description)
    self.client.projects_models.Patch.Expect(
        self._MakePatchRequest(model_ref=model_ref, model=model,
                               update_mask=['description']), model)

    no_label_update = labels_util.UpdateResult(False, None)
    self.assertEqual(model, self.models_client.Patch(model_ref,
                                                     no_label_update,
                                                     updated_description))

  def testPatchAll(self):
    labels = {'foo': 'bar', 'fizz': 'buzz'}
    updated_description = 'My New Description'
    labels_field = encoding.DictToAdditionalPropertyMessage(
        labels, self.short_msgs.Model.LabelsValue, True)
    model_ref = resources.REGISTRY.Parse('myModel',
                                         params={'projectsId': self.Project()},
                                         collection='ml.projects.models')
    model = self.short_msgs.Model(labels=labels_field,
                                  description=updated_description)
    self.client.projects_models.Patch.Expect(
        self._MakePatchRequest(model_ref=model_ref, model=model,
                               update_mask=['labels', 'description']), model)

    label_update = labels_util.UpdateResult(True, labels_field)
    self.assertEqual(model, self.models_client.Patch(
        model_ref, label_update, description=updated_description))

  def testPatchNoUpdate(self):
    model_ref = resources.REGISTRY.Parse('myModel',
                                         params={'projectsId': self.Project()},
                                         collection='ml.projects.models')
    no_label_update = labels_util.UpdateResult(False, None)
    with self.assertRaises(models.NoFieldsSpecifiedError):
      self.models_client.Patch(model_ref, no_label_update)


if __name__ == '__main__':
  test_case.main()
