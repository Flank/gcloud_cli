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

"""Unit tests for the compute flags module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections

from googlecloudsdk.calliope import actions
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.credentials import gce as c_gce
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.calliope import util


class ResourceArgumentTestBase(cli_test_base.CliTestBase):

  def SetUp(self):
    self.parser = util.ArgumentParser()
    self.parser.add_argument(
        '--project',
        metavar='PROJECT_ID',
        dest='project',
        help='Google Cloud Platform project ID to use for this invocation.',
        action=actions.StoreProperty(properties.VALUES.core.project))
    self.registry = resources.Registry()

  def _ParseArgs(self, resource_args, cmd_line):
    for resource_arg in resource_args:
      resource_arg.AddArgument(self.parser)
    return self.parser.parse_args(cmd_line)

  def _AssertArgs(self, expected, actual):
    self.assertEqual(
        set(expected + ['project']),
        set([attr for attr in dir(actual) if attr[0].islower()]))


class ResourceArgumentTest(ResourceArgumentTestBase):

  def testRequiredAsPositional_Empty(self):
    resource_arg = flags.ResourceArgument(
        global_collection='compute.backendServices')
    with self.AssertRaisesArgumentErrorMatches(
        'argument NAME: Must be specified.'):
      self._ParseArgs([resource_arg], [])
    with self.AssertRaisesArgumentErrorMatches(
        'argument NAME: Must be specified.'):
      self._ParseArgs([resource_arg], [])

  def testOptionalAsPositional_Empty(self):
    resource_arg = flags.ResourceArgument(
        required=False,
        global_collection='compute.backendServices')
    args = self._ParseArgs([resource_arg], [])
    self.assertTrue(hasattr(args, 'name'))
    self.assertIsNone(args.name)
    ref = resource_arg.ResolveAsResource(args, self.registry)
    self.assertIsNone(ref)
    self.AssertErrEquals('')

  def testRequiredAsFlag_Empty(self):
    resource_arg = flags.ResourceArgument(
        name='--instance-group',
        global_collection='compute.instanceGroup')
    with self.AssertRaisesArgumentErrorMatches(
        'argument --instance-group: Must be specified.'):
      self._ParseArgs([resource_arg], [])

  def testOptionalAsFlag_Empty(self):
    resource_arg = flags.ResourceArgument(
        name='--instance-group',
        required=False,
        global_collection='compute.instanceGroup')
    args = self._ParseArgs([resource_arg], [])
    self._AssertArgs(['instance_group'], args)
    self.assertIsNone(args.instance_group)
    ref = resource_arg.ResolveAsResource(args, self.registry)
    self.assertIsNone(ref)
    self.AssertErrEquals('')

  def testRequiredPositional_AsGlobal(self):
    resource_arg = flags.ResourceArgument(
        global_collection='compute.backendServices')

    args = self._ParseArgs([resource_arg], ['fish', '--project', 'atlantic'])
    self.assertEqual('fish', args.name)
    self._AssertArgs(['name'], args)

    ref = resource_arg.ResolveAsResource(args, self.registry)
    self.assertEqual(
        'https://compute.googleapis.com/compute/v1/projects/atlantic/global/'
        'backendServices/fish', ref.SelfLink())
    self.assertEqual('fish', ref.Name())
    self.assertEqual('atlantic', ref.project)
    self.assertEqual('fish', ref.backendService)
    self.AssertErrEquals('')

  def testOptionalPositional_AsGlobal(self):
    resource_arg = flags.ResourceArgument(
        '--backend-service',
        global_collection='compute.backendServices')
    args = self._ParseArgs(
        [resource_arg], ['--backend-service', 'fish', '--project', 'atlantic'])
    self.assertEqual('fish', args.backend_service)
    self._AssertArgs(['backend_service'], args)

    ref = resource_arg.ResolveAsResource(args, self.registry)
    self.assertEqual(
        'https://compute.googleapis.com/compute/v1/projects/atlantic/global/'
        'backendServices/fish', ref.SelfLink())
    self.assertEqual('fish', ref.Name())
    self.assertEqual('atlantic', ref.project)
    self.assertEqual('fish', ref.backendService)
    self.AssertErrEquals('')

  def testOptionalPositional_AsRegionals(self):
    resource_arg = flags.ResourceArgument(
        '--forwarding-rule',
        regional_collection='compute.forwardingRules')
    args = self._ParseArgs(
        [resource_arg],
        ['--forwarding-rule', 'fish', '--project', 'atlantic',
         '--forwarding-rule-region', 'north-sea-1'])
    self._AssertArgs(['forwarding_rule', 'forwarding_rule_region'], args)
    self.assertEqual('fish', args.forwarding_rule)

    ref = resource_arg.ResolveAsResource(
        args, self.registry, default_scope=compute_scope.ScopeEnum.REGION)
    self.assertEqual(
        'https://compute.googleapis.com/compute/v1/projects/atlantic/'
        'regions/north-sea-1/forwardingRules/fish', ref.SelfLink())
    self.assertEqual('fish', ref.Name())
    self.assertEqual('atlantic', ref.project)
    self.assertEqual('fish', ref.forwardingRule)
    self.AssertErrEquals('')

  def testRequiredPositional_AsRegionalWithoutRegion(self):
    resource_arg = flags.ResourceArgument(
        regional_collection='compute.regionOperations')

    args = self._ParseArgs(
        [resource_arg], ['fish', '--project', 'atlantic'])
    self.assertEqual('fish', args.name)
    self._AssertArgs(['name', 'region'], args)

    with self.assertRaisesRegex(
        flags.UnderSpecifiedResourceError,
        r'Underspecified resource \[fish\]. Specify the \[--region\] flag.'):
      resource_arg.ResolveAsResource(
          args, self.registry, default_scope=compute_scope.ScopeEnum.REGION)
    self.AssertErrEquals('')

  def testRequiredPositional_AsRegional(self):
    resource_arg = flags.ResourceArgument(
        regional_collection='compute.regionOperations')

    args = self._ParseArgs(
        [resource_arg],
        ['fish', '--project', 'atlantic', '--region', 'north-sea-2'])
    self.assertEqual('fish', args.name)
    self._AssertArgs(['name', 'region'], args)

    ref = resource_arg.ResolveAsResource(
        args, self.registry, default_scope=compute_scope.ScopeEnum.REGION)
    self.assertEqual(
        'https://compute.googleapis.com/compute/v1/projects/atlantic/'
        'regions/north-sea-2/operations/fish', ref.SelfLink())
    self.assertEqual('fish', ref.Name())
    self.assertEqual('atlantic', ref.project)
    self.assertEqual('north-sea-2', ref.region)
    self.assertEqual('fish', ref.operation)
    self.AssertErrEquals('')

  def testRequiredPositional_AsRegionalViaProperty(self):
    resource_arg = flags.ResourceArgument(
        regional_collection='compute.regionOperations')
    properties.VALUES.compute.region.Set('north-sea-2')
    args = self._ParseArgs(
        [resource_arg],
        ['fish', '--project', 'atlantic'])

    ref = resource_arg.ResolveAsResource(
        args, self.registry, default_scope=compute_scope.ScopeEnum.REGION)
    self.assertEqual(
        'https://compute.googleapis.com/compute/v1/projects/atlantic/'
        'regions/north-sea-2/operations/fish', ref.SelfLink())

  def testRequiredPositional_AsRegionalAndGlobal(self):
    resource_arg = flags.ResourceArgument(
        regional_collection='compute.forwardingRules',
        global_collection='compute.globalForwardingRules')

    args = self._ParseArgs(
        [resource_arg],
        ['fish', '--project', 'atlantic', '--global'])
    self.assertEqual('fish', args.name)
    self._AssertArgs(['name', 'region', 'global'], args)

    ref = resource_arg.ResolveAsResource(
        args, self.registry, default_scope=compute_scope.ScopeEnum.REGION)
    self.assertEqual(
        'https://compute.googleapis.com/compute/v1/projects/atlantic/'
        'global/forwardingRules/fish', ref.SelfLink())
    self.assertEqual('fish', ref.Name())
    self.assertEqual('atlantic', ref.project)
    self.assertEqual('fish', ref.forwardingRule)
    self.AssertErrEquals('')

  def testRequiredPositionalURL_AsRegionalAndGlobal(self):
    resource_arg = flags.ResourceArgument(
        regional_collection='compute.forwardingRules',
        global_collection='compute.globalForwardingRules')

    resource_uri = ('https://compute.googleapis.com/compute/v1/projects/atlantic/'
                    'regions/north-sea-3/forwardingRules/fish')
    args = self._ParseArgs([resource_arg], [resource_uri])
    self._AssertArgs(['name', 'region', 'global'], args)
    self.assertEqual(resource_uri, args.name)

    # Try to resolve this as default global resource even when we got regional.
    ref = resource_arg.ResolveAsResource(
        args, self.registry, default_scope=compute_scope.ScopeEnum.GLOBAL)
    self.assertEqual(resource_uri, ref.SelfLink())
    self.AssertErrEquals('')

  def testRequiredPositionalURL_AsRaiseIfUnexpectedCollection(self):
    resource_arg = flags.ResourceArgument(
        global_collection='compute.globalForwardingRules')

    resource_uri = ('https://compute.googleapis.com/compute/v1/projects/atlantic/'
                    'regions/north-sea-3/forwardingRules/fish')
    args = self._ParseArgs([resource_arg], [resource_uri])
    with self.assertRaisesRegex(
        resources.WrongResourceCollectionException,
        r'wrong collection: expected \[compute.globalForwardingRules\], '
        r'got \[compute.forwardingRules\], for path \[{0}\]'
        .format(resource_uri)):
      resource_arg.ResolveAsResource(
          args, self.registry, default_scope=compute_scope.ScopeEnum.GLOBAL)

  def testRequiredPositionalAndOptionalFlag_DifferentScopes(self):
    resource_arg1 = flags.ResourceArgument(
        name='forwarding_rule',
        regional_collection='compute.forwardingRules',
        global_collection='compute.globalForwardingRules')

    resource_arg2 = flags.ResourceArgument(
        '--operation',
        required=False,
        regional_collection='compute.regionOperations',
        zonal_collection='compute.zoneOperations')

    args = self._ParseArgs(
        [resource_arg1, resource_arg2],
        ['fish', '--project', 'atlantic', '--region', 'north-sea-3',
         '--operation', 'viking', '--operation-zone', 'skagerrak'])
    self._AssertArgs(['forwarding_rule', 'region', 'global',
                      'operation', 'operation_region', 'operation_zone'], args)
    self.assertEqual('fish', args.forwarding_rule)

    ref1 = resource_arg1.ResolveAsResource(
        args, self.registry, default_scope=compute_scope.ScopeEnum.GLOBAL)
    self.assertEqual(
        'https://compute.googleapis.com/compute/v1/projects/atlantic/'
        'regions/north-sea-3/forwardingRules/fish', ref1.SelfLink())
    self.assertEqual('fish', ref1.Name())
    self.assertEqual('atlantic', ref1.project)
    self.assertEqual('north-sea-3', ref1.region)
    self.assertEqual('fish', ref1.forwardingRule)

    ref2 = resource_arg2.ResolveAsResource(
        args, self.registry, default_scope=None)
    self.assertEqual(
        'https://compute.googleapis.com/compute/v1/projects/atlantic/'
        'zones/skagerrak/operations/viking', ref2.SelfLink())
    self.assertEqual('viking', ref2.Name())
    self.assertEqual('atlantic', ref2.project)
    self.assertEqual('skagerrak', ref2.zone)
    self.assertEqual('viking', ref2.operation)

    self.AssertErrEquals('')

  def testRequiredPositional_Plural(self):
    resource_arg = flags.ResourceArgument(
        plural=True,
        regional_collection='compute.forwardingRules',
        global_collection='compute.globalForwardingRules')

    args = self._ParseArgs(
        [resource_arg],
        ['fish', 'shark', 'whale', '--project', 'atlantic', '--global'])
    self._AssertArgs(['name', 'region', 'global'], args)
    self.assertEqual(['fish', 'shark', 'whale'], args.name)

    refs = resource_arg.ResolveAsResource(
        args, self.registry, default_scope=compute_scope.ScopeEnum.REGION)
    self.assertEqual(
        ['https://compute.googleapis.com/compute/v1/projects/atlantic/'
         'global/forwardingRules/{0}'.format(name)
         for name in ['fish', 'shark', 'whale']],
        [ref.SelfLink() for ref in refs])
    self.AssertErrEquals('')

  def testOptionalFlag_Plural(self):
    resource_arg = flags.ResourceArgument(
        '--forwarding-rules',
        plural=True,
        regional_collection='compute.forwardingRules',
        global_collection='compute.globalForwardingRules')

    args = self._ParseArgs(
        [resource_arg],
        ['--forwarding-rules', 'fish,shark,whale',
         '--project', 'atlantic', '--global-forwarding-rules'])
    self._AssertArgs(['forwarding_rules', 'forwarding_rules_region',
                      'global_forwarding_rules'], args)
    self.assertEqual(['fish', 'shark', 'whale'], args.forwarding_rules)

    refs = resource_arg.ResolveAsResource(
        args, self.registry, default_scope=compute_scope.ScopeEnum.REGION)
    self.assertEqual(
        ['https://compute.googleapis.com/compute/v1/projects/atlantic/'
         'global/forwardingRules/{0}'.format(name)
         for name in ['fish', 'shark', 'whale']],
        [ref.SelfLink() for ref in refs])
    self.AssertErrEquals('')

  def testOptionalUnderspecified_RaisesWhenCantPrompt(self):
    resource_arg = flags.ResourceArgument(
        '--forwarding-rule',
        regional_collection='compute.forwardingRules',
        global_collection='compute.globalForwardingRules')

    args = self._ParseArgs(
        [resource_arg],
        ['--forwarding-rule', 'fish',
         '--project', 'atlantic'])
    self._AssertArgs(['forwarding_rule', 'forwarding_rule_region',
                      'global_forwarding_rule'], args)
    self.assertEqual('fish', args.forwarding_rule)

    with self.assertRaisesRegex(
        flags.UnderSpecifiedResourceError,
        r'Underspecified resource \[fish\]. '
        r'Specify one of the \[--forwarding-rule-region, '
        r'--global-forwarding-rule\] flags.'):
      resource_arg.ResolveAsResource(args, self.registry, default_scope=None)
    self.AssertErrEquals('')

  def testOptionalResourceMissingWhileScopePresent(self):
    resource_arg = flags.ResourceArgument(
        '--instance-group',
        resource_name='instance group',
        required=False,
        zonal_collection='compute.instanceGroups')

    zone = 'us-central1-a'
    args = self._ParseArgs(
        [resource_arg],
        ['--project', 'atlantic', '--instance-group-zone',
         ('https://compute.googleapis.com/compute/v1/projects/my-project/zones/'
          '{0}'.format(zone))])
    self._AssertArgs(['instance_group', 'instance_group_zone'], args)
    self.assertEqual(None, args.instance_group)

    with self.assertRaisesRegex(
        exceptions.Error,
        r'Can\'t specify --instance-group-zone without specifying resource via '
        r'instance_group'):
      resource_arg.ResolveAsResource(
          args, self.registry, default_scope=compute_scope.ScopeEnum.REGION)


class ResourceArgumentWithPromptingTest(ResourceArgumentTestBase):

  def SetUp(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)

  def testOptional_UnderspecifiedSingleScoped(self):
    resource_arg = flags.ResourceArgument(
        '--forwarding-rule',
        resource_name='forwarding rule',
        regional_collection='compute.forwardingRules')

    args = self._ParseArgs(
        [resource_arg],
        ['--forwarding-rule', 'fish',
         '--project', 'atlantic'])
    self._AssertArgs(['forwarding_rule', 'forwarding_rule_region'], args)
    self.assertEqual('fish', args.forwarding_rule)

    resource = collections.namedtuple('Resource', ['name'])
    def ScopeLister(scopes, unused_underspecified_names):
      self.assertEqual([compute_scope.ScopeEnum.REGION], scopes)
      return {
          compute_scope.ScopeEnum.REGION:
              [resource(name='north-sea'), resource(name='baltic')]}
    self.WriteInput('1')
    ref = resource_arg.ResolveAsResource(
        args, self.registry, default_scope=None, scope_lister=ScopeLister)
    self.assertEqual(
        'https://compute.googleapis.com/compute/v1/projects/atlantic/'
        'regions/baltic/forwardingRules/fish',
        ref.SelfLink())
    self.AssertErrEquals(
        r'{"ux": "PROMPT_CHOICE", "message": "For the following forwarding '
        r'rule:\n - [fish]\nchoose a region:", "choices": ["baltic", '
        '"north-sea"]}\n')

  def testOptional_UnderspecifiedMultiScoped(self):
    resource_arg = flags.ResourceArgument(
        '--forwarding-rule',
        resource_name='forwarding rule',
        regional_collection='compute.forwardingRules',
        global_collection='compute.globalForwardingRules')

    args = self._ParseArgs(
        [resource_arg],
        ['--forwarding-rule', 'fish',
         '--project', 'atlantic'])
    self._AssertArgs(['forwarding_rule', 'forwarding_rule_region',
                      'global_forwarding_rule'], args)
    self.assertEqual('fish', args.forwarding_rule)

    resource = collections.namedtuple('Resource', ['name'])
    def ScopeLister(scopes, unused_underspecified_names):
      self.assertEqual(
          {compute_scope.ScopeEnum.REGION, compute_scope.ScopeEnum.GLOBAL},
          set(scopes))
      return {
          compute_scope.ScopeEnum.REGION:
              [resource(name='atlantic'), resource(name='indian')],
          compute_scope.ScopeEnum.GLOBAL:
              [resource(name='')]}

    self.WriteInput('1')
    ref = resource_arg.ResolveAsResource(
        args, self.registry, default_scope=None, scope_lister=ScopeLister)
    self.AssertErrEquals(
        r'{"ux": "PROMPT_CHOICE", "message": "For the following forwarding '
        r'rule:\n - [fish]\nchoose a region or global:", "choices": ["global", '
        '"region: atlantic", "region: indian"]}\n')
    self.assertEqual(
        'https://compute.googleapis.com/compute/v1/projects/atlantic/'
        'global/forwardingRules/fish',
        ref.SelfLink())

  def testOptional_UnderspecifiedSingleScoped_WithRegionGce(self):
    properties.VALUES.core.check_gce_metadata.Set(True)
    if c_gce.Metadata().connected:
      region = c_gce.Metadata().Region()
    else:
      region = 'north-sea'
      self.StartObjectPatch(c_gce._GCEMetadata, 'Region', return_value=region)

    resource_arg = flags.ResourceArgument(
        '--forwarding-rule',
        resource_name='forwarding rule',
        regional_collection='compute.forwardingRules')

    args = self._ParseArgs(
        [resource_arg],
        ['--forwarding-rule', 'fish',
         '--project', 'atlantic'])
    self._AssertArgs(['forwarding_rule', 'forwarding_rule_region'], args)
    self.assertEqual('fish', args.forwarding_rule)

    self.WriteInput('Y')
    ref = resource_arg.ResolveAsResource(
        args, self.registry, default_scope=None)
    self.assertEqual(
        'https://compute.googleapis.com/compute/v1/projects/atlantic/'
        'regions/{0}/forwardingRules/fish'.format(region),
        ref.SelfLink())
    self.AssertErrContains(
        'Did you mean region [{0}] for forwarding rule: [fish]'.format(region))

  def testOptional_UnderspecifiedSingleScoped_WithZoneGce(self):
    properties.VALUES.core.check_gce_metadata.Set(True)
    if c_gce.Metadata().connected:
      zone = c_gce.Metadata().Zone()
    else:
      zone = 'skagerrak'
      self.StartObjectPatch(c_gce._GCEMetadata, 'Zone', return_value=zone)

    resource_arg = flags.ResourceArgument(
        '--instance-group',
        resource_name='instance group',
        zonal_collection='compute.instanceGroups')

    args = self._ParseArgs(
        [resource_arg],
        ['--instance-group', 'fish',
         '--project', 'atlantic'])
    self._AssertArgs(['instance_group', 'instance_group_zone'], args)
    self.assertEqual('fish', args.instance_group)

    self.WriteInput('Y')
    ref = resource_arg.ResolveAsResource(
        args, self.registry, default_scope=None)
    self.assertEqual(
        'https://compute.googleapis.com/compute/v1/projects/atlantic/'
        'zones/{0}/instanceGroups/fish'.format(zone),
        ref.SelfLink())
    self.AssertErrContains(
        'Did you mean zone [{0}] for instance group: [fish]'.format(zone))

  def testZoneByUri(self):
    resource_arg = flags.ResourceArgument(
        '--instance-group',
        resource_name='instance group',
        zonal_collection='compute.instanceGroups')

    zone = 'us-central1-a'
    args = self._ParseArgs(
        [resource_arg],
        ['--instance-group', 'fish',
         '--project', 'atlantic', '--instance-group-zone',
         ('https://compute.googleapis.com/compute/v1/projects/my-project/zones/'
          '{0}'.format(zone))])
    self._AssertArgs(['instance_group', 'instance_group_zone'], args)
    self.assertEqual('fish', args.instance_group)

    ref = resource_arg.ResolveAsResource(
        args, self.registry, default_scope=None)
    self.assertEqual(
        'https://compute.googleapis.com/compute/v1/projects/atlantic/'
        'zones/{0}/instanceGroups/fish'.format(zone),
        ref.SelfLink())


class ResourceResolverTest(sdk_test_base.WithOutputCapture):

  def testBadNamesArgument(self):
    resolver = flags.ResourceResolver.FromMap(
        'instance',
        {compute_scope.ScopeEnum.ZONE: 'compute.instances'})
    with self.assertRaisesRegex(
        flags.BadArgumentException,
        r'Expected names to be a list but it is \'instance-x\''):
      resolver.ResolveResources('instance-x',
                                resource_scope=None,
                                scope_value='zone-x',
                                default_scope=compute_scope.ScopeEnum.ZONE,
                                api_resource_registry=resources.REGISTRY)

  def testBadScopesArgument(self):
    resolver = flags.ResourceResolver.FromMap(
        'instance',
        {compute_scope.ScopeEnum.ZONE: 'compute.instances'})
    with self.assertRaisesRegex(
        flags.BadArgumentException,
        'Unexpected value for default_scope ScopeEnum.REGION, '
        'expected None or ZONE'):
      resolver.ResolveResources(['instance-x'],
                                resource_scope=None,
                                scope_value='zone-x',
                                default_scope=compute_scope.ScopeEnum.REGION,
                                api_resource_registry=resources.REGISTRY)

if __name__ == '__main__':
  test_case.main()
