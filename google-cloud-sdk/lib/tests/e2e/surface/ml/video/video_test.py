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

"""e2e tests for ml video command group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from tests.lib import e2e_base
from tests.lib import test_case


class VideoTests(e2e_base.WithServiceAuth):
  """E2E tests for `ml videos` command group."""

  def SetUp(self):
    self.testdata = self.Resource('tests', 'unit', 'command_lib', 'ml',
                                  'video', 'testdata', 'toy.mp4')
    self.sample_video = 'gs://do-not-delete-ml-video-test/chicago.mp4'
    self.track = base.ReleaseTrack.GA

  def testDetectLocal(self):
    """Test that gcloud ml video detect-labels works."""
    self.Run('ml video detect-labels {}'.format(self.testdata))
    # basic assertion that label Annotations are output by the command.
    self.AssertOutputContains('segmentLabelAnnotations')

  def testDetectSynchronous(self):
    """Test that gcloud ml video detect-labels works."""
    self.Run('ml video detect-labels {}'.format(self.sample_video))
    # basic assertion that label Annotations are output by the command.
    self.AssertOutputContains('segmentLabelAnnotations')

  def testDetectWithOperations(self):
    """Test gcloud ml video detect-shot-changes, plus operations commands."""
    result = self.Run(
        'ml video detect-shot-changes {} --async'.format(self.sample_video))
    operation_id = result.name
    describe_result = self.Run(
        'ml video operations describe {}'.format(operation_id))
    self.assertEqual(describe_result.name, operation_id)
    self.Run('ml video operations wait {}'.format(operation_id))
    self.AssertErrContains(
        'Waiting for operation [{}] to complete'.format(operation_id))
    self.AssertOutputContains('shotAnnotations')


if __name__ == '__main__':
  test_case.main()
