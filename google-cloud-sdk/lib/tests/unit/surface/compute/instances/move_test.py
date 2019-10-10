# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Tests for the instances move subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections

from apitools.base.py.testing import mock as api_mock
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.instances import flags
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.api_lib.util import waiter as waiter_test_base


class InstancesMoveTest(sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase,
                        waiter_test_base.Base):

  def Client(self):
    client_class = core_apis.GetClientClass('compute', 'v1')
    return api_mock.Client(client_class,
                           real_client=core_apis.GetClientInstance(
                               'compute', 'v1', no_http=True))

  def ExpectMoveInstance(self, client):
    messages = client.MESSAGES_MODULE
    client.projects.MoveInstance.Expect(
        messages.ComputeProjectsMoveInstanceRequest(
            instanceMoveRequest=messages.InstanceMoveRequest(
                destinationZone=('{0}projects/{1}/zones/europe-west1-d'
                                 .format(client.url, self.Project())),
                targetInstance=(
                    '{0}projects/{1}/zones/us-central1-a/instances/instance-1'
                    .format(client.url, self.Project()))),
            project=self.Project()),
        messages.Operation(
            name='operation-X',
            status=messages.Operation.StatusValueValuesEnum.PENDING,
        )
    )

  def testWithOperationPolling(self):
    with self.Client() as client:
      messages = client.MESSAGES_MODULE

      self.ExpectMoveInstance(client)

      client.globalOperations.Get.Expect(
          messages.ComputeGlobalOperationsGetRequest(
              operation='operation-X',
              project=self.Project()),
          messages.Operation(
              name='operation-X',
              status=messages.Operation.StatusValueValuesEnum.DONE,
          ))
      client.instances.Get.Expect(
          messages.ComputeInstancesGetRequest(
              instance='instance-1',
              project='fake-project',
              zone='europe-west1-d'),
          messages.Instance(name='instance-1'))

      self.Run("""
          compute instances move instance-1
            --zone=us-central1-a
            --destination-zone=europe-west1-d
          """)
    self.AssertOutputEquals('')
    self.AssertErrContains('Moving gce instance instance-1')

  def testAsync(self):
    with self.Client() as client:
      self.ExpectMoveInstance(client)
      result = self.Run("""
          compute instances move
             {0}projects/{1}/zones/us-central1-a/instances/instance-1
            --destination-zone=europe-west1-d
            --async
            --format=disable
          """.format(client.url, self.Project()))

    self.assertEqual('operation-X', result.name)

    self.AssertOutputEquals('')
    self.AssertErrEquals(
        'Update in progress for gce instance instance-1 '
        '[https://compute.googleapis.com/compute/v1/'
        'projects/fake-project/global/operations/operation-X] '
        'Use [gcloud compute operations describe] command to check the status '
        'of this operation.\n')

  def testZonePrompt_NonInteractive(self):
    with self.assertRaisesRegex(
        compute_flags.UnderSpecifiedResourceError,
        r'Underspecified resource \[instance-1\]. '
        r'Specify the \[--zone\] flag.'):
      self.Run("""
          compute instances move instance-1
            --destination-zone=europe-west1-d
            --async
          """)

  def testZonePrompt_Interactive(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    resource = collections.namedtuple('Resource', ['name'])
    self.StartObjectPatch(flags, 'InstanceZoneScopeLister',
                          return_value={compute_scope.ScopeEnum.ZONE:
                                        [resource(name='us-central1-a')]})
    with self.Client() as client:
      self.ExpectMoveInstance(client)
      self.Run("""
          compute instances move instance-1
            --destination-zone=europe-west1-d
            --async
          """)

    self.AssertOutputEquals('')
    self.AssertErrEquals("""\
No zone specified. Using zone [us-central1-a] for instance: [instance-1].\n\
Update in progress for gce instance instance-1 \
[https://compute.googleapis.com/compute/v1/projects/fake-project/global/operations/\
operation-X] Use [gcloud compute operations describe] command to check the \
status of this operation.
""")


if __name__ == '__main__':
  test_case.main()
