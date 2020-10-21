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
"""Critical user journey test for deploying a new revision from source files."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib
import os

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core.util import retry
from tests.lib import cli_test_base
from tests.lib import e2e_base
from tests.lib import e2e_utils
from tests.lib import sdk_test_base
from tests.lib import test_case

SERVICE_NAME_PREFIX = 'serverless-deploy-e2e'


class DeployFromSourceTest(sdk_test_base.BundledBase, e2e_base.WithServiceAuth,
                           cli_test_base.CliTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def SetUp(self):
    self.image = 'gcr.io/cloud-sdk-integration-testing/hello'

  def _GenerateServiceName(self):
    generator = e2e_utils.GetResourceNameGenerator(
        prefix=SERVICE_NAME_PREFIX, sequence_start=0, delimiter='-')
    return next(generator)

  def _AssertSuccessMessage(self, service_name, build_type):
    self.AssertErrContains('Building using {build_type} and deploying'.format(
        build_type=build_type))
    self.AssertErrContains('to Cloud Run')
    self.AssertErrContains(
        'Service [{service_name}]'.format(service_name=service_name))
    self.AssertErrContains(
        'has been deployed and is serving 100 percent of traffic')

  @contextlib.contextmanager
  def _DeployFromSource(self, *args, **kwargs):
    service_name = kwargs.pop('service_name', self._GenerateServiceName())
    source_path = kwargs.pop('source_path', '.')
    source = '--source {}'.format(source_path)
    image = kwargs.pop('image', '')
    if image:
      image = '--image {}'.format(image)
    try:
      self.Run(
          'run deploy {service_name} {image} {source} '
          '--region us-central1 --allow-unauthenticated --platform managed'
          .format(
              service_name=service_name, image=image, source=source))
      yield service_name

    finally:
      delete_retryer = retry.Retryer(
          max_retrials=3, exponential_sleep_multiplier=2)
      delete_retryer.RetryOnException(self.Run, [
          'run services delete {service_name} --region us-central1 '
          '--quiet --platform managed'.format(service_name=service_name)
      ])

  def testDeployFromSourceWithDockerFile(self):
    source_path = os.path.relpath(
        self.Resource('tests', 'e2e', 'surface', 'run', 'test_data',
                      'hello_dockerfile'), os.getcwd())
    with self._DeployFromSource(
        source_path=source_path, image=self.image) as service_name:
      self._AssertSuccessMessage(service_name, 'Dockerfile')

  def testDeployFromSourceWithDockerFileNoImage(self):
    source_path = os.path.relpath(
        self.Resource('tests', 'e2e', 'surface', 'run', 'test_data',
                      'hello_dockerfile'), os.getcwd())
    with self._DeployFromSource(source_path=source_path) as service_name:
      self._AssertSuccessMessage(service_name, 'Dockerfile')

  def testDeployFromSourceWithBuildpack(self):
    source_path = os.path.relpath(
        self.Resource('tests', 'e2e', 'surface', 'run', 'test_data',
                      'hello_buildpacks'), os.getcwd())
    with self._DeployFromSource(
        source_path=source_path, image=self.image) as service_name:
      self._AssertSuccessMessage(service_name, 'Buildpacks')

  def testDeployFromSourceWithBuildpackNoImage(self):
    source_path = os.path.relpath(
        self.Resource('tests', 'e2e', 'surface', 'run', 'test_data',
                      'hello_buildpacks'), os.getcwd())
    with self._DeployFromSource(source_path=source_path) as service_name:
      self._AssertSuccessMessage(service_name, 'Buildpacks')


if __name__ == '__main__':
  test_case.main()
