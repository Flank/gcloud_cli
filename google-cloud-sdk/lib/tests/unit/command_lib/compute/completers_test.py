# Copyright 2015 Google Inc. All Rights Reserved.
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

"""Unit tests for the compute.completers module."""

import os

from googlecloudsdk.command_lib.compute import completers
from tests.lib import completer_test_base
from tests.lib import completer_test_data
from tests.lib.surface.compute import test_resources


def _Uris(resources):
  return [resource.selfLink for resource in resources]


_COMMAND_RESOURCES = {
    'compute.instances.list': completer_test_data.INSTANCE_URIS,
    'compute.health-checks.list': _Uris(test_resources.HEALTH_CHECKS),
    'compute.http-health-checks.list': _Uris(test_resources.HTTP_HEALTH_CHECKS),
    'compute.https-health-checks.list':
    _Uris(test_resources.HTTPS_HEALTH_CHECKS_V1),
    'compute.instance-templates.list':
    _Uris(test_resources.INSTANCE_TEMPLATES_V1),
}

_SEARCH_RESOURCES = {
    'compute.instances': completer_test_data.INSTANCE_URIS,
    'compute.healthChecks': _Uris(test_resources.HEALTH_CHECKS),
    'compute.httpHealthChecks': _Uris(test_resources.HTTP_HEALTH_CHECKS),
    'compute.httpsHealthChecks': _Uris(test_resources.HTTPS_HEALTH_CHECKS_V1),
    'compute.instanceTemplates': _Uris(test_resources.INSTANCE_TEMPLATES_V1),
}


class ComputeCompleterTest(completer_test_base.CompleterBase):

  def testRegionsCompleter(self):
    completer = self.Completer(completers.RegionsCompleter)
    self.assertItemsEqual(['asia-east1',
                           'asia-northeast1',
                           'europe-west1',
                           'us-central1',
                           'us-central2',
                           'us-east1',
                           'us-west1'],
                          completer.Complete('', self.parameter_info))
    self.assertItemsEqual(
        ['europe-west1'],
        completer.Complete('e', self.parameter_info))
    self.assertItemsEqual(
        ['europe-west1', 'us-west1'],
        completer.Complete('*w*', self.parameter_info))
    self.assertItemsEqual(
        [],
        completer.Complete('q', self.parameter_info))

  def testZonesCompleter(self):
    completer = self.Completer(completers.ZonesCompleter)
    self.assertItemsEqual(
        ['asia-east1-a',
         'asia-east1-b',
         'asia-east1-c',
         'asia-northeast1-a',
         'asia-northeast1-b',
         'asia-northeast1-c',
         'europe-west1-b',
         'europe-west1-c',
         'europe-west1-d',
         'us-central1-a',
         'us-central1-b',
         'us-central1-c',
         'us-central1-f',
         'us-central2-a',
         'us-east1-b',
         'us-east1-c',
         'us-east1-d',
         'us-west1-a',
         'us-west1-b'],
        completer.Complete('', self.parameter_info))
    self.assertItemsEqual(
        ['europe-west1-b', 'europe-west1-c', 'europe-west1-d'],
        completer.Complete('e', self.parameter_info))
    self.assertItemsEqual(
        ['europe-west1-b',
         'europe-west1-c',
         'europe-west1-d',
         'us-west1-a',
         'us-west1-b'],
        completer.Complete('*w*', self.parameter_info))
    self.assertItemsEqual(
        [],
        completer.Complete('q', self.parameter_info))


class ComputeFlagCompleterTest(completer_test_base.FlagCompleterBase):

  def testInstancesCompleter(self):
    completer = self.Completer(completers.InstancesCompleter,
                               args={'--project': None,
                                     '--zone': None},
                               command_resources=_COMMAND_RESOURCES)
    self.assertEqual(
        228,
        len(completer.Complete('', self.parameter_info)))
    self.assertItemsEqual(
        ['my_b_instance --project=my-project --zone=asia-east1-a',
         'my_b_instance --project=my-project --zone=asia-east1-b',
         'my_b_instance --project=my-project --zone=asia-east1-c',
         'my_b_instance --project=my-project --zone=asia-northeast1-a',
         'my_b_instance --project=my-project --zone=asia-northeast1-b',
         'my_b_instance --project=my-project --zone=asia-northeast1-c',
         'my_b_instance --project=my-project --zone=europe-west1-b',
         'my_b_instance --project=my-project --zone=europe-west1-c',
         'my_b_instance --project=my-project --zone=europe-west1-d',
         'my_b_instance --project=my-project --zone=us-central1-a',
         'my_b_instance --project=my-project --zone=us-central1-b',
         'my_b_instance --project=my-project --zone=us-central1-c',
         'my_b_instance --project=my-project --zone=us-central1-f',
         'my_b_instance --project=my-project --zone=us-central2-a',
         'my_b_instance --project=my-project --zone=us-east1-b',
         'my_b_instance --project=my-project --zone=us-east1-c',
         'my_b_instance --project=my-project --zone=us-east1-d',
         'my_b_instance --project=my-project --zone=us-west1-a',
         'my_b_instance --project=my-project --zone=us-west1-b',
         'my_b_instance --project=my_x_project --zone=asia-east1-a',
         'my_b_instance --project=my_x_project --zone=asia-east1-b',
         'my_b_instance --project=my_x_project --zone=asia-east1-c',
         'my_b_instance --project=my_x_project --zone=asia-northeast1-a',
         'my_b_instance --project=my_x_project --zone=asia-northeast1-b',
         'my_b_instance --project=my_x_project --zone=asia-northeast1-c',
         'my_b_instance --project=my_x_project --zone=europe-west1-b',
         'my_b_instance --project=my_x_project --zone=europe-west1-c',
         'my_b_instance --project=my_x_project --zone=europe-west1-d',
         'my_b_instance --project=my_x_project --zone=us-central1-a',
         'my_b_instance --project=my_x_project --zone=us-central1-b',
         'my_b_instance --project=my_x_project --zone=us-central1-c',
         'my_b_instance --project=my_x_project --zone=us-central1-f',
         'my_b_instance --project=my_x_project --zone=us-central2-a',
         'my_b_instance --project=my_x_project --zone=us-east1-b',
         'my_b_instance --project=my_x_project --zone=us-east1-c',
         'my_b_instance --project=my_x_project --zone=us-east1-d',
         'my_b_instance --project=my_x_project --zone=us-west1-a',
         'my_b_instance --project=my_x_project --zone=us-west1-b',
         'my_b_instance --project=their_y_project --zone=asia-east1-a',
         'my_b_instance --project=their_y_project --zone=asia-east1-b',
         'my_b_instance --project=their_y_project --zone=asia-east1-c',
         'my_b_instance --project=their_y_project --zone=asia-northeast1-a',
         'my_b_instance --project=their_y_project --zone=asia-northeast1-b',
         'my_b_instance --project=their_y_project --zone=asia-northeast1-c',
         'my_b_instance --project=their_y_project --zone=europe-west1-b',
         'my_b_instance --project=their_y_project --zone=europe-west1-c',
         'my_b_instance --project=their_y_project --zone=europe-west1-d',
         'my_b_instance --project=their_y_project --zone=us-central1-a',
         'my_b_instance --project=their_y_project --zone=us-central1-b',
         'my_b_instance --project=their_y_project --zone=us-central1-c',
         'my_b_instance --project=their_y_project --zone=us-central1-f',
         'my_b_instance --project=their_y_project --zone=us-central2-a',
         'my_b_instance --project=their_y_project --zone=us-east1-b',
         'my_b_instance --project=their_y_project --zone=us-east1-c',
         'my_b_instance --project=their_y_project --zone=us-east1-d',
         'my_b_instance --project=their_y_project --zone=us-west1-a',
         'my_b_instance --project=their_y_project --zone=us-west1-b',
         'my_b_instance --project=your_z_project --zone=asia-east1-a',
         'my_b_instance --project=your_z_project --zone=asia-east1-b',
         'my_b_instance --project=your_z_project --zone=asia-east1-c',
         'my_b_instance --project=your_z_project --zone=asia-northeast1-a',
         'my_b_instance --project=your_z_project --zone=asia-northeast1-b',
         'my_b_instance --project=your_z_project --zone=asia-northeast1-c',
         'my_b_instance --project=your_z_project --zone=europe-west1-b',
         'my_b_instance --project=your_z_project --zone=europe-west1-c',
         'my_b_instance --project=your_z_project --zone=europe-west1-d',
         'my_b_instance --project=your_z_project --zone=us-central1-a',
         'my_b_instance --project=your_z_project --zone=us-central1-b',
         'my_b_instance --project=your_z_project --zone=us-central1-c',
         'my_b_instance --project=your_z_project --zone=us-central1-f',
         'my_b_instance --project=your_z_project --zone=us-central2-a',
         'my_b_instance --project=your_z_project --zone=us-east1-b',
         'my_b_instance --project=your_z_project --zone=us-east1-c',
         'my_b_instance --project=your_z_project --zone=us-east1-d',
         'my_b_instance --project=your_z_project --zone=us-west1-a',
         'my_b_instance --project=your_z_project --zone=us-west1-b'],
        completer.Complete('my_b', self.parameter_info))

  def testInstancesCompleterWithArgs(self):
    completer = self.Completer(completers.InstancesCompleter,
                               args={'project': 'my_x_project',
                                     'zone': 'us-east1-b'},
                               command_resources=_COMMAND_RESOURCES)
    self.assertItemsEqual(
        ['my_b_instance'],
        completer.Complete('my_b', self.parameter_info))
    self.assertItemsEqual(
        ['my_a_instance'],
        completer.Complete('my_a', self.parameter_info))

  def testSearchInstancesCompleter(self):
    completer = self.Completer(completers.SearchInstancesCompleter,
                               args={'--project': None,
                                     '--zone': None},
                               search_resources=_SEARCH_RESOURCES)
    self.assertEqual(
        228,
        len(completer.Complete('', self.parameter_info)))
    self.assertItemsEqual(
        ['my_b_instance --project=my-project --zone=asia-east1-a',
         'my_b_instance --project=my-project --zone=asia-east1-b',
         'my_b_instance --project=my-project --zone=asia-east1-c',
         'my_b_instance --project=my-project --zone=asia-northeast1-a',
         'my_b_instance --project=my-project --zone=asia-northeast1-b',
         'my_b_instance --project=my-project --zone=asia-northeast1-c',
         'my_b_instance --project=my-project --zone=europe-west1-b',
         'my_b_instance --project=my-project --zone=europe-west1-c',
         'my_b_instance --project=my-project --zone=europe-west1-d',
         'my_b_instance --project=my-project --zone=us-central1-a',
         'my_b_instance --project=my-project --zone=us-central1-b',
         'my_b_instance --project=my-project --zone=us-central1-c',
         'my_b_instance --project=my-project --zone=us-central1-f',
         'my_b_instance --project=my-project --zone=us-central2-a',
         'my_b_instance --project=my-project --zone=us-east1-b',
         'my_b_instance --project=my-project --zone=us-east1-c',
         'my_b_instance --project=my-project --zone=us-east1-d',
         'my_b_instance --project=my-project --zone=us-west1-a',
         'my_b_instance --project=my-project --zone=us-west1-b',
         'my_b_instance --project=my_x_project --zone=asia-east1-a',
         'my_b_instance --project=my_x_project --zone=asia-east1-b',
         'my_b_instance --project=my_x_project --zone=asia-east1-c',
         'my_b_instance --project=my_x_project --zone=asia-northeast1-a',
         'my_b_instance --project=my_x_project --zone=asia-northeast1-b',
         'my_b_instance --project=my_x_project --zone=asia-northeast1-c',
         'my_b_instance --project=my_x_project --zone=europe-west1-b',
         'my_b_instance --project=my_x_project --zone=europe-west1-c',
         'my_b_instance --project=my_x_project --zone=europe-west1-d',
         'my_b_instance --project=my_x_project --zone=us-central1-a',
         'my_b_instance --project=my_x_project --zone=us-central1-b',
         'my_b_instance --project=my_x_project --zone=us-central1-c',
         'my_b_instance --project=my_x_project --zone=us-central1-f',
         'my_b_instance --project=my_x_project --zone=us-central2-a',
         'my_b_instance --project=my_x_project --zone=us-east1-b',
         'my_b_instance --project=my_x_project --zone=us-east1-c',
         'my_b_instance --project=my_x_project --zone=us-east1-d',
         'my_b_instance --project=my_x_project --zone=us-west1-a',
         'my_b_instance --project=my_x_project --zone=us-west1-b',
         'my_b_instance --project=their_y_project --zone=asia-east1-a',
         'my_b_instance --project=their_y_project --zone=asia-east1-b',
         'my_b_instance --project=their_y_project --zone=asia-east1-c',
         'my_b_instance --project=their_y_project --zone=asia-northeast1-a',
         'my_b_instance --project=their_y_project --zone=asia-northeast1-b',
         'my_b_instance --project=their_y_project --zone=asia-northeast1-c',
         'my_b_instance --project=their_y_project --zone=europe-west1-b',
         'my_b_instance --project=their_y_project --zone=europe-west1-c',
         'my_b_instance --project=their_y_project --zone=europe-west1-d',
         'my_b_instance --project=their_y_project --zone=us-central1-a',
         'my_b_instance --project=their_y_project --zone=us-central1-b',
         'my_b_instance --project=their_y_project --zone=us-central1-c',
         'my_b_instance --project=their_y_project --zone=us-central1-f',
         'my_b_instance --project=their_y_project --zone=us-central2-a',
         'my_b_instance --project=their_y_project --zone=us-east1-b',
         'my_b_instance --project=their_y_project --zone=us-east1-c',
         'my_b_instance --project=their_y_project --zone=us-east1-d',
         'my_b_instance --project=their_y_project --zone=us-west1-a',
         'my_b_instance --project=their_y_project --zone=us-west1-b',
         'my_b_instance --project=your_z_project --zone=asia-east1-a',
         'my_b_instance --project=your_z_project --zone=asia-east1-b',
         'my_b_instance --project=your_z_project --zone=asia-east1-c',
         'my_b_instance --project=your_z_project --zone=asia-northeast1-a',
         'my_b_instance --project=your_z_project --zone=asia-northeast1-b',
         'my_b_instance --project=your_z_project --zone=asia-northeast1-c',
         'my_b_instance --project=your_z_project --zone=europe-west1-b',
         'my_b_instance --project=your_z_project --zone=europe-west1-c',
         'my_b_instance --project=your_z_project --zone=europe-west1-d',
         'my_b_instance --project=your_z_project --zone=us-central1-a',
         'my_b_instance --project=your_z_project --zone=us-central1-b',
         'my_b_instance --project=your_z_project --zone=us-central1-c',
         'my_b_instance --project=your_z_project --zone=us-central1-f',
         'my_b_instance --project=your_z_project --zone=us-central2-a',
         'my_b_instance --project=your_z_project --zone=us-east1-b',
         'my_b_instance --project=your_z_project --zone=us-east1-c',
         'my_b_instance --project=your_z_project --zone=us-east1-d',
         'my_b_instance --project=your_z_project --zone=us-west1-a',
         'my_b_instance --project=your_z_project --zone=us-west1-b'],
        completer.Complete('my_b', self.parameter_info))

  def testSearchInstancesCompleterWithArgs(self):
    completer = self.Completer(completers.SearchInstancesCompleter,
                               args={'project': 'my_x_project',
                                     'zone': 'us-east1-b'},
                               search_resources=_SEARCH_RESOURCES)
    self.assertItemsEqual(
        ['my_b_instance'],
        completer.Complete('my_b', self.parameter_info))
    self.assertItemsEqual(
        ['my_a_instance'],
        completer.Complete('my_a', self.parameter_info))


class ComputeGRICompleterTest(completer_test_base.GRICompleterBase):

  def testHealthChecksCompleter(self):
    completer = self.Completer(completers.HealthChecksCompleter,
                               command_resources=_COMMAND_RESOURCES)
    self.assertEqual(
        5,
        len(completer.Complete('', self.parameter_info)))
    self.assertItemsEqual(
        [
            'health-check-http-1:my-project',
            'health-check-http-2:my-project',
            'health-check-https:my-project',
            'health-check-ssl:my-project',
            'health-check-tcp:my-project',
        ],
        completer.Complete('', self.parameter_info))
    self.assertItemsEqual(
        ['health-check-http-2:my-project'],
        completer.Complete('*-2', self.parameter_info))

  def testHttpHealthChecksCompleter(self):
    completer = self.Completer(completers.HttpHealthChecksCompleter,
                               command_resources=_COMMAND_RESOURCES)
    self.assertEqual(
        2,
        len(completer.Complete('', self.parameter_info)))
    self.assertItemsEqual(
        [
            'health-check-1:my-project',
            'health-check-2:my-project',
        ],
        completer.Complete('', self.parameter_info))
    self.assertItemsEqual(
        ['health-check-2:my-project'],
        completer.Complete('*-2', self.parameter_info))

  def testHttpsHealthChecksCompleter(self):
    completer = self.Completer(completers.HttpsHealthChecksCompleter,
                               command_resources=_COMMAND_RESOURCES)
    self.assertEqual(
        2,
        len(completer.Complete('', self.parameter_info)))
    self.assertItemsEqual(
        [
            'https-health-check-1:my-project',
            'https-health-check-2:my-project',
        ],
        completer.Complete('', self.parameter_info))
    self.assertItemsEqual(
        ['https-health-check-2:my-project'],
        completer.Complete('*-2', self.parameter_info))

  def testInstanceTemplatesCompleter(self):
    completer = self.Completer(completers.InstanceTemplatesCompleter,
                               command_resources=_COMMAND_RESOURCES)
    self.assertEqual(
        3,
        len(completer.Complete('', self.parameter_info)))
    self.assertItemsEqual(
        [
            'instance-template-1:my-project',
            'instance-template-2:my-project',
            'instance-template-3:my-project',
        ],
        completer.Complete('', self.parameter_info))
    self.assertItemsEqual(
        ['instance-template-2:my-project'],
        completer.Complete('*-2', self.parameter_info))

  def testInstancesCompleter(self):
    completer = self.Completer(completers.InstancesCompleter,
                               command_resources=_COMMAND_RESOURCES)
    self.assertEqual(
        228,
        len(completer.Complete('', self.parameter_info)))
    self.assertItemsEqual(
        ['my_b_instance:asia-east1-b:your_z_project',
         'my_b_instance:asia-northeast1-b:your_z_project',
         'my_b_instance:europe-west1-b:your_z_project',
         'my_b_instance:us-central1-b:your_z_project',
         'my_b_instance:us-east1-b:your_z_project',
         'my_b_instance:us-west1-b:your_z_project'],
        completer.Complete('my_b:*b:*_z_*', self.parameter_info))

  def testInstancesCompleterWithArgs(self):
    completer = self.Completer(completers.InstancesCompleter,
                               args={'project': 'my_x_project',
                                     'zone': 'us-east1-b'},
                               command_resources=_COMMAND_RESOURCES)
    self.assertItemsEqual(
        ['my_b_instance:asia-east1-b:your_z_project',
         'my_b_instance:asia-northeast1-b:your_z_project',
         'my_b_instance:europe-west1-b:your_z_project',
         'my_b_instance:us-central1-b:your_z_project',
         'my_b_instance:us-east1-b:your_z_project',
         'my_b_instance:us-west1-b:your_z_project'],
        completer.Complete('my_b:*b:*_z_*', self.parameter_info))
    self.assertItemsEqual(
        ['my_a_instance'],
        completer.Complete('my_a', self.parameter_info))
    self.assertItemsEqual(
        ['my_a_instance:europe-west1-d',
         'my_a_instance:us-east1-d'],
        completer.Complete('my_a:*d', self.parameter_info))
    self.assertItemsEqual(
        ['my_a_instance:us-east1-b:your_z_project'],
        completer.Complete('my_a:*:your_z', self.parameter_info))
    self.assertItemsEqual(
        [],
        completer.Complete('my_a:*:my_y', self.parameter_info))

  def testInstancesCompleterWithArgs2(self):
    completer = self.Completer(completers.InstancesCompleter,
                               args={'project': 'your_z_project',
                                     'zone': 'us-east1-b'},
                               command_resources=_COMMAND_RESOURCES)
    self.assertItemsEqual(
        ['my_b_instance:asia-east1-b',
         'my_b_instance:asia-northeast1-b',
         'my_b_instance:europe-west1-b',
         'my_b_instance:us-central1-b',
         'my_b_instance',
         'my_b_instance:us-west1-b'],
        completer.Complete('my_b:*b:*_z_*', self.parameter_info))
    self.assertItemsEqual(
        ['my_a_instance'],
        completer.Complete('my_a', self.parameter_info))
    self.assertItemsEqual(
        ['my_a_instance:europe-west1-d',
         'my_a_instance:us-east1-d'],
        completer.Complete('my_a:*d', self.parameter_info))
    self.assertItemsEqual(
        ['my_a_instance'],
        completer.Complete('my_a:*:your_z', self.parameter_info))
    self.assertItemsEqual(
        [],
        completer.Complete('my_a:*:my_y', self.parameter_info))

  def testSearchHealthChecksCompleter(self):
    completer = self.Completer(completers.SearchHealthChecksCompleter,
                               search_resources=_SEARCH_RESOURCES)
    self.assertEqual(
        5,
        len(completer.Complete('', self.parameter_info)))
    self.assertItemsEqual(
        [
            'health-check-http-1:my-project',
            'health-check-http-2:my-project',
            'health-check-https:my-project',
            'health-check-ssl:my-project',
            'health-check-tcp:my-project',
        ],
        completer.Complete('', self.parameter_info))
    self.assertItemsEqual(
        ['health-check-http-2:my-project'],
        completer.Complete('*-2', self.parameter_info))

  def testSearchHttpHealthChecksCompleter(self):
    completer = self.Completer(completers.SearchHttpHealthChecksCompleter,
                               search_resources=_SEARCH_RESOURCES)
    self.assertEqual(
        2,
        len(completer.Complete('', self.parameter_info)))
    self.assertItemsEqual(
        [
            'health-check-1:my-project',
            'health-check-2:my-project',
        ],
        completer.Complete('', self.parameter_info))
    self.assertItemsEqual(
        ['health-check-2:my-project'],
        completer.Complete('*-2', self.parameter_info))

  def testSearchHttpsHealthChecksCompleter(self):
    completer = self.Completer(completers.SearchHttpsHealthChecksCompleter,
                               search_resources=_SEARCH_RESOURCES)
    self.assertEqual(
        2,
        len(completer.Complete('', self.parameter_info)))
    self.assertItemsEqual(
        [
            'https-health-check-1:my-project',
            'https-health-check-2:my-project',
        ],
        completer.Complete('', self.parameter_info))
    self.assertItemsEqual(
        ['https-health-check-2:my-project'],
        completer.Complete('*-2', self.parameter_info))

  def testSearchInstanceTemplatesCompleter(self):
    completer = self.Completer(completers.SearchInstanceTemplatesCompleter,
                               search_resources=_SEARCH_RESOURCES)
    self.assertEqual(
        3,
        len(completer.Complete('', self.parameter_info)))
    self.assertItemsEqual(
        [
            'instance-template-1:my-project',
            'instance-template-2:my-project',
            'instance-template-3:my-project',
        ],
        completer.Complete('', self.parameter_info))
    self.assertItemsEqual(
        ['instance-template-2:my-project'],
        completer.Complete('*-2', self.parameter_info))

  def testSearchInstancesCompleter(self):
    completer = self.Completer(completers.SearchInstancesCompleter,
                               search_resources=_SEARCH_RESOURCES)
    self.assertEqual(
        228,
        len(completer.Complete('', self.parameter_info)))
    self.assertItemsEqual(
        ['my_b_instance:asia-east1-b:your_z_project',
         'my_b_instance:asia-northeast1-b:your_z_project',
         'my_b_instance:europe-west1-b:your_z_project',
         'my_b_instance:us-central1-b:your_z_project',
         'my_b_instance:us-east1-b:your_z_project',
         'my_b_instance:us-west1-b:your_z_project'],
        completer.Complete('my_b:*b:*_z_*', self.parameter_info))

  def testSearchInstancesCompleterWithArgs(self):
    completer = self.Completer(completers.SearchInstancesCompleter,
                               args={'project': 'my_x_project',
                                     'zone': 'us-east1-b'},
                               search_resources=_SEARCH_RESOURCES)
    self.assertItemsEqual(
        ['my_b_instance:asia-east1-b:your_z_project',
         'my_b_instance:asia-northeast1-b:your_z_project',
         'my_b_instance:europe-west1-b:your_z_project',
         'my_b_instance:us-central1-b:your_z_project',
         'my_b_instance:us-east1-b:your_z_project',
         'my_b_instance:us-west1-b:your_z_project'],
        completer.Complete('my_b:*b:*_z_*', self.parameter_info))
    self.assertItemsEqual(
        ['my_a_instance'],
        completer.Complete('my_a', self.parameter_info))
    self.assertItemsEqual(
        ['my_a_instance:europe-west1-d',
         'my_a_instance:us-east1-d'],
        completer.Complete('my_a:*d', self.parameter_info))
    self.assertItemsEqual(
        ['my_a_instance:us-east1-b:your_z_project'],
        completer.Complete('my_a:*:your_z', self.parameter_info))
    self.assertItemsEqual(
        [],
        completer.Complete('my_a:*:my_y', self.parameter_info))

  def testSearchInstancesCompleterWithArgs2(self):
    completer = self.Completer(completers.SearchInstancesCompleter,
                               args={'project': 'your_z_project',
                                     'zone': 'us-east1-b'},
                               search_resources=_SEARCH_RESOURCES)
    self.assertItemsEqual(
        ['my_b_instance:asia-east1-b',
         'my_b_instance:asia-northeast1-b',
         'my_b_instance:europe-west1-b',
         'my_b_instance:us-central1-b',
         'my_b_instance',
         'my_b_instance:us-west1-b'],
        completer.Complete('my_b:*b:*_z_*', self.parameter_info))
    self.assertItemsEqual(
        ['my_a_instance'],
        completer.Complete('my_a', self.parameter_info))
    self.assertItemsEqual(
        ['my_a_instance:europe-west1-d',
         'my_a_instance:us-east1-d'],
        completer.Complete('my_a:*d', self.parameter_info))
    self.assertItemsEqual(
        ['my_a_instance'],
        completer.Complete('my_a:*:your_z', self.parameter_info))
    self.assertItemsEqual(
        [],
        completer.Complete('my_a:*:my_y', self.parameter_info))


class ComputeTestCompleterTest(completer_test_base.CompleterBase):

  def testTestCompleter(self):
    os.environ['_ARGCOMPLETE_TEST'] = (
        'collection=compute.zones,list_command=compute zones list --uri')
    completer = self.Completer(completers.TestCompleter)
    del os.environ['_ARGCOMPLETE_TEST']
    self.assertItemsEqual(
        ['asia-east1-a',
         'asia-east1-b',
         'asia-east1-c',
         'asia-northeast1-a',
         'asia-northeast1-b',
         'asia-northeast1-c',
         'europe-west1-b',
         'europe-west1-c',
         'europe-west1-d',
         'us-central1-a',
         'us-central1-b',
         'us-central1-c',
         'us-central1-f',
         'us-central2-a',
         'us-east1-b',
         'us-east1-c',
         'us-east1-d',
         'us-west1-a',
         'us-west1-b'],
        completer.Complete('', self.parameter_info))
    self.assertItemsEqual(
        ['europe-west1-b', 'europe-west1-c', 'europe-west1-d'],
        completer.Complete('e', self.parameter_info))
    self.assertItemsEqual(
        ['europe-west1-b',
         'europe-west1-c',
         'europe-west1-d',
         'us-west1-a',
         'us-west1-b'],
        completer.Complete('*w*', self.parameter_info))
    self.assertItemsEqual(
        [],
        completer.Complete('q', self.parameter_info))

  def testTestCompleterBadTestParameters(self):
    try:
      del os.environ['_ARGCOMPLETE_TEST']
    except KeyError:
      pass
    with self.assertRaises(completers.TestParametersRequired):
      self.Completer(completers.TestCompleter)


if __name__ == '__main__':
  completer_test_base.main()
