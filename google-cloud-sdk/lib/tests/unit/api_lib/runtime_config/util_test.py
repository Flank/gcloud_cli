# Copyright 2016 Google Inc. All Rights Reserved.
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

"""Tests for googlecloudsdk.api_lib.runtime_config.util."""

from __future__ import absolute_import
from __future__ import unicode_literals
import argparse

from apitools.base.protorpclite import messages

from googlecloudsdk.api_lib.runtime_config import util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import properties
from tests.lib import sdk_test_base

MESSAGE_MODULE = apis.GetMessagesModule('runtimeconfig', 'v1beta1')


class UtilTest(sdk_test_base.SdkBase):

  def SetUp(self):
    # Set a default project name.
    properties.VALUES.core.project.Set('test-project')

  def testProjectPath(self):
    self.assertEqual('projects/my-project',
                     util.ProjectPath('my-project'))

  def testConfigPath(self):
    self.assertEqual('projects/my-project/configs/my-config',
                     util.ConfigPath('my-project', 'my-config'))

  def testVariablePath(self):
    self.assertEqual('projects/my-project/configs/my-config/variables/myvar',
                     util.VariablePath('my-project', 'my-config', 'myvar'))
    self.assertEqual('projects/my-project/configs/my-config/variables/myvar',
                     util.VariablePath('my-project', 'my-config', '/myvar'))
    self.assertEqual(
        'projects/my-project/configs/my-config/variables/myvar/mysubvar',
        util.VariablePath('my-project', 'my-config', '/myvar/mysubvar'))

  def testWaiterPath(self):
    self.assertEqual('projects/my-project/configs/my-config/waiters/my-waiter',
                     util.WaiterPath('my-project', 'my-config', 'my-waiter'))

  def testParseVariableNameSingleSegment(self):
    args = argparse.Namespace(config_name='foo')
    resource = util.ParseVariableName('bar', args)
    self.assertEqual(resource.projectsId, 'test-project')
    self.assertEqual(resource.configsId, 'foo')
    self.assertEqual(resource.variablesId, 'bar')
    self.assertEqual(resource.Name(), 'bar')

  def testParseVariableNameMultiSegment(self):
    args = argparse.Namespace(config_name='foo')
    resource = util.ParseVariableName('bar/bar2', args)
    self.assertEqual(resource.projectsId, 'test-project')
    self.assertEqual(resource.configsId, 'foo')
    self.assertEqual(resource.variablesId, 'bar/bar2')
    self.assertEqual(resource.Name(), 'bar/bar2')

  def testParseVariableNameHttp(self):
    args = argparse.Namespace()
    url = ('https://runtimeconfig.googleapis.com/v1beta1/projects/other-proj'
           '/configs/other-config/variables/other-var/var2')
    resource = util.ParseVariableName(url, args)
    self.assertEqual(resource.projectsId, 'other-proj')
    self.assertEqual(resource.configsId, 'other-config')
    self.assertEqual(resource.variablesId, 'other-var/var2')
    self.assertEqual(resource.Name(), 'other-var/var2')

  def testParseConfigName(self):
    resource = util.ParseConfigName('foobar')
    self.assertEqual(resource.projectsId, 'test-project')
    self.assertEqual(resource.configsId, 'foobar')
    self.assertEqual(resource.Name(), 'foobar')

  def testParseConfigNameHttp(self):
    url = ('https://runtimeconfig.googleapis.com/v1beta1/projects/other-proj'
           '/configs/other-config')
    resource = util.ParseConfigName(url)
    self.assertEqual(resource.projectsId, 'other-proj')
    self.assertEqual(resource.configsId, 'other-config')
    self.assertEqual(resource.Name(), 'other-config')

  def testParseWaiterName(self):
    args = argparse.Namespace(config_name='foo')
    resource = util.ParseWaiterName('bar', args)
    self.assertEqual(resource.projectsId, 'test-project')
    self.assertEqual(resource.configsId, 'foo')
    self.assertEqual(resource.Name(), 'bar')

  def testParseWaiterNameHttp(self):
    args = argparse.Namespace()
    url = ('https://runtimeconfig.googleapis.com/v1beta1/projects/other-proj'
           '/configs/other-config/waiters/my-waiter')
    resource = util.ParseWaiterName(url, args)
    self.assertEqual(resource.projectsId, 'other-proj')
    self.assertEqual(resource.configsId, 'other-config')
    self.assertEqual(resource.Name(), 'my-waiter')

  def testConfigName(self):
    self.assertEqual('foo', util.ConfigName(
        argparse.Namespace(config_name='foo')))
    self.assertEqual(None, util.ConfigName(
        argparse.Namespace(), required=False))

    with self.assertRaises(exceptions.RequiredArgumentException):
      util.ConfigName(argparse.Namespace())

  def testFormatConfig(self):
    config = MESSAGE_MODULE.RuntimeConfig(
        name='projects/my-project/configs/my-config',
        description='foobar'
    )
    munged_config = {
        'atomicName': 'projects/my-project/configs/my-config',
        'name': 'my-config',
        'description': 'foobar',
    }
    self.assertEqual(util.FormatConfig(config), munged_config)

  def testFormatVariable(self):
    variable = MESSAGE_MODULE.Variable(
        name='projects/my-project/configs/my-config/variables/my/var',
        value=b'asdf',
        state=MESSAGE_MODULE.Variable.StateValueValuesEnum.UPDATED,
        updateTime='2016-04-29T00:00:00Z',
    )
    munged_variable = {
        'atomicName': 'projects/my-project/configs/my-config/variables/my/var',
        'name': 'my/var',
        'value': 'YXNkZg==',
        'state': 'UPDATED',
        'updateTime': '2016-04-29T00:00:00Z',
    }
    self.assertEqual(munged_variable, util.FormatVariable(variable))

  def testFormatVariableDecodeValue(self):
    variable = MESSAGE_MODULE.Variable(
        name='projects/my-project/configs/my-config/variables/my/var',
        value=b'asdf',
        state=MESSAGE_MODULE.Variable.StateValueValuesEnum.UPDATED,
        updateTime='2016-04-29T00:00:00Z',)
    munged_variable = {
        'atomicName': 'projects/my-project/configs/my-config/variables/my/var',
        'name': 'my/var',
        'value': b'asdf',
        'state': 'UPDATED',
        'updateTime': '2016-04-29T00:00:00Z',
    }
    self.assertEqual(munged_variable, util.FormatVariable(variable, True))

  def testFormatVariableOutputText(self):
    variable = MESSAGE_MODULE.Variable(
        name='projects/my-project/configs/my-config/variables/my/var',
        text='qwer',
        state=MESSAGE_MODULE.Variable.StateValueValuesEnum.UPDATED,
        updateTime='2016-04-29T00:00:00Z',)
    munged_variable = {
        'atomicName': 'projects/my-project/configs/my-config/variables/my/var',
        'name': 'my/var',
        'value': 'qwer',
        'text': 'qwer',
        'state': 'UPDATED',
        'updateTime': '2016-04-29T00:00:00Z',
    }
    self.assertEqual(util.FormatVariable(variable, True), munged_variable)

  def testFormatWaiter(self):
    waiter = MESSAGE_MODULE.Waiter(
        name='projects/my-project/configs/my-config/waiters/my-waiter',
        timeout='120',
        success=MESSAGE_MODULE.EndCondition(
            cardinality=MESSAGE_MODULE.Cardinality(
                path='/success',
                number=2,
            )
        ),
        failure=MESSAGE_MODULE.EndCondition(
            cardinality=MESSAGE_MODULE.Cardinality(
                path='/failure',
                number=1,
            )
        ),
        done=True,
        error=MESSAGE_MODULE.Status(
            code=9,
            message='failure'
        ),
        createTime='2016-04-29T00:00:00Z',
    )
    munged_waiter = {
        'atomicName': 'projects/my-project/configs/my-config/waiters/my-waiter',
        'name': 'my-waiter',
        'timeout': '120',
        'success': {
            'cardinality': {
                'path': '/success',
                'number': 2
            }
        },
        'failure': {
            'cardinality': {
                'path': '/failure',
                'number': 1
            }
        },
        'done': True,
        'error': {
            'code': 9,
            'message': 'failure'
        },
        'createTime': '2016-04-29T00:00:00Z'
    }
    self.assertEqual(util.FormatWaiter(waiter), munged_waiter)

  def testDictWithShortNameRejectsExistingAtomicName(self):
    class MessageWithAtomicName(messages.Message):
      atomicName = messages.StringField(1)  # pylint: disable=invalid-name
      name = messages.StringField(2)

    with self.assertRaises(ValueError):
      util._DictWithShortName(
          MessageWithAtomicName(atomicName='foo', name='bar'),
          lambda n: n
      )

  def testDictWithShortNameNoNameField(self):
    class MessageWithoutName(messages.Message):
      foo = messages.StringField(2)

    result = util._DictWithShortName(
        MessageWithoutName(foo='bar'),
        lambda n: n
    )
    self.assertEqual(result, {'foo': 'bar'})

if __name__ == '__main__':
  sdk_test_base.main()
