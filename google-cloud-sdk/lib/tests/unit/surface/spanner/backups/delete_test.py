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
"""Tests for Spanner backups delete command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import resources
from tests.lib.apitools import http_error
from tests.lib.surface.spanner import base


class BackupsDeleteTest(base.SpannerTestBase):
  """Cloud Spanner backups delete tests."""

  def SetUp(self):
    self.backup_ref = resources.REGISTRY.Parse(
        'thebackup',
        params={
            'projectsId': self.Project(),
            'instancesId': 'theinstance',
        },
        collection='spanner.projects.instances.backups')

  def testDelete(self):
    self.client.projects_instances_backups.Get.Expect(
        request=self.msgs.SpannerProjectsInstancesBackupsGetRequest(
            name=self.backup_ref.RelativeName()),
        response=self.msgs.Backup(name=self.backup_ref.RelativeName()))
    self.client.projects_instances_backups.Delete.Expect(
        request=self.msgs.SpannerProjectsInstancesBackupsDeleteRequest(
            name=self.backup_ref.RelativeName()),
        response=self.msgs.Empty())
    self.WriteInput('y\n')
    self.Run('spanner backups delete thebackup --instance=theinstance')

  def testDeleteWithDefaultInstance(self):
    self.client.projects_instances_backups.Get.Expect(
        request=self.msgs.SpannerProjectsInstancesBackupsGetRequest(
            name=self.backup_ref.RelativeName()),
        response=self.msgs.Backup(name=self.backup_ref.RelativeName()))
    self.client.projects_instances_backups.Delete.Expect(
        request=self.msgs.SpannerProjectsInstancesBackupsDeleteRequest(
            name=self.backup_ref.RelativeName()),
        response=self.msgs.Empty())
    self.WriteInput('y\n')
    self.Run('config set spanner/instance theinstance')
    self.Run('spanner backups delete thebackup')

  def testDeleteForNonExistentBackup(self):
    self.client.projects_instances_backups.Get.Expect(
        request=self.msgs.SpannerProjectsInstancesBackupsGetRequest(
            name=self.backup_ref.RelativeName()),
        exception=http_error.MakeHttpError(code=404,
                                           message='Backup not found'))
    with self.AssertRaisesHttpExceptionMatches('Backup not found'):
      self.WriteInput('y\n')
      self.Run('spanner backups delete thebackup --instance=theinstance')

