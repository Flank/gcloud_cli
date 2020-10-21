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
"""Unit tests for the Serverless deploy command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.api_lib.run import service
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.builds import submit_util
from googlecloudsdk.command_lib.run import config_changes
from tests.lib.surface.run import base
import mock


class ServerlessDeployFromSourceTestAlpha(base.ServerlessSurfaceBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def SetUp(self):
    self.image = 'gcr.io/thing/stuff'
    self.service_name = 'my-service'
    self.StartObjectPatch(os.path, 'isdir', return_value=True)
    self.service = service.Service.New(self.mock_serverless_client,
                                       self.Project())
    self.service.domain = 'https://foo-bar.baz'
    self.service.status.latestReadyRevisionName = 'rev.1'
    self.service.status_traffic.SetPercent('rev.1', 100)
    self.service.spec_traffic.SetPercent('rev.1', 100)
    self.operations.GetService.return_value = self.service
    self.operations.ReleaseService.return_value = self.service
    self.app = mock.NonCallableMock()
    self.StartObjectPatch(config_changes, 'ImageChange', return_value=self.app)
    self.launch_stage_changes = mock.NonCallableMock()
    self.StartObjectPatch(
        config_changes,
        'SetLaunchStageAnnotationChange',
        return_value=self.launch_stage_changes)
    self.build_messages = core_apis.GetMessagesModule('cloudbuild', 'v1')
    self.build_config = mock.NonCallableMock()
    self.create_build_config_mock = self.StartObjectPatch(
        submit_util, 'CreateBuildConfigAlpha', return_value=self.build_config)

  def _SetServiceName(self, name):
    self.service.name = name

  def _AssertSuccessMessage(self, serv, build_type):
    self.AssertErrContains('Building using {build_type} and deploying'.format(
        build_type=build_type))
    self.AssertErrContains('to Cloud Run')
    self.AssertErrContains(
        'Service [{serv}] revision [{rev}] has been deployed '
        'and is serving 100 percent of traffic.\nService URL: {url}'.format(
            serv=serv, rev='rev.1', url='https://foo-bar.baz'))

  def testDeployFromSourceWithDockerfile(self):
    source_path = self.Resource('tests', 'unit', 'surface', 'run', 'testdata',
                                'hello_dockerfile')
    self._SetServiceName(self.service_name)
    self.Run('run deploy {service_name} --image={image} --source {source_path}'
             .format(
                 service_name=self.service_name,
                 image=self.image,
                 source_path=source_path))
    self.create_build_config_mock.assert_called_once_with(
        self.image, False, self.build_messages, None, None, True, False,
        source_path, None, None, None, None, None, None, None)
    self.operations.ReleaseService.assert_called_once_with(
        self._ServiceRef(self.service_name),
        [self.app, self.launch_stage_changes],
        mock.ANY,
        asyn=False,
        allow_unauthenticated=None,
        prefetch=self.service,
        build_config=self.build_config,
        build_messages=self.build_messages)
    self._AssertSuccessMessage(self.service_name, 'Dockerfile')

  def testDeployFromSourceWithDockerfileNoImage(self):
    source_path = self.Resource('tests', 'unit', 'surface', 'run', 'testdata',
                                'hello_dockerfile')
    self._SetServiceName(self.service_name)
    self.Run('run deploy {service_name} --source {source_path}'.format(
        service_name=self.service_name, source_path=source_path))
    self.create_build_config_mock.assert_called_once_with(
        mock.ANY, False, self.build_messages, None, None, True, False,
        source_path, None, None, None, None, None, None, None)
    build_args, _ = self.create_build_config_mock.call_args
    image = build_args[0]
    image_prefix = 'gcr.io/{projectId}/cloud-run-source-deploy/{service}'.format(
        projectId=self.Project(), service=self.service_name)
    self.assertTrue(image.startswith(image_prefix))
    self.operations.ReleaseService.assert_called_once_with(
        self._ServiceRef(self.service_name),
        [self.app, self.launch_stage_changes],
        mock.ANY,
        asyn=False,
        allow_unauthenticated=None,
        prefetch=self.service,
        build_config=self.build_config,
        build_messages=self.build_messages)
    self._AssertSuccessMessage(self.service_name, 'Dockerfile')

  def testDeployFromSourceWithBuildpacks(self):
    source_path = self.Resource('tests', 'unit', 'surface', 'run', 'testdata',
                                'hello_buildpacks')
    self._SetServiceName(self.service_name)
    self.Run('run deploy {service_name} --image={image} --source {source_path}'
             .format(
                 service_name=self.service_name,
                 image=self.image,
                 source_path=source_path))
    self.create_build_config_mock.assert_called_once_with(
        None, False, self.build_messages, None, None, True, False,
        source_path, None, None, None, None, None, None, mock.ANY)
    build_args, _ = self.create_build_config_mock.call_args
    pack = build_args[-1]
    self.assertEqual(pack, [{'image': self.image}])
    self.operations.ReleaseService.assert_called_once_with(
        self._ServiceRef(self.service_name),
        [self.app, self.launch_stage_changes],
        mock.ANY,
        asyn=False,
        allow_unauthenticated=None,
        prefetch=self.service,
        build_config=self.build_config,
        build_messages=self.build_messages)
    self._AssertSuccessMessage(self.service_name, 'Buildpacks')

  def testDeployFromSourceWithBuildpacksNoImage(self):
    source_path = self.Resource('tests', 'unit', 'surface', 'run', 'testdata',
                                'hello_buildpacks')
    self._SetServiceName(self.service_name)
    self.Run('run deploy {service_name} --source {source_path}'.format(
        service_name=self.service_name, source_path=source_path))
    self.create_build_config_mock.assert_called_once_with(
        None, False, self.build_messages, None, None, True, False,
        source_path, None, None, None, None, None, None, mock.ANY)
    build_args, _ = self.create_build_config_mock.call_args
    pack = build_args[-1]
    image = pack[0].get('image')
    image_prefix = 'gcr.io/{projectId}/cloud-run-source-deploy/{service}'.format(
        projectId=self.Project(), service=self.service_name)
    self.assertTrue(image.startswith(image_prefix))
    self.operations.ReleaseService.assert_called_once_with(
        self._ServiceRef(self.service_name),
        [self.app, self.launch_stage_changes],
        mock.ANY,
        asyn=False,
        allow_unauthenticated=None,
        prefetch=self.service,
        build_config=self.build_config,
        build_messages=self.build_messages)
    self._AssertSuccessMessage(self.service_name, 'Buildpacks')
