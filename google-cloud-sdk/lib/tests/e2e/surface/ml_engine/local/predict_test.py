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
"""e2e tests for ml local predict command."""
from __future__ import absolute_import
from __future__ import unicode_literals
import subprocess

from googlecloudsdk.core.util import files
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.ml_engine import base


def _VerifyTensorflow():
  python_executables = files.SearchForExecutableOnPath('python')
  if not python_executables:
    raise RuntimeError('No python executable available')
  python_executable = python_executables[0]
  command = [python_executable, '-c', 'import tensorflow']
  proc = subprocess.Popen(command,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  stdout, stderr = proc.communicate()
  if proc.returncode:
    raise RuntimeError(
        'Could not verify Tensorflow install.\n'
        'Python location: {python}\n'
        'Command to test: {command}\n'
        '----------------stdout----------------\n'
        '{stdout}'
        '----------------stderr----------------'
        '{stderr}'.format(python=python_executable, command=command,
                          stdout=stdout, stderr=stderr))

try:
  _VerifyTensorflow()
except RuntimeError as err:
  tensorflow_available = False
  reason = 'Needs tensorflow installed: ' + str(err)
else:
  tensorflow_available = True
  reason = 'Needs tensorflow installed'


# If this test is skipped, we have very little effective coverage of this code
# path and it should be treated as a high-priority issue.
@sdk_test_base.Filters.RunOnlyInBundle
@test_case.Filters.RunOnlyIf(tensorflow_available, reason)
class PredictTest(base.MlGaPlatformTestBase):
  """E2E tests for ml-engine local predict command."""

  @property
  def model_path(self):
    return self.Resource(
        'tests', 'e2e', 'surface', 'ml_engine', 'testdata', 'savedmodel')

  def testLocalPredict(self):
    json_instances = self.Resource('tests', 'e2e', 'surface', 'ml_engine',
                                   'testdata', 'predict_sample.tensor.json')

    results = self.Run(
        'ml-engine local predict '
        '    --model-dir={} '
        '    --json-instances={}'.format(self.model_path, json_instances))

    # Prediction output should look something like the following:
    # {'predictions' : [{'prediction': 0, 'key': 0, scores: [0, 1, ...]}, ...]}
    self.AssertOutputMatches(r"""KEY PREDICTION SCORES
0 5 \[0\.037207[e0-9-]+, 0\.000525[e0-9-]+, 0\.017123[e0-9-]+, 0\.389779[e0-9-]+, 2\.245763[e0-9-]+, 0\.527397[e0-9-]+, 0\.000427[e0-9-]+, 0\.004393[e0-9-]+, 0\.020065[e0-9-]+, 0\.003058[e0-9-]+\]
1 0 \[0\.994211[e0-9-]+, 1\.877721[e0-9-]+, 7\.398535[e0-9-]+, 5\.808983[e0-9-]+, 4\.643065[e0-9-]+, 0\.005415[e0-9-]+, 1\.582628[e0-9-]+, 1\.317303[e0-9-]+, 0\.000206[e0-9-]+, 4\.196298[e0-9-]+\]
2 4 \[0\.002662[e0-9-]+, 0\.000740[e0-9-]+, 0\.011052[e0-9-]+, 0\.033408[e0-9-]+, 0\.649263[e0-9-]+, 0\.011686[e0-9-]+, 0\.026567[e0-9-]+, 0\.017565[e0-9-]+, 0\.013800[e0-9-]+, 0\.233252[e0-9-]+\]
3 1 \[1\.044201[e0-9-]+, 0\.960750[e0-9-]+, 0\.007184[e0-9-]+, 0\.002896[e0-9-]+, 0\.000209[e0-9-]+, 0\.001832[e0-9-]+, 0\.000330[e0-9-]+, 0\.000459[e0-9-]+, 0\.026060[e0-9-]+, 0\.000266[e0-9-]+\]
4 9 \[4\.231131[e0-9-]+, 0\.000237[e0-9-]+, 6\.584568[e0-9-]+, 0\.000148[e0-9-]+, 0\.129414[e0-9-]+, 0\.001136[e0-9-]+, 0\.000142[e0-9-]+, 0\.016885[e0-9-]+, 0\.004945[e0-9-]+, 0\.847020[e0-9-]+\]
5 2 \[0\.003328[e0-9-]+, 0\.000146[e0-9-]+, 0\.845181[e0-9-]+, 0\.019072[e0-9-]+, 0\.000210[e0-9-]+, 0\.001520[e0-9-]+, 0\.000516[e0-9-]+, 0\.018605[e0-9-]+, 0\.023360[e0-9-]+, 0\.088058[e0-9-]+\]
6 1 \[2\.845632[e0-9-]+, 0\.988403[e0-9-]+, 0\.001692[e0-9-]+, 0\.007031[e0-9-]+, 1\.160552[e0-9-]+, 0\.000452[e0-9-]+, 0\.000142[e0-9-]+, 0\.000114[e0-9-]+, 0\.001822[e0-9-]+, 0\.000329[e0-9-]+\]
7 3 \[8\.305619[e0-9-]+, 6\.980495[e0-9-]+, 0\.002076[e0-9-]+, 0\.980704[e0-9-]+, 1\.283699[e0-9-]+, 0\.001915[e0-9-]+, 1\.080777[e0-9-]+, 0\.000127[e0-9-]+, 0\.013786[e0-9-]+, 0\.001297[e0-9-]+\]
8 1 \[1\.916230[e0-9-]+, 0\.980750[e0-9-]+, 0\.001764[e0-9-]+, 0\.006697[e0-9-]+, 0\.000128[e0-9-]+, 0\.003971[e0-9-]+, 0\.000656[e0-9-]+, 0\.000788[e0-9-]+, 0\.004152[e0-9-]+, 0\.001070[e0-9-]+\]
9 4 \[0\.000282[e0-9-]+, 1\.802669[e0-9-]+, 0\.000287[e0-9-]+, 6\.428515[e0-9-]+, 0\.964252[e0-9-]+, 0\.005196[e0-9-]+, 0\.015701[e0-9-]+, 0\.000438[e0-9-]+, 0\.004905[e0-9-]+, 0\.008852[e0-9-]+\]
""", normalize_space=True)
    self.assertEqual(list(results.keys()), ['predictions'])
    predictions = results['predictions']
    self.assertEqual(len(predictions), 10)
    expected_keys = set(['prediction', 'key', 'scores'])
    for prediction in predictions:
      self.assertSetEqual(set(prediction.keys()), expected_keys)


if __name__ == '__main__':
  test_case.main()
