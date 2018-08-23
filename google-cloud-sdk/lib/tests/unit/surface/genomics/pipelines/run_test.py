# -*- coding: utf-8 -*- #
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

"""Tests for genomics pipelines run command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from googlecloudsdk.api_lib.genomics import exceptions
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface.genomics import base

PIPELINE_JSON = """{"name": "pipeline1",
 "description": "pipeline1",
 "inputParameters":[
   {"name": "lit","defaultValue":"xyz"},
   {"name":"ref1",
    "description":"xyzref",
    "localCopy":{"disk":"disk1","path":"ref"}
   }
 ],
 "docker": {
   "imageName": "ubuntu",
   "cmd": "echo hello"
  },
  "resources": {
    "minimumRamGb": 1,
    "minimumCpuCores": 1,
    "preemptible":true,
    "zones":["us-central1-c"],
    "disks":[
      {"name":"disk1",
  "type": "PERSISTENT_SSD",
  "sizeGb": 10,
  "autoDelete":true,
  "mountPoint":"/mnt/disk1"
  },
  {"name": "disk2",
  "type": "PERSISTENT_SSD",
  "sizeGb": 20,
  "mountPoint":"/mnt/disk2"
  }]}}"""

PIPELINE_YAML = """
name: pipeline1
description: pipeline1
inputParameters:
- name: lit
  defaultValue: xyz
- name: ref1
  description: xyzref
  localCopy:
    disk: disk1
    path: ref
docker:
  cmd: "echo hello"
  imageName: ubuntu
resources:
  disks:
  - name: disk1
    autoDelete: true
    mountPoint: /mnt/disk1
    sizeGb: 10
    type: PERSISTENT_SSD
  - name: disk2
    mountPoint: /mnt/disk2
    sizeGb: 20
    type: PERSISTENT_SSD
  minimumCpuCores: 1
  minimumRamGb: 1
  preemptible: true
  zones: [us-central1-c]
"""

PIPELINE_YAML_BARE = """
name: pipeline1
docker:
  cmd: "echo hello"
  imageName: ubuntu
"""

INPUT_FROM_FILE = "val3"

messages = apis.GetMessagesModule("genomics", "v1alpha2")

PIPELINE_OBJECT = messages.RunPipelineRequest(
    ephemeralPipeline=messages.Pipeline(
        name="pipeline1",
        description="pipeline1",
        projectId="fake-project",
        inputParameters=[
            messages.PipelineParameter(
                name="lit", defaultValue="xyz"), messages.PipelineParameter(
                    name="ref1",
                    description="xyzref",
                    localCopy=messages.LocalCopy(disk="disk1",
                                                 path="ref"))
        ],
        docker=messages.DockerExecutor(imageName="ubuntu",
                                       cmd="echo hello"),
        resources=messages.PipelineResources(
            minimumCpuCores=1,
            minimumRamGb=1,
            preemptible=True,
            zones=["us-central1-c"],
            disks=[
                messages.Disk(
                    name="disk1",
                    type=messages.Disk.TypeValueValuesEnum.PERSISTENT_SSD,
                    sizeGb=10,
                    autoDelete=True,
                    mountPoint="/mnt/disk1"), messages.Disk(
                        name="disk2",
                        type=messages.Disk.TypeValueValuesEnum.PERSISTENT_SSD,
                        sizeGb=20,
                        mountPoint="/mnt/disk2")
            ])),
    pipelineArgs=messages.RunPipelineArgs(
        projectId="fake-project",
        logging=messages.LoggingOptions(gcsPath="gs://logs"),
        inputs=messages.RunPipelineArgs.InputsValue(additionalProperties=[
            messages.RunPipelineArgs.InputsValue.AdditionalProperty(
                key="ref1", value="val1")
        ]),
        outputs=messages.RunPipelineArgs.OutputsValue(),
        resources=messages.PipelineResources(preemptible=True),
        serviceAccount=messages.ServiceAccount(email="default")))

PIPELINE_OBJECT_WITH_OVERRIDES = messages.RunPipelineRequest(
    ephemeralPipeline=messages.Pipeline(
        name="pipeline1",
        description="pipeline1",
        projectId="fake-project",
        inputParameters=[
            messages.PipelineParameter(
                name="lit", defaultValue="xyz"), messages.PipelineParameter(
                    name="ref1",
                    description="xyzref",
                    localCopy=messages.LocalCopy(disk="disk1",
                                                 path="ref"))
        ],
        docker=messages.DockerExecutor(imageName="ubuntu",
                                       cmd="echo hello"),
        resources=messages.PipelineResources(
            minimumCpuCores=1,
            minimumRamGb=1,
            preemptible=True,
            zones=["us-central1-c"],
            disks=[
                messages.Disk(
                    name="disk1",
                    type=messages.Disk.TypeValueValuesEnum.PERSISTENT_SSD,
                    sizeGb=10,
                    autoDelete=True,
                    mountPoint="/mnt/disk1"), messages.Disk(
                        name="disk2",
                        type=messages.Disk.TypeValueValuesEnum.PERSISTENT_SSD,
                        sizeGb=20,
                        mountPoint="/mnt/disk2")
            ])),
    pipelineArgs=messages.RunPipelineArgs(
        projectId="fake-project",
        logging=messages.LoggingOptions(gcsPath="gs://logs"),
        inputs=messages.RunPipelineArgs.InputsValue(additionalProperties=[
            messages.RunPipelineArgs.InputsValue.AdditionalProperty(
                key="ref1", value="val1"),
            messages.RunPipelineArgs.InputsValue.AdditionalProperty(
                key="ref2", value="val2"),
            messages.RunPipelineArgs.InputsValue.AdditionalProperty(
                key="ref3", value="val3")
        ]),
        outputs=messages.RunPipelineArgs.OutputsValue(),
        labels=messages.RunPipelineArgs.LabelsValue(additionalProperties=[
            messages.RunPipelineArgs.LabelsValue.AdditionalProperty(
                key="label1", value="val1"),
            messages.RunPipelineArgs.LabelsValue.AdditionalProperty(
                key="label2", value="val2"),
            messages.RunPipelineArgs.LabelsValue.AdditionalProperty(
                key="label3", value="val3")
        ]),
        resources=messages.PipelineResources(
            preemptible=True,
            minimumRamGb=30,
            zones=["us-east1-d", "us-east1-c"],
            disks=[
                messages.Disk(name="disk1", sizeGb=80), messages.Disk(
                    name="disk2", sizeGb=90)
            ]),
        serviceAccount=messages.ServiceAccount(email="default")))

PIPELINE_OBJECT_BARE = messages.RunPipelineRequest(
    ephemeralPipeline=messages.Pipeline(
        name="pipeline1",
        projectId="fake-project",
        docker=messages.DockerExecutor(imageName="ubuntu",
                                       cmd="echo hello")),
    pipelineArgs=messages.RunPipelineArgs(
        projectId="fake-project",
        logging=messages.LoggingOptions(gcsPath="gs://logs"),
        inputs=messages.RunPipelineArgs.InputsValue(),
        outputs=messages.RunPipelineArgs.OutputsValue(),
        resources=messages.PipelineResources(preemptible=False),
        serviceAccount=messages.ServiceAccount(email="default")))


class RunTest(base.GenomicsUnitTest):
  """Unit tests for genomics pipelines run command."""

  def testPipelinesRun(self):
    pipeline_path = self.Touch(self.temp_path, contents=PIPELINE_YAML)
    response = messages.Operation(name="operations/ENS123456789")
    self.mocked_client_v1a2.pipelines.Run.Expect(
        request=PIPELINE_OBJECT,
        response=response)
    self.RunGenomics(["pipelines", "run", "--pipeline-file", pipeline_path,
                      "--inputs", "ref1=val1",
                      "--logging", "gs://logs",
                      "--preemptible"])
    self.AssertOutputEquals("")
    self.AssertErrContains("Running [operations/ENS123456789].\n")

  def testPipelinesRunJson(self):
    pipeline_path = self.Touch(self.temp_path, contents=PIPELINE_JSON)
    response = messages.Operation(name="operations/ENS123456789")
    self.mocked_client_v1a2.pipelines.Run.Expect(
        request=PIPELINE_OBJECT,
        response=response)
    self.RunGenomics(["pipelines", "run", "--pipeline-file", pipeline_path,
                      "--inputs", "ref1=val1",
                      "--logging", "gs://logs",
                      "--preemptible"])
    self.AssertOutputEquals("")
    self.AssertErrContains("Running [operations/ENS123456789].")

  def testPipelinesRunWithOverrides(self):
    pipeline_path = self.Touch(self.temp_path, contents=PIPELINE_JSON)
    response = messages.Operation(name="operations/ENS123456789")
    self.mocked_client_v1a2.pipelines.Run.Expect(
        request=PIPELINE_OBJECT_WITH_OVERRIDES,
        response=response)
    self.RunGenomics(["pipelines", "run",
                      "--pipeline-file", pipeline_path,
                      "--memory", "30",
                      "--inputs", "ref1=val1,ref2=val2",
                      "--inputs", "ref3=val3",
                      "--labels", "label1=val1,label2=val2",
                      "--labels", "label3=val3",
                      "--disk-size", "disk1:80,disk2:90",
                      "--logging", "gs://logs",
                      "--preemptible",
                      "--zones", "us-east1-d,us-east1-c"])
    self.AssertOutputEquals("")
    self.AssertErrContains("Running [operations/ENS123456789].\n")

  def testPipelinesRunWithDefaultZone(self):
    properties.VALUES.compute.zone.Set("us-east1-d")

    pipeline_path = self.Touch(self.temp_path, contents=PIPELINE_YAML_BARE)
    response = messages.Operation(name="operations/ENS123456789")
    expected_request = copy.deepcopy(PIPELINE_OBJECT_BARE)
    expected_request.pipelineArgs.resources.zones = ["us-east1-d"]

    self.mocked_client_v1a2.pipelines.Run.Expect(
        request=expected_request,
        response=response)
    self.RunGenomics(["pipelines", "run", "--pipeline-file", pipeline_path,
                      "--logging", "gs://logs"])
    self.AssertOutputEquals("")
    self.AssertErrContains("Running [operations/ENS123456789].\n")

  def testPipelinesRunWithInputsFromFile(self):
    pipeline_path = self.Touch(self.temp_path, contents=PIPELINE_JSON)
    input_val_path = self.Touch(self.temp_path, contents=INPUT_FROM_FILE)
    response = messages.Operation(name="operations/ENS123456789")
    self.mocked_client_v1a2.pipelines.Run.Expect(
        request=PIPELINE_OBJECT_WITH_OVERRIDES,
        response=response)
    self.RunGenomics(["pipelines", "run",
                      "--pipeline-file", pipeline_path,
                      "--memory", "30",
                      "--inputs", "ref1=val1,ref2=val2",
                      "--inputs-from-file", "ref3=%s" % input_val_path,
                      "--labels", "label1=val1,label2=val2",
                      "--labels", "label3=val3",
                      "--disk-size", "disk1:80,disk2:90",
                      "--logging", "gs://logs",
                      "--preemptible",
                      "--zones", "us-east1-d,us-east1-c"])
    self.AssertOutputEquals("")
    self.AssertErrContains("Running [operations/ENS123456789].\n")

  def testPipelinesRunFileNotFound(self):
    filename = "nonexistent"
    with self.assertRaises(files.Error):
      self.RunGenomics(["pipelines", "run", "--pipeline-file", filename])

  def testPipelinesRunBadJson(self):
    pipeline_path = self.Touch(self.temp_path, contents="malformed")
    with self.assertRaises(exceptions.GenomicsInputFileError):
      self.RunGenomics(["pipelines", "run", "--pipeline-file", pipeline_path])

  def testPipelinesRunDuplicateInputs(self):
    pipeline_path = self.Touch(self.temp_path, contents=PIPELINE_JSON)
    with self.assertRaisesRegex(
        cli_test_base.MockArgumentError,
        'argument --inputs: "ref3" cannot be specified multiple times; '
        'received: val3a, val3b'):
      self.RunGenomics(["pipelines", "run",
                        "--pipeline-file", pipeline_path,
                        "--memory", "30",
                        "--inputs", "ref1=val1,ref2=val2",
                        "--inputs", "ref3=val3a",
                        "--inputs", "ref3=val3b",
                        "--disk-size", "disk1:80,disk2:90",
                        "--logging", "gs://logs",
                        "--preemptible",
                        "--zones", "us-east1-d,us-east1-c"])

  def testPipelinesRunInputsOverlapInputsFromFile(self):
    pipeline_path = self.Touch(self.temp_path, contents=PIPELINE_JSON)
    with self.assertRaisesRegex(
        exceptions.GenomicsError,
        "--inputs and --inputs-from-file may not specify overlapping "
        "values: ref3"):
      self.RunGenomics(["pipelines", "run",
                        "--pipeline-file", pipeline_path,
                        "--memory", "30",
                        "--inputs", "ref1=val1,ref2=val2",
                        "--inputs", "ref3=val3a",
                        "--inputs-from-file", "ref3=my_file.txt",
                        "--disk-size", "disk1:80,disk2:90",
                        "--logging", "gs://logs",
                        "--preemptible",
                        "--zones", "us-east1-d,us-east1-c"])

  def testPipelinesRunDuplicateLabels(self):
    pipeline_path = self.Touch(self.temp_path, contents=PIPELINE_JSON)
    with self.assertRaisesRegex(
        cli_test_base.MockArgumentError,
        'argument --labels: "label1" cannot be specified multiple times; '
        'received: val1a, val1b'):
      self.RunGenomics(["pipelines", "run",
                        "--pipeline-file", pipeline_path,
                        "--labels", "label1=val1a",
                        "--labels", "label1=val1b",
                        "--logging", "gs://logs",
                        "--preemptible",
                        "--zones", "us-east1-d,us-east1-c"])

if __name__ == "__main__":
  test_case.main()
