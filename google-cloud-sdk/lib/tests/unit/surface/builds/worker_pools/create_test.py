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
"""Tests that exercise workerpool creation."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
from apitools.base.protorpclite import protojson
from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import exceptions as c_exceptions
from googlecloudsdk.core import properties
from tests.lib import e2e_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.cli_test_base import MockArgumentError


# TODO(b/29358031): Move WithMockHttp somewhere more appropriate for unit tests.
class CreateTest(e2e_base.WithMockHttp, sdk_test_base.WithFakeAuth,
                 sdk_test_base.WithTempCWD):

  def SetUp(self):
    self.StartPatch('time.sleep')  # To speed up tests with polling

    self.mocked_cloudbuild_v1alpha1 = mock.Client(
        core_apis.GetClientClass('cloudbuild', 'v1alpha1'))
    self.mocked_cloudbuild_v1alpha1.Mock()
    self.addCleanup(self.mocked_cloudbuild_v1alpha1.Unmock)
    self.msg = core_apis.GetMessagesModule('cloudbuild', 'v1alpha1')

    self.project_id = 'my-project'
    properties.VALUES.core.project.Set(self.project_id)

    self.frozen_time_str = '2018-11-12T00:10:00+00:00'

  def _Run(self, args):
    self.Run(args)

  def testCreateFromFile(self):
    wp_in = self.msg.WorkerPool()
    wp_in.workerConfig = self.msg.WorkerConfig()
    wp_in.name = 'fake_name'

    wp_out = copy.deepcopy(wp_in)
    wp_out.createTime = self.frozen_time_str
    wp_out.status = self.msg.WorkerPool.StatusValueValuesEnum.RUNNING

    self.mocked_cloudbuild_v1alpha1.projects_workerPools.Create.Expect(
        self.msg.CloudbuildProjectsWorkerPoolsCreateRequest(
            parent=u'projects/{}'.format(self.project_id), workerPool=wp_in),
        response=wp_out)

    wp_path = self.Touch(
        '.', 'workerpool.yaml', contents=protojson.encode_message(wp_in))

    self._Run([
        'alpha', 'builds', 'worker-pools', 'create', '--config-from-file',
        wp_path
    ])
    self.AssertOutputContains(
        """\
NAME CREATE_TIME STATUS
fake_name {} RUNNING
""".format(self.frozen_time_str),
        normalize_space=True)

  def testCreateFromFileWithFlags(self):
    wp_in = self.msg.WorkerPool()
    wp_in.workerConfig = self.msg.WorkerConfig()
    wp_in.name = 'fake_name'

    wp_out = copy.deepcopy(wp_in)
    wp_out.createTime = self.frozen_time_str
    wp_out.status = self.msg.WorkerPool.StatusValueValuesEnum.RUNNING

    wp_path = self.Touch(
        '.', 'workerpool.yaml', contents=protojson.encode_message(wp_in))
    with self.assertRaises(MockArgumentError):
      self._Run([
          'alpha', 'builds', 'worker-pools', 'create', wp_in.name,
          '--config-from-file', wp_path
      ])

  def testCreateWithNoFlags(self):
    with self.assertRaises(MockArgumentError):
      self._Run(['alpha', 'builds', 'worker-pools', 'create'])

  def testCreateWithNameOnly(self):
    wp_in = self.msg.WorkerPool()
    wp_in.workerConfig = self.msg.WorkerConfig()
    wp_in.name = 'fake_name'

    wp_out = copy.deepcopy(wp_in)
    wp_out.createTime = self.frozen_time_str
    wp_out.status = self.msg.WorkerPool.StatusValueValuesEnum.RUNNING

    self.mocked_cloudbuild_v1alpha1.projects_workerPools.Create.Expect(
        self.msg.CloudbuildProjectsWorkerPoolsCreateRequest(
            parent=u'projects/{}'.format(self.project_id), workerPool=wp_in),
        response=wp_out)

    self._Run(['alpha', 'builds', 'worker-pools', 'create', wp_in.name])
    self.AssertOutputContains(
        """\
NAME CREATE_TIME STATUS
fake_name {} RUNNING
""".format(self.frozen_time_str),
        normalize_space=True)

  def testCreateWithWorkerCount(self):
    wp_in = self.msg.WorkerPool()
    wp_in.workerConfig = self.msg.WorkerConfig()
    wp_in.name = 'fake_name'
    wp_in.workerCount = 3

    wp_out = copy.deepcopy(wp_in)
    wp_out.createTime = self.frozen_time_str
    wp_out.status = self.msg.WorkerPool.StatusValueValuesEnum.RUNNING

    self.mocked_cloudbuild_v1alpha1.projects_workerPools.Create.Expect(
        self.msg.CloudbuildProjectsWorkerPoolsCreateRequest(
            parent=u'projects/{}'.format(self.project_id), workerPool=wp_in),
        response=wp_out)

    self._Run([
        'alpha', 'builds', 'worker-pools', 'create', wp_in.name,
        '--worker-count',
        str(wp_in.workerCount)
    ])
    self.AssertOutputContains(
        """\
NAME CREATE_TIME STATUS
fake_name {} RUNNING
""".format(self.frozen_time_str),
        normalize_space=True)

  def testCreateWithRegions(self):
    wp_in = self.msg.WorkerPool()
    wp_in.workerConfig = self.msg.WorkerConfig()
    wp_in.name = 'fake_name'

    wp_in.regions = [
        self.msg.WorkerPool.RegionsValueListEntryValuesEnum.us_central1,
        self.msg.WorkerPool.RegionsValueListEntryValuesEnum.us_east1
    ]

    wp_out = copy.deepcopy(wp_in)
    wp_out.createTime = self.frozen_time_str
    wp_out.status = self.msg.WorkerPool.StatusValueValuesEnum.RUNNING

    self.mocked_cloudbuild_v1alpha1.projects_workerPools.Create.Expect(
        self.msg.CloudbuildProjectsWorkerPoolsCreateRequest(
            parent=u'projects/{}'.format(self.project_id), workerPool=wp_in),
        response=wp_out)

    self._Run([
        'alpha', 'builds', 'worker-pools', 'create', wp_in.name, '--regions',
        'us-central1,us-east1'
    ])
    self.AssertOutputContains(
        """\
NAME CREATE_TIME STATUS
fake_name {} RUNNING
""".format(self.frozen_time_str),
        normalize_space=True)

  def testCreateWithMachineType(self):
    wp_in = self.msg.WorkerPool()
    wp_in.workerConfig = self.msg.WorkerConfig()
    wp_in.name = 'fake_name'
    wp_in.workerConfig.machineType = 'fakemachine'

    wp_out = copy.deepcopy(wp_in)
    wp_out.createTime = self.frozen_time_str
    wp_out.status = self.msg.WorkerPool.StatusValueValuesEnum.RUNNING

    self.mocked_cloudbuild_v1alpha1.projects_workerPools.Create.Expect(
        self.msg.CloudbuildProjectsWorkerPoolsCreateRequest(
            parent='projects/{}'.format(self.project_id), workerPool=wp_in),
        response=wp_out)

    self._Run([
        'alpha', 'builds', 'worker-pools', 'create', wp_in.name,
        '--worker-machine-type', wp_in.workerConfig.machineType
    ])
    self.AssertOutputContains(
        """\
NAME CREATE_TIME STATUS
fake_name {} RUNNING
""".format(self.frozen_time_str),
        normalize_space=True)

  def testCreateWithDisk(self):
    wp_in = self.msg.WorkerPool()
    wp_in.workerConfig = self.msg.WorkerConfig()
    wp_in.name = 'fake_name'
    wp_in.workerConfig.diskSizeGb = 123

    wp_out = copy.deepcopy(wp_in)
    wp_out.createTime = self.frozen_time_str
    wp_out.status = self.msg.WorkerPool.StatusValueValuesEnum.RUNNING

    self.mocked_cloudbuild_v1alpha1.projects_workerPools.Create.Expect(
        self.msg.CloudbuildProjectsWorkerPoolsCreateRequest(
            parent='projects/{}'.format(self.project_id), workerPool=wp_in),
        response=wp_out)

    self._Run([
        'alpha', 'builds', 'worker-pools', 'create', wp_in.name,
        '--worker-disk-size',
        str(wp_in.workerConfig.diskSizeGb)
    ])
    self.AssertOutputContains(
        """\
NAME CREATE_TIME STATUS
fake_name {} RUNNING
""".format(self.frozen_time_str),
        normalize_space=True)

  def testCreateWithIncompleteNetwork1(self):
    with self.assertRaises(c_exceptions.RequiredArgumentException):
      self._Run([
          'alpha', 'builds', 'worker-pools', 'create', 'wpname',
          '--worker-network-name', 'networkname'
      ])

  def testCreateWithIncompleteNetwork2(self):
    with self.assertRaises(c_exceptions.RequiredArgumentException):
      self._Run([
          'alpha', 'builds', 'worker-pools', 'create', 'wpname',
          '--worker-network-subnet', 'subnetname'
      ])

  def testCreateWithIncompleteNetwork3(self):
    with self.assertRaises(c_exceptions.RequiredArgumentException):
      self._Run([
          'alpha', 'builds', 'worker-pools', 'create', 'wpname',
          '--worker-network-project', 'projectid'
      ])

  def testCreateWithIncompleteNetwork4(self):
    with self.assertRaises(c_exceptions.RequiredArgumentException):
      self._Run([
          'alpha', 'builds', 'worker-pools', 'create', 'wpname',
          '--worker-network-name', 'networkname', '--worker-network-subnet',
          'subnetname'
      ])

  def testCreateWithIncompleteNetwork5(self):
    with self.assertRaises(c_exceptions.RequiredArgumentException):
      self._Run([
          'alpha', 'builds', 'worker-pools', 'create', 'wpname',
          '--worker-network-name', 'networkname', '--worker-network-project',
          'projectid'
      ])

  def testCreateWithIncompleteNetwork6(self):
    with self.assertRaises(c_exceptions.RequiredArgumentException):
      self._Run([
          'alpha', 'builds', 'worker-pools', 'create', 'wpname',
          '--worker-network-subnet', 'subnetname', '--worker-network-project',
          'projectid'
      ])

  def testCreateWithCompleteNetwork(self):
    wp_in = self.msg.WorkerPool()
    wp_in.workerConfig = self.msg.WorkerConfig()
    wp_in.name = 'fake_name'
    wp_in.workerConfig.network = self.msg.Network()
    wp_in.workerConfig.network.network = 'networkname'
    wp_in.workerConfig.network.subnetwork = 'subnetname'
    wp_in.workerConfig.network.projectId = 'project'

    wp_out = copy.deepcopy(wp_in)
    wp_out.createTime = self.frozen_time_str
    wp_out.status = self.msg.WorkerPool.StatusValueValuesEnum.RUNNING

    self.mocked_cloudbuild_v1alpha1.projects_workerPools.Create.Expect(
        self.msg.CloudbuildProjectsWorkerPoolsCreateRequest(
            parent='projects/{}'.format(self.project_id), workerPool=wp_in),
        response=wp_out)

    self._Run([
        'alpha', 'builds', 'worker-pools', 'create', wp_in.name,
        '--worker-network-name', wp_in.workerConfig.network.network,
        '--worker-network-subnet', wp_in.workerConfig.network.subnetwork,
        '--worker-network-project', wp_in.workerConfig.network.projectId
    ])
    self.AssertOutputContains(
        """\
NAME CREATE_TIME STATUS
fake_name {} RUNNING
""".format(self.frozen_time_str),
        normalize_space=True)

  def testCreateWithTag(self):
    wp_in = self.msg.WorkerPool()
    wp_in.workerConfig = self.msg.WorkerConfig()
    wp_in.name = 'fake_name'
    wp_in.workerConfig.tag = 'faketag'

    wp_out = copy.deepcopy(wp_in)
    wp_out.createTime = self.frozen_time_str
    wp_out.status = self.msg.WorkerPool.StatusValueValuesEnum.RUNNING

    self.mocked_cloudbuild_v1alpha1.projects_workerPools.Create.Expect(
        self.msg.CloudbuildProjectsWorkerPoolsCreateRequest(
            parent='projects/{}'.format(self.project_id), workerPool=wp_in),
        response=wp_out)

    self._Run([
        'alpha', 'builds', 'worker-pools', 'create', wp_in.name, '--worker-tag',
        wp_in.workerConfig.tag
    ])
    self.AssertOutputContains(
        """\
NAME CREATE_TIME STATUS
fake_name {} RUNNING
""".format(self.frozen_time_str),
        normalize_space=True)


if __name__ == '__main__':
  test_case.main()
