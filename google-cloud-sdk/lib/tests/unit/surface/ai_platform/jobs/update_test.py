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
"""ai-platform jobs update tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ml_engine import jobs
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.ml_engine import base


@parameterized.named_parameters(
    ('GA_ai_platform', calliope_base.ReleaseTrack.GA, 'ai-platform'),
    ('GA_ml_engine', calliope_base.ReleaseTrack.GA, 'ml-engine'),
)
class UpdateSurfaceTest(base.MlGaPlatformTestBase, parameterized.TestCase):

  def _MakeJob(self, name=None, labels=None):
    if labels is not None:
      labels_cls = self.short_msgs.Job.LabelsValue
      labels = labels_cls(additionalProperties=[
          labels_cls.AdditionalProperty(key=key, value=value) for key, value in
          sorted(labels.items())
      ])
    return self.short_msgs.Job(
        jobId=name,
        labels=labels
    )

  def _ExpectPoll(self):
    self.client.projects_operations.Get.Expect(
        request=self.msgs.MlProjectsOperationsGetRequest(
            name='projects/{}/operations/opId'.format(self.Project())),
        response=self.msgs.GoogleLongrunningOperation(
            name='opName', done=True))

  def _ExpectGet(self, name='myJob', **kwargs):
    job = self._MakeJob(name=name, **kwargs)
    self.client.projects_jobs.Get.Expect(
        self.msgs.MlProjectsJobsGetRequest(
            name='projects/{}/jobs/{}'.format(self.Project(), name),
        ),
        job)

  def _ExpectPatch(self, update_mask, **kwargs):
    job = self._MakeJob(**kwargs)
    self.client.projects_jobs.Patch.Expect(
        self.msgs.MlProjectsJobsPatchRequest(
            name='projects/{}/jobs/myJob'.format(self.Project()),
            googleCloudMlV1Job=job,
            updateMask=update_mask
        ),
        job)

  def testUpdateNoUpdateRequested(self, track, module_name):
    self.track = track

    with self.assertRaises(jobs.NoFieldsSpecifiedError):
      self.Run('{} jobs update myJob'.format(module_name))

  def testUpdateNewLabelsNoOp(self, track, module_name):
    self.track = track

    self._ExpectGet(labels={'key': 'value'})
    self.Run(
        '{} jobs update myJob --update-labels key=value'.format(module_name))

  def testUpdateNewLabels(self, track, module_name):
    self.track = track

    self._ExpectGet()
    self._ExpectPatch('labels', labels={'key': 'value'})
    self.Run(
        '{} jobs update myJob --update-labels key=value'.format(module_name))

  def testUpdateClearLabels(self, track, module_name):
    self.track = track

    self._ExpectGet(labels={'key': 'value'})
    self._ExpectPatch('labels', labels={})
    self.Run('{} jobs update myJob --clear-labels'.format(module_name))

  def testUpdateRemoveLabels(self, track, module_name):
    self.track = track

    self._ExpectGet(labels={'a': '1', 'b': '2', 'c': '3'})
    self._ExpectPatch('labels', labels={'a': '1', 'c': '3'})
    self.Run('{} jobs update myJob --remove-labels b'.format(module_name))


if __name__ == '__main__':
  test_case.main()
