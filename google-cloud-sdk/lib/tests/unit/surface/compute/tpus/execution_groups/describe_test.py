# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.exceptions import HttpNotFoundError
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.projects import util as p_util
from googlecloudsdk.core import properties
from tests.lib.surface.compute.tpus.execution_groups import base


NAME = 'testinggcloud'
ZONE = 'central2-a'
PROJECT = 'fake-project'


class DescribeTest(base.TpuUnitTestBase):

  def PreSetUp(self):
    self._SetTrack(calliope_base.ReleaseTrack.ALPHA)
    self._SetApiVersion('v1alpha1')
    self.compute_api_version = 'alpha'

  def SetUp(self):
    self.StartObjectPatch(p_util, 'GetProjectNumber', return_value=12321)
    properties.VALUES.core.user_output_enabled.Set(True)

  def _expectTPUGetCall(self, name, project, zone, node):
    self.mock_tpu_client.projects_locations_nodes.Get.Expect(
        request=self.tpu_messages.TpuProjectsLocationsNodesGetRequest(
            name='projects/{}/locations/{}/nodes/{}'.format(
                project, zone, name)),
        exception=None,
        response=node
        )

  def _expectTPUGetCallWithHttpNotFoundError(self, name, project, zone):
    self.mock_tpu_client.projects_locations_nodes.Get.Expect(
        request=self.tpu_messages.TpuProjectsLocationsNodesGetRequest(
            name='projects/{}/locations/{}/nodes/{}'.format(
                project, zone, name)),
        exception=HttpNotFoundError(None, None, None),
        response=None
        )

  def _expectInstancesGetCall(self, name, project, zone, instance):
    self.mock_instance_client.instances.Get.Expect(
        request=self.instances_messages.ComputeInstancesGetRequest(
            instance=name,
            project=project,
            zone=zone,
            ),
        exception=None,
        response=instance)

  def _expectInstancesGetCallWithHttpNotFoundError(self, name, project, zone):
    self.mock_instance_client.instances.Get.Expect(
        request=self.instances_messages.ComputeInstancesGetRequest(
            instance=name,
            project=project,
            zone=zone
            ),
        exception=HttpNotFoundError(None, None, None),
        response=None
        )

  def _makeDefaultExpectedNode(self):
    return self.tpu_messages.Node(
        name=NAME,
        acceleratorType='fakeAccelType',
        tensorflowVersion='fakeTFVersion',
        serviceAccount='fakeSA',
        createTime='fakeTime',
        state=self.tpu_messages.Node.StateValueValuesEnum.STATE_UNSPECIFIED,
        health=self.tpu_messages.Node.HealthValueValuesEnum.HEALTH_UNSPECIFIED,
        networkEndpoints=[
            self.tpu_messages.NetworkEndpoint(ipAddress='fakeIPAddress')
        ],
        schedulingConfig=self.tpu_messages.SchedulingConfig(preemptible=True)
    )

  def _makeDefaultExpectedInstance(self):
    return self.instances_messages.Instance(
        name=NAME,
        zone=ZONE,
        labels=self.instances_messages.Instance.LabelsValue(
            additionalProperties=[
                self.instances_messages.Instance.LabelsValue.AdditionalProperty(
                    key='ctpu', value=NAME)
            ]),
        creationTimestamp='fakeTime',
        machineType='fakeMachineType',
        networkInterfaces=[self.instances_messages.NetworkInterface(
            networkIP='fakeIP'
            )]
        )

  def testDescribeBasicSuccess(self):
    expected_node = self.tpu_messages.Node(name=NAME)
    expected_instance = self.instances_messages.Instance(
        name=NAME,
        zone=ZONE,
        labels=self.instances_messages.Instance.LabelsValue(
            additionalProperties=[
                self.instances_messages.Instance.LabelsValue.AdditionalProperty(
                    key='ctpu', value=NAME)
            ]))
    self._expectTPUGetCall(NAME, PROJECT, ZONE, expected_node)
    self._expectInstancesGetCall(NAME, PROJECT, ZONE, expected_instance)
    self.Run("""
      compute tpus execution-groups describe {} --zone {}
    """.format(NAME, ZONE))
    self.AssertOutputEquals("""\
    FIELD VALUE
    Compute Engine Instance IP Address: []
    Compute Engine Created:
    Compute Engine Machine Type:
    TPU Accelerator Type:
    TPU IP Address: []
    TPU TF Version:
    TPU Service Account:
    TPU Created:
    TPU State:
    TPU Health:
    TPU Preemptible:
    """, normalize_space=True)

  def testDescribeSuccessFieldsMatch(self):
    self._expectTPUGetCall(NAME, PROJECT, ZONE, self._makeDefaultExpectedNode())
    self._expectInstancesGetCall(
        NAME, PROJECT, ZONE, self._makeDefaultExpectedInstance())
    self.Run("""
      compute tpus execution-groups describe {} --zone {}
    """.format(NAME, ZONE))
    self.AssertOutputEquals("""\
    FIELD VALUE
    Compute Engine Instance IP Address: fakeIP
    Compute Engine Created: fakeTime
    Compute Engine Machine Type: fakeMachineType
    TPU Accelerator Type: fakeAccelType
    TPU IP Address: fakeIPAddress
    TPU TF Version: fakeTFVersion
    TPU Service Account: fakeSA
    TPU Created: fakeTime
    TPU State: STATE_UNSPECIFIED
    TPU Health: HEALTH_UNSPECIFIED
    TPU Preemptible: True
    """, normalize_space=True)

  def testDescribeInstanceFoundNodeNotFound(self):
    self._expectTPUGetCallWithHttpNotFoundError(NAME, PROJECT, ZONE)
    self._expectInstancesGetCall(
        NAME, PROJECT, ZONE, self._makeDefaultExpectedInstance())
    self.Run("""
      compute tpus execution-groups describe {} --zone {}
    """.format(NAME, ZONE))
    self.AssertOutputEquals("""\
    FIELD VALUE
    Compute Engine Instance IP Address: fakeIP
    Compute Engine Created: fakeTime
    Compute Engine Machine Type: fakeMachineType
    TPU Node status: Not Found
    """, normalize_space=True)

  def testDescribeFailsWithInstanceNotFound(self):
    self._expectInstancesGetCallWithHttpNotFoundError(NAME, PROJECT, ZONE)
    self.Run("""
      compute tpus execution-groups describe {} --zone {}
    """.format(NAME, ZONE))
    self.AssertOutputEquals("""\
    FIELD VALUE
    Execution Group Status: Not Found
    """, normalize_space=True)

  def testDescribeFailsWithIncorrectInstanceLabel(self):
    expected_instance = self._makeDefaultExpectedInstance()
    expected_instance.labels = None
    self._expectInstancesGetCall(NAME, PROJECT, ZONE, expected_instance)
    self.Run("""
      compute tpus execution-groups describe {} --zone {}
    """.format(NAME, ZONE))
    self.AssertOutputEquals(
        """\
    FIELD VALUE
    Execution Group Status: Not Found
    """, normalize_space=True)

