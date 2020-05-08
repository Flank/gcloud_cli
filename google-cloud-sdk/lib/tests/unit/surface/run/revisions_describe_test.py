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
"""Unit tests for the `run revisions describe` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.run import revision
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.run import flags
from tests.lib.surface.run import base


class DescribeTest(base.ServerlessSurfaceBase):
  """Tests outputs of describe command."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.fake_revision = revision.Revision.New(
        self.mock_serverless_client, 'us-central1.fake-project')
    self.fake_revision.name = '12345'
    self.fake_revision.metadata.creationTimestamp = '2018/01/01 00:00:00'
    self.fake_revision.annotations[revision.AUTHOR_ANNOTATION] = 'Tom'
    self.fake_revision.container.env = [
        self.serverless_messages.EnvVar(name='n1', value='v1'),
        self.serverless_messages.EnvVar(name='n2', value='v2')]

  def testDescribe_Succeed_Default(self):
    """Tests successful describe with default output format."""
    self.operations.GetRevision.return_value = self.fake_revision
    self.Run('run revisions describe 12345')
    self.operations.GetRevision.assert_called_once_with(
        self._RevisionRef('12345'))
    for s in [
        'Revision 12345 in namespace us-central1.fake-project',
        'Env vars:',
        'n1',
        'v1',
        'n2',
        'v2',
    ]:
      self.AssertOutputContains(s)

  def testDescribe_Succeed_CustomFormat(self):
    """Tests successful describe with custom output format."""
    self.operations.GetRevision.return_value = self.fake_revision
    custom_title = 'MyTitle'
    custom_labels = ['MyAuthorLabel', 'MyBuildArtifactLabel']
    custom_format_string = ('table[box,title={}](author:label={},'
                            'gcs_location:label={})'
                            .format(custom_title, *custom_labels))
    self.Run('run revisions describe 12345 --format={}'.format(
        custom_format_string))
    self.operations.GetRevision.assert_called_once_with(
        self._RevisionRef('12345'))
    self.AssertOutputContains(custom_title)
    for label in custom_labels:
      self.AssertOutputContains(label)

  def testDescribe_Fail_MissingRevision(self):
    """Tests describe fail with not found revision."""
    self.operations.GetRevision.return_value = None
    with self.assertRaises(flags.ArgumentError) as context:
      self.Run('run revisions describe 123')
    self.assertIn(
        'Cannot find revision [123]', str(context.exception))
    self.operations.GetRevision.assert_called_once_with(
        self._RevisionRef('123'))


class DescribeTestBeta(DescribeTest):
  """Tests outputs of describe command."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class DescribeTestAlpha(DescribeTestBeta):
  """Tests outputs of describe command."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
