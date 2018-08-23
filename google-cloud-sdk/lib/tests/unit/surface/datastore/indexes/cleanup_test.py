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
"""Tests of the datastore indexes cleanup command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from __future__ import with_statement

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core.console import console_io
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.app import util as test_util


@parameterized.parameters(calliope_base.ReleaseTrack.GA,
                          calliope_base.ReleaseTrack.BETA,
                          calliope_base.ReleaseTrack.ALPHA)
class CleanupTests(test_util.AppTestBase, test_util.WithAppData,
                   test_case.WithInput):

  def SetUp(self):
    self.StartPatch('time.sleep')

  def testCleanNoIndexFile(self, track):
    self.track = track
    f = self.WriteApp('app.yaml', service='default')
    with self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        'You must provide the path to a valid index.yaml file.'):
      self.Run('--quiet datastore indexes cleanup ' + f)

  def testNo(self, track):
    self.track = track
    f = self.Touch(self.temp_path, 'index.yaml', 'indexes:\n')
    self.WriteInput('n\n')
    with self.assertRaises(console_io.OperationCancelledError):
      self.Run('datastore indexes cleanup ' + f)

  def testClean(self, track):
    self.track = track
    f = self.Touch(self.temp_path, 'index.yaml', 'indexes:\n')
    self.WriteInput('y\n')
    cat_index = ('- kind: Cat\n'
                 '  properties:\n'
                 '  - direction: asc\n'
                 '    name: whiskers\n')
    diff_response_body = ('indexes:\n' '---\n' 'indexes:\n' + cat_index)

    self.AddResponse(
        'https://appengine.google.com/api/datastore/index/diff',
        expected_params={'app_id': [self.PROJECT]},
        expected_body='{}\n',
        response_code=200,
        response_body=diff_response_body)
    self.AddResponse(
        'https://appengine.google.com/api/datastore/index/delete',
        expected_params={'app_id': [self.PROJECT]},
        expected_body='indexes:\n' + cat_index,
        response_code=200,
        response_body='indexes:\n')
    self.Run('datastore indexes cleanup ' + f)


if __name__ == '__main__':
  test_case.main()
