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

"""Tests for surface.app.migrate_config."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import shutil

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core.util import files
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


class MigrateConfigTest(cli_test_base.CliTestBase, sdk_test_base.WithTempCWD):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.config_dir = self.Resource('tests', 'unit', 'surface', 'app',
                                    'test_data', 'config')

  def testCron(self):
    shutil.copy(os.path.join(self.config_dir, 'cron.xml'), 'cron.xml')
    expected = files.ReadFileContents(
        os.path.join(self.config_dir, 'cron.yaml'))
    self.Run('app migrate-config cron-xml-to-yaml cron.xml')
    self.AssertFileNotExists('cron.xml')
    self.AssertFileExistsWithContents(expected, 'cron.yaml')
    self.AssertFileExists('cron.xml.bak')

  def testQueue(self):
    shutil.copy(os.path.join(self.config_dir, 'queue.xml'), 'queue.xml')
    expected = files.ReadFileContents(
        os.path.join(self.config_dir, 'queue.yaml'))
    self.Run('app migrate-config queue-xml-to-yaml queue.xml')
    self.AssertFileNotExists('queue.xml')
    self.AssertFileExistsWithContents(expected, 'queue.yaml')
    self.AssertFileExists('queue.xml.bak')

  def testDispatch(self):
    shutil.copy(os.path.join(self.config_dir, 'dispatch.xml'), 'dispatch.xml')
    expected = files.ReadFileContents(
        os.path.join(self.config_dir, 'dispatch.yaml'))
    self.Run('app migrate-config dispatch-xml-to-yaml dispatch.xml')
    self.AssertFileNotExists('dispatch.xml')
    self.AssertFileExistsWithContents(expected, 'dispatch.yaml')
    self.AssertFileExists('dispatch.xml.bak')

  def testIndexes(self):
    shutil.copy(os.path.join(self.config_dir, 'datastore-indexes.xml'),
                'datastore-indexes.xml')
    expected = files.ReadFileContents(
        os.path.join(self.config_dir, 'index.yaml'))
    self.Run('app migrate-config datastore-indexes-xml-to-yaml '
             'datastore-indexes.xml')
    self.AssertFileNotExists('datastore-indexes.xml')
    self.AssertFileExistsWithContents(expected, 'index.yaml')
    self.AssertFileExists('datastore-indexes.xml.bak')

  def testIndexesMerged(self):
    """When there are two xml files that are merged to one."""
    shutil.copy(os.path.join(self.config_dir, 'datastore-indexes.xml'),
                'datastore-indexes.xml')
    shutil.copy(os.path.join(self.config_dir, 'auto-datastore-indexes.xml'),
                'auto-datastore-indexes.xml')
    expected = files.ReadFileContents(
        os.path.join(self.config_dir, 'index_merged.yaml'))
    self.Run('app migrate-config datastore-indexes-xml-to-yaml '
             'datastore-indexes.xml '
             '--generated-indexes-file=auto-datastore-indexes.xml')
    self.AssertFileNotExists('datastore-indexes.xml')
    self.AssertFileNotExists('auto-datastore-indexes.xml')
    self.AssertFileExistsWithContents(expected, 'index.yaml')
    self.AssertFileExists('datastore-indexes.xml.bak')
    self.AssertFileExists('auto-datastore-indexes.xml.bak')

