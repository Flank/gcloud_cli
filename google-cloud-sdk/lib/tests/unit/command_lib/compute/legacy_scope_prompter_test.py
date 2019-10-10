# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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

"""Unit tests for the compute flags module wrt scope_prompter."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import client_adapter
from googlecloudsdk.api_lib.compute import scope_prompter
from googlecloudsdk.calliope import actions
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.credentials import gce as c_gce
from tests.lib import test_case
from tests.lib.calliope import util
from tests.lib.surface.compute import test_base
from six.moves import zip


class MockComputeCommand(scope_prompter.ScopePrompter):

  def __init__(self, registry, compute_client, resource_type):
    self._resources = registry
    self._compute = compute_client
    self._resource_type = resource_type

  @property
  def resource_type(self):
    return self._resource_type

  @property
  def compute(self):
    return self._compute

  @property
  def resources(self):
    return self._resources

  @property
  def http(self):
    pass

  @property
  def project(self):
    pass

  @property
  def batch_url(self):
    pass


class EquivalenceTest(test_base.BaseTest):

  def SetUp(self):
    self.parser = util.ArgumentParser()
    self.parser.add_argument(
        '--project',
        metavar='PROJECT_ID',
        dest='project',
        help='Google Cloud Platform project ID to use for this invocation.',
        action=actions.StoreProperty(properties.VALUES.core.project))
    self.registry = resources.Registry()
    self.compute_client = client_adapter.ClientAdapter(api_default_version='v1')
    self.client = self.compute_client.apitools_client
    self.messages = self.compute_client.messages

    self.StartObjectPatch(console_io, 'CanPrompt', return_value=True)
    self.StartObjectPatch(console_io, 'IsInteractive', return_value=True)

  def _ParseArgs(self, resource_args, cmd_line):
    for resource_arg in resource_args:
      resource_arg.AddArgument(self.parser.parser._calliope_command.ai)
    return self.parser.parse_args(cmd_line + ['--project', 'atlantic'])

  def _AssertArgs(self, expected, actual):
    self.assertEqual(
        set(expected + ['project']),
        set([attr for attr in dir(actual) if not attr.startswith('_')]))

  def MakeCommand(self, resource_type=None):
    return MockComputeCommand(
        registry=self.registry,
        compute_client=self.client,
        resource_type=resource_type)

  def _WithGceZone(self, zone=None):
    properties.VALUES.core.check_gce_metadata.Set(True)
    if c_gce.Metadata().connected:
      zone = c_gce.Metadata().Zone()
    else:
      self.StartObjectPatch(c_gce._GCEMetadata, 'Zone', return_value=zone)
    return zone

  def testGlobal(self):
    resource_arg = flags.ResourceArgument(
        global_collection='compute.backendServices')

    args = self._ParseArgs([resource_arg], ['fish'])
    resource_ref = resource_arg.ResolveAsResource(args, self.registry)
    self.assertEqual(
        'https://compute.googleapis.com/compute/v1/projects/atlantic/global/'
        'backendServices/fish', resource_ref.SelfLink())

    prompter_ref = self.MakeCommand().CreateGlobalReference(
        args.name, resource_type='backendServices')
    self.assertEqual(resource_ref, prompter_ref)

    self.AssertOutputEquals('')
    self.AssertErrEquals('')

  def testRegional(self):
    resource_arg = flags.ResourceArgument(
        '--forwarding-rule',
        regional_collection='compute.forwardingRules')
    args = self._ParseArgs(
        [resource_arg],
        ['--forwarding-rule', 'fish',
         '--forwarding-rule-region', 'north-sea-1'])
    resource_ref = resource_arg.ResolveAsResource(
        args, self.registry, default_scope=compute_scope.ScopeEnum.REGION)
    self.assertEqual(
        'https://compute.googleapis.com/compute/v1/projects/atlantic/'
        'regions/north-sea-1/forwardingRules/fish', resource_ref.SelfLink())

    command = self.MakeCommand(resource_type='forwardingRules')
    prompter_ref = command.CreateRegionalReference(
        args.forwarding_rule,
        region_arg=args.forwarding_rule_region,
        resource_type='forwardingRules')
    self.assertEqual(resource_ref, prompter_ref)

    self.AssertOutputEquals('')
    self.AssertErrEquals('')

  def testZonal(self):
    resource_arg = flags.ResourceArgument(
        '--operation',
        zonal_collection='compute.zoneOperations')
    args = self._ParseArgs(
        [resource_arg],
        ['--operation', 'viking', '--operation-zone', 'skagerrak'])
    resource_ref = resource_arg.ResolveAsResource(
        args, self.registry, default_scope=compute_scope.ScopeEnum.ZONE)
    self.assertEqual(
        'https://compute.googleapis.com/compute/v1/projects/atlantic'
        '/zones/skagerrak/operations/viking',
        resource_ref.SelfLink())

    command = self.MakeCommand(resource_type='zoneOperations')
    prompter_ref = command.CreateZonalReference(
        args.operation,
        zone_arg=args.operation_zone,
        resource_type='zoneOperations')
    self.assertEqual(resource_ref, prompter_ref)

    self.AssertOutputEquals('')
    self.AssertErrEquals('')

  def testZonalSingleUnderspecified_WithPromptUseGce(self):
    """Parses zonal argument without zone being specified while on GCE.

    Expect a prompt 'Do you mean zone ...'.
    """
    zone = self._WithGceZone('skagerrak')

    resource_arg = flags.ResourceArgument(
        '--operation',
        resource_name='operation',
        plural=True,
        zonal_collection='compute.zoneOperations')
    operation_names = ['viking', 'norse', 'inuit']
    args = self._ParseArgs(
        [resource_arg], ['--operation', ','.join(operation_names)])

    self.WriteInput('Y')
    resource_refs = resource_arg.ResolveAsResource(
        args, self.registry, default_scope=compute_scope.ScopeEnum.ZONE)
    self.AssertErrContains(
        'Did you mean zone [{0}] for operation: [viking, norse, inuit]'
        .format(zone))
    self.ClearErr()
    for operation_name, resource_ref in zip(operation_names, resource_refs):
      self.assertEqual(
          'https://compute.googleapis.com/compute/v1/projects/atlantic'
          '/zones/{0}/operations/{1}'.format(zone, operation_name),
          resource_ref.SelfLink())

    self.WriteInput('Y')
    command = self.MakeCommand(resource_type='zoneOperations')
    prompter_refs = command.CreateZonalReferences(
        args.operation,
        zone_arg=args.operation_zone,
        resource_type='zoneOperations')
    for prompter_ref, resource_ref in zip(prompter_refs, resource_refs):
      self.assertEqual(resource_ref, prompter_ref)

    self.AssertOutputEquals('')
    self.AssertErrContains(
        'Did you mean zone [{0}] for zone operations: [viking, norse, inuit]?'
        .format(zone))

if __name__ == '__main__':
  test_case.main()
