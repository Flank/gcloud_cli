# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Tests that exercise workerpool config parsing."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import io

from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.api_lib.cloudbuild import workerpool_config
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core.util import files
from tests.lib import sdk_test_base
from tests.lib import test_case


class WorkerpoolConfigTest(sdk_test_base.WithTempCWD):

  def SetUp(self):
    self.messages = core_apis.GetMessagesModule('cloudbuild', 'v1alpha1')
    self._regions = self.messages.WorkerPool.RegionsValueListEntryValuesEnum

  def testNoFile(self):
    with self.assertRaises(files.MissingFileError):
      workerpool_config.LoadWorkerpoolConfigFromPath('not-here.json',
                                                     self.messages)

  def testBadEncoding(self):
    self.Touch('.', 'garbage.garbage', """this file is neither json nor yaml""")
    with self.assertRaisesRegex(cloudbuild_util.ParserError,
                                'Could not parse as a dictionary'):
      workerpool_config.LoadWorkerpoolConfigFromPath('garbage.garbage',
                                                     self.messages)

  def testLoadJson(self):
    self.Touch(
        '.', 'basic.json', """\
{
  "name": "wpname",
  "project_id": "argo-workerpool-test",
  "worker_count": 2,
  "regions": ["us-central1"],
  "worker_config": {
    "network": {
      "project_id": "argo-workerpool-test",
      "network": "argo-workerpool-test-network",
      "subnetwork": "argo-workerpool-test-subnet",
    },
  },
}
""")
    wp = workerpool_config.LoadWorkerpoolConfigFromPath('basic.json',
                                                        self.messages)
    self.assertEqual(
        wp,
        self.messages.WorkerPool(
            name='wpname',
            projectId='argo-workerpool-test',
            workerCount=2,
            regions=[self._regions.us_central1],
            workerConfig=self.messages.WorkerConfig(
                network=self.messages.Network(
                    projectId='argo-workerpool-test',
                    network='argo-workerpool-test-network',
                    subnetwork='argo-workerpool-test-subnet'))))

  def testLoadYaml(self):
    self.Touch(
        '.', 'basic.yaml', """\
name: wpname
project_id: argo-workerpool-test
worker_count: 2
regions: [us-central1]
worker_config:
  network:
    project_id: argo-workerpool-test
    network: argo-workerpool-test-network
    subnetwork: argo-workerpool-test-subnet
""")
    wp = workerpool_config.LoadWorkerpoolConfigFromPath('basic.yaml',
                                                        self.messages)
    self.assertEqual(
        wp,
        self.messages.WorkerPool(
            name='wpname',
            projectId='argo-workerpool-test',
            workerCount=2,
            regions=[self._regions.us_central1],
            workerConfig=self.messages.WorkerConfig(
                network=self.messages.Network(
                    projectId='argo-workerpool-test',
                    network='argo-workerpool-test-network',
                    subnetwork='argo-workerpool-test-subnet'))))

  def testYamlSyntaxError(self):
    """Misplaced brace at the end of the document."""
    self.Touch(
        '.', 'error.yaml', """\
name: wpname
project_id: argo-workerpool-test
worker_count: 2
regions: us-central1
worker_config:
  network:
    project_id: argo-workerpool-test
    network: argo-workerpool-test-network
    subnetwork: argo-workerpool-test-subnet
}
""")
    with self.assertRaisesRegex(cloudbuild_util.ParserError, 'error.yaml'):
      workerpool_config.LoadWorkerpoolConfigFromPath('error.yaml',
                                                     self.messages)

  def testYamlUnusedField(self):
    """testYamlUnusedField checks a misindented field."""
    self.Touch(
        '.', 'error.yaml', """\
name: wpname
project_id: argo-workerpool-test
worker_count: 2
regions: ["us-central1"]
worker_config:
network:
  project_id: argo-workerpool-test
  network: argo-workerpool-test-network
  subnetwork: argo-workerpool-test-subnet
""")
    with self.assertRaisesRegex(
        cloudbuild_util.ParseProtoException,
        r'error.yaml as workerpool config: .network: unused'):
      workerpool_config.LoadWorkerpoolConfigFromPath('error.yaml',
                                                     self.messages)

  def testJsonUnusedField(self):
    """testJsonUnusedField checks a misplaced field."""
    self.Touch(
        '.', 'error.json', """\
{
  "name": "wpname",
  "project_id": "argo-workerpool-test",
  "worker_count": 2,
  "regions": ["us-central1"],
  "network": {
    "project_id": "argo-workerpool-test",
    "network": "argo-workerpool-test-network",
    "subnetwork": "argo-workerpool-test-subnet",
  },
}
""")
    with self.assertRaisesRegex(
        cloudbuild_util.ParseProtoException,
        r'error.json as workerpool config: .network: unused'):
      workerpool_config.LoadWorkerpoolConfigFromPath('error.json',
                                                     self.messages)

  def testYamlUnusedNested(self):
    """Only present an error for the highest-level mistake."""
    self.Touch(
        '.', 'error.yaml', """\
name: wpname
project_id: argo-workerpool-test
worker_count: 2
regions: us-central1
worker_config:
  network:
    project_id: argo-workerpool-test
    network: argo-workerpool-test-network
    subnetwork: argo-workerpool-test-subnet
extra:
  data:
    is: "bad"
""")
    with self.assertRaisesRegex(
        cloudbuild_util.ParseProtoException,
        r'error\.yaml as workerpool config: \.extra: unused'):
      workerpool_config.LoadWorkerpoolConfigFromPath('error.yaml',
                                                     self.messages)

  def testYamlMultipleUnused(self):
    """More than one mistake on the same level gets a more interesting error."""
    self.Touch(
        '.', 'error.yaml', """\
name: wpname
project_id: argo-workerpool-test
worker_count: 2
regions: ["us-central1"]
worker_config:
  network:
    project_id: argo-workerpool-test
    network: argo-workerpool-test-network
    subnetwork: argo-workerpool-test-subnet
extra:
  data:
    is: "bad"
nonsense: "bad as well"
""")
    with self.assertRaisesRegex(
        cloudbuild_util.ParseProtoException,
        r'error\.yaml as workerpool config: \.\{extra,nonsense\}: unused'):
      workerpool_config.LoadWorkerpoolConfigFromPath('error.yaml',
                                                     self.messages)

  def testLoadJson_FromStream(self):
    data = io.StringIO(u"""\
{
  "name": "wpname",
  "project_id": "argo-workerpool-test",
  "worker_count": 2,
  "regions": ["us-central1"],
  "worker_config": {
    "network": {
      "project_id": "argo-workerpool-test",
      "network": "argo-workerpool-test-network",
      "subnetwork": "argo-workerpool-test-subnet",
    },
  },
}
""")
    wp = workerpool_config.LoadWorkerpoolConfigFromStream(
        data, self.messages, 'mypath')
    self.assertEqual(
        wp,
        self.messages.WorkerPool(
            name='wpname',
            projectId='argo-workerpool-test',
            workerCount=2,
            regions=[self._regions.us_central1],
            workerConfig=self.messages.WorkerConfig(
                network=self.messages.Network(
                    projectId='argo-workerpool-test',
                    network='argo-workerpool-test-network',
                    subnetwork='argo-workerpool-test-subnet'))))

  def testJsonSyntaxError_FromStream(self):
    """Misplaced brace at the end of the document."""
    data = io.StringIO(u"""\
{
  "name": "wpname",
  "project_id": "argo-workerpool-test",
  "worker_count": 2,
  "regions": ["us-central1"],
  "worker_config": {
    "network": {
      "project_id": "argo-workerpool-test",
      "network": "argo-workerpool-test-network",
      "subnetwork": "argo-workerpool-test-subnet",
    },
  },
}}
""")
    with self.assertRaisesRegex(cloudbuild_util.ParserError, 'parsing mypath'):
      workerpool_config.LoadWorkerpoolConfigFromStream(data, self.messages,
                                                       'mypath')


if __name__ == '__main__':
  test_case.main()
