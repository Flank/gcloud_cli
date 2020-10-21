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
"""e2e tests for ai-platform online prediction."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties

from tests.lib import e2e_base
from tests.lib import parameterized
from tests.lib import test_case


@parameterized.parameters('ml-engine', 'ai-platform')
class MlOnlinePredictionTests(e2e_base.WithServiceAuth):
  """e2e tests for ai-platform online prediction."""

  MODEL_ID = 'do_not_delete_model'
  VERSION_ID = 'do_not_delete_version'

  def testOnlinePrediction(self, module_name):
    r"""Tests online prediction.

    This test is predicated on the existence of a trained model in the project.
    This model can easily be reproduced; it just takes
    several minutes:

    $ gcloud config set project $PROJECT
    $ gcloud ml-engine models create do_not_delete_model --regions=us-central1
    $ MODEL_DIR="${CLOUDSDK_TEST_DIR}/e2e/surface/ml_engine/testdata/savedmodel"
    $ RUNTIME_VER="latest-available-tensorflow-version-placeholder"
    $ gcloud ml-engine versions create do_not_delete_version \
        --model do_not_delete_model \
        --origin "${MODEL_DIR}" \
        --staging-bucket gs://${PROJECT}-ml
        --runtime-version "$RUNTIME_VER"

    Args:
      module_name : The surface command to run. One of "ai-platform" or it's
        alias "ml-engine".
    """
    json_instances = self.Resource('tests', 'e2e', 'surface', 'ai_platform',
                                   'testdata', 'predict_sample.tensor.json')
    properties.VALUES.core.user_output_enabled.Set(False)
    results = self.Run(('{module_name} predict '
                        '  --model={model_id} '
                        '  --version={version_id} '
                        '  --json-instances={json_instances}').format(
                            module_name=module_name,
                            model_id=self.MODEL_ID,
                            version_id=self.VERSION_ID,
                            json_instances=json_instances))

    # Make some assertions about the structure of the results. The results
    # themselves are non-deterministic, but we don't really care about whether
    # they're any good in this test. Just that we got *something*.
    predictions = results.get('predictions')
    self.assertEqual(len(predictions), 10)
    for prediction in predictions:
      self.assertSetEqual(set(prediction.keys()),
                          set(('prediction', 'key', 'scores')))


if __name__ == '__main__':
  test_case.main()
