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
"""ai-platform models create tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import exceptions as core_exceptions
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.ml_engine import base


@parameterized.parameters('ml-engine', 'ai-platform')
class CreateSurfaceTestGA(base.MlGaPlatformTestBase):

  def _MakeModel(self, name='myModel', regions=('us-central1',),
                 labels=None, online_prediction_logging=False,
                 online_prediction_console_logging=False, description=None):
    if labels is not None:
      labels_cls = self.short_msgs.Model.LabelsValue
      labels = labels_cls(additionalProperties=[
          labels_cls.AdditionalProperty(key=key, value=value) for key, value in
          sorted(labels.items())
      ])
    return self.short_msgs.Model(
        name=name,
        regions=regions,
        onlinePredictionLogging=online_prediction_logging,
        onlinePredictionConsoleLogging=online_prediction_console_logging,
        labels=labels,
        description=description
    )

  def _ExpectModel(self, **kwargs):
    model = self._MakeModel(**kwargs)
    self.client.projects_models.Create.Expect(
        self.msgs.MlProjectsModelsCreateRequest(
            googleCloudMlV1Model=model,
            parent='projects/{}'.format(self.Project())
        ),
        model)

  def testCreate(self, module_name):
    self._ExpectModel()
    self.Run('{} models create myModel'.format(module_name))

  def testCreateEnableLogging(self, module_name):
    self._ExpectModel(online_prediction_logging=True)
    self.Run('{} models create myModel --enable-logging'.format(module_name))

  def testCreateSingleRegion(self, module_name):
    self._ExpectModel(regions=['us-east1'])
    self.Run('{} models create myModel --regions us-east1'.format(module_name))

  def testCreateMultipleRegions(self, module_name):
    self._ExpectModel(regions=['us-central1', 'us-east1'])
    self.Run('{} models create myModel --regions us-central1,us-east1'.format(
        module_name))

  def testCreateLabels(self, module_name):
    self._ExpectModel(labels={'key1': 'value1', 'key2': 'value2'})
    self.Run('{} models create myModel --labels key1=value1,key2=value2'.format(
        module_name))

  def testCreateDescription(self, module_name):
    self._ExpectModel(description='Foo')
    self.Run('{} models create myModel --description Foo'.format(module_name))

  def testConflictingRegionFlag(self, module_name):
    with self.assertRaisesRegex(
        core_exceptions.Error,
        'Only one of --region or --regions can be specified.'):
      self.Run(
          '{} models create myModel --region regionA --regions regionB'.format(
              module_name))

  # NOTE that this test only checks the request. endpoint is not tested here.
  def testCreateRegionFlag(self, module_name):
    self._ExpectModel(regions=['europe-west4'])
    self.Run(
        '{} models create myModel --region europe-west4'.format(module_name))


@parameterized.parameters('ml-engine', 'ai-platform')
class CreateSurfaceTestBeta(base.MlBetaPlatformTestBase, CreateSurfaceTestGA):

  def testCreateEnableConsoleLogging(self, module_name):
    self._ExpectModel(online_prediction_console_logging=True)
    self.Run('{} models create myModel --enable-console-logging'.format(
        module_name))


class CreateSurfaceTestAlpha(base.MlAlphaPlatformTestBase,
                             CreateSurfaceTestBeta):
  pass


if __name__ == '__main__':
  test_case.main()
