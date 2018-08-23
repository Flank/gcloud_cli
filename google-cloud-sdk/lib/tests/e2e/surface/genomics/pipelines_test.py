# -*- coding: utf-8 -*- #
# Copyright 2014 Google Inc. All Rights Reserved.
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

"""Integration test for 'genomics pipelines' commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties
from tests.lib import e2e_utils
from tests.lib import test_case
from tests.lib.surface.genomics import base

PIPELINE_JSON = """{"name": "gcloud_test_pipeline",
 "description": "Pipeline for gcloud e2e test.",
 "inputParameters":[
   {"name": "greeting","defaultValue":"Hello"},
 ],
 "docker": {
   "imageName": "ubuntu",
   "cmd": "echo $greeting"
  },
  "resources": {
    "minimumRamGb": 1,
    "minimumCpuCores": 1,
    "preemptible":true,
    "zones":["us-central1-a", "us-central1-b", "us-central1-c"]
}}"""


class PipelinesIntegrationTest(base.GenomicsIntegrationTest):

  def SetUp(self):
    properties.VALUES.core.disable_prompts.Set(True)
    properties.VALUES.core.user_output_enabled.Set(False)

  def testCreate(self):
    pipeline_path = self.Touch(self.temp_path, contents=PIPELINE_JSON)

    log_dir = 'gs://do-not-delete-genomics-pipelines-test/{0}/'.format(
        next(e2e_utils.GetResourceNameGenerator(prefix='e2e')))

    op = self.RunGenomics(
        ['pipelines', 'run', '--pipeline-file', pipeline_path,
         '--logging', log_dir])
    result = self.RunGenomics(['operations', 'describe', op.name])
    self.assertEqual(result.name, op.name)


if __name__ == '__main__':
  test_case.main()
