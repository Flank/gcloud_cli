# Copyright 2017 Google Inc. All Rights Reserved.
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

"""Unit tests for the parser_completer module.

Although the test completers in this module derive from ListCommandCompleter,
each overrides the Update() method to bypass the list command logic and instead
returns a fixed list of parsed resource tuples.
"""

from googlecloudsdk.api_lib.util import resource_search
from googlecloudsdk.calliope import parser_completer
from googlecloudsdk.command_lib.util import completers
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_attr
from tests.lib import completer_test_base
from tests.lib import completer_test_completers as test_completers
from tests.lib.calliope import util as calliope_test_util
from tests.lib.core import core_completer_test_base
from tests.lib.surface.compute import test_resources


class ParserCompleterTest(completer_test_base.CompleterBase):

  def MockExecute(self, command, call_arg_complete=False):
    self.commands.append(command)

  def AssertListCommand(self, expected_command):
    if not self.commands:
      actual_command = None
    elif len(self.commands) == 1:
      actual_command = self.commands[0]
    else:
      actual_command = self.commands
    self.assertEquals(expected_command, actual_command)

  def SetUp(self):
    properties.VALUES.core.project.Set('my-project')
    self.commands = []
    self.StartObjectPatch(
        console_attr.ConsoleAttr,
        'GetTermSize',
        return_value=[120, 24])
    self.StartObjectPatch(
        core_completer_test_base.MockNamespace,
        '_Execute',
        side_effect=self.MockExecute)
    self.StartObjectPatch(
        resource_search,
        'List',
        return_value=[x.selfLink for x in test_resources.INSTANCES_V1],
        autospec=True)

  def Run(self, completer, expected_command=None, expected_completions=None,
          args=None):
    completer = parser_completer.ArgumentCompleter(
        completer, core_completer_test_base.MockArgument('id'))
    completions = completer(
        '', core_completer_test_base.MockNamespace(args=args))
    self.assertEqual(expected_completions or [], completions)
    self.AssertListCommand(expected_command)

  def testListCommandCompleter(self):
    self.Run(
        test_completers.ListCommandCompleter,
        ['compute', 'instances', 'list', '--uri', '--quiet',
         '--format=disable'])

  def testListCommandWithNoUriCompleter(self):
    self.Run(
        test_completers.ListCommandWithNoUriCompleter,
        ['compute', 'instances', 'list', '--complete-me', '--quiet'])

  def testListCommandWithFormatCompleter(self):
    self.Run(
        test_completers.ListCommandWithFormatCompleter,
        ['compute', 'instances', 'list', '--format=value(id)', '--quiet'])

  def testListCommandWithQuietCompleter(self):
    self.Run(
        test_completers.ListCommandWithQuietCompleter,
        ['compute', 'instances', 'list', '--quiet'])

  def testListCommandWithFlagsCompleter(self):
    self.Run(
        test_completers.ListCommandWithFlagsCompleter,
        ['compute', 'instances', 'list', '--uri', '--quiet',
         '--format=disable'],
        args={'flag': 'value'})

  def testListCommandCompleterGoodApiVersion(self):
    self.Run(
        test_completers.ListCommandCompleterGoodApiVersion,
        ['compute', 'instances', 'list', '--uri', '--quiet',
         '--format=disable'])

  def testListCommandCompleterBadApiVersion(self):
    self.Run(
        test_completers.ListCommandCompleterBadApiVersion,
        expected_completions=[
            'ERROR: ListCommandCompleterBadApiVersion resource completer '
            'failed.',
            'REASON: The [compute] API does not have version [v0] in the '
            'APIs map'])

  def testFunctionCompleterBadMojo(self):

    def _BadFunctionCompleter(prefix):
      del prefix
      raise ValueError('Incomplete completions are completely messed up.')

    self.Run(
        _BadFunctionCompleter,
        expected_completions=[
            'ERROR: _BadFunctionCompleter resource completer failed.     ',
            'REASON: Incomplete completions are completely messed up.    '])

  def testResourceParamCompleter(self):
    self.Run(
        test_completers.ResourceParamCompleter,
        ['compute', 'zones', 'list', '--uri', '--quiet',
         '--format=disable'])

  def testResourceSearchCompleter(self):
    self.Run(
        test_completers.ResourceSearchCompleter,
        expected_completions=['instance-1', 'instance-2', 'instance-3'])

  def testMultiResourceCompleter(self):
    self.Run(
        test_completers.MultiResourceCompleter,
        expected_command=[
            ['compute', 'regions', 'list', '--uri',
             '--quiet', '--format=disable'],
            ['compute', 'zones', 'list', '--uri',
             '--quiet', '--format=disable'],
        ])

  def testNoCacheCompleter(self):
    self.Run(
        test_completers.NoCacheCompleter,
        expected_completions=['role/major', 'role/minor'])


class GlobalCompleter(completers.ListCommandCompleter):
  """A completer with instance and project parameters."""

  def __init__(self, **kwargs):
    super(GlobalCompleter, self).__init__(
        collection='tests.globalInstance',
        additional_params=['global'],
        timeout=1,
        **kwargs)

  def Update(self, parameter_info=None, aggregations=None):
    return [
        ['a-project', 'name-1'],
        ['a-project', 'name-2'],
        ['b-project', 'name-3'],
        ['b-project', 'name-4'],
    ]


class RegionalCompleter(completers.ListCommandCompleter):
  """A completer with instance, region and project parameters."""

  def __init__(self, **kwargs):
    super(RegionalCompleter, self).__init__(
        collection='tests.regionalInstance',
        timeout=1,
        **kwargs)

  def Update(self, parameter_info=None, aggregations=None):
    return [
        ['a-project', 'a-region', 'name-1'],
        ['a-project', 'b-region', 'name-2'],
        ['b-project', 'a-region', 'name-3'],
        ['b-project', 'b-region', 'name-4'],
    ]


class ZonalCompleter(completers.ListCommandCompleter):
  """A completer with instance, zone and project parameters."""

  def __init__(self, **kwargs):
    super(ZonalCompleter, self).__init__(
        collection='tests.zonalInstance',
        timeout=1,
        **kwargs)

  def Update(self, parameter_info=None, aggregations=None):
    return [
        ['a-project', 'a-zone', 'name-1'],
        ['a-project', 'b-zone', 'name-2'],
        ['b-project', 'a-zone', 'name-3'],
        ['b-project', 'b-zone', 'name-4'],
    ]


class MultiGlobalRegionalZonalCompleter(completers.MultiResourceCompleter):
  """A mixed global, regional, zonal completer."""

  def __init__(self, **kwargs):
    super(MultiGlobalRegionalZonalCompleter, self).__init__(
        completers=[GlobalCompleter, RegionalCompleter, ZonalCompleter],
        **kwargs)

  def Update(self, parameter_info=None, aggregations=None):
    return [
        ['a-project', 'a-zone', 'name-1'],
        ['a-project', 'b-zone', 'name-2'],
        ['b-project', 'a-zone', 'name-3'],
        ['b-project', 'b-zone', 'name-4'],
    ]


class TrialCompleter(completers.ListCommandCompleter):
  """A completer that uses the completion prefix as a test operation."""

  def __init__(self, **kwargs):
    super(TrialCompleter, self).__init__(
        collection='tests.testInstance',
        timeout=1,
        **kwargs)
    self.operation = None

  def Complete(self, prefix=None, parameter_info=None):
    self.operation = prefix
    if self.operation == 'no-error':
      return [self.operation]
    elif self.operation == 'unknown-method-error':
      self.UnknownMethod()
    elif self.operation == 'no-parameters':
      self.parameters = []
    elif self.operation == 'GetParameterFlag-no-property-no-value':
      return [
          parameter_info.GetFlag(parameter_name=self.parameters[0].name,
                                 parameter_value=None,
                                 check_properties=False),
      ]
    elif self.operation == 'GetParameterFlag-no-property-value':
      return [
          parameter_info.GetFlag(parameter_name=self.parameters[0].name,
                                 parameter_value='no-property-value',
                                 check_properties=True),
      ]
    elif self.operation == 'GetParameterFlag-property-no-value':
      return [
          parameter_info.GetFlag(parameter_name=self.parameters[0].name,
                                 parameter_value=None,
                                 check_properties=True),
      ]
    elif self.operation == 'GetParameterFlag-property-value':
      return [
          parameter_info.GetFlag(parameter_name=self.parameters[0].name,
                                 parameter_value='property-value',
                                 check_properties=True),
      ]
    return super(TrialCompleter, self).Complete(
        prefix=prefix, parameter_info=parameter_info)

  def Update(self, parameter_info=None, aggregations=None):
    if self.operation == 'update-error':
      raise ValueError('Catastrophic cache update failure.')


class MockFromString(object):

  PROPERTIES = {
      'tests/test': 'test-property-value',
      'tests/project': 'a-project',
      'tests/region': 'a-region',
      'tests/zone': 'a-zone',
  }

  def __init__(self, prop):
    self._prop = prop

  def Get(self):
    try:
      return self.PROPERTIES[self._prop]
    except KeyError as e:
      raise properties.NoSuchPropertyError(e)


class MockGetCollectionInfo(object):

  PARAMS = {
      'tests.testInstance': ['test'],
      'tests.testInstance@v0alpha0': ['test'],
      'tests.globalInstance': ['project', 'instance'],
      'tests.regionalInstance': ['project', 'region', 'instance'],
      'tests.zonalInstance': ['project', 'zone', 'instance'],
  }

  def __init__(self, collection, api_version=None):
    if api_version:
      self.api_version = api_version
      try:
        self._params = self.PARAMS[collection + '@' + api_version]
        return
      except KeyError:
        pass
    else:
      self.api_version = 'v1'
    self._params = self.PARAMS[collection]

  @property
  def params(self):
    return self._params

  def GetParams(self, subcollection):
    del subcollection
    return self._params


class ParserCompleterFlagTest(completer_test_base.FlagCompleterBase):

  def SetUp(self):
    self.StartObjectPatch(
        console_attr.ConsoleAttr,
        'GetTermSize',
        return_value=[120, 24])
    self.StartObjectPatch(
        properties,
        'FromString',
        side_effect=MockFromString)
    self.StartObjectPatch(
        resources.REGISTRY,
        'GetCollectionInfo',
        side_effect=MockGetCollectionInfo)
    self.parser = calliope_test_util.ArgumentParser()
    self.parser.add_argument('--project', help='Auxilio aliis.')
    self.parser.add_argument('--global', action='store_true',
                             help='Auxilio aliis.')
    self.parser.add_argument('--region', help='Auxilio aliis.')
    self.parser.add_argument('--zone', help='Auxilio aliis.')

  def testZonalCompleter(self):
    self.parser.add_argument('instance', completer=ZonalCompleter,
                             help='Auxilio aliis.')
    parsed_args = self.parser.parse_args(['name'])

    positional_completers = self.parser.data.positional_completers
    self.assertEquals(1, len(positional_completers))

    completer_class = list(positional_completers)[0]
    self.assertEquals(ZonalCompleter, completer_class)

    positional_args = self.parser.positional_args
    self.assertEquals(1, len(positional_args))

    instance_arg = parsed_args.GetPositionalArgument('instance')
    self.assertEquals(instance_arg, positional_args[0])

    completer = instance_arg.completer
    self.assertEquals(ZonalCompleter, completer.completer_class)

    self.AssertSetEquals(
        [
            'name-1',
            'name-2 --zone=b-zone',
            'name-3 --project=b-project',
            'name-4 --project=b-project --zone=b-zone',
        ],
        completer(prefix='name', parsed_args=parsed_args))
    self.AssertSetEquals(
        ['name-1'],
        completer(prefix='name-1', parsed_args=parsed_args))
    self.AssertSetEquals(
        ['name-2 --zone=b-zone'],
        completer(prefix='name-2', parsed_args=parsed_args))
    self.AssertSetEquals(
        ['name-3 --project=b-project'],
        completer(prefix='name-3', parsed_args=parsed_args))
    self.AssertSetEquals(
        ['name-4 --project=b-project --zone=b-zone'],
        completer(prefix='name-4', parsed_args=parsed_args))

  def testZonalCompleterWithProjectEqProperty(self):
    self.parser.add_argument('instance', completer=ZonalCompleter,
                             help='Auxilio aliis.')
    parsed_args = self.parser.parse_args(['--project=a-project', 'name'])

    completer = parsed_args.GetPositionalArgument('instance').completer
    self.assertEquals(ZonalCompleter, completer.completer_class)

    self.AssertSetEquals(
        [
            'name-1',
            'name-2 --zone=b-zone',
        ],
        completer(prefix='name', parsed_args=parsed_args))
    self.AssertSetEquals(
        ['name-1'],
        completer(prefix='name-1', parsed_args=parsed_args))
    self.AssertSetEquals(
        ['name-2 --zone=b-zone'],
        completer(prefix='name-2', parsed_args=parsed_args))
    self.AssertSetEquals(
        [],
        completer(prefix='name-3', parsed_args=parsed_args))
    self.AssertSetEquals(
        [],
        completer(prefix='name-4', parsed_args=parsed_args))

  def testZonalCompleterWithProjectNeProperty(self):
    self.parser.add_argument('instance', completer=ZonalCompleter,
                             help='Auxilio aliis.')
    parsed_args = self.parser.parse_args(['--project=b-project', 'name'])

    completer = parsed_args.GetPositionalArgument('instance').completer
    self.assertEquals(ZonalCompleter, completer.completer_class)

    self.AssertSetEquals(
        [
            'name-3',
            'name-4 --zone=b-zone',
        ],
        completer(prefix='name', parsed_args=parsed_args))
    self.AssertSetEquals(
        [],
        completer(prefix='name-1', parsed_args=parsed_args))
    self.AssertSetEquals(
        [],
        completer(prefix='name-2', parsed_args=parsed_args))
    self.AssertSetEquals(
        ['name-3'],
        completer(prefix='name-3', parsed_args=parsed_args))
    self.AssertSetEquals(
        ['name-4 --zone=b-zone'],
        completer(prefix='name-4', parsed_args=parsed_args))

  def testZonalCompleterWithZoneEqProperty(self):
    self.parser.add_argument('instance', completer=ZonalCompleter,
                             help='Auxilio aliis.')
    parsed_args = self.parser.parse_args(['--zone=a-zone', 'name'])

    completer = parsed_args.GetPositionalArgument('instance').completer
    self.assertEquals(ZonalCompleter, completer.completer_class)

    self.AssertSetEquals(
        [
            'name-1',
            'name-3 --project=b-project',
        ],
        completer(prefix='name', parsed_args=parsed_args))
    self.AssertSetEquals(
        ['name-1'],
        completer(prefix='name-1', parsed_args=parsed_args))
    self.AssertSetEquals(
        [],
        completer(prefix='name-2', parsed_args=parsed_args))
    self.AssertSetEquals(
        ['name-3 --project=b-project'],
        completer(prefix='name-3', parsed_args=parsed_args))
    self.AssertSetEquals(
        [],
        completer(prefix='name-4', parsed_args=parsed_args))

  def testZonalCompleterWithZoneNeProperty(self):
    self.parser.add_argument('instance', completer=ZonalCompleter,
                             help='Auxilio aliis.')
    parsed_args = self.parser.parse_args(['--zone=b-zone', 'name'])

    completer = parsed_args.GetPositionalArgument('instance').completer
    self.assertEquals(ZonalCompleter, completer.completer_class)

    self.AssertSetEquals(
        [
            'name-2',
            'name-4 --project=b-project',
        ],
        completer(prefix='name', parsed_args=parsed_args))
    self.AssertSetEquals(
        [],
        completer(prefix='name-1', parsed_args=parsed_args))
    self.AssertSetEquals(
        ['name-2'],
        completer(prefix='name-2', parsed_args=parsed_args))
    self.AssertSetEquals(
        [],
        completer(prefix='name-3', parsed_args=parsed_args))
    self.AssertSetEquals(
        ['name-4 --project=b-project'],
        completer(prefix='name-4', parsed_args=parsed_args))

  def testZonalCompleterWithProjectEqPropertyZoneEqProperty(self):
    self.parser.add_argument('instance', completer=ZonalCompleter,
                             help='Auxilio aliis.')
    parsed_args = self.parser.parse_args(
        ['--project=a-project', '--zone=a-zone', 'name'])

    completer = parsed_args.GetPositionalArgument('instance').completer
    self.assertEquals(ZonalCompleter, completer.completer_class)

    self.AssertSetEquals(
        ['name-1'],
        completer(prefix='name', parsed_args=parsed_args))
    self.AssertSetEquals(
        ['name-1'],
        completer(prefix='name-1', parsed_args=parsed_args))
    self.AssertSetEquals(
        [],
        completer(prefix='name-2', parsed_args=parsed_args))
    self.AssertSetEquals(
        [],
        completer(prefix='name-3', parsed_args=parsed_args))
    self.AssertSetEquals(
        [],
        completer(prefix='name-4', parsed_args=parsed_args))

  def testZonalCompleterWithProjectEqPropertyZoneNeProperty(self):
    self.parser.add_argument('instance', completer=ZonalCompleter,
                             help='Auxilio aliis.')
    parsed_args = self.parser.parse_args(
        ['--project=a-project', '--zone=b-zone', 'name'])

    completer = parsed_args.GetPositionalArgument('instance').completer
    self.assertEquals(ZonalCompleter, completer.completer_class)

    self.AssertSetEquals(
        ['name-2'],
        completer(prefix='name', parsed_args=parsed_args))
    self.AssertSetEquals(
        [],
        completer(prefix='name-1', parsed_args=parsed_args))
    self.AssertSetEquals(
        ['name-2'],
        completer(prefix='name-2', parsed_args=parsed_args))
    self.AssertSetEquals(
        [],
        completer(prefix='name-3', parsed_args=parsed_args))
    self.AssertSetEquals(
        [],
        completer(prefix='name-4', parsed_args=parsed_args))

  def testZonalCompleterWithProjectNePropertyZoneEqProperty(self):
    self.parser.add_argument('instance', completer=ZonalCompleter,
                             help='Auxilio aliis.')
    parsed_args = self.parser.parse_args(
        ['--project=b-project', '--zone=a-zone', 'name'])

    completer = parsed_args.GetPositionalArgument('instance').completer
    self.assertEquals(ZonalCompleter, completer.completer_class)

    self.AssertSetEquals(
        ['name-3'],
        completer(prefix='name', parsed_args=parsed_args))
    self.AssertSetEquals(
        [],
        completer(prefix='name-1', parsed_args=parsed_args))
    self.AssertSetEquals(
        [],
        completer(prefix='name-2', parsed_args=parsed_args))
    self.AssertSetEquals(
        ['name-3'],
        completer(prefix='name-3', parsed_args=parsed_args))
    self.AssertSetEquals(
        [],
        completer(prefix='name-4', parsed_args=parsed_args))

  def testZonalCompleterWithProjectNePropertyZoneNeProperty(self):
    self.parser.add_argument('instance', completer=ZonalCompleter,
                             help='Auxilio aliis.')
    parsed_args = self.parser.parse_args(
        ['--project=b-project', '--zone=b-zone', 'name'])

    completer = parsed_args.GetPositionalArgument('instance').completer
    self.assertEquals(ZonalCompleter, completer.completer_class)

    self.AssertSetEquals(
        ['name-4'],
        completer(prefix='name', parsed_args=parsed_args))
    self.AssertSetEquals(
        [],
        completer(prefix='name-1', parsed_args=parsed_args))
    self.AssertSetEquals(
        [],
        completer(prefix='name-2', parsed_args=parsed_args))
    self.AssertSetEquals(
        [],
        completer(prefix='name-3', parsed_args=parsed_args))
    self.AssertSetEquals(
        ['name-4'],
        completer(prefix='name-4', parsed_args=parsed_args))

  def testRegionalCompleter(self):
    self.parser.add_argument('instance', completer=RegionalCompleter,
                             help='Auxilio aliis.')
    parsed_args = self.parser.parse_args(['name'])

    completer = parsed_args.GetPositionalArgument('instance').completer
    self.assertEquals(RegionalCompleter, completer.completer_class)

    self.AssertSetEquals(
        [
            'name-1',
            'name-2 --region=b-region',
            'name-3 --project=b-project',
            'name-4 --project=b-project --region=b-region',
        ],
        completer(prefix='name', parsed_args=parsed_args))
    self.AssertSetEquals(
        ['name-1'],
        completer(prefix='name-1', parsed_args=parsed_args))
    self.AssertSetEquals(
        ['name-2 --region=b-region'],
        completer(prefix='name-2', parsed_args=parsed_args))
    self.AssertSetEquals(
        ['name-3 --project=b-project'],
        completer(prefix='name-3', parsed_args=parsed_args))
    self.AssertSetEquals(
        ['name-4 --project=b-project --region=b-region'],
        completer(prefix='name-4', parsed_args=parsed_args))

  def testGlobalCompleter(self):
    self.parser.add_argument('instance', completer=GlobalCompleter,
                             help='Auxilio aliis.')
    parsed_args = self.parser.parse_args(['name'])

    completer = parsed_args.GetPositionalArgument('instance').completer
    self.assertEquals(GlobalCompleter, completer.completer_class)

    self.AssertSetEquals(
        [
            'name-1 --global',
            'name-2 --global',
            'name-3 --project=b-project --global',
            'name-4 --project=b-project --global',
        ],
        completer(prefix='name', parsed_args=parsed_args))
    self.AssertSetEquals(
        ['name-1 --global'],
        completer(prefix='name-1', parsed_args=parsed_args))
    self.AssertSetEquals(
        ['name-2 --global'],
        completer(prefix='name-2', parsed_args=parsed_args))
    self.AssertSetEquals(
        ['name-3 --project=b-project --global'],
        completer(prefix='name-3', parsed_args=parsed_args))
    self.AssertSetEquals(
        ['name-4 --project=b-project --global'],
        completer(prefix='name-4', parsed_args=parsed_args))

  def testMultiGlobalRegionalZonalCompleterQualifiedParameterNames(self):
    self.parser.add_argument(
        'instance', completer=MultiGlobalRegionalZonalCompleter,
        help='Auxilio aliis.')
    parsed_args = self.parser.parse_args(['name'])

    arg_completer = parsed_args.GetPositionalArgument('instance').completer
    self.assertEquals(MultiGlobalRegionalZonalCompleter,
                      arg_completer._completer_class)
    multi_completer = arg_completer._completer_class(cache=self.cache)

    qualified_parameter_names = {'region', 'zone'}
    for sub_completer in multi_completer.completers:
      self.AssertSetEquals(
          qualified_parameter_names,
          sub_completer.qualified_parameter_names,
          '{} qualified_parameter_names error'.format(
              sub_completer.__class__.__name__))

  def testMultiGlobalRegionalZonalCompleterInstance(self):
    self.parser.add_argument('instance',
                             completer=MultiGlobalRegionalZonalCompleter,
                             help='Auxilio aliis.')
    parsed_args = self.parser.parse_args(['name'])

    completer = parsed_args.GetPositionalArgument('instance').completer
    self.assertEquals(MultiGlobalRegionalZonalCompleter,
                      completer.completer_class)

    self.AssertSetEquals(
        [
            'name-1 --global',
            'name-1 --region=a-region',
            'name-1 --zone=a-zone',
            'name-2 --global',
            'name-2 --region=b-region',
            'name-2 --zone=b-zone',
            'name-3 --project=b-project --global',
            'name-3 --project=b-project --region=a-region',
            'name-3 --project=b-project --zone=a-zone',
            'name-4 --project=b-project --global',
            'name-4 --project=b-project --region=b-region',
            'name-4 --project=b-project --region=b-region',
            'name-4 --project=b-project --zone=b-zone',
        ],
        completer(prefix='name', parsed_args=parsed_args))
    self.AssertSetEquals(
        [
            'name-1 --global',
            'name-1 --region=a-region',
            'name-1 --zone=a-zone',
        ],
        completer(prefix='name-1', parsed_args=parsed_args))
    self.AssertSetEquals(
        [
            'name-2 --global',
            'name-2 --region=b-region',
            'name-2 --zone=b-zone',
        ],
        completer(prefix='name-2', parsed_args=parsed_args))
    self.AssertSetEquals(
        [
            'name-3 --project=b-project --region=a-region',
            'name-3 --project=b-project --global',
            'name-3 --project=b-project --zone=a-zone',
        ],
        completer(prefix='name-3', parsed_args=parsed_args))
    self.AssertSetEquals(
        [
            'name-4 --project=b-project --region=b-region',
            'name-4 --project=b-project --zone=b-zone',
            'name-4 --project=b-project --global',
        ],
        completer(prefix='name-4', parsed_args=parsed_args))

  def testMultiGlobalRegionalZonalCompleterFlag(self):
    self.parser.add_argument('--instance',
                             completer=MultiGlobalRegionalZonalCompleter,
                             help='Auxilio aliis.')
    self.parser.add_argument('--instance-project', help='Auxilio aliis.')
    self.parser.add_argument('--instance-global', help='Auxilio aliis.')
    self.parser.add_argument('--instance-region', help='Auxilio aliis.')
    self.parser.add_argument('--instance-zone', help='Auxilio aliis.')
    parsed_args = self.parser.parse_args(['--instance=name'])

    completer = parsed_args.GetFlagArgument('instance').completer
    self.assertEquals(MultiGlobalRegionalZonalCompleter,
                      completer.completer_class)

    self.AssertSetEquals(
        [
            'name-1 --instance-global',
            'name-1 --instance-region=a-region',
            'name-1 --instance-zone=a-zone',
            'name-2 --instance-global',
            'name-2 --instance-region=b-region',
            'name-2 --instance-zone=b-zone',
            'name-3 --instance-project=b-project --instance-global',
            'name-3 --instance-project=b-project --instance-region=a-region',
            'name-3 --instance-project=b-project --instance-zone=a-zone',
            'name-4 --instance-project=b-project --instance-global',
            'name-4 --instance-project=b-project --instance-region=b-region',
            'name-4 --instance-project=b-project --instance-zone=b-zone',
        ],
        completer(prefix='name', parsed_args=parsed_args))
    self.AssertSetEquals(
        [
            'name-1 --instance-zone=a-zone',
            'name-1 --instance-global',
            'name-1 --instance-region=a-region',
        ],
        completer(prefix='name-1', parsed_args=parsed_args))
    self.AssertSetEquals(
        [
            'name-2 --instance-zone=b-zone',
            'name-2 --instance-region=b-region',
            'name-2 --instance-global',
        ],
        completer(prefix='name-2', parsed_args=parsed_args))
    self.AssertSetEquals(
        [
            'name-3 --instance-project=b-project --instance-region=a-region',
            'name-3 --instance-project=b-project --instance-zone=a-zone',
            'name-3 --instance-project=b-project --instance-global',
        ],
        completer(prefix='name-3', parsed_args=parsed_args))
    self.AssertSetEquals(
        [
            'name-4 --instance-project=b-project --instance-region=b-region',
            'name-4 --instance-project=b-project --instance-global',
            'name-4 --instance-project=b-project --instance-zone=b-zone',
        ],
        completer(prefix='name-4', parsed_args=parsed_args))

  def testGlobalRegionalZonalCompleterFlags(self):
    self.parser.add_argument('--g-instance', completer=GlobalCompleter,
                             help='Auxilio aliis.')
    self.parser.add_argument('--g-instance-project', help='Auxilio aliis.')
    self.parser.add_argument('--g-instance-global', help='Auxilio aliis.')
    self.parser.add_argument('--r-instance', completer=RegionalCompleter,
                             help='Auxilio aliis.')
    self.parser.add_argument('--r-instance-project', help='Auxilio aliis.')
    self.parser.add_argument('--r-instance-region', help='Auxilio aliis.')
    self.parser.add_argument('--z-instance', completer=ZonalCompleter,
                             help='Auxilio aliis.')
    self.parser.add_argument('--z-instance-project', help='Auxilio aliis.')
    self.parser.add_argument('--z-instance-zone', help='Auxilio aliis.')
    parsed_args = self.parser.parse_args([
        '--g-instance=name-1',
        '--r-instance=name-2',
        '--z-instance=name-3',
    ])

    g_completer = parsed_args.GetFlagArgument('g_instance').completer
    self.assertEquals(GlobalCompleter, g_completer.completer_class)

    r_completer = parsed_args.GetFlagArgument('r_instance').completer
    self.assertEquals(RegionalCompleter, r_completer.completer_class)

    z_completer = parsed_args.GetFlagArgument('z_instance').completer
    self.assertEquals(ZonalCompleter, z_completer.completer_class)

    self.AssertSetEquals(
        [
            'name-1 --g-instance-global',
            'name-2 --g-instance-global',
            'name-3 --g-instance-project=b-project --g-instance-global',
            'name-4 --g-instance-project=b-project --g-instance-global',
        ],
        g_completer(prefix='name', parsed_args=parsed_args))
    self.AssertSetEquals(
        [
            'name-1',
            'name-2 --r-instance-region=b-region',
            'name-3 --r-instance-project=b-project',
            'name-4 --r-instance-project=b-project'
            ' --r-instance-region=b-region',
        ],
        r_completer(prefix='name', parsed_args=parsed_args))
    self.AssertSetEquals(
        [
            'name-1',
            'name-2 --z-instance-zone=b-zone',
            'name-3 --z-instance-project=b-project',
            'name-4 --z-instance-project=b-project --z-instance-zone=b-zone',
        ],
        z_completer(prefix='name', parsed_args=parsed_args))

  def testTestCompleter(self):
    self.parser.add_argument('--instance', completer=TrialCompleter,
                             help='Auxilio aliis.')
    self.parser.add_argument('--test', help='Auxilio aliis.')
    parsed_args = self.parser.parse_args(['--instance=name'])

    completer = parsed_args.GetFlagArgument('instance').completer
    self.assertEquals(TrialCompleter, completer.completer_class)

    self.assertEquals(
        [
            'no-error',
        ],
        completer(prefix='no-error', parsed_args=parsed_args))
    self.assertEquals(
        [
            'unknown-method-errorERROR: '
            'tests.testInstance resource completer failed.',
            'unknown-method-errorREASON: '
            "'TrialCompleter' object has no attribute 'UnknownMethod'",
        ],
        completer(prefix='unknown-method-error', parsed_args=parsed_args))
    self.assertEquals(
        [
            'update-errorERROR: '
            'tests.testInstance resource completer failed.',
            'update-errorREASON: '
            'Catastrophic cache update failure.      ',
        ],
        completer(prefix='update-error', parsed_args=parsed_args))
    self.assertEquals(
        [
            'no-parametersERROR: '
            'tests.testInstance resource completer failed.',
            'no-parametersREASON: '
            "'NoneType' object is not iterable      ",
        ],
        completer(prefix='no-parameters', parsed_args=parsed_args))
    self.assertEquals(
        [
            None,
        ],
        completer(prefix='GetParameterFlag-no-property-no-value',
                  parsed_args=parsed_args))
    self.assertEquals(
        [
            '--test=no-property-value',
        ],
        completer(prefix='GetParameterFlag-no-property-value',
                  parsed_args=parsed_args))
    self.assertEquals(
        [
            '--test=test-property-value',
        ],
        completer(prefix='GetParameterFlag-property-no-value',
                  parsed_args=parsed_args))
    self.assertEquals(
        [
            '--test=property-value',
        ],
        completer(prefix='GetParameterFlag-property-value',
                  parsed_args=parsed_args))


if __name__ == '__main__':
  completer_test_base.main()
