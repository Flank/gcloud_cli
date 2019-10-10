# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Unit tests for image version command util."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.composer import image_versions_util as util
from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.surface.composer import base


class ImageVersionsUtilBetaTest(base.EnvironmentsUnitTest):

  def PreSetUp(self):
    self.SetTrack(calliope_base.ReleaseTrack.BETA)

  def _SetTestMessages(self):
    # pylint: disable=invalid-name
    # super(ImageVersionsUtilBetaTest, self)._SetTestMessages()
    self.PYTHON_VERSION = '2'
    self.PAGE_SIZE = 1000

  def testListImageVersionUpgrades(self):
    self._SetTestMessages()

    # Configure mock service calls
    software_config = self.messages.SoftwareConfig(
        imageVersion=self.TEST_UPGRADEABLE_IMAGE_VERSION,
        pythonVersion=self.PYTHON_VERSION)
    config = self.messages.EnvironmentConfig(softwareConfig=software_config)
    env_response = self.MakeEnvironment(self.TEST_PROJECT, self.TEST_LOCATION,
                                        self.TEST_ENVIRONMENT_ID, config)

    self.ExpectEnvironmentGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        response=env_response)

    image_version_resp = self.messages.ListImageVersionsResponse(
        imageVersions=self.test_image_versions_list, nextPageToken=None)
    self.ExpectEnvironmentsListUpgrades(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.PAGE_SIZE,
        response=image_version_resp)

    # Set expected results based on an environment running:
    #   image-version: composer-1.3.2-airflow-1.9.0 & python-version: 2
    self.assertEquals('composer-1.3.2-airflow-1.9.0',
                      self.TEST_UPGRADEABLE_IMAGE_VERSION)
    self.assertEquals('2', self.PYTHON_VERSION)
    expected_filtered_list = [
        self.messages.ImageVersion(
            imageVersionId='composer-1.3.2-airflow-1.9.1',
            isDefault=False,
            supportedPythonVersions=['2']),
        self.messages.ImageVersion(
            imageVersionId='composer-1.3.10-airflow-1.9.0',
            isDefault=False,
            supportedPythonVersions=['2', '3']),
        self.messages.ImageVersion(
            imageVersionId='composer-1.4.0-airflow-1.9.0',
            isDefault=True,
            supportedPythonVersions=['2', '3']),
        self.messages.ImageVersion(
            imageVersionId='composer-1.4.0-airflow-1.9.1',
            isDefault=False,
            supportedPythonVersions=['2', '3']),
        self.messages.ImageVersion(
            imageVersionId='composer-1.4.0-airflow-1.10.0',
            isDefault=False,
            supportedPythonVersions=['2', '3']),
        self.messages.ImageVersion(
            imageVersionId='composer-1.4.0-airflow-1.10.1',
            isDefault=False,
            supportedPythonVersions=['2', '3'])
    ]

    env_resource = resources.REGISTRY.Parse(
        self.TEST_ENVIRONMENT_ID,
        params={
            'projectsId': self.TEST_PROJECT,
            'locationsId': self.TEST_LOCATION
        },
        collection='composer.projects.locations.environments')

    actual_list = util.ListImageVersionUpgrades(env_resource, self.track)
    self.assertEquals(expected_filtered_list, actual_list)

  def testValidateCandidateVersionStringsSuccess(self):
    valid = [('composer-1.2.3-airflow-1.2.3', 'composer-1.10.3-airflow-1.2.3'),
             ('composer-1.2.3-airflow-1.2.3', 'composer-1.2.10-airflow-1.2.3'),
             ('composer-1.2.3-airflow-1.2.3', 'composer-1.10.3-airflow-1.2.10'),
             ('composer-1.2.3-airflow-1.2.3', 'composer-latest-airflow-9.9.9')]
    for (cur, cand) in valid:
      self.assertTrue(util._ValidateCandidateImageVersionId(cur, cand))

  def testValidateCandidateVersionStringsFailures(self):
    self.assertFalse(
        util._ValidateCandidateImageVersionId('composer-1.2.3-airflow-1.2.3',
                                              'composer-1.0.0-airflow-1.2.3'))
    self.assertFalse(
        util._ValidateCandidateImageVersionId('composer-1.2.3-airflow-1.2.3',
                                              'composer-1.2.3-airflow-1.0.0'))
    self.assertFalse(
        util._ValidateCandidateImageVersionId('composer-1.2.3-airflow-1.2.3',
                                              'composer-1.2.3-airflow-1.2.3'))

  def testIsValidAirflowUpgrade(self):
    valid = [('1.0.0', '1.0.1'), ('1.0.0', '1.1.0'), ('1.0.0', '2.0.0')]
    for (cur, cand) in valid:
      self.assertTrue(util._IsAirflowVersionUpgradeCompatible(cur, cand))

    invalid = [('1.1.1', '0.0.2'), ('1.1.1', '1.1.0'), ('1.1.1', '1.0.1'),
               ('1.0.0', '0.0.9')]
    for (cur, cand) in invalid:
      self.assertFalse(util._IsAirflowVersionUpgradeCompatible(cur, cand))

  def testIsValidComposerUpgrade(self):
    valid = [('1.0.0', '1.0.8'), ('1.0.0', '1.0.10'), ('1.0.0', '1.10.0'),
             ('1.0.0', '1.10.10')]
    for (cur, cand) in valid:
      self.assertTrue(
          util._IsComposerVersionUpgradeCompatible(cur, cand),
          ('expects version: {} to be upgradeable to candidate: '
           '{}'.format(cur, cand)))

    invalid = [('1.0.0', '0.9.0'), ('1.2.3', '1.1.3'), ('1.2.3', '1.2.2'),
               ('1.0.0', '2.0.0')]
    for (cur, cand) in invalid:
      self.assertFalse(
          util._IsComposerVersionUpgradeCompatible(cur, cand),
          ('expects version: {} not to be upgradeable to '
           'candidate: {}'.format(cur, cand)))


class ImageVersionsUtilAlphaTest(ImageVersionsUtilBetaTest):

  def PreSetUp(self):
    self.SetTrack(calliope_base.ReleaseTrack.ALPHA)


if __name__ == '__main__':
  test_case.main()
