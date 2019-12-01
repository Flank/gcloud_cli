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

"""Tests for life sciences pipelines run command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from googlecloudsdk.api_lib.lifesciences import exceptions
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib.surface.lifesciences import base

messages = apis.GetMessagesModule('lifesciences', 'v2beta')

PIPELINE_JSON = """{
  "actions": [
    {
      "imageUri": "bash",
      "commands": [
        "sleep", "1"
      ],
      "mounts": [
        {
          "disk": "disk1",
          "path": "/disk1",
        }
      ]
    }
  ],
  "resources": {
    "regions": [
      "us-east1",
      "us-central1"
    ],
    "virtualMachine": {
      "machineType": "n1-standard-1",
      "preemptible": true,
      "disks": [
        {
          "name": "disk1",
          "sizeGb": 100,
        }
      ],
      "serviceAccount": {
        "email": "test@google.com",
        "scopes": [
          "https://www.googleapis.com/auth/compute",
        ]
      }
    }
  },
  "environment": {
    "key": "value"
  }
}"""

PIPELINE_OBJECT_SCOPES = [
    'https://www.googleapis.com/auth/compute',
    'https://www.googleapis.com/auth/cloud-platform']

PIPELINE_OBJECT = messages.RunPipelineRequest(
    pipeline=messages.Pipeline(
        actions=[messages.Action(
            imageUri='bash',
            commands=['sleep', '1'],
            mounts=[messages.Mount(
                disk='disk1',
                path='/disk1')])],
        resources=messages.Resources(
            regions=['us-east1', 'us-central1'],
            virtualMachine=messages.VirtualMachine(
                machineType='n1-standard-1',
                preemptible=True,
                disks=[messages.Disk(
                    name='disk1',
                    sizeGb=100)],
                serviceAccount=messages.ServiceAccount(
                    email='test@google.com',
                    scopes=PIPELINE_OBJECT_SCOPES))),
        environment=messages.Pipeline.EnvironmentValue(
            additionalProperties=[
                messages.Pipeline.EnvironmentValue.AdditionalProperty(
                    key='key', value='value')])))

PIPELINE_CLI_OBJECT = messages.RunPipelineRequest(
    pipeline=messages.Pipeline(
        actions=[
            messages.Action(
                imageUri='google/cloud-sdk:slim',
                commands=['/bin/sh', '-c',
                          'gsutil -m -q cp gs://bucket/in ${in}'],
                mounts=[messages.Mount(
                    disk='gcloud-shared',
                    path='/gcloud-shared')]),
            messages.Action(
                imageUri='bash',
                commands=['-c', 'cp ${in} ${out}'],
                entrypoint='bash',
                mounts=[messages.Mount(
                    disk='gcloud-shared',
                    path='/gcloud-shared')]),
            messages.Action(
                imageUri='google/cloud-sdk:slim',
                commands=['/bin/sh', '-c',
                          'gsutil -m -q cp ${out} gs://bucket/out'],
                mounts=[messages.Mount(
                    disk='gcloud-shared',
                    path='/gcloud-shared')]),
            messages.Action(
                imageUri='google/cloud-sdk:slim',
                commands=[
                    '/bin/sh', '-c',
                    'gsutil -m -q cp /google/logs/output gs://bucket/'],
                alwaysRun=True)],
        resources=messages.Resources(
            zones=['us-east1-d'],
            virtualMachine=messages.VirtualMachine(
                machineType='n1-standard-1',
                preemptible=True,
                disks=[messages.Disk(
                    name='gcloud-shared',
                    sizeGb=200)],
                serviceAccount=messages.ServiceAccount(scopes=[
                    'https://www.googleapis.com/auth/cloud-platform']))),
        environment=messages.Pipeline.EnvironmentValue(
            additionalProperties=[
                messages.Pipeline.EnvironmentValue.AdditionalProperty(
                    key='in', value='/gcloud-shared/input0'),
                messages.Pipeline.EnvironmentValue.AdditionalProperty(
                    key='out', value='/gcloud-shared/output0')])))


PIPELINE_MINIMAL_OBJECT = messages.RunPipelineRequest(
    pipeline=messages.Pipeline(
        actions=[
            messages.Action(
                imageUri='bash',
                commands=['sleep', '1'])],
        resources=messages.Resources(
            virtualMachine=messages.VirtualMachine(
                machineType='n1-standard-1',
                serviceAccount=messages.ServiceAccount(scopes=[
                    'https://www.googleapis.com/auth/cloud-platform']))),
        environment=messages.Pipeline.EnvironmentValue(
            additionalProperties=[])))

PIPELINE_MINIMAL_JSON = """{
  "actions": [
    {
      "imageUri": "bash",
      "commands": [
        "sleep", "1"
      ]
    }
  ],
}"""

PIPELINE_INPUT_OBJECT = messages.RunPipelineRequest(
    pipeline=messages.Pipeline(
        actions=[
            messages.Action(
                imageUri='bash',
                commands=['sleep', '1'],
                mounts=[messages.Mount(
                    disk='gcloud-shared',
                    path='/gcloud-shared')])],
        resources=messages.Resources(
            virtualMachine=messages.VirtualMachine(
                machineType='n1-standard-1',
                disks=[messages.Disk(
                    name='gcloud-shared')],
                serviceAccount=messages.ServiceAccount(scopes=[
                    'https://www.googleapis.com/auth/cloud-platform']))),
        environment=messages.Pipeline.EnvironmentValue(
            additionalProperties=[
                messages.Pipeline.EnvironmentValue.AdditionalProperty(
                    key='key', value='value')])))


class RunTest(base.LifeSciencesUnitTest):
  """Unit tests for life sciences pipelines run command."""

  def _runFileTest(self, request, pipeline_file=None, command_line=None):
    response = messages.Operation(name='operations/123456789')
    request_wrapper = messages.LifesciencesProjectsLocationsPipelinesRunRequest(
        parent='projects/fake-project/locations/us-central1',
        runPipelineRequest=request)
    self.mocked_client.projects_locations_pipelines.Run.Expect(
        request=request_wrapper,
        response=response)

    cmds = ['pipelines', 'run']
    if command_line:
      cmds += command_line
    if pipeline_file:
      pipeline_path = self.Touch(self.temp_path, contents=pipeline_file)
      cmds += ['--pipeline-file', pipeline_path]

    self.RunLifeSciences(cmds)
    self.AssertOutputEquals('')
    self.AssertErrContains('Running [operations/123456789].\n')

  def testWorkflowsRunPipeline(self):
    self._runFileTest(PIPELINE_OBJECT, PIPELINE_JSON)

  def testWorkflowsRunPipeline_Minimal(self):
    self._runFileTest(PIPELINE_MINIMAL_OBJECT, PIPELINE_MINIMAL_JSON)

  def testWorkflowsRunPipeline_Regions(self):
    request = copy.deepcopy(PIPELINE_MINIMAL_OBJECT)
    request.pipeline.resources.regions = ['us-central1']
    self._runFileTest(request, PIPELINE_MINIMAL_JSON,
                      ['--regions', 'us-central1'])

  def testWorkflowsRunPipeline_DefaultRegions(self):
    properties.VALUES.compute.region.Set('us-central1')
    request = copy.deepcopy(PIPELINE_MINIMAL_OBJECT)
    request.pipeline.resources.regions = ['us-central1']
    self._runFileTest(request, PIPELINE_MINIMAL_JSON)

  def testWorkflowsRunPipeline_DefaultZones(self):
    properties.VALUES.compute.zone.Set('us-east1-d')
    request = copy.deepcopy(PIPELINE_MINIMAL_OBJECT)
    request.pipeline.resources.zones = ['us-east1-d']
    self._runFileTest(request, PIPELINE_MINIMAL_JSON)

  def testWorkflowsRunPipeline_ServiceAccount(self):
    request = copy.deepcopy(PIPELINE_MINIMAL_OBJECT)
    (request.pipeline.resources.virtualMachine
     .serviceAccount) = self.messages.ServiceAccount(
         email='test@google.com',
         scopes=[
             'https://www.googleapis.com/auth/compute',
             'https://www.googleapis.com/auth/cloud-platform'])

    self._runFileTest(request, PIPELINE_MINIMAL_JSON, [
        '--service-account-email', 'test@google.com',
        '--service-account-scopes', 'https://www.googleapis.com/auth/compute'])

  def testWorkflowsRunPipeline_NetworkAndSubnetwork(self):
    request = copy.deepcopy(PIPELINE_MINIMAL_OBJECT)
    request.pipeline.resources.virtualMachine.network = (
        self.messages.Network(
            network='test-network-name',
            subnetwork='test-subnetwork-name'))
    self._runFileTest(request, PIPELINE_MINIMAL_JSON, [
        '--network', 'test-network-name',
        '--subnetwork', 'test-subnetwork-name'])

  def testWorkflowsRunPipeline_NetworkOrSubnetwork(self):
    request = copy.deepcopy(PIPELINE_MINIMAL_OBJECT)
    request.pipeline.resources.virtualMachine.network = (
        self.messages.Network(network='test-network-name'))
    self._runFileTest(request, PIPELINE_MINIMAL_JSON, [
        '--network', 'test-network-name'])

    request = copy.deepcopy(PIPELINE_MINIMAL_OBJECT)
    request.pipeline.resources.virtualMachine.network = (
        self.messages.Network(subnetwork='test-subnetwork-name'))
    self._runFileTest(request, PIPELINE_MINIMAL_JSON, [
        '--subnetwork', 'test-subnetwork-name'])

  def testWorkflowsRunPipeline_BootDiskSize(self):
    request = copy.deepcopy(PIPELINE_MINIMAL_OBJECT)
    request.pipeline.resources.virtualMachine.bootDiskSizeGb = 20
    self._runFileTest(request, PIPELINE_MINIMAL_JSON, [
        '--boot-disk-size', '20'])

  def testWorkflowsRunPipeline_Logging(self):
    request = copy.deepcopy(PIPELINE_MINIMAL_OBJECT)
    request.pipeline.actions.append(messages.Action(
        imageUri='google/cloud-sdk:slim',
        commands=[
            '/bin/sh', '-c',
            'gsutil -m -q cp /google/logs/output gs://bucket/'],
        alwaysRun=True))
    self._runFileTest(request, PIPELINE_MINIMAL_JSON,
                      ['--logging', 'gs://bucket/'])

  def testWorkflowsRunPipeline_Inputs(self):
    self._runFileTest(PIPELINE_INPUT_OBJECT, PIPELINE_MINIMAL_JSON,
                      ['--inputs', 'key=value'])

  def testWorkflowsRunPipeline_DiskSizeAndInputs(self):
    self._runFileTest(PIPELINE_INPUT_OBJECT, PIPELINE_MINIMAL_JSON,
                      ['--inputs', 'key=value', '--disk-size', 'd1:10'])

  def testWorkflowsRunPipeline_PipelineAndCommand(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.RunLifeSciences(['pipelines', 'run', '--pipeline-file', 'test.json',
                        '--command-line', 'sleep'])

  def testWorkflowsRunPipeline_NoPipelineOrCommand(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.RunLifeSciences(['pipelines', 'run'])

  def testWorkflowsRunPipeline_InvalidDiskSize(self):
    with self.assertRaises(exceptions.LifeSciencesError):
      self.RunLifeSciences(['pipelines', 'run', '--disk-size', '7',
                        '--command-line', 'sleep', '--docker-image', 'bash'])

  def testWorkflowsRunPipeline_CLI(self):
    self._runFileTest(PIPELINE_CLI_OBJECT, command_line=[
        '--docker-image', 'bash', '--command-line', 'cp ${in} ${out}',
        '--inputs', 'in=gs://bucket/in', '--outputs', 'out=gs://bucket/out',
        '--logging', 'gs://bucket/', '--preemptible', '--zones', 'us-east1-d',
        '--disk-size', 'gcloud-shared:200'])

  def testWorkflowsRunPipeline_Set(self):
    self._runFileTest(PIPELINE_OBJECT, PIPELINE_JSON,
                      ['--env-vars', 'key=value'])

