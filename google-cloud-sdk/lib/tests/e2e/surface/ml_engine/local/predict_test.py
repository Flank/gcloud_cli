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


@sdk_test_base.Filters.RunOnlyInBundle
@test_case.Filters.RunOnlyIf(tensorflow_available, reason)
class PredictTest(base.MlGaPlatformTestBase):
  """E2E tests for ml-engine local predict command."""

  @property
  def model_path(self):
    return self.Resource(
        'tests', 'e2e', 'surface', 'ml_engine', 'testdata', 'savedmodel')

  @test_case.Filters.skip('Failing', 'b/74100495')
  def testLocalPredict(self):
    json_instances = self.Resource('tests', 'e2e', 'surface', 'ml_engine',
                                   'testdata', 'predict_sample.tensor.json')

    results = self.Run(
        'ml-engine local predict '
        '    --model-dir={} '
        '    --json-instances={}'.format(self.model_path, json_instances))

    # Prediction output should look something like the following:
    # {'predictions' : [{'prediction': 0, 'key': 0, scores: [0, 1, ...]}, ...]}
    self.AssertOutputEquals("""\
   KEY PREDICTION SCORES
   0 5 [0.03720792755484581, 0.000525299459695816, 0.017123309895396233, 0.38977929949760437, 2.2457632439909503e-05, 0.5273975133895874, 0.0004271556972526014, 0.004393656738102436, 0.020065197721123695, 0.003058194648474455]
   1 0 [0.9942118525505066, 1.877721267362631e-08, 7.398535672109574e-05, 5.8089830417884514e-05, 4.643065949494485e-07, 0.005415628664195538, 1.5826281014597043e-05, 1.3173030311008915e-05, 0.00020670564845204353, 4.196298959868727e-06]
   2 4 [0.0026627909392118454, 0.0007401782204397023, 0.011052398011088371, 0.033408358693122864, 0.6492634415626526, 0.011686679907143116, 0.026567857712507248, 0.01756538450717926, 0.01380055770277977, 0.23325228691101074]
   3 1 [1.0442015991429798e-05, 0.9607503414154053, 0.007184232585132122, 0.0028961985372006893, 0.00020977950771339238, 0.001832223846577108, 0.0003304879064671695, 0.00045924721052870154, 0.026060616597533226, 0.00026646663900464773]
   4 9 [4.231131697451929e-06, 0.00023704864725004882, 6.584568473044783e-05, 0.00014825542166363448, 0.12941400706768036, 0.0011368460254743695, 0.00014203799946699291, 0.016885999590158463, 0.00494557898491621, 0.847020149230957]
   5 2 [0.003328167600557208, 0.0001462145592086017, 0.845181405544281, 0.019072329625487328, 0.00021079870930407196, 0.0015205801464617252, 0.0005163856549188495, 0.018605133518576622, 0.023360637947916985, 0.0880584567785263]
   6 1 [2.845632707249024e-07, 0.9884036183357239, 0.0016925788950175047, 0.007031117100268602, 1.1605520739976782e-05, 0.0004524619725998491, 0.0001423014618922025, 0.00011432881001383066, 0.0018221850041300058, 0.0003294442722108215]
   7 3 [8.305619849124923e-05, 6.980495982134016e-06, 0.0020761892665177584, 0.9807042479515076, 1.2836997029808117e-06, 0.0019158918876200914, 1.080777337847394e-06, 0.00012782453268300742, 0.013786294497549534, 0.0012971358373761177]
   8 1 [1.916230030474253e-05, 0.9807501435279846, 0.00176465162076056, 0.00669778510928154, 0.00012866438191849738, 0.003971755504608154, 0.000656182412058115, 0.0007888341788202524, 0.004152034409344196, 0.0010708875488489866]
   9 4 [0.00028221827233210206, 1.802669976314064e-05, 0.0002877244260162115, 6.428515916923061e-05, 0.9642527103424072, 0.0051962342113256454, 0.015701889991760254, 0.0004386625369079411, 0.004905771464109421, 0.00885253120213747]
""", normalize_space=True)
    self.assertEquals(results.keys(), ['predictions'])
    predictions = results['predictions']
    self.assertEquals(len(predictions), 10)
    expected_keys = set(['prediction', 'key', 'scores'])
    for prediction in predictions:
      self.assertSetEqual(set(prediction.keys()), expected_keys)


if __name__ == '__main__':
  test_case.main()
