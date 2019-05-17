# -*- coding: utf-8 -*- #
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
"""Unit tests for externalized runtimes."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io
import json
import logging
import os
import textwrap

from gae_ext_runtime import ext_runtime
from googlecloudsdk.api_lib.app import ext_runtime_adapter
from googlecloudsdk.core import config
from googlecloudsdk.core import log
from googlecloudsdk.core import yaml
from googlecloudsdk.core.console import console_io
from tests.lib import sdk_test_base
from tests.lib import test_case
import mock


class TestBase(sdk_test_base.SdkBase):

  def LogInfoFake(self, message):
    self.log.append(('info', message))

  def LogWarnFake(self, message):
    self.err.append(('warn', message))

  def LogErrFake(self, message):
    self.err.append(('error', message))

  def LogPrintFake(self, message):
    self.log.append(('print', message))

  def PromptFake(self, message):
    self.prompt_message = message
    return 'user response'

  def CanPromptFake(self):
    return self.can_prompt

  def SetUp(self):
    self.runtime_def_dir = (
        self.Resource('tests', 'unit', 'api_lib', 'app', 'testdata',
                      'runtime_def'))

    # We use "patch" here rather than Assert{Out,Err}Contains here for several
    # reasons:
    # 1) We want to ensure that standard output is logged as "info" and
    #    standard error is logged as "warning" without incurring dependencies
    #    on the rendering conventions of the underlying logging facility.
    # 2) We want to verify that message processing occurs in a well-defined
    #    order with respect to "info" message fall-through and message
    #    processing will not be sent to output.
    self.log_info_patch = mock.patch.object(logging, 'info',
                                            new=self.LogInfoFake)
    self.log_info_patch.start()
    self.log_warn_patch = mock.patch.object(logging, 'warn',
                                            new=self.LogWarnFake)
    self.log_warn_patch.start()
    self.log_warning_patch = mock.patch.object(logging, 'warning',
                                               new=self.LogWarnFake)
    self.log_warning_patch.start()
    self.log_err_patch = mock.patch.object(logging, 'error',
                                           new=self.LogErrFake)
    self.log_err_patch.start()
    self.log_print_patch = mock.patch.object(log.status, 'Print',
                                             new=self.LogPrintFake)
    self.log_print_patch.start()
    self.prompt_response_fake = (
        mock.patch.object(console_io, 'PromptResponse', new=self.PromptFake))
    self.prompt_response_fake.start()
    self.prompt_message = None

    self.can_prompt_fake = (
        mock.patch.object(console_io, 'CanPrompt', new=self.CanPromptFake))
    self.can_prompt_fake.start()
    self.can_prompt = True

    # We have to break these up into two different attributes because order is
    # not guaranteed across stderr versus stdin/stdout processing.
    self.log = []
    self.err = []
    self.env = ext_runtime_adapter.GCloudExecutionEnvironment()

  def TearDown(self):
    self.can_prompt_fake.stop()
    self.prompt_response_fake.stop()
    self.log_info_patch.stop()
    self.log_err_patch.stop()
    self.log_warn_patch.stop()
    self.log_warning_patch.stop()
    self.log_print_patch.stop()


@test_case.Filters.DoNotRunOnPy3('Deprecated command; no py3 support')
class GetRuntimeDefDirTest(sdk_test_base.SdkBase):

  def SetUp(self):
    # Clear the environment variable set by the test housing so that we fall
    # through to config.Paths().sdk_root when getting the runtime definition
    # root.
    self.old_runtime_root = os.environ.get('CLOUDSDK_APP_RUNTIME_ROOT')
    if self.old_runtime_root is not None:
      del os.environ['CLOUDSDK_APP_RUNTIME_ROOT']

  def TearDown(self):
    if self.old_runtime_root is not None:
      os.environ['CLOUDSDK_APP_RUNTIME_ROOT'] = self.old_runtime_root

  def testGetRuntimeDefDir(self):
    self.StartPropertyPatch(config.Paths, 'sdk_root', return_value=None)
    with self.assertRaises(ext_runtime_adapter.NoRuntimeRootError):
      ext_runtime_adapter._GetRuntimeDefDir()


@test_case.Filters.DoNotRunOnPy3('Deprecated command; no py3 support')
class LowLevelTests(TestBase):

  def SetUp(self):
    self.rt = ext_runtime.ExternalizedRuntime.Load(self.runtime_def_dir,
                                                   self.env)

  def testErrorPaths(self):
    # Verify that we log an error if a query_user message is received without
    # a prompt.
    self.rt._ProcessMessage(None, {'type': 'query_user'}, None, None, None)
    self.assertEqual(self.err,
                     [('error',
                       ext_runtime._MISSING_FIELD_ERROR.format('prompt',
                                                               'query_user'))])

  def testPromptDefaults(self):
    # Verify that we get the default value when issue query_user while running
    # non-interactively.
    self.can_prompt = False
    result = io.BytesIO()
    self.rt._ProcessMessage(result,
                            {'type': 'query_user', 'prompt': 'hi user',
                             'default': 'my default value'}, None, None, None)
    self.assertEqual(json.loads(result.getvalue())['result'],
                     'my default value')

  def testPromptNoDefault(self):
    # Verify that we get an error when we issue query_user with no default
    # while running interactively.
    self.can_prompt = False
    result = io.BytesIO()
    self.rt._ProcessMessage(result,
                            {'type': 'query_user', 'prompt': 'hi user'},
                            None, None, None)
    self.assertEqual(self.err,
                     [('error',
                       ext_runtime._NO_DEFAULT_ERROR.format('hi user'))])


@test_case.Filters.DoNotRunOnPy3('Deprecated command; no py3 support')
class CommunicationTests(TestBase):

  # pylint:disable=unused-argument
  def ProcessMessageFake(self, plugin_stdin, message, collector, params,
                         runtime_data):
    unused_args = collector
    self.log.append(('msg', message))

  def SetUp(self):
    self.process_message_patch = mock.patch.object(
        ext_runtime.ExternalizedRuntime, '_ProcessMessage',
        new=self.ProcessMessageFake)
    self.process_message_patch.start()

  def TearDown(self):
    self.process_message_patch.stop()

  def testRunPlugin(self):
    rt = ext_runtime.ExternalizedRuntime.Load(self.runtime_def_dir, self.env)
    rt.RunPlugin('fake_section_name', {'python': 'bin/plugin1'},
                 ext_runtime.Params())

    # This output comes from ./testdata/runtime_def/bin/plugin1
    self.assertEqual(
        self.log,
        [('info', 'fake_section_name: this should go to info'),
         ('msg', {'type': 'info', 'message': 'this should also go to info'})])
    self.assertEqual(
        self.err,
        [('warn', 'fake_section_name: this should go to warning')])

  def testPluginNotFound(self):
    rt = ext_runtime.ExternalizedRuntime.Load(self.runtime_def_dir, self.env)
    with self.assertRaises(ext_runtime.PluginInvocationFailed):
      rt.RunPlugin('fake_section_name', {'python': 'bin/does_not_exist'},
                   ext_runtime.Params())


@test_case.Filters.DoNotRunOnPy3('Deprecated command; no py3 support')
class PluginTests(TestBase):

  def testDetect(self):
    rt = ext_runtime.ExternalizedRuntime.Load(self.runtime_def_dir, self.env)
    params = ext_runtime.Params()
    configurator = rt.Detect(self.temp_path, params)
    self.assertIsInstance(configurator,
                          ext_runtime.ExternalRuntimeConfigurator)
    self.assertEqual(configurator.runtime, rt)
    self.assertEqual(configurator.params, params)
    self.assertEqual(configurator.data,
                     {'a': 'got data', 'test_string': 'test value',
                      'user_data': 'user response'})

    # Make sure the prompt gave us back what we expect.
    self.assertIn('gimme some data', self.prompt_message)
    self.assertIn('reasonable default', self.prompt_message)

  def testValidation(self):
    # Make sure everything comes through as we expect it to.
    cfg = {'name': 'foo', 'description': 'this is foo', 'author': 'Joe Foo',
           'detect': {'python': 'python command'},
           'generate_configs': {'files_to_copy': ['first', 'second']},
           'prebuild': {'python': 'pre build command'},
           'postbuild': {'python': 'post build command'}}
    self.assertEqual(ext_runtime.ExternalizedRuntime('path', cfg,
                                                     self.env).config,
                     {'name': 'foo', 'description': 'this is foo',
                      'author': 'Joe Foo',
                      'detect': {'python': 'python command'},
                      'generateConfigs': {'filesToCopy': ['first', 'second']},
                      'prebuild': {'python': 'pre build command'},
                      'postbuild': {'python': 'post build command'}})

    for field in ('generate_configs', 'detect', 'prebuild', 'postbuild'):
      cfg = {field: 'invalid value'}
      with self.assertRaises(ext_runtime.InvalidRuntimeDefinition):
        ext_runtime.ExternalizedRuntime('path', cfg, self.env)

  def testGenerate(self):
    def Fix(unix_path):
      return ext_runtime._NormalizePath('X', unix_path)
    rt = ext_runtime.ExternalizedRuntime(
        Fix('/runtime/def/root'),
        {'generate_configs': {
            'files_to_copy': ['data/foo', 'data/bar', 'data/exists']}},
        self.env)
    params = ext_runtime.Params()
    cfg = ext_runtime.ExternalRuntimeConfigurator(rt, params, {},
                                                  None,
                                                  Fix('/dest/path'),
                                                  self.env)
    copied = []
    # pylint:disable=unused-argument
    def ExistsFake(filename):
      return filename.endswith('exists')
    def IsFileFake(filename):
      return True
    def OpenFake(filename, mode):
      openfile = mock.mock_open(read_data='contents')
      f = openfile()
      def WriteFake(contents):
        copied.append(filename)
      f.write.side_effect = WriteFake
      return f

    with mock.patch.object(os.path, 'exists', new=ExistsFake):
      with mock.patch.object(os.path, 'isfile', new=IsFileFake):
        with mock.patch('gae_ext_runtime.ext_runtime.open', OpenFake,
                        create=True):
          cfg.GenerateConfigs()
          self.assertEqual(sorted(copied),
                           [Fix('dest/path/data/bar'),
                            Fix('dest/path/data/foo')])

    self.assertIn(
        ('print', ext_runtime.WRITING_FILE_MESSAGE.format('data/foo',
                                                          Fix('/dest/path'))),
        self.log)
    self.assertIn(
        ('print', ext_runtime.WRITING_FILE_MESSAGE.format('data/bar',
                                                          Fix('/dest/path'))),
        self.log)
    self.assertIn(
        ('print', ext_runtime.FILE_EXISTS_MESSAGE.format('data/exists')),
        self.log)

  def testGenerateNoWrite(self):
    """Test the ext_runtime generates contents of config files correctly."""
    def Fix(unix_path):
      return ext_runtime._NormalizePath('X', unix_path)
    rt = ext_runtime.ExternalizedRuntime(
        Fix('/runtime/def/root'),
        {'generate_configs': {
            'files_to_copy': ['data/foo', 'data/bar', 'data/exists']}},
        self.env)
    params = ext_runtime.Params()
    cfg = ext_runtime.ExternalRuntimeConfigurator(rt, params, {},
                                                  None,
                                                  Fix('/dest/path'),
                                                  self.env)

    # pylint:disable=unused-argument
    def ExistsFake(filename):
      return filename.endswith('exists')
    def IsFileFake(filename):
      return True
    def OpenFake(filename, mode):
      openfile = mock.mock_open(read_data='contents')
      return openfile()

    with mock.patch.object(os.path, 'exists', new=ExistsFake):
      with mock.patch.object(os.path, 'isfile', new=IsFileFake):
        with mock.patch('gae_ext_runtime.ext_runtime.open', OpenFake,
                        create=True):
          cfg_files = cfg.GenerateConfigData()
          self.assertEqual(['contents', 'contents'],
                           [cfg_file.contents for cfg_file in cfg_files])
          self.assertEqual({'data/bar', 'data/foo'},
                           {cfg_file.filename for cfg_file in cfg_files})

  def testGenerateBadFile(self):
    rt = ext_runtime.ExternalizedRuntime(
        '/runtime/def/root',
        {'generate_configs': {'files_to_copy': ['data/foo', 'data/bar']}},
        self.env)
    params = ext_runtime.Params()
    cfg = ext_runtime.ExternalRuntimeConfigurator(rt, params, {},
                                                  None,
                                                  '/dest/path',
                                                  self.env)
    with mock.patch.object(os.path, 'isfile', new=lambda path: False):
      with self.assertRaises(ext_runtime.InvalidRuntimeDefinition):
        cfg.GenerateConfigs()
      with self.assertRaises(ext_runtime.InvalidRuntimeDefinition):
        cfg.GenerateConfigData()

  def GetConfigurator(self, deploy):
    rt = ext_runtime.ExternalizedRuntime.Load(self.runtime_def_dir, self.env)
    params = ext_runtime.Params(deploy=deploy)
    self.Touch(directory=self.temp_path, name='exists', contents='my contents')
    configurator = rt.Detect(self.temp_path, params)
    return configurator

  def GenerateFromTestRuntime(self, deploy):
    configurator = self.GetConfigurator(deploy)
    return configurator.GenerateConfigs()

  def GenerateConfigDataFromTestRuntime(self, deploy):
    configurator = self.GetConfigurator(deploy)
    return configurator.GenerateConfigData()

  def testPluginGeneratedFiles(self):
    self.GenerateFromTestRuntime(deploy=False)

    self.AssertFileExistsWithContents('this is foo', self.temp_path, 'foo')
    self.assertIn(
        ('print', ext_runtime.WRITING_FILE_MESSAGE.format('foo',
                                                          self.temp_path)),
        self.log)
    self.AssertFileExistsWithContents('this is bar', self.temp_path, 'bar')
    self.assertIn(
        ('print', ext_runtime.WRITING_FILE_MESSAGE.format('bar',
                                                          self.temp_path)),
        self.log)
    self.assertIn(
        ('print', ext_runtime.FILE_EXISTS_MESSAGE.format('exists')),
        self.log)
    info_path = os.path.join(self.temp_path, 'info')
    self.assertTrue(os.path.exists(info_path))
    with open(info_path) as fp:
      self.assertEqual(json.load(fp),
                       {'params': {'deploy': False,
                                   'custom': False,
                                   'runtime': None,
                                   'appinfo': None},
                        'runtime_data': {'a': 'got data',
                                         'test_string': 'test value',
                                         'user_data': 'user response'},
                        'type': 'get_config_response'})

  def testPluginGeneratedFilesNoWrite(self):
    """Test that GenerateConfigData works correctly with plugin."""
    def ExistsFake(filename):
      return filename.endswith('exists')
    with self.StartObjectPatch(os.path, 'exists', side_effect=ExistsFake):
      cfg_files = self.GenerateConfigDataFromTestRuntime(deploy=False)
      self.assertEqual({f.filename for f in cfg_files},
                       {'foo', 'bar', 'info'})
      for gen_file in cfg_files:
        if gen_file.filename == 'foo':
          self.assertEqual(gen_file.contents, 'this is foo')
        elif gen_file.filename == 'bar':
          self.assertEqual(gen_file.contents, 'this is bar')
        elif gen_file.filename == 'info':
          self.assertEqual(json.loads(gen_file.contents),
                           {'params': {'deploy': False,
                                       'custom': False,
                                       'runtime': None,
                                       'appinfo': None},
                            'runtime_data': {'a': 'got data',
                                             'test_string': 'test value',
                                             'user_data': 'user response'},
                            'type': 'get_config_response'})

  def testLoggingDuringDeploy(self):
    # Verify that 'deploy' uses info logging instead of printing.
    self.GenerateFromTestRuntime(deploy=True)
    self.assertIn(
        ('info', ext_runtime.WRITING_FILE_MESSAGE.format('foo',
                                                         self.temp_path)),
        self.log)
    self.assertIn(
        ('info', ext_runtime.WRITING_FILE_MESSAGE.format('bar',
                                                         self.temp_path)),
        self.log)
    self.assertIn(
        ('info', ext_runtime.FILE_EXISTS_MESSAGE.format('exists')),
        self.log)

  def testMaybeWriteAppYaml_AppYamlAlreadyExists(self):
    """Tests that file exists message is printed if app.yaml exists."""
    rt = ext_runtime.ExternalizedRuntime.Load(self.runtime_def_dir, self.env)
    runtime_config = yaml.load(textwrap.dedent("""\
        runtime: python
        env: 2
        entrypoint: run_me_some_python!
        handlers:
        - url: .*
          script: request
        """))
    params = ext_runtime.Params()
    self.Touch(directory=self.temp_path, name='app.yaml',
               contents='my contents')
    configurator = rt.Detect(self.temp_path, params)
    configurator.SetGeneratedAppInfo(runtime_config)
    configurator.MaybeWriteAppYaml()
    self.assertIn(('print',
                   ext_runtime.FILE_EXISTS_MESSAGE.format('app.yaml')),
                  self.log)

  def testMaybeWriteAppYaml_GeneratedAppInfo(self):
    """Tests that file exists message not printed if app.yaml doesn't exist."""
    rt = ext_runtime.ExternalizedRuntime.Load(self.runtime_def_dir, self.env)
    runtime_config = yaml.load(textwrap.dedent("""\
        runtime: python
        env: 2
        entrypoint: run_me_some_python!
        handlers:
        - url: .*
          script: request
        """))
    params = ext_runtime.Params()
    self.Touch(directory=self.temp_path, name='exists', contents='my contents')
    configurator = rt.Detect(self.temp_path, params)
    configurator.SetGeneratedAppInfo(runtime_config)
    configurator.MaybeWriteAppYaml()
    self.assertNotIn(('print',
                      ext_runtime.FILE_EXISTS_MESSAGE.format('app.yaml')),
                     self.log)
    self.AssertFileExistsWithContents(yaml.dump(runtime_config),
                                      self.temp_path,
                                      'app.yaml')

if __name__ == '__main__':
  test_case.main()
