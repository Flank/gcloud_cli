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

"""Tests for genomics pipelines run command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from googlecloudsdk.api_lib.genomics import exceptions
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import properties
from tests.lib.surface.genomics import base

messages = apis.GetMessagesModule('genomics', 'v2alpha1')

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
    "projectId": "fake-project",
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
    'https://www.googleapis.com/auth/devstorage.read_write']

PIPELINE_OBJECT = messages.RunPipelineRequest(
    pipeline=messages.Pipeline(
        actions=[messages.Action(
            imageUri='bash',
            commands=['sleep', '1'],
            mounts=[messages.Mount(
                disk='disk1',
                path='/disk1')])],
        resources=messages.Resources(
            projectId='fake-project',
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
                imageUri='google/cloud-sdk:alpine',
                commands=['/bin/sh', '-c',
                          'gsutil -q cp gs://bucket/in ${in}'],
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
                imageUri='google/cloud-sdk:alpine',
                commands=['/bin/sh', '-c',
                          'gsutil -q cp ${out} gs://bucket/out'],
                mounts=[messages.Mount(
                    disk='gcloud-shared',
                    path='/gcloud-shared')]),
            messages.Action(
                imageUri='google/cloud-sdk:alpine',
                commands=[
                    '/bin/sh', '-c',
                    'gsutil -q cp /google/logs/output gs://bucket/'],
                flags=[
                    messages.Action.FlagsValueListEntryValuesEnum.ALWAYS_RUN])],
        resources=messages.Resources(
            projectId='fake-project',
            zones=['us-east1-d'],
            virtualMachine=messages.VirtualMachine(
                machineType='n1-standard-1',
                preemptible=True,
                disks=[messages.Disk(
                    name='gcloud-shared',
                    sizeGb=200)],
                serviceAccount=messages.ServiceAccount(scopes=[
                    'https://www.googleapis.com/auth/devstorage.read_write']))),
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
            projectId='fake-project',
            virtualMachine=messages.VirtualMachine(
                machineType='n1-standard-1',
                serviceAccount=messages.ServiceAccount(scopes=[
                    'https://www.googleapis.com/auth/devstorage.read_write']))),
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
            projectId='fake-project',
            virtualMachine=messages.VirtualMachine(
                machineType='n1-standard-1',
                disks=[messages.Disk(
                    name='gcloud-shared')],
                serviceAccount=messages.ServiceAccount(scopes=[
                    'https://www.googleapis.com/auth/devstorage.read_write']))),
        environment=messages.Pipeline.EnvironmentValue(
            additionalProperties=[
                messages.Pipeline.EnvironmentValue.AdditionalProperty(
                    key='key', value='value')])))


class RunTest(base.GenomicsUnitTest):
  """Unit tests for genomics pipelines run command."""

  def _runFileTest(self, request, pipeline_file=None, command_line=None):
    response = messages.Operation(name='operations/123456789')
    self.mocked_client_v2.pipelines.Run.Expect(
        request=request,
        response=response)

    cmds = ['pipelines', 'run']
    if command_line:
      cmds += command_line
    if pipeline_file:
      pipeline_path = self.Touch(self.temp_path, contents=pipeline_file)
      cmds += ['--pipeline-file', pipeline_path]

    self.RunGenomics(cmds)
    self.AssertOutputEquals('')
    self.AssertErrContains('Running [operations/123456789].\n')

  def testPipelinesRun(self):
    self._runFileTest(PIPELINE_OBJECT, PIPELINE_JSON)

  def testPipelinesRun_Minimal(self):
    self._runFileTest(PIPELINE_MINIMAL_OBJECT, PIPELINE_MINIMAL_JSON)

  def testPipelinesRun_CustomMachine_Cpus(self):
    request = copy.deepcopy(PIPELINE_MINIMAL_OBJECT)
    request.pipeline.resources.virtualMachine.machineType = 'custom-2-3840'
    self._runFileTest(request, PIPELINE_MINIMAL_JSON, ['--cpus', '2'])

  def testPipelinesRun_CustomMachine_Memory(self):
    request = copy.deepcopy(PIPELINE_MINIMAL_OBJECT)
    request.pipeline.resources.virtualMachine.machineType = 'custom-1-4096'
    self._runFileTest(request, PIPELINE_MINIMAL_JSON, ['--memory', '4.096'])

  def testPipelinesRun_CustomMachine_CpusAndMemory(self):
    request = copy.deepcopy(PIPELINE_MINIMAL_OBJECT)
    request.pipeline.resources.virtualMachine.machineType = 'custom-2-4096'
    self._runFileTest(request, PIPELINE_MINIMAL_JSON,
                      ['--cpus', '2', '--memory', '4.096'])

  def testPipelinesRun_Regions(self):
    request = copy.deepcopy(PIPELINE_MINIMAL_OBJECT)
    request.pipeline.resources.regions = ['us-central1']
    self._runFileTest(request, PIPELINE_MINIMAL_JSON,
                      ['--regions', 'us-central1'])

  def testPipelinesRun_DefaultRegions(self):
    properties.VALUES.compute.region.Set('us-central1')
    request = copy.deepcopy(PIPELINE_MINIMAL_OBJECT)
    request.pipeline.resources.regions = ['us-central1']
    self._runFileTest(request, PIPELINE_MINIMAL_JSON)

  def testPipelinesRun_DefaultZones(self):
    properties.VALUES.compute.zone.Set('us-east1-d')
    request = copy.deepcopy(PIPELINE_MINIMAL_OBJECT)
    request.pipeline.resources.zones = ['us-east1-d']
    self._runFileTest(request, PIPELINE_MINIMAL_JSON)

  def testPipelinesRun_ServiceAccount(self):
    request = copy.deepcopy(PIPELINE_MINIMAL_OBJECT)
    (request.pipeline.resources.virtualMachine
     .serviceAccount) = self.messages_v2.ServiceAccount(
         email='test@google.com',
         scopes=[
             'https://www.googleapis.com/auth/compute',
             'https://www.googleapis.com/auth/devstorage.read_write'])

    self._runFileTest(request, PIPELINE_MINIMAL_JSON, [
        '--service-account-email', 'test@google.com',
        '--service-account-scopes', 'https://www.googleapis.com/auth/compute'])

  def testPipelinesRun_Logging(self):
    request = copy.deepcopy(PIPELINE_MINIMAL_OBJECT)
    request.pipeline.actions.append(messages.Action(
        imageUri='google/cloud-sdk:alpine',
        commands=[
            '/bin/sh', '-c',
            'gsutil -q cp /google/logs/output gs://bucket/'],
        flags=[messages.Action.FlagsValueListEntryValuesEnum.ALWAYS_RUN]))
    self._runFileTest(request, PIPELINE_MINIMAL_JSON,
                      ['--logging', 'gs://bucket/'])

  def testPipelinesRun_Inputs(self):
    self._runFileTest(PIPELINE_INPUT_OBJECT, PIPELINE_MINIMAL_JSON,
                      ['--inputs', 'key=value'])

  def testPipelinesRun_PipelineAndCommand(self):
    with self.assertRaises(exceptions.GenomicsError):
      self.RunGenomics(['pipelines', 'run', '--pipeline-file', 'test.json',
                        '--command-line', 'sleep'])

  def testPipelinesRun_NoPipelineOrCommand(self):
    with self.assertRaises(exceptions.GenomicsError):
      self.RunGenomics(['pipelines', 'run'])

  def testPipelinesRun_InvalidDiskSize(self):
    with self.assertRaises(exceptions.GenomicsError):
      self.RunGenomics(['pipelines', 'run', '--disk-size', '7',
                        '--command-line', 'sleep', '--docker-image', 'bash'])

  def testPipelinesRun_CLI(self):
    self._runFileTest(PIPELINE_CLI_OBJECT, command_line=[
        '--docker-image', 'bash', '--command-line', 'cp ${in} ${out}',
        '--inputs', 'in=gs://bucket/in', '--outputs', 'out=gs://bucket/out',
        '--logging', 'gs://bucket/', '--preemptible', '--zones', 'us-east1-d',
        '--disk-size', 'gcloud-shared:200'])
