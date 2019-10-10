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

"""Unit tests for the calliope.parameter_info_lib module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.util import parameter_info_lib
from googlecloudsdk.core import properties
from tests.lib import completer_test_data
from tests.lib import sdk_test_base
from tests.lib import subtests
from tests.lib import test_case
from tests.lib.core import core_completer_test_base


class MockArgument(object):

  def __init__(self, name):
    self.name = name
    self.dest = parameter_info_lib.GetDestFromFlag(name)


class GetDestFromParamTest(subtests.Base):

  def RunSubTest(self, param, prefix=None):
    return parameter_info_lib.GetDestFromParam(param, prefix=prefix)

  def testGetDestFromParam(self):
    def T(expected, param, prefix=None):
      self.Run(expected, param, prefix=prefix, depth=2)

    T('project', 'project')
    T('project', 'projectId')
    T('project', 'projectsId')
    T('project', 'projectsID')

    T('project_name', 'projectName')
    T('project_name', 'project_name')

    T('foo_project', 'project', prefix='foo')
    T('foo_project', 'projectId', prefix='foo')
    T('foo_project', 'projectsId', prefix='foo')
    T('foo_project', 'projectsID', prefix='foo')

    T('foo_project_name', 'projectName', prefix='foo')
    T('foo_project_name', 'project_name', prefix='foo')


class GetFlagFromDestTest(subtests.Base):

  def RunSubTest(self, dest):
    return parameter_info_lib.GetFlagFromDest(dest)

  def testGetFlagFromDest(self):
    def T(expected, dest):
      self.Run(expected, dest, depth=2)

    T('--project', 'project')
    T('--source-dir', 'source_dir')


class GetDestFromFlagTest(subtests.Base):

  def RunSubTest(self, flag):
    return parameter_info_lib.GetDestFromFlag(flag)

  def testGetDestFromFlag(self):
    def T(expected, dest):
      self.Run(expected, dest, depth=2)

    T('project', '--project')
    T('source_dir', '--source-dir')
    T('source_dir', '--source-dir--')
    T('source_dir', '--source-dir__')
    T('source_dir', '--source_dir__')


class ParameterInfoByConventionTest(sdk_test_base.SdkBase):

  def SetUp(self):
    properties.VALUES.core.project.Set('myxproject')
    self.parsed_args = core_completer_test_base.MockNamespace(
        args={
            'instance': 'my_z_instance',  # positional, no flag representation
            '--project': None,  # properties fallback
            '--undefined': None,  # flag not specified
            '--zone': 'zone-1',  # flag specified
        },
    )
    self.parameter_info = parameter_info_lib.ParameterInfoByConvention(
        self.parsed_args,
        MockArgument('instance'),
        collection='test.resource',
    )

  def testGetDest(self):
    self.assertEqual('instance',
                     self.parameter_info.GetDest('instance'))
    self.assertEqual('project',
                     self.parameter_info.GetDest('project'))
    self.assertEqual('undefined',
                     self.parameter_info.GetDest('undefined'))
    self.assertEqual('zone',
                     self.parameter_info.GetDest('zone'))

  def testGetFlag(self):
    self.assertEqual(None,
                     self.parameter_info.GetFlag('instance'))
    self.assertEqual('--project=myxproject',
                     self.parameter_info.GetFlag('project'))
    self.assertEqual(None,
                     self.parameter_info.GetFlag('undefined'))
    self.assertEqual('--zone=zone-1',
                     self.parameter_info.GetFlag('zone'))

  def testGetValue(self):
    self.assertEqual('my_z_instance',
                     self.parameter_info.GetValue('instance'))
    self.assertEqual('myxproject',
                     self.parameter_info.GetValue('project'))
    self.assertEqual(None,
                     self.parameter_info.GetValue('undefined'))
    self.assertEqual('zone-1',
                     self.parameter_info.GetValue('zone'))

  def testExecute(self):
    self.assertEqual(completer_test_data.PROJECT_URIS,
                     self.parameter_info.Execute(['projects', 'list']))


if __name__ == '__main__':
  test_case.main()
