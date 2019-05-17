# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""ai-platform versions update tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ml_engine import versions_api
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.ml_engine import base


@parameterized.parameters('ml-engine', 'ai-platform')
class UpdateSurfaceTestGA(base.MlGaPlatformTestBase):

  def _MakeVersion(self,
                   name=None,
                   labels=None,
                   description=None,
                   prediction_class=None,
                   package_uris=None):
    if labels is not None:
      labels_cls = self.short_msgs.Version.LabelsValue
      labels = labels_cls(additionalProperties=[
          labels_cls.AdditionalProperty(key=key, value=value)
          for key, value in sorted(labels.items())
      ])
    return self.short_msgs.Version(
        name=name,
        labels=labels,
        description=description,
        packageUris=package_uris or [],
        predictionClass=prediction_class)

  def _ExpectPoll(self):
    self.client.projects_operations.Get.Expect(
        request=self.msgs.MlProjectsOperationsGetRequest(
            name='projects/{}/operations/opId'.format(self.Project())),
        response=self.msgs.GoogleLongrunningOperation(name='opName', done=True))

  def _ExpectGet(self, model='myModel', name='myVersion', **kwargs):
    version = self._MakeVersion(name=name, **kwargs)
    self.client.projects_models_versions.Get.Expect(
        self.msgs.MlProjectsModelsVersionsGetRequest(
            name='projects/{}/models/{}/versions/{}'.format(
                self.Project(), model, name),), version)

  def _ExpectPatch(self, update_mask, **kwargs):
    version = self._MakeVersion(**kwargs)
    self.client.projects_models_versions.Patch.Expect(
        self.msgs.MlProjectsModelsVersionsPatchRequest(
            name='projects/{}/models/myModel/versions/myVersion'.format(
                self.Project()),
            googleCloudMlV1Version=version,
            updateMask=update_mask),
        self.msgs.GoogleLongrunningOperation(name='opId'))

  def testUpdateNoUpdateRequested(self, module_name):
    with self.assertRaises(versions_api.NoFieldsSpecifiedError):
      self.Run(
          '{} versions update myVersion --model myModel'.format(module_name))

  def testUpdateNewLabelsNoOp(self, module_name):
    self._ExpectGet(labels={'key': 'value'})
    self.Run('{} versions update myVersion --model myModel '
             '--update-labels key=value'.format(module_name))

  def testUpdateNewLabels(self, module_name):
    self._ExpectGet()
    self._ExpectPatch('labels', labels={'key': 'value'})
    self._ExpectPoll()
    self.Run('{} versions update myVersion --model myModel '
             '--update-labels key=value'.format(module_name))

  def testUpdateClearLabels(self, module_name):
    self._ExpectGet(labels={'key': 'value'})
    self._ExpectPatch('labels', labels={})
    self._ExpectPoll()
    self.Run('{} versions update myVersion --model myModel '
             '--clear-labels'.format(module_name))

  def testUpdateRemoveLabels(self, module_name):
    self._ExpectGet(labels={'a': '1', 'b': '2'})
    self._ExpectPatch('labels', labels={'a': '1'})
    self._ExpectPoll()
    self.Run('{} versions update myVersion --model myModel '
             '--remove-labels b'.format(module_name))

  def testUpdateAll(self, module_name):
    self._ExpectGet()
    self._ExpectPatch(
        'labels,description', labels={'key': 'value'}, description='Foo')
    self._ExpectPoll()
    self.Run('{} versions update myVersion --model myModel '
             '--update-labels key=value --description Foo'.format(module_name))
    self.AssertErrContains('Updated AI Platform version [myVersion].')


class UpdateSurfaceTestBeta(base.MlBetaPlatformTestBase, UpdateSurfaceTestGA):

  pass


class UpdateSurfaceTestAlpha(base.MlAlphaPlatformTestBase,
                             UpdateSurfaceTestBeta):
  pass


if __name__ == '__main__':
  test_case.main()
