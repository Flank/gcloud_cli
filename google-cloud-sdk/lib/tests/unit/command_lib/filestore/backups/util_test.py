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

# Lint as: python3
"""Tests for Cloud Filestore backups command libary."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.filestore.backups import util
from tests.lib.surface.filestore import base


class CloudFilestoreBackupsUtilTest(base.CloudFilestoreUnitTestBase):
  _TRACK = calliope_base.ReleaseTrack.ALPHA

  class ArgsMock(object):
    """Mock arguments."""
    source_backup = None
    source_backup_region = None

  class ResourceMock(object):
    """Mock googlecloudsdk.core.resources.Resource."""
    # pylint: disable=invalid-name
    locationsId = None
    # pylint: enable=invalid-name

  def SetUp(self):
    self.SetUpTrack(self._TRACK)

  def testAddBackupNameToRequestWithRegion(self):
    args = self.ArgsMock()
    args.source_backup = "my-backup"
    args.source_backup_region = "us-central1-c"

    resource = self.ResourceMock()
    # pylint: disable=invalid-name
    resource.locationsId = "us-west1-c"
    # pylint: enable=invalid-name

    req = self.messages.FileProjectsLocationsInstancesRestoreRequest()
    req.restoreInstanceRequest = self.messages.RestoreInstanceRequest()

    util.AddBackupNameToRequest(resource, args, req)

    self.assertEqual(
        req.restoreInstanceRequest.sourceBackup,
        "projects/fake-project/locations/us-central1-c/backups/my-backup")

  def testAddBackupNameToRequestNoRegion(self):
    args = self.ArgsMock()
    args.source_backup = "my-backup"

    resource = self.ResourceMock()
    # pylint: disable=invalid-name
    resource.locationsId = "us-west1-c"
    # pylint: enable=invalid-name

    req = self.messages.FileProjectsLocationsInstancesRestoreRequest()
    req.restoreInstanceRequest = self.messages.RestoreInstanceRequest()

    util.AddBackupNameToRequest(resource, args, req)

    self.assertEqual(
        req.restoreInstanceRequest.sourceBackup, None)

  def testAddBackupNameToRequestNoBackup(self):
    args = self.ArgsMock()

    resource = self.ResourceMock()
    # pylint: disable=invalid-name
    resource.locationsId = "us-west1-c"
    # pylint: enable=invalid-name

    req = self.messages.FileProjectsLocationsInstancesRestoreRequest()
    req.restoreInstanceRequest = self.messages.RestoreInstanceRequest()

    util.AddBackupNameToRequest(resource, args, req)

    self.assertEqual(req.restoreInstanceRequest.sourceBackup, None)


if __name__ == "__main__":
  calliope_base.main()
