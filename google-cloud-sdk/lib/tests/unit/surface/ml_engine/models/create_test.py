# -*- coding: utf-8 -*- #
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
"""ml-engine models create tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.ml_engine import base


@parameterized.named_parameters(
    ('Alpha', calliope_base.ReleaseTrack.ALPHA),
    ('Beta', calliope_base.ReleaseTrack.BETA),
    ('GA', calliope_base.ReleaseTrack.GA),
)
class CreateSurfaceTest(base.MlGaPlatformTestBase, parameterized.TestCase):

  def SetUp(self):
    pass

  def _MakeModel(self, name='myModel', regions=('us-central1',),
                 online_prediction_logging=False, labels=None,
                 description=None):
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

  def testCreate(self, track):
    self.track = track

    self._ExpectModel()
    self.Run('ml-engine models create myModel')

  def testCreateEnableLogging(self, track):
    self.track = track

    self._ExpectModel(online_prediction_logging=True)
    self.Run('ml-engine models create myModel --enable-logging')

  def testCreateSingleRegion(self, track):
    self.track = track

    self._ExpectModel(regions=['us-east1'])
    self.Run('ml-engine models create myModel --regions us-east1')

  def testCreateMultipleRegions(self, track):
    self.track = track

    self._ExpectModel(regions=['us-central1', 'us-east1'])
    self.Run('ml-engine models create myModel --regions us-central1,us-east1')

  def testCreateLabels(self, track):
    self.track = track

    self._ExpectModel(labels={'key1': 'value1', 'key2': 'value2'})
    self.Run('ml-engine models create myModel --labels key1=value1,key2=value2')

  def testCreateDescription(self, track):
    self.track = track

    self._ExpectModel(description='Foo')
    self.Run('ml-engine models create myModel --description Foo')


if __name__ == '__main__':
  test_case.main()
