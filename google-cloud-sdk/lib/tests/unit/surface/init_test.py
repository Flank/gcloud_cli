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

"""Test for the gcloud init."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
import os
import re
import sys

from googlecloudsdk.api_lib.cloudresourcemanager import projects_api
from googlecloudsdk.calliope import exceptions as c_exc
from googlecloudsdk.core import config
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import properties
from googlecloudsdk.core.configurations import named_configs
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.credentials import store as c_store
from googlecloudsdk.core.diagnostics import network_diagnostics
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import platforms
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.apitools import http_error

import mock
import six
from six.moves import zip


def _GetWelcomeMessage():
  return ('Welcome! This command will take you through the configuration of '
          'gcloud.\n\n')


def _GetCurrentConfigMessage(config_name):
  return ('Your current configuration has been set to: [{}]\n\n'
          .format(config_name))


def _GetCurrentSettings(config_name, log_http=False):
  lines = [
      'Settings from your current configuration [{}] are:'.format(config_name),
      'component_manager:',
      '  disable_update_check: \'True\'',
      'core:',
      '  account: fake_account',
      '  check_gce_metadata: \'False\'',
      '  disable_usage_reporting: \'True\'',
      '  interactive_ux_style: TESTING']
  if log_http:
    lines.append('  log_http: \'true\'')
  lines += [
      '  should_prompt_to_enable_api: \'False\'',
      '  user_output_enabled: \'True\'',
      '',
      ''
  ]
  return '\n'.join(lines)


def _GetPickAccount(accounts, preselected_account=None):
  if preselected_account and preselected_account not in accounts:
    if not accounts:
      return ('\n[{}] is not a credentialed account.\n'
              .format(preselected_account))
    return ('\n[{}] is not one of your credentialed accounts [{}].\n'
            .format(preselected_account, ','.join(accounts)))
  return ('{{"ux": "PROMPT_CHOICE", "message": "Choose the account you would '
          'like to use to perform operations for this configuration:", '
          '"choices": {}}}\n'
          .format(json.dumps(accounts + ['Log in with a new account'])))


def _GetPickConfigurationMessage(inactive_configs, current_config=None,
                                 new_config=True):
  choices = []
  if current_config:
    choices.append(
        'Re-initialize this configuration [{}] with new settings '
        .format(current_config))
  choices.append('Create a new configuration')
  for c in inactive_configs:
    choices.append(
        'Switch to and re-initialize existing configuration: [{}]'.format(c))

  lines = [console_io.JsonUXStub(
      console_io.UXElementType.PROMPT_CHOICE,
      message='Pick configuration to use:',
      choices=choices)]
  if new_config:
    lines.append(
        '{"ux": "PROMPT_RESPONSE", "message": "Enter configuration name. Names '
        'start with a lower case letter and contain only lower case letters '
        'a-z, digits 0-9, and hyphens \'-\':  "}')
  else:
    # If active config or no config is chosen, a blank line prints.
    lines.append('')
  return '\n'.join(lines)


def _GetDiagnosticsMessage(errors=False, exit_diagnostic=True):
  result = ('You can skip diagnostics next time by using the following flag:\n'
            '  gcloud init --skip-diagnostics\n\n')
  if errors:
    result += (
        '{"ux": "PROMPT_CONTINUE", "message": "Network errors detected.", '
        '"prompt_string": "Would you like to continue anyway"}\n')
    if exit_diagnostic:
      result += ('You can re-run diagnostics with the following command:\n'
                 '  gcloud info --run-diagnostics\n\n')
  return result


def _GetLoginPromptMessage():
  return ('{"ux": "PROMPT_CONTINUE", "prompt_string": "You must log in to '
          'continue. Would you like to log in"}\n')


def _GetLoggedInAsMessage(account):
  return 'You are logged in as: [{}].\n\n'.format(account)


def _GetNoProjectsMessage():
  return ('{"ux": "PROMPT_CONTINUE", "message": "This account has no projects."'
          ', "prompt_string": "Would you like to create one?"}\n')


def _GetEnterProjectMessage():
  return (
      '{"ux": "PROMPT_RESPONSE", "message": "Enter a Project ID. Note that a '
      'Project ID CANNOT be changed later.\\nProject IDs must be 6-30 '
      'characters (lowercase ASCII, digits, or\\nhyphens) in length and start '
      'with a lowercase letter. "}')


def _GetPickProjectMessage(projects, created=None,
                           preselected_project=None,
                           create_error=None):
  lines = []
  if preselected_project and preselected_project not in projects:
    lines.extend([
        '{{"ux": "PROMPT_CONTINUE", "message": "[{}] is not one of your '
        'projects [{}]. ", "prompt_string": "Would you like to create it?"}}'
        .format(preselected_project, ','.join(projects)),
        '',
    ])
    return '\n'.join(lines)

  if projects:
    lines.append(
        '{{"ux": "PROMPT_CHOICE", "message": "Pick cloud project to use: ", '
        '"choices": {}}}'
        .format(json.dumps(sorted(projects) + ['Create a new project'])))
  else:
    lines.extend([
        '{"ux": "PROMPT_CONTINUE", "message": "This account has no projects.", '
        '"prompt_string": "Would you like to create it?"}'
    ])
  if created:
    lines.extend([
        '{"ux": "PROMPT_RESPONSE", "message": "Enter a Project ID. Note that '
        'a Project ID CANNOT be changed later.\\nProject IDs must be 6-30 '
        'characters (lowercase ASCII, digits, or\\nhyphens) in length and '
        'start with a lowercase letter. "}'])
    if create_error:
      lines[-1] += 'WARNING: Project creation failed: {}'.format(create_error)
      lines.extend([
          'Please make sure to create the project [{}] using'.format(created),
          '    $ gcloud projects create {}'.format(created),
          'or change to another project using',
          '    $ gcloud config set project <PROJECT ID>',
          ''])
  else:
    if create_error:
      raise ValueError('Cannot pick a message with a creation failure but no '
                       'creation message.')
    lines.append('')
  return '\n'.join(lines)


def _GetCurrentProjectMessage(project):
  return 'Your current project has been set to: [{}].\n\n'.format(project)


def _GetComputeMessage(skip=False, zone=None, region=None, zones=None,
                       regions=None):
  if skip:
    return (
        'Not setting default zone/region (this feature makes it easier to use\n'
        '[gcloud compute] by setting an appropriate default value for the\n'
        '--zone and --region flag).\n'
        'See https://cloud.google.com/compute/docs/gcloud-compute section on '
        'how to set\n'
        'default compute region and zone manually. If you would like [gcloud '
        'init] to be\n'
        'able to do this for you the next time you run it, make sure the\n'
        'Compute Engine API is enabled for your project on the\n'
        'https://console.developers.google.com/apis page.\n\n')

  lines = []
  if zones:
    lines.append(
        '{"ux": "PROMPT_CONTINUE", "prompt_string": "Do you want to configure '
        'a default Compute Region and Zone?"}')
    lines.append(
        r'{{"ux": "PROMPT_CHOICE", "message": "Which Google Compute Engine '
        r'zone would you like to use as project default?\nIf you do not '
        r'specify a zone via a command line flag while working with Compute '
        r'Engine resources, the default is assumed.", "choices": {}}}'
        .format(json.dumps(zones + ['Do not set default zone'])))
  if regions:
    lines.append(
        r'{{"ux": "PROMPT_CHOICE", "message": "Which Google Compute Engine '
        r'region would you like to use as project default?\nIf you do not '
        r'specify a region via a command line flag while working with Compute '
        r'Engine resources, the default is assumed.", "choices": {}}}'
        .format(json.dumps(regions + ['Do not set default region'])))
    lines.append('')
    return '\n'.join(lines)

  if zone and region:
    lines.extend([
        'Your project default Compute Engine zone has been set to [{}].'
        .format(zone),
        'You can change it by running [gcloud config set compute/zone NAME].\n',
        'Your project default Compute Engine region has been set to [{}].'
        .format(region),
        'You can change it by running [gcloud config set compute/region '
        'NAME].\n\n'
    ])
  else:
    lines.append(
        '{"ux": "PROMPT_CONTINUE", "prompt_string": "Do you want to configure '
        'a default Compute Region and Zone?"}\n')

  return '\n'.join(lines)


def _GetBotoMessage(error=False):
  if error:
    return (
        'Error creating a default .boto configuration file. '
        'Please run [gsutil config -n] if you would like to create this file.\n'
    )
  return (
      'Created a default .boto configuration file at [{}]. See this file and\n'
      '[https://cloud.google.com/storage/docs/gsutil/commands/config] for '
      'more\n'
      'information about configuring Google Cloud Storage.\n'
      .format(os.path.join(files.GetHomeDir(), '.boto')))


def _GetReadyToUseMessage(account, project, zone=None, region=None):
  lines = [
      'Your Google Cloud SDK is configured and ready to use!\n',
      '* Commands that require authentication will use {} by default'
      .format(account),
      '* Commands will reference project `{}` by default'.format(project)
  ]
  if region:
    lines.append('* Compute Engine commands will use region `{}` by default'
                 .format(region))
  if zone:
    lines.append('* Compute Engine commands will use zone `{}` by default\n'
                 .format(zone))
  lines.extend([
      'Run `gcloud help config` to learn how to change individual settings\n',
      'This gcloud configuration is called [default]. You can create additional'
      ' configurations if you work with multiple accounts and/or projects.',
      'Run `gcloud topic configurations` to learn more.',
      '',
      'Some things to try next:',
      '',
      '* Run `gcloud --help` to see the Cloud Platform services you can '
      'interact with. And run `gcloud help COMMAND` to get help on any '
      'gcloud command.',
      '* Run `gcloud topic --help` to learn about advanced features of the SDK '
      'like arg files and output formatting',
      ''
  ])
  return '\n'.join(lines)


def Obj(d):
  name = b'obj' if six.PY2 else 'obj'
  return type(name, (object,), d)


def GetFakeCred(account):
  cred_mock = mock.MagicMock()
  cred_mock.id_token = {'email': account}
  properties.VALUES.core.account.Set(account)
  return cred_mock


class Executor(object):
  """Helper to register mock actions to be taken on command executions."""

  def __init__(self, cli):
    self.cli = cli
    self.has_been_executed = []
    self.to_execute = []

  def Register(self, command, action):
    self.to_execute.append((tuple(command), action))

  def Execute(self, command, call_arg_complete=None):
    del call_arg_complete  # Unused in Execute
    cmd = tuple(param for param in command if param
                not in ['--no-user-output-enabled', '--verbosity=none'])
    if not self.to_execute or cmd != self.to_execute[0][0]:
      raise ValueError(
          'Command {0} is called but is not expected. Expected commands: {1}'
          .format(cmd, [cmd[0] for cmd in self.to_execute]))
    cmd, action = self.to_execute.pop(0)
    self.has_been_executed.append(cmd)
    if isinstance(action, BaseException):
      raise action
    if hasattr(action, '__call__'):
      return action(command)
    return action

  def IsRegisteredPath(self, cmd):
    if self.to_execute:
      for to_execute in self.to_execute:
        key = to_execute[0]
        if len(cmd) <= len(key):
          matches = True
          for c, k in zip(cmd, key):
            if c != k:
              matches = False
              break
          if matches:
            return True
    raise RuntimeError('Command [{0}] has not been registered'.format(cmd))


class MockExecutionUtils(object):
  """Helper to mock execution_utils.Exec."""

  def __init__(self):
    self.Reset()

  def Reset(self):
    self.commands_to_execute = []

  def Exec(self, command, *unused_args, **unused_kwargs):
    if not self.commands_to_execute:
      raise ValueError('Command: {0} is called but not expected. No calls '
                       'expected.'.format(command))
    next_command, return_code = self.commands_to_execute[0]

    if command != next_command:
      raise ValueError('Command {0} is called but not expected. Expected '
                       'command: {1}'.format(command, next_command))

    self.commands_to_execute.pop(0)
    return return_code

  def Register(self, command, return_code):
    self.commands_to_execute.append((command, return_code))


class InitNoAuthTest(
    cli_test_base.CliTestBase,
    sdk_test_base.WithFakeAuth,
    sdk_test_base.WithOutputCapture,
    test_case.WithInput):

  def Project(self):
    return None

  def ResetExecutor(self):
    self.executor = Executor(self.cli)
    self.run_mock = self.StartObjectPatch(
        self.cli, 'Execute', side_effect=self.executor.Execute)

  def ResetExecutionUtils(self):
    self.mock_execution_utils = MockExecutionUtils()
    self.exec_mock = self.StartObjectPatch(
        execution_utils, 'Exec', side_effect=self.mock_execution_utils.Exec)

  def SetUp(self):
    self.actual_execute = self.cli.Execute
    is_valid_command = self.cli.IsValidCommand
    def CheckCommand(cmd):
      if not is_valid_command(cmd):
        raise RuntimeError('Unknown command [{0}]'.format(cmd))
      return self.executor.IsRegisteredPath(cmd)
    self.StartObjectPatch(
        self.cli, 'IsValidCommand', side_effect=CheckCommand)
    self.check_network_mock = self.StartObjectPatch(
        network_diagnostics.NetworkDiagnostic, 'RunChecks', return_value=True)
    self.projects_list_mock = self.StartObjectPatch(projects_api, 'List')
    self.projects_create_mock = self.StartObjectPatch(projects_api, 'Create')
    self.projects_list_mock.return_value = iter([])
    self.ResetExecutor()
    self.ResetExecutionUtils()

    # Mocks to support gsutil calls.
    self.fake_sdk_root = 'fakesdkroot'
    self.mock_sdk_root = self.StartPropertyPatch(
        config.Paths, 'sdk_root', return_value=self.fake_sdk_root)
    self.boto_path = files.ExpandHomeDir(os.path.join('~', '.boto'))

    # Remove the .boto file if it exists, otherwise the test runs won't create
    # it. These tests don't actually create the .boto file, so we don't need to
    # clean it up after the run. The code under test will only create this file
    # if it doesn't already exist, so we need to make sure it doesn't exist
    # before the test runs.
    if os.path.exists(self.boto_path):
      os.remove(self.boto_path)

    paths = config.Paths()
    if os.path.exists(paths.named_config_directory):
      files.RmTree(paths.named_config_directory)
    if os.path.isfile(paths.named_config_activator_path):
      os.remove(paths.named_config_activator_path)
    properties.VALUES.app.runtime_root.Set(None)

  def TearDown(self):
    if sys.exc_info():
      # There is already an exception, don't try to validate things that didn't
      # get run because they just mask the real exception.
      return
    for remaining_commands in (self.executor.to_execute,
                               self.mock_execution_utils.commands_to_execute):
      if remaining_commands:
        self.fail('Following commands were expected but not called: {0}'
                  .format(remaining_commands))

  def AssertProperties(self, props):
    for prop, value in six.iteritems(props):
      path = prop.split('/')
      cfg = properties.VALUES.AllValues()
      for part in path:
        self.assertIn(part, cfg)
        cfg = cfg[part]
      self.assertEqual(value, cfg)

  def AssertActiveConfig(self, name):
    configurations = self.actual_execute(
        ['config', 'configurations', 'list', '--no-user-output-enabled'])
    self.assertIn((name, True),
                  [(c['name'], c['is_active']) for c in configurations],
                  '[{0}] is not active'.format(name))

  def RunCmd(self, *args):
    self.Run(('init') + tuple(args))

  def RunScenario(self, scenario, exec_commands=None, console_only=False,
                  skip_diagnostics=False, preselected_account=None,
                  preselected_project=None, log_http=False):
    if exec_commands is None:
      exec_commands = []
    init_cmd = ['init']
    if console_only:
      init_cmd += ['--console-only']
    if skip_diagnostics:
      init_cmd += ['--skip-diagnostics']
    if preselected_account:
      init_cmd += ['--account', preselected_account]
    if preselected_project:
      init_cmd += ['--project', preselected_project]
    if log_http:
      init_cmd += ['--log-http']
    self.executor.Register(init_cmd, self.actual_execute)
    for command in scenario:
      if log_http:
        command[0].append('--log-http')
      self.executor.Register(*command)
    for command, return_code in exec_commands:
      if log_http:
        command[0] += ' --log-http'
      self.mock_execution_utils.Register(command, return_code)
    self.Run(init_cmd)

  def WithConfigurations(self, config_names,
                         active_config=None, picked_config=None):
    if not config_names:
      return []
    for name in config_names:
      self.actual_execute(['config', 'configurations', 'create', name])
    if not active_config:
      active_config = config_names[0]
    self.actual_execute(['config', 'configurations', 'activate',
                         active_config])
    if picked_config:
      try:
        idx = config_names.index(picked_config)
      except ValueError:
        self.WriteInput('2')  # Create
        self.WriteInput(picked_config)
      else:
        if picked_config == active_config:
          self.WriteInput('1')
        else:
          active_idx = config_names.index(active_config)
          if idx < active_idx:  # Is picked one before active
            self.WriteInput(str(idx + 3))  # Add extra since active is first
          else:
            self.WriteInput(str(idx + 2))

    return []

  def WithAuth(self, credentials, login=None, browser=True,
               selected_account=None, selected_number=None,
               selected_unknown=False, login_continue_response='Y'):
    if not login:
      login = selected_account
    if not credentials:
      self.WriteInput(login_continue_response)
    commands = []
    self.StartObjectPatch(c_store, 'AvailableAccounts',
                          return_value=credentials)
    if ((not credentials and login_continue_response == 'Y')
        or not selected_account or selected_unknown):
      commands += [(['auth', 'login', '--force', '--brief'] +
                    ([] if browser else ['--no-launch-browser']),
                    lambda cmd: GetFakeCred(login) if login else None)]

    if selected_account:
      if selected_number:
        self.WriteInput(str(selected_number))
    return commands

  def WithProjects(self, projects, selected_project=None, create_project=None):
    results = [Obj({'projectId': project}) for project in projects]
    self.projects_list_mock.return_value = iter(results)
    commands = []
    if not selected_project and len(projects) == 1:
      selected_project = projects[0]
    if selected_project:
      if create_project:
        self.WriteInput(selected_project + '\n' + create_project)
      else:
        self.WriteInput(selected_project + '\n')
    return commands

  def WithRegions(self, meta_zone=None, meta_region=None,
                  actual_meta_zone_region=None,
                  exception=None, region_list=None, zone_list=None,
                  zone_choice=None, region_choice=None,
                  auto_select_region=None):
    if exception is not None:
      return [(['compute', 'project-info', 'describe', '--quiet'], exception)]

    project_info = None
    if meta_zone or meta_region:
      items = []
      if meta_zone:
        items.append({'key': 'google-compute-default-zone', 'value': meta_zone})
      if meta_region:
        items.append({'key': 'google-compute-default-region',
                      'value': meta_region})
      project_info = {
          'commonInstanceMetadata': {
              'items': items
          }
      }
    elif region_list or zone_list:
      self.WriteInput('Y')
    else:
      self.WriteInput('N')

    commands = [
        (['compute', 'project-info', 'describe', '--quiet'], project_info),
    ]
    if not actual_meta_zone_region:
      actual_meta_zone_region = meta_region
    if meta_zone:
      commands += [
          (['compute', 'zones', 'describe', meta_zone],
           {'name': meta_zone, 'region': actual_meta_zone_region}),
      ]
    if meta_region:
      commands += [
          (['compute', 'regions', 'describe', meta_region],
           {'name': meta_region}),
      ]
    else:
      commands.append((['compute', 'zones', 'list'], zone_list))
      if zone_choice is not None:
        self.WriteInput(str(zone_choice))
        if not isinstance(zone_choice, six.string_types + (int,)):
          raise ValueError(('zone_choice [{zone_choice}] should be an int or '
                            'str, was a [{choice_type}]').format(
                                zone_choice=zone_choice,
                                choice_type=type(zone_choice)))

        if region_list is not None:
          commands.append((['compute', 'regions', 'list'], region_list))
      if auto_select_region is not None:
        commands += [
            (['compute', 'regions', 'describe', auto_select_region],
             {'name': auto_select_region}),
        ]
      else:
        commands.append((['compute', 'regions', 'list'], region_list))
        if region_choice is not None:
          self.WriteInput(str(region_choice))
    return commands

  def WithGsutilConfig(self, return_code=0):
    current_os = platforms.OperatingSystem.Current()
    if current_os == platforms.OperatingSystem.WINDOWS:
      gsutil = 'gsutil.cmd'
    elif current_os == platforms.OperatingSystem.MACOSX:
      gsutil = 'gsutil'
    else:
      gsutil = 'gsutil'
    gsutil_path = os.path.join(self.fake_sdk_root, 'bin', gsutil)
    args = [gsutil_path, 'config', '-n', '-o', self.boto_path]
    if current_os == platforms.OperatingSystem.WINDOWS:
      args = ['cmd', '/c'] + args
    return [(args, return_code)]

  def WithContinueWhileStillNetworkIssues(self, continue_anyway=True):
    self.WriteInput('Y' if continue_anyway else 'N')
    return []

  def testNoAuthExit(self):
    self.RunScenario(self.WithConfigurations([]) + self.WithAuth([]))
    self.AssertActiveConfig('default')
    self.assertMultiLineEqual(
        _GetWelcomeMessage() +
        _GetCurrentConfigMessage('default') +
        _GetDiagnosticsMessage() +
        _GetLoginPromptMessage(),
        self.GetErr())
    self.AssertOutputEquals('')

  def testNoProjects(self):
    self.RunScenario(
        self.WithConfigurations([]) +
        self.WithAuth([], login='foo@google.com') +
        self.WithProjects([]))
    self.AssertProperties({
        'core/account': 'foo@google.com',
    })
    self.AssertActiveConfig('default')
    self.assertMultiLineEqual('', self.GetOutput())
    self.assertMultiLineEqual(
        _GetWelcomeMessage() +
        _GetCurrentConfigMessage('default') +
        _GetDiagnosticsMessage() +
        _GetLoginPromptMessage() +
        _GetLoggedInAsMessage('foo@google.com') +
        _GetNoProjectsMessage() +
        _GetEnterProjectMessage(),
        self.GetErr()
    )

  def testNetworkIssuesExit(self):
    self.check_network_mock.return_value = False
    self.RunScenario(
        self.WithConfigurations([]) +
        self.WithContinueWhileStillNetworkIssues(False))
    self.assertTrue(self.check_network_mock.called)
    self.assertMultiLineEqual(
        _GetWelcomeMessage() +
        _GetCurrentConfigMessage('default') +
        _GetDiagnosticsMessage(errors=True, exit_diagnostic=True),
        self.GetErr()
    )
    self.AssertActiveConfig('default')

  def testNetworkIssuesContinue(self):
    self.check_network_mock.return_value = False
    self.RunScenario(
        self.WithConfigurations([]) +
        self.WithContinueWhileStillNetworkIssues(True) +
        self.WithAuth([], login='foo@google.com') +
        self.WithProjects(['golden-project']),
        self.WithGsutilConfig())
    self.AssertActiveConfig('default')
    self.assertTrue(self.check_network_mock.called)
    self.assertMultiLineEqual('', self.GetOutput())
    self.assertMultiLineEqual(
        _GetWelcomeMessage() +
        _GetCurrentConfigMessage('default') +
        _GetDiagnosticsMessage(errors=True, exit_diagnostic=False) +
        _GetLoginPromptMessage() +
        _GetLoggedInAsMessage('foo@google.com') +
        _GetPickProjectMessage(['golden-project']) +
        _GetCurrentProjectMessage('golden-project') +
        _GetComputeMessage(skip=True) +
        _GetBotoMessage() +
        _GetReadyToUseMessage('foo@google.com', 'golden-project'),
        self.GetErr()
    )

  def testChangeCredentials(self):
    self.RunScenario(
        self.WithConfigurations([]) +
        self.WithAuth([]))
    self.assertMultiLineEqual('', self.GetOutput())
    self.assertMultiLineEqual(
        _GetWelcomeMessage() +
        _GetCurrentConfigMessage('default') +
        _GetDiagnosticsMessage() +
        _GetLoginPromptMessage(),
        self.GetErr()
    )

  def testChangeCredentialsWithConfigVar(self):
    # If the configuration is overridden, we just use that for the name even
    # though it does not exist yet.
    os.environ[config.CLOUDSDK_ACTIVE_CONFIG_NAME] = 'foo'
    self.RunScenario(
        self.WithConfigurations([]) +
        self.WithAuth([]))
    self.assertMultiLineEqual('', self.GetOutput())
    self.assertMultiLineEqual(
        _GetWelcomeMessage() +
        _GetCurrentConfigMessage('foo') +
        _GetDiagnosticsMessage() +
        _GetLoginPromptMessage(),
        self.GetErr()
    )

  def testChangeCredentialsWithConfigVarExistingConfigs(self):
    # If the configuration is overridden, we just use that for the name even
    # though it does not exist yet.
    os.environ[config.CLOUDSDK_ACTIVE_CONFIG_NAME] = 'foo'
    named_configs.ConfigurationStore.CreateConfig('good-one')
    self.RunScenario(
        self.WithConfigurations([]) +
        self.WithAuth([]))
    self.assertMultiLineEqual('', self.GetOutput())
    self.assertMultiLineEqual(
        _GetWelcomeMessage() +
        _GetCurrentConfigMessage('foo') +
        _GetDiagnosticsMessage() +
        _GetLoginPromptMessage(),
        self.GetErr()
    )

  def testSingleProjectNotSelected(self):
    self.RunScenario(
        self.WithConfigurations([]) +
        self.WithAuth([], login='foo@google.com') +
        self.WithProjects(['golden-project']) +
        self.WithRegions(),
        self.WithGsutilConfig())

    self.AssertProperties({
        'core/account': 'foo@google.com',
        'core/project': 'golden-project',
    })
    self.AssertActiveConfig('default')

    self.assertMultiLineEqual('', self.GetOutput())
    self.assertMultiLineEqual(
        _GetWelcomeMessage() +
        _GetCurrentConfigMessage('default') +
        _GetDiagnosticsMessage() +
        _GetLoginPromptMessage() +
        _GetLoggedInAsMessage('foo@google.com') +
        _GetPickProjectMessage(['golden-project']) +
        _GetCurrentProjectMessage('golden-project') +
        _GetComputeMessage(skip=False) +
        _GetBotoMessage() +
        _GetReadyToUseMessage('foo@google.com', 'golden-project'),
        self.GetErr()
    )

  def testSingleProjectSelected(self):
    self.RunScenario(
        self.WithConfigurations([]) +
        self.WithAuth([], login='foo@google.com') +
        self.WithProjects(['golden-project']) +
        self.WithRegions(meta_zone='good-zone', meta_region='bad-region'),
        self.WithGsutilConfig())
    self.AssertProperties({
        'compute/zone': 'good-zone',
        'compute/region': 'bad-region',
        'core/account': 'foo@google.com',
        'core/project': 'golden-project',
    })
    self.AssertActiveConfig('default')
    self.assertMultiLineEqual('', self.GetOutput())

    self.assertMultiLineEqual(
        _GetWelcomeMessage() +
        _GetCurrentConfigMessage('default') +
        _GetDiagnosticsMessage() +
        _GetLoginPromptMessage() +
        _GetLoggedInAsMessage('foo@google.com') +
        _GetPickProjectMessage(['golden-project']) +
        _GetCurrentProjectMessage('golden-project') +
        _GetComputeMessage(zone='good-zone', region='bad-region') +
        _GetBotoMessage() +
        _GetReadyToUseMessage(
            'foo@google.com', 'golden-project',
            zone='good-zone', region='bad-region'),
        self.GetErr()
    )

  def testSingleProjectSelected2222(self):
    self.RunScenario(
        self.WithConfigurations([]) +
        self.WithAuth([], login='foo@google.com') +
        self.WithProjects(['other-project'], selected_project='2',
                          create_project='golden-project') +
        self.WithRegions(meta_zone='good-zone', meta_region='bad-region'),
        self.WithGsutilConfig())
    self.AssertProperties({
        'compute/zone': 'good-zone',
        'compute/region': 'bad-region',
        'core/account': 'foo@google.com',
        'core/project': 'golden-project',
    })
    self.AssertActiveConfig('default')
    self.assertMultiLineEqual('', self.GetOutput())

    self.assertMultiLineEqual(
        _GetWelcomeMessage() +
        _GetCurrentConfigMessage('default') +
        _GetDiagnosticsMessage() +
        _GetLoginPromptMessage() +
        _GetLoggedInAsMessage('foo@google.com') +
        _GetPickProjectMessage(['other-project'], created='golden-project') +
        _GetCurrentProjectMessage('golden-project') +
        _GetComputeMessage(zone='good-zone', region='bad-region') +
        _GetBotoMessage() +
        _GetReadyToUseMessage(
            'foo@google.com', 'golden-project',
            zone='good-zone', region='bad-region'),
        self.GetErr()
    )

  def testSingleProjectCreateFails(self):
    create_error = http_error.MakeHttpError(
        code=409, message='Message.')
    self.projects_create_mock.side_effect = create_error
    self.RunScenario(
        self.WithConfigurations([]) +
        self.WithAuth([], login='foo@google.com') +
        self.WithProjects(['other-project'], selected_project='2',
                          create_project='taken-project'))
    self.assertMultiLineEqual(
        _GetWelcomeMessage() +
        _GetCurrentConfigMessage('default') +
        _GetDiagnosticsMessage() +
        _GetLoginPromptMessage() +
        _GetLoggedInAsMessage('foo@google.com') +
        _GetPickProjectMessage(['other-project'], created='taken-project',
                               create_error=str(create_error)),
        self.GetErr())

  def testNoProjectsUnknownPreSelected(self):
    preselected_project = 'golden-project'
    projects = []
    self.RunScenario(
        self.WithConfigurations([]) +
        self.WithAuth([], login='foo@google.com') +
        self.WithProjects(projects, selected_project=preselected_project) +
        self.WithRegions(meta_zone='good-zone', meta_region='bad-region'),
        self.WithGsutilConfig(), preselected_project=preselected_project)
    self.AssertProperties({
        'core/account': 'foo@google.com',
    })
    self.assertMultiLineEqual('', self.GetOutput())

    self.assertMultiLineEqual(
        _GetWelcomeMessage() +
        _GetCurrentConfigMessage('default') +
        _GetDiagnosticsMessage() +
        _GetLoginPromptMessage() +
        _GetLoggedInAsMessage('foo@google.com') +
        _GetPickProjectMessage([]) +
        _GetCurrentProjectMessage('golden-project') +
        _GetComputeMessage(zone='good-zone', region='bad-region') +
        _GetBotoMessage() +
        _GetReadyToUseMessage(
            'foo@google.com', 'golden-project',
            zone='good-zone', region='bad-region'),
        self.GetErr()
    )

  def testOneProjectUnknownPreSelected(self):
    preselected_project = 'unknown-project'
    projects = ['golden-project']
    self.RunScenario(
        self.WithConfigurations([]) +
        self.WithAuth([], login='foo@google.com') +
        self.WithProjects(projects, selected_project=preselected_project) +
        self.WithRegions(meta_zone='good-zone', meta_region='bad-region'),
        self.WithGsutilConfig(), preselected_project=preselected_project)
    self.AssertProperties({
        'core/account': 'foo@google.com',
    })
    self.assertMultiLineEqual('', self.GetOutput())

    self.assertMultiLineEqual(
        _GetWelcomeMessage() +
        _GetCurrentConfigMessage('default') +
        _GetDiagnosticsMessage() +
        _GetLoginPromptMessage() +
        _GetLoggedInAsMessage('foo@google.com') +
        _GetPickProjectMessage(
            projects, preselected_project=preselected_project) +
        _GetCurrentProjectMessage('unknown-project') +
        _GetComputeMessage(zone='good-zone', region='bad-region') +
        _GetBotoMessage() +
        _GetReadyToUseMessage(
            'foo@google.com', 'unknown-project',
            zone='good-zone', region='bad-region'),
        self.GetErr()
    )

  def testOneProjectKnownPreSelected(self):
    preselected_project = 'golden-project'
    projects = [preselected_project]
    self.RunScenario(
        self.WithConfigurations([]) +
        self.WithAuth([], login='foo@google.com') +
        self.WithProjects(projects, selected_project=preselected_project) +
        self.WithRegions(meta_zone='good-zone', meta_region='bad-region'),
        self.WithGsutilConfig(), preselected_project=preselected_project)
    self.AssertProperties({
        'compute/zone': 'good-zone',
        'compute/region': 'bad-region',
        'core/account': 'foo@google.com',
        'core/project': preselected_project,
    })
    self.assertMultiLineEqual('', self.GetOutput())

    self.assertMultiLineEqual(
        _GetWelcomeMessage() +
        _GetCurrentConfigMessage('default') +
        _GetDiagnosticsMessage() +
        _GetLoginPromptMessage() +
        _GetLoggedInAsMessage('foo@google.com') +
        _GetCurrentProjectMessage('golden-project') +
        _GetComputeMessage(zone='good-zone', region='bad-region') +
        _GetBotoMessage() +
        _GetReadyToUseMessage(
            'foo@google.com', 'golden-project',
            zone='good-zone', region='bad-region'),
        self.GetErr()
    )

  def testMultipleProjectsKnownPreSelected(self):
    preselected_project = 'golden-project'
    projects = [preselected_project, 'old-project']
    self.RunScenario(
        self.WithConfigurations([]) +
        self.WithAuth([], login='foo@google.com') +
        self.WithProjects(projects, selected_project=preselected_project) +
        self.WithRegions(meta_zone='good-zone', meta_region='bad-region'),
        self.WithGsutilConfig(), preselected_project=preselected_project)
    self.AssertProperties({
        'compute/zone': 'good-zone',
        'compute/region': 'bad-region',
        'core/account': 'foo@google.com',
        'core/project': preselected_project,
    })
    self.assertMultiLineEqual('', self.GetOutput())

    self.assertMultiLineEqual(
        _GetWelcomeMessage() +
        _GetCurrentConfigMessage('default') +
        _GetDiagnosticsMessage() +
        _GetLoginPromptMessage() +
        _GetLoggedInAsMessage('foo@google.com') +
        _GetCurrentProjectMessage('golden-project') +
        _GetComputeMessage(zone='good-zone', region='bad-region') +
        _GetBotoMessage() +
        _GetReadyToUseMessage(
            'foo@google.com', 'golden-project',
            zone='good-zone', region='bad-region'),
        self.GetErr()
    )

  def testMultipleProjectsUnknownPreSelected(self):
    preselected_project = 'unknown-project'
    projects = ['golden-project', 'old-project']
    self.RunScenario(
        self.WithConfigurations([]) +
        self.WithAuth([], login='foo@google.com') +
        self.WithProjects(projects, selected_project=preselected_project) +
        self.WithRegions(meta_zone='good-zone', meta_region='bad-region'),
        self.WithGsutilConfig(), preselected_project=preselected_project)
    self.AssertProperties({
        'core/account': 'foo@google.com',
    })
    self.assertMultiLineEqual('', self.GetOutput())

    self.assertMultiLineEqual(
        _GetWelcomeMessage() +
        _GetCurrentConfigMessage('default') +
        _GetDiagnosticsMessage() +
        _GetLoginPromptMessage() +
        _GetLoggedInAsMessage('foo@google.com') +
        _GetPickProjectMessage(
            projects, preselected_project=preselected_project) +
        _GetCurrentProjectMessage(preselected_project) +
        _GetComputeMessage(zone='good-zone', region='bad-region') +
        _GetBotoMessage() +
        _GetReadyToUseMessage(
            'foo@google.com', preselected_project,
            zone='good-zone', region='bad-region'),
        self.GetErr()
    )

  def testMultipleProjectsTypoSelected(self):
    selected_project = 'yuor-project'
    projects = ['your-project', 'project2']
    self.RunScenario(
        self.WithConfigurations([]) +
        self.WithAuth([], login='foo@google.com') +
        self.WithProjects(projects, selected_project=selected_project) +
        self.WithRegions(meta_zone='good-zone', meta_region='bad-region'),
        self.WithGsutilConfig())
    self.AssertProperties({
        'core/account': 'foo@google.com',
    })
    self.assertMultiLineEqual('', self.GetOutput())

    self.assertMultiLineEqual(
        _GetWelcomeMessage() +
        _GetCurrentConfigMessage('default') +
        _GetDiagnosticsMessage() +
        _GetLoginPromptMessage() +
        _GetLoggedInAsMessage('foo@google.com') +
        _GetPickProjectMessage(projects),
        self.GetErr()
    )

  def testNoAccountsUnknownSelected(self):
    credentials = []
    self.RunScenario(
        self.WithConfigurations([]) +
        self.WithAuth(credentials) +
        self.WithGsutilConfig())
    self.AssertProperties({
        'core/account': 'fake_account',
    })
    self.assertMultiLineEqual('', self.GetOutput())

    self.assertMultiLineEqual(
        _GetWelcomeMessage() +
        _GetCurrentConfigMessage('default') +
        _GetDiagnosticsMessage() +
        _GetLoginPromptMessage(),
        self.GetErr()
    )

  def testOneAccountUnknownSelected(self):
    active_account = 'foo@google.com'
    selected_account = 'unknown@google.com'
    credentials = [active_account]
    self.RunScenario(
        self.WithConfigurations([]) +
        self.WithAuth(credentials,
                      selected_account=selected_account,
                      selected_number=2,
                      selected_unknown=True) +
        self.WithGsutilConfig())
    self.AssertProperties({
        'core/account': selected_account,
    })
    self.assertMultiLineEqual('', self.GetOutput())

    self.assertMultiLineEqual(
        _GetWelcomeMessage() +
        _GetCurrentConfigMessage('default') +
        _GetDiagnosticsMessage() +
        _GetPickAccount(credentials) +
        _GetLoggedInAsMessage(selected_account) +
        _GetNoProjectsMessage() +
        _GetEnterProjectMessage(),
        self.GetErr()
    )

  def testOneAccountKnownSelected(self):
    # Prevent environment override for `gcloud config list`.
    os.environ.pop('CLOUDSDK_CORE_ACCOUNT', None)
    selected_account = 'foo@google.com'
    project = 'golden-project'
    credentials = [selected_account]
    self.RunScenario(
        self.WithConfigurations([]) +
        self.WithAuth(
            credentials, selected_account=selected_account, selected_number=1) +
        self.WithProjects([project]) +
        self.WithRegions(meta_zone='good-zone', meta_region='bad-region'),
        self.WithGsutilConfig())
    self.AssertProperties({
        'compute/zone': 'good-zone',
        'compute/region': 'bad-region',
        'core/account': selected_account,
        'core/project': project,
    })
    self.assertMultiLineEqual('', self.GetOutput())

    self.assertMultiLineEqual(
        _GetWelcomeMessage() +
        _GetCurrentConfigMessage('default') +
        _GetDiagnosticsMessage() +
        _GetPickAccount(credentials) +
        _GetLoggedInAsMessage('foo@google.com') +
        _GetPickProjectMessage([project]) +
        _GetCurrentProjectMessage('golden-project') +
        _GetComputeMessage(zone='good-zone', region='bad-region') +
        _GetBotoMessage() +
        _GetReadyToUseMessage(
            'foo@google.com', 'golden-project',
            zone='good-zone', region='bad-region'),
        self.GetErr()
    )

  def testUnknownAccountSelectedNoLogin(self):
    self.RunScenario(
        self.WithConfigurations([]) +
        self.WithAuth([], login_continue_response='N'))
    self.AssertProperties({
        'core/account': 'fake_account',
    })
    self.assertMultiLineEqual('', self.GetOutput())

    self.assertMultiLineEqual(
        _GetWelcomeMessage() +
        _GetCurrentConfigMessage('default') +
        _GetDiagnosticsMessage() +
        _GetLoginPromptMessage(),
        self.GetErr()
    )

  def testMultipleAccountsUnknownSelected(self):
    # Prevent environment override for `gcloud config list`.
    os.environ.pop('CLOUDSDK_CORE_ACCOUNT', None)
    selected_account = 'unknown@google.com'
    active_account = 'foo@google.com'
    project = 'golden-project'
    credentials = [active_account, 'bar@google.com']
    self.RunScenario(
        self.WithConfigurations([]) +
        self.WithAuth(credentials,
                      selected_account=selected_account,
                      selected_number=3,
                      selected_unknown=True) +
        self.WithProjects([project]) +
        self.WithRegions(meta_zone='good-zone', meta_region='bad-region'),
        self.WithGsutilConfig())
    self.AssertProperties({
        'compute/zone': 'good-zone',
        'compute/region': 'bad-region',
        'core/account': selected_account,
        'core/project': project,
    })
    self.assertMultiLineEqual('', self.GetOutput())

    self.assertMultiLineEqual(
        _GetWelcomeMessage() +
        _GetCurrentConfigMessage('default') +
        _GetDiagnosticsMessage() +
        _GetPickAccount(credentials) +
        _GetLoggedInAsMessage('unknown@google.com') +
        _GetPickProjectMessage([project]) +
        _GetCurrentProjectMessage('golden-project') +
        _GetComputeMessage(zone='good-zone', region='bad-region') +
        _GetBotoMessage() +
        _GetReadyToUseMessage(
            'unknown@google.com', 'golden-project',
            zone='good-zone', region='bad-region'),
        self.GetErr()
    )

  def testMultipleAccountsKnownSelected(self):
    # Prevent environment override for `gcloud config list`.
    os.environ.pop('CLOUDSDK_CORE_ACCOUNT', None)
    selected_account = 'foo@google.com'
    project = 'golden-project'
    credentials = [selected_account, 'bar@google.com']
    self.RunScenario(
        self.WithConfigurations([]) +
        self.WithAuth(
            credentials, selected_account=selected_account, selected_number=1) +
        self.WithProjects([project]) +
        self.WithRegions(meta_zone='good-zone', meta_region='bad-region'),
        self.WithGsutilConfig())
    self.AssertProperties({
        'compute/zone': 'good-zone',
        'compute/region': 'bad-region',
        'core/account': selected_account,
        'core/project': project,
    })
    self.assertMultiLineEqual('', self.GetOutput())

    self.assertMultiLineEqual(
        _GetWelcomeMessage() +
        _GetCurrentConfigMessage('default') +
        _GetDiagnosticsMessage() +
        _GetPickAccount(credentials) +
        _GetLoggedInAsMessage('foo@google.com') +
        _GetPickProjectMessage([project]) +
        _GetCurrentProjectMessage('golden-project') +
        _GetComputeMessage(zone='good-zone', region='bad-region') +
        _GetBotoMessage() +
        _GetReadyToUseMessage(
            'foo@google.com', 'golden-project',
            zone='good-zone', region='bad-region'),
        self.GetErr()
    )

  def testNoAccountsUnknownPreSelected(self):
    preselected_account = 'unknown@google.com'
    credentials = []
    self.RunScenario(
        self.WithConfigurations([]) +
        self.WithAuth(credentials) +
        self.WithGsutilConfig(), preselected_account=preselected_account)
    self.AssertProperties({
        'core/account': 'fake_account',
    })
    self.assertMultiLineEqual('', self.GetOutput())

    self.assertMultiLineEqual(
        _GetWelcomeMessage() +
        _GetCurrentConfigMessage('default') +
        _GetDiagnosticsMessage() +
        _GetPickAccount(credentials, preselected_account=preselected_account),
        self.GetErr()
    )

  def testOneAccountUnknownPreSelected(self):
    preselected_account = 'unknown@google.com'
    credentials = ['foo@google.com']
    self.RunScenario(
        self.WithConfigurations([]) +
        self.WithAuth(credentials, selected_account=preselected_account) +
        self.WithGsutilConfig(), preselected_account=preselected_account)
    self.AssertProperties({
        'core/account': 'fake_account',
    })
    self.assertMultiLineEqual('', self.GetOutput())

    self.assertMultiLineEqual(
        _GetWelcomeMessage() +
        _GetCurrentConfigMessage('default') +
        _GetDiagnosticsMessage() +
        _GetPickAccount(credentials, preselected_account=preselected_account),
        self.GetErr()
    )

  def testOneAccountKnownPreSelected(self):
    # Prevent environment override for `gcloud config list`.
    os.environ.pop('CLOUDSDK_CORE_ACCOUNT', None)
    preselected_account = 'foo@google.com'
    project = 'golden-project'
    credentials = [preselected_account]
    self.RunScenario(
        self.WithConfigurations([]) +
        self.WithAuth(credentials, selected_account=preselected_account) +
        self.WithProjects([project]) +
        self.WithRegions(meta_zone='good-zone', meta_region='bad-region'),
        self.WithGsutilConfig(), preselected_account=preselected_account)
    self.AssertProperties({
        'compute/zone': 'good-zone',
        'compute/region': 'bad-region',
        'core/account': preselected_account,
        'core/project': project,
    })
    self.assertMultiLineEqual('', self.GetOutput())

    self.assertMultiLineEqual(
        _GetWelcomeMessage() +
        _GetCurrentConfigMessage('default') +
        _GetDiagnosticsMessage() +
        _GetLoggedInAsMessage('foo@google.com') +
        _GetPickProjectMessage([project]) +
        _GetCurrentProjectMessage('golden-project') +
        _GetComputeMessage(zone='good-zone', region='bad-region') +
        _GetBotoMessage() +
        _GetReadyToUseMessage(
            'foo@google.com', 'golden-project',
            zone='good-zone', region='bad-region'),
        self.GetErr()
    )

  def testMultipleAccountsKnownPreSelected(self):
    # Prevent environment override for `gcloud config list`.
    os.environ.pop('CLOUDSDK_CORE_ACCOUNT', None)
    preselected_account = 'foo@google.com'
    project = 'golden-project'
    credentials = [preselected_account, 'bar@google.com']

    self.RunScenario(
        self.WithConfigurations([]) +
        self.WithAuth(credentials, selected_account=preselected_account) +
        self.WithProjects([project]) +
        self.WithRegions(meta_zone='good-zone', meta_region='bad-region'),
        self.WithGsutilConfig(), preselected_account=preselected_account)
    self.AssertProperties({
        'compute/zone': 'good-zone',
        'compute/region': 'bad-region',
        'core/account': preselected_account,
        'core/project': project,
    })
    self.assertMultiLineEqual('', self.GetOutput())

    self.assertMultiLineEqual(
        _GetWelcomeMessage() +
        _GetCurrentConfigMessage('default') +
        _GetDiagnosticsMessage() +
        _GetLoggedInAsMessage('foo@google.com') +
        _GetPickProjectMessage([project]) +
        _GetCurrentProjectMessage('golden-project') +
        _GetComputeMessage(zone='good-zone', region='bad-region') +
        _GetBotoMessage() +
        _GetReadyToUseMessage(
            'foo@google.com', 'golden-project',
            zone='good-zone', region='bad-region'),
        self.GetErr()
    )

  def testMultipleAccountsUnknownPreSelected(self):
    # Prevent environment override for `gcloud config list`.
    os.environ.pop('CLOUDSDK_CORE_ACCOUNT', None)
    preselected_account = 'unknown@google.com'
    project = 'golden-project'
    credentials = ['foo@google.com', 'bar@google.com']
    self.RunScenario(
        self.WithConfigurations([]) +
        self.WithAuth(credentials, selected_account=preselected_account) +
        self.WithProjects([project]) +
        self.WithRegions(meta_zone='good-zone', meta_region='bad-region'),
        self.WithGsutilConfig(), preselected_account=preselected_account)
    self.assertMultiLineEqual('', self.GetOutput())

    self.assertMultiLineEqual(
        _GetWelcomeMessage() +
        _GetCurrentConfigMessage('default') +
        _GetDiagnosticsMessage() +
        _GetPickAccount(credentials, preselected_account=preselected_account),
        self.GetErr()
    )

  def testZoneTypoSelected(self):
    self.RunScenario(
        self.WithConfigurations([]) +
        self.WithAuth([], login='foo@google.com') +
        self.WithProjects(['golden-project']) +
        self.WithRegions(
            zone_list=[{'name': 'A-zone', 'region': 'AAA'},
                       {'name': 'B-zone', 'region': 'BBB'}],
            zone_choice='B-zonf',
            region_list=[{'name': 'AAA'}, {'name': 'BBB'}],
            auto_select_region='BBB'),
        self.WithGsutilConfig())
    self.assertMultiLineEqual('', self.GetOutput())

    self.assertMultiLineEqual(
        _GetWelcomeMessage() +
        _GetCurrentConfigMessage('default') +
        _GetDiagnosticsMessage() +
        _GetLoginPromptMessage() +
        _GetLoggedInAsMessage('foo@google.com') +
        _GetPickProjectMessage(['golden-project']) +
        _GetCurrentProjectMessage('golden-project') +
        _GetComputeMessage(zone='good-zone', region='bad-region',
                           zones=['A-zone', 'B-zone'],
                           regions=['AAA', 'BBB']) +
        _GetBotoMessage() +
        _GetReadyToUseMessage(
            'foo@google.com', 'golden-project'),
        self.GetErr()
    )

  def testZoneChoiceAutoSelectRegion(self):
    self.RunScenario(
        self.WithConfigurations([]) +
        self.WithAuth([], login='foo@google.com') +
        self.WithProjects(['golden-project']) +
        self.WithRegions(
            zone_list=[{'name': 'A-zone', 'region': 'AAA'},
                       {'name': 'B-zone', 'region': 'BBB'}],
            zone_choice=2,
            auto_select_region='BBB'),
        self.WithGsutilConfig())
    self.AssertProperties({
        'compute/zone': 'B-zone',
        'compute/region': 'BBB',
        'core/account': 'foo@google.com',
        'core/project': 'golden-project',
    })
    self.AssertActiveConfig('default')
    # Make sure prompts are displayed.
    self.assertMultiLineEqual('', self.GetOutput())

    self.assertMultiLineEqual(
        _GetWelcomeMessage() +
        _GetCurrentConfigMessage('default') +
        _GetDiagnosticsMessage() +
        _GetLoginPromptMessage() +
        _GetLoggedInAsMessage('foo@google.com') +
        _GetPickProjectMessage(['golden-project']) +
        _GetCurrentProjectMessage('golden-project') +
        _GetComputeMessage(zone='B-zone', region='BBB',
                           zones=['A-zone', 'B-zone']) +
        _GetBotoMessage() +
        _GetReadyToUseMessage(
            'foo@google.com', 'golden-project',
            zone='B-zone', region='BBB'),
        self.GetErr()
    )

  def testZoneChoiceTextAutoSelectRegion(self):
    self.RunScenario(
        self.WithConfigurations([]) +
        self.WithAuth([], login='foo@google.com') +
        self.WithProjects(['golden-project']) +
        self.WithRegions(
            zone_list=[{'name': 'A-zone', 'region': 'AAA'},
                       {'name': 'B-zone', 'region': 'BBB'}],
            zone_choice='B-zone',
            auto_select_region='BBB'),
        self.WithGsutilConfig())
    self.AssertProperties({
        'compute/zone': 'B-zone',
        'compute/region': 'BBB',
        'core/account': 'foo@google.com',
        'core/project': 'golden-project',
    })
    self.AssertActiveConfig('default')
    # Make sure prompts are displayed.
    self.assertMultiLineEqual('', self.GetOutput())

    self.assertMultiLineEqual(
        _GetWelcomeMessage() +
        _GetCurrentConfigMessage('default') +
        _GetDiagnosticsMessage() +
        _GetLoginPromptMessage() +
        _GetLoggedInAsMessage('foo@google.com') +
        _GetPickProjectMessage(['golden-project']) +
        _GetCurrentProjectMessage('golden-project') +
        _GetComputeMessage(zone='B-zone', region='BBB',
                           zones=['A-zone', 'B-zone']) +
        _GetBotoMessage() +
        _GetReadyToUseMessage(
            'foo@google.com', 'golden-project',
            zone='B-zone', region='BBB'),
        self.GetErr()
    )

  def testDontConfigureCompute(self):
    self.RunScenario(
        self.WithConfigurations([]) +
        self.WithAuth([], login='foo@google.com') +
        self.WithProjects(['golden-project']) +
        self.WithRegions(),
        self.WithGsutilConfig())
    self.AssertProperties({
        'core/account': 'foo@google.com',
        'core/project': 'golden-project',
    })
    self.assertMultiLineEqual('', self.GetOutput())

    self.assertMultiLineEqual(
        _GetWelcomeMessage() +
        _GetCurrentConfigMessage('default') +
        _GetDiagnosticsMessage() +
        _GetLoginPromptMessage() +
        _GetLoggedInAsMessage('foo@google.com') +
        _GetPickProjectMessage(['golden-project']) +
        _GetCurrentProjectMessage('golden-project') +
        _GetComputeMessage() +
        _GetBotoMessage() +
        _GetReadyToUseMessage('foo@google.com', 'golden-project'),
        self.GetErr()
    )

  def testNoComputeApis(self):
    self.RunScenario(
        self.WithConfigurations([]) +
        self.WithAuth([], login='foo@google.com') +
        self.WithProjects(['golden-project']) +
        self.WithRegions(exception=SystemExit(25)),
        self.WithGsutilConfig())
    self.assertMultiLineEqual('', self.GetOutput())

    self.assertMultiLineEqual(
        _GetWelcomeMessage() +
        _GetCurrentConfigMessage('default') +
        _GetDiagnosticsMessage() +
        _GetLoginPromptMessage() +
        _GetLoggedInAsMessage('foo@google.com') +
        _GetPickProjectMessage(['golden-project']) +
        _GetCurrentProjectMessage('golden-project') +
        _GetComputeMessage(skip=True) +
        _GetBotoMessage() +
        _GetReadyToUseMessage('foo@google.com', 'golden-project'),
        self.GetErr()
    )

  def testCreateConfiguration(self):
    self.RunScenario(
        self.WithConfigurations(['good-one'], picked_config='newconfig') +
        self.WithAuth([]))
    self.AssertActiveConfig('newconfig')
    self.assertMultiLineEqual('', self.GetOutput())

    self.assertMultiLineEqual(
        'Created [good-one].\n'
        'Activated [good-one].\n'
        'Activated [good-one].\n' +
        _GetWelcomeMessage() +
        _GetCurrentSettings('good-one') +
        _GetPickConfigurationMessage([], 'good-one') +
        _GetCurrentConfigMessage('newconfig') +
        _GetDiagnosticsMessage() +
        _GetLoginPromptMessage(),
        self.GetErr()
    )

  def testCreateConfiguration_WithWhitespace(self):
    self.RunScenario(
        self.WithConfigurations(['good-one'], picked_config='  newconfig  ') +
        self.WithAuth([]))
    self.AssertActiveConfig('newconfig')
    self.assertMultiLineEqual('', self.GetOutput())

    self.assertMultiLineEqual(
        'Created [good-one].\n'
        'Activated [good-one].\n'
        'Activated [good-one].\n' +
        _GetWelcomeMessage() +
        _GetCurrentSettings('good-one') +
        _GetPickConfigurationMessage([], 'good-one') +
        _GetCurrentConfigMessage('newconfig') +
        _GetDiagnosticsMessage() +
        _GetLoginPromptMessage(),
        self.GetErr()
    )

  def testReinitializeActiveConfiguration(self):
    self.RunScenario(
        self.WithConfigurations(['active-one'],
                                active_config='active-one',
                                picked_config='active-one') +
        self.WithAuth([]))
    self.AssertActiveConfig('active-one')
    self.AssertProperties({})
    self.assertMultiLineEqual('', self.GetOutput())

    self.assertMultiLineEqual(
        'Created [active-one].\n'
        'Activated [active-one].\n'
        'Activated [active-one].\n' +
        _GetWelcomeMessage() +
        _GetCurrentSettings('active-one') +
        _GetPickConfigurationMessage([], 'active-one', new_config=False) +
        _GetCurrentConfigMessage('active-one') +
        _GetDiagnosticsMessage() +
        _GetLoginPromptMessage(),
        self.GetErr()
    )

  def testSwitchToConfiguration(self):
    self.RunScenario(
        self.WithConfigurations(['active-one', 'other-one'],
                                active_config='active-one',
                                picked_config='other-one') +
        self.WithAuth([]))
    self.AssertActiveConfig('other-one')
    self.AssertProperties({})
    self.assertMultiLineEqual('', self.GetOutput())

    self.assertMultiLineEqual(
        'Created [active-one].\n'
        'Activated [active-one].\n'
        'Created [other-one].\n'
        'Activated [other-one].\n'
        'Activated [active-one].\n' +
        _GetWelcomeMessage() +
        _GetCurrentSettings('active-one') +
        _GetPickConfigurationMessage(['other-one'], 'active-one',
                                     new_config=False) +
        _GetCurrentConfigMessage('other-one') +
        _GetDiagnosticsMessage() +
        _GetLoginPromptMessage(),
        self.GetErr()
    )

  def testWithDisabledPrompts(self):
    properties.VALUES.core.disable_prompts.Set(True)
    with self.assertRaisesRegex(
        c_exc.InvalidArgumentException,
        re.escape('Invalid value for [disable_prompts/--quiet]: '
                  'gcloud init command cannot run with disabled prompts.')):
      self.RunScenario([])
    self.assertMultiLineEqual('', self.GetOutput())

    self.assertMultiLineEqual(
        _GetWelcomeMessage() +
        'ERROR: (gcloud.init) Invalid value for [disable_prompts/--quiet]: '
        'gcloud init command cannot run with disabled prompts.\n',
        self.GetErr()
    )

  def testWithCommandException(self):
    # Make sure most command exceptions propagate out.
    self.StartObjectPatch(c_store, 'AvailableAccounts', return_value=[])
    with self.assertRaisesRegex(RuntimeError, 'booboo'):
      self.RunScenario([
          (['auth', 'login', '--force', '--brief'], RuntimeError('booboo'))
      ])
    self.assertMultiLineEqual('', self.GetOutput())

    self.assertMultiLineEqual(
        _GetWelcomeMessage() +
        _GetCurrentConfigMessage('default') +
        _GetDiagnosticsMessage() +
        _GetLoginPromptMessage(),
        self.GetErr()
    )

  def testWithExperimentalCommandException(self):
    # Make sure experimental command are swallowed.
    self.projects_list_mock.side_effect = RuntimeError('oops')
    self.RunScenario(
        self.WithConfigurations([]) +
        self.WithAuth([], login='foo@google.com'))

    self.assertMultiLineEqual('', self.GetOutput())

    self.assertMultiLineEqual(
        _GetWelcomeMessage() +
        _GetCurrentConfigMessage('default') +
        _GetDiagnosticsMessage() +
        _GetLoginPromptMessage() +
        _GetLoggedInAsMessage('foo@google.com') +
        'WARNING: Listing available projects failed: oops\n' +
        '{"ux": "PROMPT_RESPONSE", "message": "Enter project id you would like '
        'to use:  "}',
        self.GetErr()
    )

  def testWithCommandSystemExit(self):
    self.StartObjectPatch(c_store, 'AvailableAccounts', return_value=[])
    with self.assertRaisesRegex(
        c_exc.FailedSubCommand,
        re.escape('Failed command: [auth login --force --brief] '
                  'with exit code [25]')):
      self.RunScenario([
          (['auth', 'login', '--force', '--brief'], lambda cmd: sys.exit(25))
      ])
    self.assertMultiLineEqual('', self.GetOutput())

    self.assertMultiLineEqual(
        _GetWelcomeMessage() +
        _GetCurrentConfigMessage('default') +
        _GetDiagnosticsMessage() +
        _GetLoginPromptMessage() +
        'ERROR: (gcloud.init) Failed command: [auth login --force --brief] '
        'with exit code [25]\n',
        self.GetErr()
    )

  def testWithConsoleOnly(self):
    self.RunScenario(
        self.WithConfigurations([]) +
        self.WithAuth([], login='foo@google.com', browser=False) +
        self.WithProjects([]),
        console_only=True)

    self.AssertProperties({
        'core/account': 'foo@google.com',
    })
    self.AssertActiveConfig('default')
    self.assertMultiLineEqual('', self.GetOutput())

    self.assertMultiLineEqual(
        _GetWelcomeMessage() +
        _GetCurrentConfigMessage('default') +
        _GetDiagnosticsMessage() +
        _GetLoginPromptMessage() +
        _GetLoggedInAsMessage('foo@google.com') +
        _GetNoProjectsMessage() +
        _GetEnterProjectMessage(),
        self.GetErr()
    )

  def testWithSkipDiagnostics(self):
    self.RunScenario(
        self.WithConfigurations([]) +
        self.WithAuth([], login='foo@google.com') +
        self.WithProjects(['golden-project']),
        self.WithGsutilConfig(),
        skip_diagnostics=True)
    self.assertFalse(self.check_network_mock.called)
    self.assertMultiLineEqual('', self.GetOutput())

    self.assertMultiLineEqual(
        _GetWelcomeMessage() +
        _GetCurrentConfigMessage('default') +
        _GetLoginPromptMessage() +
        _GetLoggedInAsMessage('foo@google.com') +
        _GetPickProjectMessage(['golden-project']) +
        _GetCurrentProjectMessage('golden-project') +
        _GetComputeMessage(skip=True) +
        _GetBotoMessage() +
        _GetReadyToUseMessage(
            'foo@google.com', 'golden-project'),
        self.GetErr()
    )

  def testWithLogHttp(self):
    self.RunScenario(
        self.WithConfigurations(['active-one'], picked_config='newconfig') +
        self.WithAuth([]),
        log_http=True
    )
    self.AssertActiveConfig('newconfig')
    self.assertMultiLineEqual('', self.GetOutput())

    self.assertMultiLineEqual(
        'Created [active-one].\n'
        'Activated [active-one].\n'
        'Activated [active-one].\n' +
        _GetWelcomeMessage() +
        _GetCurrentSettings('active-one', log_http=True) +
        _GetPickConfigurationMessage([], current_config='active-one') +
        _GetCurrentConfigMessage('newconfig') +
        _GetDiagnosticsMessage() +
        _GetLoginPromptMessage(),
        self.GetErr()
    )

  def testGsutilConfig_NoSdkRoot(self):
    # Return no SDK root.
    self.mock_sdk_root.__get__ = mock.Mock(return_value=None)
    self.RunScenario(
        self.WithConfigurations([]) +
        self.WithAuth([], login='foo@google.com') +
        self.WithProjects(['golden-project']) +
        self.WithRegions(meta_zone='good-zone', meta_region='bad-region'))
    self.assertMultiLineEqual('', self.GetOutput())

    self.assertMultiLineEqual(
        _GetWelcomeMessage() +
        _GetCurrentConfigMessage('default') +
        _GetDiagnosticsMessage() +
        _GetLoginPromptMessage() +
        _GetLoggedInAsMessage('foo@google.com') +
        _GetPickProjectMessage(['golden-project']) +
        _GetCurrentProjectMessage('golden-project') +
        _GetComputeMessage(zone='good-zone', region='bad-region') +
        _GetReadyToUseMessage(
            'foo@google.com', 'golden-project',
            zone='good-zone', region='bad-region'),
        self.GetErr()
    )

  def testGsutilConfig_BotoAlreadyExists(self):
    # Create a ~/.boto file.
    boto_file = self.Touch(files.GetHomeDir(),
                           name='.boto',
                           contents='foo')
    self.StartObjectPatch(files, 'ExpandHomeDir', return_value=boto_file)
    self.RunScenario(
        self.WithConfigurations([]) +
        self.WithAuth([], login='foo@google.com') +
        self.WithProjects(['golden-project']) +
        self.WithRegions(meta_zone='good-zone', meta_region='bad-region'))
    self.assertMultiLineEqual('', self.GetOutput())

    self.assertMultiLineEqual(
        _GetWelcomeMessage() +
        _GetCurrentConfigMessage('default') +
        _GetDiagnosticsMessage() +
        _GetLoginPromptMessage() +
        _GetLoggedInAsMessage('foo@google.com') +
        _GetPickProjectMessage(['golden-project']) +
        _GetCurrentProjectMessage('golden-project') +
        _GetComputeMessage(zone='good-zone', region='bad-region') +
        _GetReadyToUseMessage(
            'foo@google.com', 'golden-project',
            zone='good-zone', region='bad-region'),
        self.GetErr()
    )

  def testGsutilConfig_ErrorRunningGsutil(self):
    self.RunScenario(
        self.WithConfigurations([]) +
        self.WithAuth([], login='foo@google.com') +
        self.WithProjects(['golden-project']) +
        self.WithRegions(meta_zone='good-zone', meta_region='bad-region'),
        self.WithGsutilConfig(return_code=1))
    self.assertMultiLineEqual('', self.GetOutput())

    self.assertMultiLineEqual(
        _GetWelcomeMessage() +
        _GetCurrentConfigMessage('default') +
        _GetDiagnosticsMessage() +
        _GetLoginPromptMessage() +
        _GetLoggedInAsMessage('foo@google.com') +
        _GetPickProjectMessage(['golden-project']) +
        _GetCurrentProjectMessage('golden-project') +
        _GetComputeMessage(zone='good-zone', region='bad-region') +
        _GetBotoMessage(error=True) +
        _GetReadyToUseMessage(
            'foo@google.com', 'golden-project',
            zone='good-zone', region='bad-region'),
        self.GetErr()
    )


class InitNoExecutorMockingTest(cli_test_base.CliTestBase):

  def testWithProjectPositional(self):
    with self.assertRaisesRegex(
        c_exc.InvalidArgumentException,
        r'Invalid value for \[my-project\]:.*`gcloud init` has changed.*'):
      self.Run('init my-project')

    self.assertMultiLineEqual('', self.GetOutput())

    self.assertMultiLineEqual(
        'ERROR: (gcloud.init) Invalid value for [my-project]: '
        '`gcloud init` has changed and no longer takes a PROJECT argument. '
        'Please use `gcloud source repos clone` to clone this project\'s '
        'source repositories.\n',
        self.GetErr()
    )


if __name__ == '__main__':
  test_case.main()
