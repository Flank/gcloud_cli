# Copyright 2015 Google Inc. All Rights Reserved.
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

"""Tests of the datastore create-indexes command."""

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import with_statement

from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core.console import console_io
from tests.lib import test_case
from tests.lib.surface.app import util as test_util


class IndexTests(test_util.AppTestBase, test_util.WithAppData,
                 test_case.WithInput):

  def SetUp(self):
    self.StartPatch('time.sleep')

  def testCreateNoIndexFile(self):
    f = self.WriteApp('app.yaml', service='default')
    with self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        'You must provide the path to a valid index.yaml file.'):
      self.Run('datastore create-indexes ' + f)

  def testCreateNo(self):
    self.strict = False
    self.MakeApp()
    self.WriteInput('n\n')
    with self.assertRaises(console_io.OperationCancelledError):
      self.Run('datastore create-indexes ' +
               self.FullPath('index.yaml'))

  def testCreate(self):
    self.strict = False
    self.MakeApp()
    self.WriteInput('y\n')
    self.Run(
        'datastore create-indexes ' + self.FullPath('index.yaml'))
    self.AssertRequested(
        'https://appengine.google.com/api/datastore/index/add',
        {'app_id': self.PROJECT})


if __name__ == '__main__':
  test_case.main()
