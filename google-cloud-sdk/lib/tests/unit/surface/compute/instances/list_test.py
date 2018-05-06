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
"""Tests for the instances list subcommand."""
import sys
import textwrap

from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.command_lib.compute import completers
from googlecloudsdk.core import properties
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import completer_test_data
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources
from tests.lib.surface.compute import utils

mbeta = core_apis.GetMessagesModule('compute', 'beta')


def _DefaultImageOf(api_version):
  return ('https://www.googleapis.com/compute/{ver}/projects/debian-cloud/'
          'global/images/'
          'debian-9-stretch-v20170619').format(ver=api_version)


class InstancesListTest(test_base.BaseTest, completer_test_base.CompleterBase):

  def SetUp(self):
    api_mock = utils.ComputeApiMock('v1').Start()
    self.addCleanup(api_mock.Stop)

    # instances list implementation always uses this implementation
    self.implementation = lister.ZonalParallelLister(
        api_mock.adapter, api_mock.adapter.apitools_client.instances,
        api_mock.resources)

  def testSimpleCase(self):
    self.ExpectListerInvoke(
        scope_set=self.MakeAllScopes(zonal=True),
        result=resource_projector.MakeSerializable(test_resources.INSTANCES_V1),
        with_implementation=self.implementation)
    self.Run("""
        compute instances list --uri
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1/instances/instance-1
            https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1/instances/instance-2
            https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1/instances/instance-3
            """))
    self.AssertErrEquals('')

  def testPositionalArgsWithSimpleNames(self):
    self.ExpectListerInvoke(
        scope_set=self.MakeAllScopes(zonal=True),
        result=resource_projector.MakeSerializable(test_resources.INSTANCES_V1),
        with_implementation=self.implementation)
    self.Run("""
        compute instances list
          instance-1 instance-2
          --uri
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1/instances/instance-1
            https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1/instances/instance-2
            """))

  def testPositionalArgsWithUri(self):
    self.ExpectListerInvoke(
        scope_set=self.MakeAllScopes(zonal=True),
        result=resource_projector.MakeSerializable(test_resources.INSTANCES_V1),
        with_implementation=self.implementation)
    self.Run("""
        compute instances list
          https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1/instances/instance-1
          --uri
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1/instances/instance-1
            """))

  def testPositionalArgsWithUriAndSimpleName(self):
    self.ExpectListerInvoke(
        scope_set=self.MakeAllScopes(zonal=True),
        result=resource_projector.MakeSerializable(test_resources.INSTANCES_V1),
        with_implementation=self.implementation)
    self.Run("""
        compute instances list
          https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1/instances/instance-1
          instance-3
          --uri
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1/instances/instance-1
            https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1/instances/instance-3
            """))

  def testPositionalArgsWithSimpleNamesAndZoneFlag(self):
    self.ExpectListerInvoke(
        scope_set=self.MakeZoneSet(['zone-1']),
        result=resource_projector.MakeSerializable(test_resources.INSTANCES_V1),
        with_implementation=self.implementation)
    self.Run("""
        compute instances list
          instance-1 instance-2
          --zones zone-1
          --uri
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1/instances/instance-1
            https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1/instances/instance-2
            """))

  def testPositionalArgsWithSimpleNameAndUriAndZoneFlag(self):
    self.ExpectListerInvoke(
        scope_set=self.MakeZoneSet(['zone-1']),
        result=resource_projector.MakeSerializable(test_resources.INSTANCES_V1),
        with_implementation=self.implementation)
    self.Run("""
        compute instances list
          instance-1
          https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1/instances/instance-3
          --zones zone-1
          --uri
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1/instances/instance-1
            https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1/instances/instance-3
            """))

  def testNameRegexes(self):
    self.ExpectListerInvoke(
        scope_set=self.MakeAllScopes(zonal=True),
        result=resource_projector.MakeSerializable(test_resources.INSTANCES_V1),
        with_implementation=self.implementation)
    self.Run("""
        compute instances list
          --uri
          --regexp "instance-1|instance-.*"
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1/instances/instance-1
            https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1/instances/instance-2
            https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1/instances/instance-3
            """))

  def testAscendingSortByOfAPIField(self):
    self.ExpectListerInvoke(
        scope_set=self.MakeAllScopes(zonal=True),
        result=resource_projector.MakeSerializable(test_resources.INSTANCES_V1),
        with_implementation=self.implementation)
    self.Run("""
        compute instances list
          --sort-by networkInterfaces[].accessConfigs[].natIP
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME       ZONE   MACHINE_TYPE  PREEMPTIBLE INTERNAL_IP EXTERNAL_IP   STATUS
            instance-2 zone-1 n1-standard-1             10.0.0.2    23.251.133.74 RUNNING
            instance-1 zone-1 n1-standard-1             10.0.0.1    23.251.133.75 RUNNING
            instance-3 zone-1 n1-standard-2             10.0.0.3    23.251.133.76 RUNNING
            """), normalize_space=True)

  def testAscendingSortByOfTableColumn(self):
    self.ExpectListerInvoke(
        scope_set=self.MakeAllScopes(zonal=True),
        result=resource_projector.MakeSerializable(test_resources.INSTANCES_V1),
        with_implementation=self.implementation)
    self.Run("""
        compute instances list
          --sort-by EXTERNAL_IP
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME       ZONE   MACHINE_TYPE  PREEMPTIBLE INTERNAL_IP EXTERNAL_IP   STATUS
            instance-2 zone-1 n1-standard-1             10.0.0.2    23.251.133.74 RUNNING
            instance-1 zone-1 n1-standard-1             10.0.0.1    23.251.133.75 RUNNING
            instance-3 zone-1 n1-standard-2             10.0.0.3    23.251.133.76 RUNNING
            """), normalize_space=True)

  def testDescendingSortByOfAPIField(self):
    self.ExpectListerInvoke(
        scope_set=self.MakeAllScopes(zonal=True),
        result=resource_projector.MakeSerializable(test_resources.INSTANCES_V1),
        with_implementation=self.implementation)
    self.Run("""
        compute instances list
          --sort-by ~name
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME       ZONE   MACHINE_TYPE  PREEMPTIBLE INTERNAL_IP EXTERNAL_IP    STATUS
            instance-3 zone-1 n1-standard-2             10.0.0.3    23.251.133.76  RUNNING
            instance-2 zone-1 n1-standard-1             10.0.0.2    23.251.133.74  RUNNING
            instance-1 zone-1 n1-standard-1             10.0.0.1    23.251.133.75  RUNNING
            """), normalize_space=True)

  def testDescendingSortByOfTableColumn(self):
    self.ExpectListerInvoke(
        scope_set=self.MakeAllScopes(zonal=True),
        result=resource_projector.MakeSerializable(test_resources.INSTANCES_V1),
        with_implementation=self.implementation)
    self.Run("""
        compute instances list
          --sort-by ~EXTERNAL_IP
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME       ZONE   MACHINE_TYPE  PREEMPTIBLE INTERNAL_IP EXTERNAL_IP    STATUS
            instance-3 zone-1 n1-standard-2             10.0.0.3    23.251.133.76  RUNNING
            instance-1 zone-1 n1-standard-1             10.0.0.1    23.251.133.75  RUNNING
            instance-2 zone-1 n1-standard-1             10.0.0.2    23.251.133.74  RUNNING
            """), normalize_space=True)

  def testLimit(self):
    self.ExpectListerInvoke(
        scope_set=self.MakeAllScopes(zonal=True),
        max_results=1,
        result=resource_projector.MakeSerializable(test_resources.INSTANCES_V1),
        with_implementation=self.implementation)
    self.Run("""
        compute instances list --uri --limit 1
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1/instances/instance-1
            """))

  def testLimitWithZero(self):
    with self.AssertRaisesArgumentErrorRegexp(
        r'--limit: Value must be greater than or equal to 1; received: 0'):
      self.Run("""
          compute instances list --limit 0
          """)

  def testLimitWithNegativeValue(self):
    with self.AssertRaisesArgumentErrorRegexp(
        r'--limit: Value must be greater than or equal to 1; received: -10'):
      self.Run("""
          compute instances list --limit -10
          """)

  def testLimitWithVeryLargeValue(self):
    with self.AssertRaisesArgumentErrorRegexp(
        r'--limit: Value must be less than or equal to '
        r'{0}; received: 10000000000000000000000'.format(sys.maxsize)):
      self.Run("""
          compute instances list --uri --limit 10000000000000000000000
          """)

  def testWithOneZone(self):
    self.ExpectListerInvoke(
        scope_set=self.MakeZoneSet(['zone-1']),
        result=resource_projector.MakeSerializable(test_resources.INSTANCES_V1),
        with_implementation=self.implementation)
    self.Run("""
        compute instances list --uri --zones zone-1
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1/instances/instance-1
            https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1/instances/instance-2
            https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1/instances/instance-3
            """))

  def testWithManyZones(self):
    self.ExpectListerInvoke(
        scope_set=self.MakeZoneSet(['zone-1', 'zone-2', 'zone-3']),
        result=resource_projector.MakeSerializable(test_resources.INSTANCES_V1),
        with_implementation=self.implementation)
    self.Run("""
        compute instances list --uri --zones zone-1,zone-2,zone-3
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1/instances/instance-1
            https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1/instances/instance-2
            https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1/instances/instance-3
            """))

  def testZoneCannotBeEmpty(self):
    with self.AssertRaisesArgumentErrorRegexp(
        '--zones: expected one argument'):
      self.Run("""
          compute instances list --zones
          """)

  def testTableOutput(self):
    self.ExpectListerInvoke(
        scope_set=self.MakeAllScopes(zonal=True),
        result=resource_projector.MakeSerializable(test_resources.INSTANCES_V1),
        with_implementation=self.implementation)
    self.Run("""
        compute instances list
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME       ZONE   MACHINE_TYPE  PREEMPTIBLE INTERNAL_IP EXTERNAL_IP   STATUS
            instance-1 zone-1 n1-standard-1             10.0.0.1    23.251.133.75 RUNNING
            instance-2 zone-1 n1-standard-1             10.0.0.2    23.251.133.74 RUNNING
            instance-3 zone-1 n1-standard-2             10.0.0.3    23.251.133.76 RUNNING
            """), normalize_space=True)

  # The following is a list of preemptible VM instances, suitable for use as a
  # return value of GetZonalResources().
  PREEMPTIBLE_INSTANCES = [
      # One preemptible VM instance
      mbeta.Instance(
          machineType=(
              'https://www.googleapis.com/compute/beta/projects/my-project/'
              'zones/zone-1/machineTypes/n1-standard-1'),
          name='preemptible-1',
          networkInterfaces=[
              mbeta.NetworkInterface(
                  networkIP='10.0.0.1',
                  accessConfigs=[
                      mbeta.AccessConfig(natIP='23.251.133.75'),
                  ],
              ),
          ],
          scheduling=mbeta.Scheduling(
              automaticRestart=False,
              onHostMaintenance=mbeta.Scheduling.
              OnHostMaintenanceValueValuesEnum.TERMINATE,
              preemptible=True),
          status=mbeta.Instance.StatusValueValuesEnum.RUNNING,
          selfLink=('https://www.googleapis.com/compute/beta/projects/'
                    'my-project/zones/zone-1/instances/preemptible-1'),
          zone=('https://www.googleapis.com/compute/beta/projects/'
                'my-project/zones/zone-1')),
      # One non-preemptible (premium) VM instance
      mbeta.Instance(
          machineType=(
              'https://www.googleapis.com/compute/beta/projects/my-project/'
              'zones/zone-1/machineTypes/n1-standard-1'),
          name='premium-1',
          networkInterfaces=[
              mbeta.NetworkInterface(
                  networkIP='10.0.0.2',
                  accessConfigs=[
                      mbeta.AccessConfig(natIP='23.251.133.76'),
                  ],
              ),
          ],
          scheduling=mbeta.Scheduling(
              automaticRestart=True,
              onHostMaintenance=mbeta.Scheduling.
              OnHostMaintenanceValueValuesEnum.MIGRATE,
              preemptible=False),
          status=mbeta.Instance.StatusValueValuesEnum.RUNNING,
          selfLink=('https://www.googleapis.com/compute/beta/projects/'
                    'my-project/zones/zone-1/instances/premium-1'),
          zone=('https://www.googleapis.com/compute/beta/projects/'
                'my-project/zones/zone-1')),
  ]

  def testPreemptibleVms(self):
    self.ExpectListerInvoke(
        scope_set=self.MakeAllScopes(zonal=True),
        result=resource_projector.MakeSerializable(self.PREEMPTIBLE_INSTANCES),
        with_implementation=self.implementation)
    self.Run("""
        compute instances list
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME          ZONE   MACHINE_TYPE  PREEMPTIBLE INTERNAL_IP EXTERNAL_IP   STATUS
            preemptible-1 zone-1 n1-standard-1 true        10.0.0.1    23.251.133.75 RUNNING
            premium-1     zone-1 n1-standard-1             10.0.0.2    23.251.133.76 RUNNING
            """), normalize_space=True)

  def testRegexpWithParentheses(self):
    self.ExpectListerInvoke(
        scope_set=self.MakeAllScopes(['my-project'], zonal=True),
        result=resource_projector.MakeSerializable(test_resources.INSTANCES_V1))

    result = list(
        self.Run('compute instances list '
                 '--regexp "instance(-.)?" '
                 '--format=disable'))

    self.assertListEqual(
        result,
        resource_projector.MakeSerializable(test_resources.INSTANCES_V1))

  def testInstancesCompleter(self):
    self.ExpectListerInvoke(
        scope_set=self.MakeAllScopes(zonal=True),
        result=resource_projector.MakeSerializable(test_resources.INSTANCES_V1),
        with_implementation=self.implementation)
    self.RunCompleter(
        completers.InstancesCompleter,
        expected_command=[
            'compute',
            'instances',
            'list',
            '--uri',
            '--quiet',
            '--format=disable',
        ],
        expected_completions=[
            'instance-1',
            'instance-2',
            'instance-3',
        ],
        cli=self.cli,
    )

  def testInstancesCompleterIgnoreZoneProperty(self):
    prev_default = properties.VALUES.compute.zone.Get(required=False)
    properties.VALUES.compute.zone.Set('non-matching-zone')
    self.ExpectListerInvoke(
        scope_set=self.MakeAllScopes(zonal=True),
        result=resource_projector.MakeSerializable(test_resources.INSTANCES_V1),
        with_implementation=self.implementation)
    self.RunCompleter(
        completers.InstancesCompleter,
        prefix='*-1',
        expected_command=[
            'compute',
            'instances',
            'list',
            '--uri',
            '--quiet',
            '--format=disable',
            '--project=my-project',
        ],
        expected_completions=[
            'instance-1 --zone=zone-1',
        ],
        cli=self.cli,
        args={
            '--project': 'my-project',
            '--zone': None,
        },
    )
    properties.VALUES.compute.zone.Set(prev_default)

  def testInstancesCompleterZoneFlag(self):
    self.ExpectListerInvoke(
        scope_set=self.MakeAllScopes(zonal=True),
        result=resource_projector.MakeSerializable(test_resources.INSTANCES_V1),
        with_implementation=self.implementation)
    self.RunCompleter(
        completers.InstancesCompleter,
        expected_command=[
            'compute',
            'instances',
            'list',
            '--uri',
            '--quiet',
            '--format=disable',
            '--project=my-project',
        ],
        expected_completions=[
            'instance-1',
            'instance-2',
            'instance-3',
        ],
        cli=self.cli,
        args={
            '--project': 'my-project',
            '--zone': 'zone-1',
        },
    )

  def testSearchInstancesCompleter(self):
    self.RunCompleter(
        completers.SearchInstancesCompleter,
        prefix='my_a',
        search_resources={
            'compute.instances': completer_test_data.INSTANCE_URIS,
        },
        expected_completions=['my_a_instance'] * 76,
        cli=self.cli,
    )

  def testSearchInstancesCompleterIgnoreZoneProperty(self):
    prev_default = properties.VALUES.compute.zone.Get(required=False)
    properties.VALUES.compute.zone.Set('non-matching-zone')
    self.RunCompleter(
        completers.SearchInstancesCompleter,
        search_resources={
            'compute.instances': completer_test_data.INSTANCE_URIS,
        },
        prefix='my_a',
        expected_completions=[
            'my_a_instance --zone=asia-east1-a',
            'my_a_instance --zone=asia-east1-b',
            'my_a_instance --zone=asia-east1-c',
            'my_a_instance --zone=asia-northeast1-a',
            'my_a_instance --zone=asia-northeast1-b',
            'my_a_instance --zone=asia-northeast1-c',
            'my_a_instance --zone=europe-west1-b',
            'my_a_instance --zone=europe-west1-c',
            'my_a_instance --zone=europe-west1-d',
            'my_a_instance --zone=us-central1-a',
            'my_a_instance --zone=us-central1-b',
            'my_a_instance --zone=us-central1-c',
            'my_a_instance --zone=us-central1-f',
            'my_a_instance --zone=us-central2-a',
            'my_a_instance --zone=us-east1-b',
            'my_a_instance --zone=us-east1-c',
            'my_a_instance --zone=us-east1-d',
            'my_a_instance --zone=us-west1-a',
            'my_a_instance --zone=us-west1-b',
        ],
        args={
            '--project': 'my_x_project',
            '--zone': None,
        },
    )
    properties.VALUES.compute.zone.Set(prev_default)

  def testSearchInstancesCompleterZoneFlag(self):
    self.RunCompleter(
        completers.SearchInstancesCompleter,
        search_resources={
            'compute.instances': completer_test_data.INSTANCE_URIS,
        },
        expected_completions=[
            'my_a_instance',
            'my_b_instance',
            'my_c_instance',
        ],
        cli=self.cli,
        args={
            '--project': 'my_x_project',
            '--zone': 'us-east1-c',
        },
    )


if __name__ == '__main__':
  test_case.main()
