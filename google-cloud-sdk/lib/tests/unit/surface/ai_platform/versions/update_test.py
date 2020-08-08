# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
                   package_uris=None,
                   manual_scaling=None,
                   auto_scaling=None):
    if labels is not None:
      labels_cls = self.short_msgs.Version.LabelsValue
      labels = labels_cls(additionalProperties=[
          labels_cls.AdditionalProperty(key=key, value=value)
          for key, value in sorted(labels.items())
      ])
    if manual_scaling:
      manual_scaling = self.short_msgs.ManualScaling(
          nodes=manual_scaling['nodes'])
    if auto_scaling:
      auto_scaling = self.short_msgs.AutoScaling(
          minNodes=auto_scaling['minNodes'])
    return self.short_msgs.Version(
        name=name,
        labels=labels,
        description=description,
        packageUris=package_uris or [],
        predictionClass=prediction_class,
        manualScaling=manual_scaling,
        autoScaling=auto_scaling)

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
        'description,labels', labels={'key': 'value'}, description='Foo')
    self._ExpectPoll()
    self.Run('{} versions update myVersion --model myModel '
             '--update-labels key=value --description Foo'.format(module_name))
    self.AssertErrContains('Updated AI Platform version [myVersion].')

  def testUpdateFromConfig(self, module_name):
    yaml_contents = """\
        description: Foo
        manualScaling:
          nodes: 10
    """
    yaml_path = self.Touch(self.temp_path, 'version.yaml', yaml_contents)
    self._ExpectPatch(
        'description,manualScaling.nodes',
        description='Foo',
        manual_scaling={'nodes': 10},
    )
    self._ExpectPoll()
    self.Run('{} versions update myVersion --model myModel '
             '--config {}'.format(module_name, yaml_path))

  def testUpdateFromConfigWithDescription(self, module_name):
    yaml_contents = """\
        description: Foo
    """
    yaml_path = self.Touch(self.temp_path, 'version.yaml', yaml_contents)
    self._ExpectPatch(
        'description',
        description='Foo'
    )
    self._ExpectPoll()
    self.Run('{} versions update myVersion --model myModel '
             '--config {}'.format(module_name, yaml_path))

  # Since we defer validation of the actual autoScaling values to the API,
  # here we only test the expect behavior of the surface namely that it parses
  # the yaml values correctly and passes them to the API.
  # Specifically, the API is expected to raise errors for
  # the following conditions (based on current validation rules):
  # - invalid autoscaling field names
  # - both automaticScaling and manualScaling specified in same config
  # - invalid values for minNodes
  def testUpdateFromConfigWithAutoScaling(self, module_name):
    yaml_contents = """\
        autoScaling:
          minNodes: 10
    """
    yaml_path = self.Touch(self.temp_path, 'version.yaml', yaml_contents)
    self._ExpectPatch(
        'autoScaling.minNodes',
        auto_scaling={'minNodes': 10},
    )
    self._ExpectPoll()
    self.Run('{} versions update myVersion --model myModel '
             '--config {}'.format(module_name, yaml_path))

  def testUpdateFromConfigManualScaling(self, module_name):
    yaml_contents = """\
        manualScaling:
          nodes: 10
    """
    yaml_path = self.Touch(self.temp_path, 'version.yaml', yaml_contents)
    self._ExpectPatch(
        'manualScaling.nodes',
        manual_scaling={'nodes': 10}
    )
    self._ExpectPoll()
    self.Run('{} versions update myVersion --model myModel '
             '--config {}'.format(module_name, yaml_path))

  # Note that the backend is expected to validate and reject this request,
  # so here we simply verify that the request is sent with both
  # options.
  def testUpdateFromConfigWithBothManualAndAutoScaling(self, module_name):
    yaml_contents = """\
        autoScaling:
          minNodes: 31
        manualScaling:
          nodes: 41
    """
    yaml_path = self.Touch(self.temp_path, 'version.yaml', yaml_contents)
    self._ExpectPatch(
        'autoScaling.minNodes,manualScaling.nodes',
        auto_scaling={'minNodes': 31},
        manual_scaling={'nodes': 41},
    )
    self._ExpectPoll()
    self.Run('{} versions update myVersion --model myModel '
             '--config {}'.format(module_name, yaml_path))


@parameterized.parameters('ml-engine', 'ai-platform')
class UpdateSurfaceTestBeta(base.MlBetaPlatformTestBase, UpdateSurfaceTestGA):
  pass


@parameterized.parameters('ml-engine', 'ai-platform')
class UpdateSurfaceTestAlpha(base.MlAlphaPlatformTestBase,
                             UpdateSurfaceTestBeta):
  pass


if __name__ == '__main__':
  test_case.main()
