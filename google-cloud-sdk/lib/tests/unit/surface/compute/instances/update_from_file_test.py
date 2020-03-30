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
"""Tests for the `compute instances update-from-file` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
import os

from apitools.base.py import exceptions
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.core.util import files
from tests.lib import test_case
from tests.lib.surface.compute import test_base
import six


class InstancesUpdateFromFileTest(test_base.BaseTest,
                                  test_case.WithOutputCapture):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def SetUp(self):
    self.SelectApi(self.api_version)
    scheduling = self.messages.Scheduling(
        automaticRestart=False,
        onHostMaintenance=self.messages.Scheduling
        .OnHostMaintenanceValueValuesEnum.TERMINATE,
        preemptible=False)
    self._instance = self.messages.Instance(
        machineType=(
            'https://compute.googleapis.com/compute/{}/projects/my-project/'
            'zones/zone-1/machineTypes/n1-standard-1'.format(self.api_version)),
        name='instance-1',
        fingerprint=six.ensure_binary('abcdefg'),
        networkInterfaces=[
            self.messages.NetworkInterface(
                networkIP='10.0.0.1',
                accessConfigs=[
                    self.messages.AccessConfig(natIP='23.251.133.75'),
                ],
            ),
        ],
        scheduling=scheduling,
        status=self.messages.Instance.StatusValueValuesEnum.RUNNING,
        selfLink=(
            'https://compute.googleapis.com/compute/{}/projects/my-project/'
            'zones/zone-1/instances/instance-1'.format(self.api_version)),
        zone=('https://compute.googleapis.com/compute/{}/projects/my-project/'
              'zones/zone-1'.format(self.api_version)))
    self._modified_instance = copy.deepcopy(self._instance)
    self._modified_instance.scheduling.automaticRestart = True
    self.make_requests.side_effect = iter([
        [self._instance],
        [self._instance],
    ])

  def _RunUpdate(self, command):
    self.Run('compute instances update-from-file ' + command)

  def _WriteFile(self, file_name, instance):
    """Writes instance message to file and returns the full filename."""
    full_file_name = os.path.join(self.temp_path, file_name)
    with files.FileWriter(full_file_name) as stream:
      export_util.Export(message=instance, stream=stream)
    return full_file_name

  def testUpdateFromFile(self):
    """Tests updatng an instance from a local yaml configuration file."""

    file_name = self._WriteFile('update-from-file.yaml',
                                self._modified_instance)

    self._RunUpdate(
        'instance-1 --zone=zone-1 --project=my-project --source {0}'.format(
            file_name))

    self.CheckRequests([(self.compute.instances, 'Update',
                         self.messages.ComputeInstancesUpdateRequest(
                             instance='instance-1',
                             zone='zone-1',
                             project='my-project',
                             instanceResource=self._modified_instance))])

  def testUpdateFromStdIn(self):
    """Tests updating an instance from stdin."""
    self.WriteInput(export_util.Export(self._modified_instance))
    self._RunUpdate('instance-1 --zone=zone-1 --project=my-project')
    self.CheckRequests([(self.compute.instances, 'Update',
                         self.messages.ComputeInstancesUpdateRequest(
                             instance='instance-1',
                             zone='zone-1',
                             project='my-project',
                             instanceResource=self._modified_instance))])

  def testUpdateNoFingerprint(self):
    """Tests command's failure if no fingerprint in configuration."""
    instance = self.messages.Instance(name='instance-1')
    file_name = self._WriteFile('no-fingerprint.yaml', instance)

    with self.assertRaises(exceptions.InvalidUserInputError):
      self._RunUpdate(
          'instance-1 --zone=zone-1 --project=my-project --source {0}'.format(
              file_name))

      # Command should send no requests.
      self.CheckRequests([])
      self.AssertErrContains(
          '"{}" is missing the instance\'s base64 fingerprint field.'.format(
              file_name))

  def testUpdateRequestSpecificFlags(self):
    """Tests --minimal-action and --most-disruptive-allowed-action flags."""
    file_name = self._WriteFile('update-flags.yaml', self._modified_instance)
    self._RunUpdate(
        ('instance-1 --zone=zone-1 --project=my-project --source {0} '
         '--most-disruptive-allowed-action=RESTART --minimal-action=REFRESH'
        ).format(file_name))
    self.CheckRequests([
        (self.compute.instances, 'Update',
         self.messages.ComputeInstancesUpdateRequest(
             instance='instance-1',
             zone='zone-1',
             project='my-project',
             instanceResource=self._modified_instance,
             minimalAction=self.messages.ComputeInstancesUpdateRequest
             .MinimalActionValueValuesEnum.REFRESH,
             mostDisruptiveAllowedAction=self.messages
             .ComputeInstancesUpdateRequest
             .MostDisruptiveAllowedActionValueValuesEnum.RESTART))
    ])


class InstancesUpdateFromFileBetaTest(InstancesUpdateFromFileTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'


class InstancesUpdateFromFileAlphaTest(InstancesUpdateFromFileBetaTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'


if __name__ == '__main__':
  test_case.main()
