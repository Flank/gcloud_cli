# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Tests that exercise workerpool patching."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
from apitools.base.protorpclite import protojson
from apitools.base.py import encoding
from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import e2e_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.cli_test_base import MockArgumentError
import six


# TODO(b/29358031): Move WithMockHttp somewhere more appropriate for unit tests.
class UpdateTestBeta(e2e_base.WithMockHttp, sdk_test_base.WithFakeAuth,
                     sdk_test_base.WithTempCWD):

  # Override only this method in subsequent classes for other release tracks.
  def PreSetUp(self):
    self.release_track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    self.api_version = cloudbuild_util.RELEASE_TRACK_TO_API_VERSION[
        self.release_track]
    self.StartPatch('time.sleep')  # To speed up tests with polling
    self.mocked_cloudbuild_client = mock.Client(
        core_apis.GetClientClass('cloudbuild', self.api_version))
    self.mocked_cloudbuild_client.Mock()
    self.addCleanup(self.mocked_cloudbuild_client.Unmock)
    self.msg = core_apis.GetMessagesModule('cloudbuild', self.api_version)

    self.project_id = 'my-project'
    self.workerpool_location = 'my-location'
    properties.VALUES.core.project.Set(self.project_id)

    self.frozen_time_str = '2018-11-12T00:10:00+00:00'

  def _Run(self, args):
    if self.release_track.prefix:
      self.Run([self.release_track.prefix] + args)
    else:
      self.Run(args)

  def testUpdateFromFile(self):
    wp_in = self.msg.WorkerPool()
    wp_in.workerConfig = self.msg.WorkerConfig()
    wp_in.name = 'fake_name'
    update_mask = cloudbuild_util.MessageToFieldPaths(wp_in)

    wp_out = copy.deepcopy(wp_in)
    wp_out.createTime = self.frozen_time_str
    wp_out.state = self.msg.WorkerPool.StateValueValuesEnum.RUNNING

    self.mocked_cloudbuild_client.projects_locations_workerPools.Patch.Expect(
        self.msg.CloudbuildProjectsLocationsWorkerPoolsPatchRequest(
            name='projects/{}/locations/{}/workerPools/{}'.format(
                self.project_id, self.workerpool_location, wp_in.name),
            workerPool=wp_in,
            updateMask=','.join(update_mask)),
        response=self.msg.Operation(
            response=encoding.JsonToMessage(self.msg.Operation.ResponseValue,
                                            encoding.MessageToJson(wp_out))))

    wp_path = self.Touch(
        '.', 'workerpool.yaml', contents=protojson.encode_message(wp_in))

    self._Run([
        'builds',
        'worker-pools',
        'update',
        '--config-from-file',
        wp_path,
        '--region',
        self.workerpool_location,
    ])
    self.AssertOutputContains(
        """\
NAME CREATE_TIME STATE
fake_name {} RUNNING
""".format(self.frozen_time_str),
        normalize_space=True)

  def testUpdateFromFileWithFlags(self):
    wp_in = self.msg.WorkerPool()
    wp_in.workerConfig = self.msg.WorkerConfig()
    wp_in.name = 'fake_name'

    wp_out = copy.deepcopy(wp_in)
    wp_out.createTime = self.frozen_time_str
    wp_out.state = self.msg.WorkerPool.StateValueValuesEnum.RUNNING

    wp_path = self.Touch(
        '.', 'workerpool.yaml', contents=protojson.encode_message(wp_in))
    with self.assertRaises(MockArgumentError):
      self._Run([
          'builds', 'worker-pools', 'update', wp_in.name, '--region',
          self.workerpool_location, '--config-from-file', wp_path
      ])

  def testUpdateWithNoFlags(self):
    with self.assertRaises(MockArgumentError):
      self._Run(['builds', 'worker-pools', 'update'])

  def testUpdateWithNameOnly(self):
    wp_in = self.msg.WorkerPool()
    wp_in.workerConfig = self.msg.WorkerConfig()
    wp_in.name = 'fake_name'
    update_mask = cloudbuild_util.MessageToFieldPaths(wp_in)

    wp_out = copy.deepcopy(wp_in)
    wp_out.createTime = self.frozen_time_str
    wp_out.state = self.msg.WorkerPool.StateValueValuesEnum.RUNNING

    self.mocked_cloudbuild_client.projects_locations_workerPools.Patch.Expect(
        self.msg.CloudbuildProjectsLocationsWorkerPoolsPatchRequest(
            name='projects/{}/locations/{}/workerPools/{}'.format(
                self.project_id, self.workerpool_location, wp_in.name),
            workerPool=wp_in,
            updateMask=','.join(update_mask)),
        response=self.msg.Operation(
            response=encoding.JsonToMessage(self.msg.Operation.ResponseValue,
                                            encoding.MessageToJson(wp_out))))

    self._Run([
        'builds', 'worker-pools', 'update', wp_in.name, '--region',
        self.workerpool_location
    ])
    self.AssertOutputContains(
        """\
NAME CREATE_TIME STATE
fake_name {} RUNNING
""".format(self.frozen_time_str),
        normalize_space=True)

  def testUpdateWithMachineType(self):
    wp_in = self.msg.WorkerPool()
    wp_in.workerConfig = self.msg.WorkerConfig()
    wp_in.name = 'fake_name'
    wp_in.workerConfig.machineType = 'fakemachine'
    update_mask = cloudbuild_util.MessageToFieldPaths(wp_in)

    wp_out = copy.deepcopy(wp_in)
    wp_out.createTime = self.frozen_time_str
    wp_out.state = self.msg.WorkerPool.StateValueValuesEnum.RUNNING

    self.mocked_cloudbuild_client.projects_locations_workerPools.Patch.Expect(
        self.msg.CloudbuildProjectsLocationsWorkerPoolsPatchRequest(
            name='projects/{}/locations/{}/workerPools/{}'.format(
                self.project_id, self.workerpool_location, wp_in.name),
            workerPool=wp_in,
            updateMask=','.join(update_mask)),
        response=self.msg.Operation(
            response=encoding.JsonToMessage(self.msg.Operation.ResponseValue,
                                            encoding.MessageToJson(wp_out))))

    self._Run([
        'builds', 'worker-pools', 'update', wp_in.name, '--region',
        self.workerpool_location, '--worker-machine-type',
        wp_in.workerConfig.machineType
    ])
    self.AssertOutputContains(
        """\
NAME CREATE_TIME STATE
fake_name {} RUNNING
""".format(self.frozen_time_str),
        normalize_space=True)

  def testUpdateWithDisk(self):
    wp_in = self.msg.WorkerPool()
    wp_in.workerConfig = self.msg.WorkerConfig()
    wp_in.name = 'fake_name'
    wp_in.workerConfig.diskSizeGb = 123
    update_mask = cloudbuild_util.MessageToFieldPaths(wp_in)

    wp_out = copy.deepcopy(wp_in)
    wp_out.createTime = self.frozen_time_str
    wp_out.state = self.msg.WorkerPool.StateValueValuesEnum.RUNNING

    self.mocked_cloudbuild_client.projects_locations_workerPools.Patch.Expect(
        self.msg.CloudbuildProjectsLocationsWorkerPoolsPatchRequest(
            name='projects/{}/locations/{}/workerPools/{}'.format(
                self.project_id, self.workerpool_location, wp_in.name),
            workerPool=wp_in,
            updateMask=','.join(update_mask)),
        response=self.msg.Operation(
            response=encoding.JsonToMessage(self.msg.Operation.ResponseValue,
                                            encoding.MessageToJson(wp_out))))

    self._Run([
        'builds', 'worker-pools', 'update', wp_in.name, '--region',
        self.workerpool_location, '--worker-disk-size',
        six.text_type(wp_in.workerConfig.diskSizeGb)
    ])
    self.AssertOutputContains(
        """\
NAME CREATE_TIME STATE
fake_name {} RUNNING
""".format(self.frozen_time_str),
        normalize_space=True)


class UpdateTestAlpha(UpdateTestBeta):

  # Override only this method in subsequent classes for other release tracks.
  def PreSetUp(self):
    self.release_track = calliope_base.ReleaseTrack.ALPHA

  def testUpdateFromFile(self):
    wp_in = self.msg.WorkerPool()
    wp_in.workerConfig = self.msg.WorkerConfig()
    wp_in.name = 'fake_name'
    update_mask = cloudbuild_util.MessageToFieldPaths(wp_in)

    wp_out = copy.deepcopy(wp_in)
    wp_out.createTime = self.frozen_time_str
    wp_out.state = self.msg.WorkerPool.StateValueValuesEnum.RUNNING

    self.mocked_cloudbuild_client.projects_workerPools.Patch.Expect(
        self.msg.CloudbuildProjectsWorkerPoolsPatchRequest(
            name='projects/{}/workerPools/{}'.format(self.project_id,
                                                     wp_in.name),
            workerPool=wp_in,
            updateMask=','.join(update_mask)),
        response=wp_out)

    wp_path = self.Touch(
        '.', 'workerpool.yaml', contents=protojson.encode_message(wp_in))

    self._Run(
        ['builds', 'worker-pools', 'update', '--config-from-file', wp_path])
    self.AssertOutputContains(
        """\
NAME CREATE_TIME STATE
fake_name {} RUNNING
""".format(self.frozen_time_str),
        normalize_space=True)

  def testUpdateFromFileWithFlags(self):
    wp_in = self.msg.WorkerPool()
    wp_in.workerConfig = self.msg.WorkerConfig()
    wp_in.name = 'fake_name'

    wp_out = copy.deepcopy(wp_in)
    wp_out.createTime = self.frozen_time_str
    wp_out.state = self.msg.WorkerPool.StateValueValuesEnum.RUNNING

    wp_path = self.Touch(
        '.', 'workerpool.yaml', contents=protojson.encode_message(wp_in))
    with self.assertRaises(MockArgumentError):
      self._Run([
          'builds', 'worker-pools', 'update', wp_in.name, '--config-from-file',
          wp_path
      ])

  def testUpdateWithNoFlags(self):
    with self.assertRaises(MockArgumentError):
      self._Run(['builds', 'worker-pools', 'update'])

  def testUpdateWithNameOnly(self):
    wp_in = self.msg.WorkerPool()
    wp_in.workerConfig = self.msg.WorkerConfig()
    wp_in.name = 'fake_name'
    update_mask = cloudbuild_util.MessageToFieldPaths(wp_in)

    wp_out = copy.deepcopy(wp_in)
    wp_out.createTime = self.frozen_time_str
    wp_out.state = self.msg.WorkerPool.StateValueValuesEnum.RUNNING

    self.mocked_cloudbuild_client.projects_workerPools.Patch.Expect(
        self.msg.CloudbuildProjectsWorkerPoolsPatchRequest(
            name='projects/{}/workerPools/{}'.format(self.project_id,
                                                     wp_in.name),
            workerPool=wp_in,
            updateMask=','.join(update_mask)),
        response=wp_out)

    self._Run(['builds', 'worker-pools', 'update', wp_in.name])
    self.AssertOutputContains(
        """\
NAME CREATE_TIME STATE
fake_name {} RUNNING
""".format(self.frozen_time_str),
        normalize_space=True)

  def testUpdateWithRegion(self):
    wp_in = self.msg.WorkerPool()
    wp_in.workerConfig = self.msg.WorkerConfig()
    wp_in.name = 'fake_name'
    wp_in.region = 'fake_region'
    update_mask = cloudbuild_util.MessageToFieldPaths(wp_in)

    wp_out = copy.deepcopy(wp_in)
    wp_out.createTime = self.frozen_time_str
    wp_out.state = self.msg.WorkerPool.StateValueValuesEnum.RUNNING

    self.mocked_cloudbuild_client.projects_workerPools.Patch.Expect(
        self.msg.CloudbuildProjectsWorkerPoolsPatchRequest(
            name='projects/{}/workerPools/{}'.format(self.project_id,
                                                     wp_in.name),
            workerPool=wp_in,
            updateMask=','.join(update_mask)),
        response=wp_out)

    self._Run([
        'builds', 'worker-pools', 'update', wp_in.name, '--region=fake_region'
    ])
    self.AssertOutputContains(
        """\
NAME CREATE_TIME STATE
fake_name {} RUNNING
""".format(self.frozen_time_str),
        normalize_space=True)

  def testUpdateWithMachineType(self):
    wp_in = self.msg.WorkerPool()
    wp_in.workerConfig = self.msg.WorkerConfig()
    wp_in.name = 'fake_name'
    wp_in.workerConfig.machineType = 'fakemachine'
    update_mask = cloudbuild_util.MessageToFieldPaths(wp_in)

    wp_out = copy.deepcopy(wp_in)
    wp_out.createTime = self.frozen_time_str
    wp_out.state = self.msg.WorkerPool.StateValueValuesEnum.RUNNING

    self.mocked_cloudbuild_client.projects_workerPools.Patch.Expect(
        self.msg.CloudbuildProjectsWorkerPoolsPatchRequest(
            name='projects/{}/workerPools/{}'.format(self.project_id,
                                                     wp_in.name),
            workerPool=wp_in,
            updateMask=','.join(update_mask)),
        response=wp_out)

    self._Run([
        'builds', 'worker-pools', 'update', wp_in.name, '--worker-machine-type',
        wp_in.workerConfig.machineType
    ])
    self.AssertOutputContains(
        """\
NAME CREATE_TIME STATE
fake_name {} RUNNING
""".format(self.frozen_time_str),
        normalize_space=True)

  def testUpdateWithDisk(self):
    wp_in = self.msg.WorkerPool()
    wp_in.workerConfig = self.msg.WorkerConfig()
    wp_in.name = 'fake_name'
    wp_in.workerConfig.diskSizeGb = 123
    update_mask = cloudbuild_util.MessageToFieldPaths(wp_in)

    wp_out = copy.deepcopy(wp_in)
    wp_out.createTime = self.frozen_time_str
    wp_out.state = self.msg.WorkerPool.StateValueValuesEnum.RUNNING

    self.mocked_cloudbuild_client.projects_workerPools.Patch.Expect(
        self.msg.CloudbuildProjectsWorkerPoolsPatchRequest(
            name='projects/{}/workerPools/{}'.format(self.project_id,
                                                     wp_in.name),
            workerPool=wp_in,
            updateMask=','.join(update_mask)),
        response=wp_out)

    self._Run([
        'builds', 'worker-pools', 'update', wp_in.name, '--worker-disk-size',
        six.text_type(wp_in.workerConfig.diskSizeGb)
    ])
    self.AssertOutputContains(
        """\
NAME CREATE_TIME STATE
fake_name {} RUNNING
""".format(self.frozen_time_str),
        normalize_space=True)


if __name__ == '__main__':
  test_case.main()
