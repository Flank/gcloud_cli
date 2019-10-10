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
"""Unit tests for environments create."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.composer import base


class _ListUpgradesTestBase(base.EnvironmentsUnitTest):

  # Must be called after self.SetTrack() for self.messages to be present
  def _SetTestMessages(self):
    # pylint: disable=invalid-name
    self.PYTHON_VERSION = '2'


class ListUpgradesBetaTest(_ListUpgradesTestBase):

  def PreSetUp(self):
    self.SetTrack(calliope_base.ReleaseTrack.BETA)

  def _SetTestMessages(self):
    # pylint: disable=invalid-name
    super(ListUpgradesBetaTest, self)._SetTestMessages()

    self.PAGE_SIZE = 1000
    self.TEST_SUPPORTED_IMAGE_VERSIONS = [
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
            imageVersionId='composer-1.4.0-airflow-1.9.8',
            isDefault=False,
            supportedPythonVersions=['3']),
        self.messages.ImageVersion(
            imageVersionId='composer-1.4.0-airflow-1.10.0',
            isDefault=False,
            supportedPythonVersions=['2', '3']),
        self.messages.ImageVersion(
            imageVersionId='composer-1.4.0-airflow-1.10.1',
            isDefault=False,
            supportedPythonVersions=['2', '3']),
        self.messages.ImageVersion(
            imageVersionId='composer-1.5.0-airflow-1.10.1',
            isDefault=False,
            supportedPythonVersions=['3']),
        self.messages.ImageVersion(
            imageVersionId='composer-9.9.9-airflow-9.9.9',
            isDefault=False,
            supportedPythonVersions=['3'])
    ]

  def testSuccessfulEnvironmentListUpgrade(self):
    """Test that list of upgrades can be fetched."""
    self._SetTestMessages()

    software_config = self.messages.SoftwareConfig(
        imageVersion=self.TEST_UPGRADEABLE_IMAGE_VERSION,
        pythonVersion=self.PYTHON_VERSION)
    config = self.messages.EnvironmentConfig(softwareConfig=software_config)

    expected_get_response = self.MakeEnvironment(
        self.TEST_PROJECT, self.TEST_LOCATION, self.TEST_ENVIRONMENT_ID, config)

    self.ExpectEnvironmentGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        response=expected_get_response)

    image_version_resp = self.messages.ListImageVersionsResponse(
        imageVersions=self.TEST_SUPPORTED_IMAGE_VERSIONS, nextPageToken=None)
    self.ExpectEnvironmentsListUpgrades(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.PAGE_SIZE,
        response=image_version_resp)

    # Based on:
    #  image-version:   composer-1.3.2-airflow-1.9.0
    #  python-version:  2
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

    actual = self.RunEnvironments('list-upgrades', '--project',
                                  self.TEST_PROJECT, '--location',
                                  self.TEST_LOCATION, self.TEST_ENVIRONMENT_ID)

    self.assertEquals(expected_filtered_list, actual)


class ListUpgradesAlphaTest(ListUpgradesBetaTest):

  def PreSetUp(self):
    self.SetTrack(calliope_base.ReleaseTrack.ALPHA)


if __name__ == '__main__':
  test_case.main()
