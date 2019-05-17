# -*- coding: utf-8 -*- #
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

"""Tests for the yaml command schema."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import itertools
import re

from googlecloudsdk.api_lib.util import resource as resource_util
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.apis import registry
from googlecloudsdk.command_lib.util.apis import resource_arg_schema
from googlecloudsdk.command_lib.util.apis import yaml_command_schema_util as util
from googlecloudsdk.core import resources
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib.command_lib.util.apis import base

import mock


class ResourceArgSchemaTests(sdk_test_base.SdkBase, parameterized.TestCase):
  """Tests of the command schema."""

  def SetUp(self):
    reg = resources.REGISTRY
    reg.registered_apis['foo'] = ['v1']
    zone_collection = resource_util.CollectionInfo(
        'foo', 'v1', '', '', 'projects.zones',
        'projects/{projectsId}/zones/{zonesId}',
        {'': 'projects/{projectsId}/zones/{zonesId}'},
        ['projectsId', 'zonesId'])
    # pylint:disable=protected-access
    reg._RegisterCollection(zone_collection)

  def testResource(self):
    r = resource_arg_schema.YAMLResourceArgument.FromData(
        {
            'help_text': 'group help',
            'spec': {'name': 'zone', 'collection': 'foo.projects.zones',
                     'attributes': [
                         {'parameter_name': 'projectsId',
                          'attribute_name': 'project',
                          'help': 'help1'},
                         {'parameter_name': 'zonesId',
                          'attribute_name': 'zone',
                          'help': 'help2'}]},
            'removed_flags': ['zone'],
            'is_positional': False})
    self.assertEqual(r.group_help, 'group help')
    self.assertEqual(r.removed_flags, ['zone'])
    self.assertEqual(r.is_positional, False)

    mock_resource = mock.MagicMock(
        full_name='foo.projects.zones',
        api_version='v1',
        detailed_params=['projectsId', 'zonesId'])
    spec = r.GenerateResourceSpec(mock_resource)
    project_attr, zone_attr = spec.attributes[0], spec.attributes[1]
    self.assertEqual(project_attr.name, 'project')
    self.assertEqual(project_attr.help_text, 'help1')
    self.assertEqual(
        project_attr.fallthroughs,
        concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG.fallthroughs)
    self.assertEqual(zone_attr.name, 'zone')
    self.assertEqual(zone_attr.help_text, 'help2')
    self.assertEqual(zone_attr.fallthroughs, [])
    self.assertTrue(spec.disable_auto_completers)

  def testPluralNameInResource(self):
    r = resource_arg_schema.YAMLResourceArgument.FromData(
        {
            'help_text': 'group help',
            'spec': {'name': 'zone', 'collection': 'foo.projects.zones',
                     'plural_name': 'zones',
                     'attributes': [
                         {'parameter_name': 'projectsId',
                          'attribute_name': 'project',
                          'help': 'help1'},
                         {'parameter_name': 'zonesId',
                          'attribute_name': 'zone',
                          'help': 'help2'}]},
            'removed_flags': ['zone'],
            'is_positional': False})

    mock_resource = mock.MagicMock(
        full_name='foo.projects.zones',
        api_version='v1',
        detailed_params=['projectsId', 'zonesId'])
    spec = r.GenerateResourceSpec(mock_resource)
    self.assertEqual('zones', spec.plural_name)

  def testResourceWithFlagNameOverride(self):
    arg_schema = resource_arg_schema.YAMLResourceArgument.FromData(
        {
            'help_text': 'group help',
            'spec': {'name': 'zone', 'collection': 'foo.projects.zones',
                     'attributes': [
                         {'parameter_name': 'projectsId',
                          'attribute_name': 'project',
                          'help': 'help1'},
                         {'parameter_name': 'zonesId',
                          'attribute_name': 'zone',
                          'help': 'help2'}]},
            'removed_flags': ['zone'],
            'arg_name': 'alt-zone',
            'is_positional': False})
    self.assertEqual(arg_schema.group_help, 'group help')
    self.assertEqual(arg_schema.removed_flags, ['zone'])
    self.assertFalse(arg_schema.is_positional)
    spec = arg_schema.GenerateResourceSpec(
        mock.MagicMock(
            full_name='foo.projects.zones',
            api_version='v1',
            detailed_params=['projectsId', 'zonesId']))
    project_attr, zone_attr = spec.attributes[0], spec.attributes[1]
    self.assertEqual(project_attr.name, 'project')
    self.assertEqual(project_attr.help_text, 'help1')
    self.assertEqual(spec.name, 'alt-zone')
    self.assertEqual(zone_attr.help_text, 'help2')
    self.assertTrue(spec.disable_auto_completers)

  def testResourceWithProjectProperty(self):
    r = resource_arg_schema.YAMLResourceArgument.FromData(
        {
            'help_text': 'group help',
            'spec': {'name': 'zone', 'collection': 'foo.projects.zones',
                     'attributes': [
                         {'parameter_name': 'projectsId',
                          'attribute_name': 'project',
                          'help': 'help1',
                          'prop': 'core/project'},
                         {'parameter_name': 'zonesId',
                          'attribute_name': 'zone',
                          'help': 'help2'}]},
            'removed_flags': ['zone'],
            'is_positional': False})

    mock_resource = mock.MagicMock(
        full_name='foo.projects.zones',
        api_version='v1',
        detailed_params=['projectsId', 'zonesId'])
    spec = r.GenerateResourceSpec(mock_resource)

    project_attr = spec.attributes[0]

    # Should only use the project property one time.
    self.assertEqual(
        project_attr.fallthroughs,
        concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG.fallthroughs)

  def testResourceWithIgnoredProject(self):
    r = resource_arg_schema.YAMLResourceArgument.FromData(
        {
            'help_text': 'group help',
            'spec': {'name': 'zone', 'collection': 'foo.projects.zones',
                     'attributes': [
                         {'parameter_name': 'zonesId',
                          'attribute_name': 'zone',
                          'help': 'help2'}]},
            'removed_flags': ['zone'],
            'is_positional': False})

    mock_resource = mock.MagicMock(
        full_name='foo.projects.zones',
        api_version='v1',
        detailed_params=['projectsId', 'zonesId'])
    spec = r.GenerateResourceSpec(mock_resource)
    project_attr = spec.attributes[0]

    self.assertEqual(project_attr.name, 'project')
    self.assertEqual(project_attr.help_text,
                     'The Cloud project for the {resource}.')
    self.assertEqual(
        project_attr.fallthroughs,
        concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG.fallthroughs)

  def testResourceWithCompleters(self):
    r = resource_arg_schema.YAMLResourceArgument.FromData(
        {
            'help_text': 'group help',
            'spec': {'name': 'zone', 'collection': 'foo.projects.zones',
                     'attributes': [
                         {'parameter_name': 'projectsId',
                          'attribute_name': 'project',
                          'help': 'help1'},
                         {'parameter_name': 'zonesId',
                          'attribute_name': 'zone',
                          'help': 'help2',
                          'completion_id_field': 'zoneField',
                          'completion_request_params': [
                              {'fieldName': 'field1', 'value': 'value1'}]}],
                     'disable_auto_completers': False},
            'removed_flags': ['zone'],
            'is_positional': False})

    mock_resource = mock.MagicMock(
        full_name='foo.projects.zones',
        api_version='v1',
        detailed_params=['projectsId', 'zonesId'])
    spec = r.GenerateResourceSpec(mock_resource)
    self.assertFalse(spec.disable_auto_completers)
    zone_attr = spec.attributes[1]
    self.assertEqual('zoneField', zone_attr.completion_id_field)
    self.assertEqual({'field1': 'value1'}, zone_attr.completion_request_params)

  def testRemovedFlagsValidation(self):
    with self.assertRaisesRegex(
        util.InvalidSchemaError,
        r'Removed flag \[asdf\] for resource arg \[zone\] references an '
        r'attribute that does not exist. Valid attributes are '
        r'\[project, zone\]'):
      resource_arg_schema.YAMLResourceArgument.FromData(
          {
              'help_text': 'group help',
              'spec': {'name': 'zone', 'collection': 'foo.projects.zones',
                       'attributes': [
                           {'parameter_name': 'projectsId',
                            'attribute_name': 'project',
                            'help': 'help1'},
                           {'parameter_name': 'zonesId',
                            'attribute_name': 'zone',
                            'help': 'help2'}]},
              'removed_flags': ['asdf']})

  @parameterized.named_parameters(
      ('Flag', {'arg_name': 'other-zone'}, '--other-zone'),
      ('Positional', {'arg_name': 'other-zone', 'is_positional': True},
       'OTHER_ZONE'))
  def testWithCommandFallthroughs(self, fallthrough_def, arg_name):
    r = resource_arg_schema.YAMLResourceArgument.FromData(
        {
            'help_text': 'group help',
            'spec': {'name': 'zone', 'collection': 'foo.projects.zones',
                     'attributes': [
                         {'parameter_name': 'projectsId',
                          'attribute_name': 'project',
                          'help': 'help1'},
                         {'parameter_name': 'zonesId',
                          'attribute_name': 'zone',
                          'help': 'help2'}]},
            'command_level_fallthroughs': {
                'zone': [fallthrough_def]}})
    expected = {'zone': [arg_name]}
    self.assertEqual(expected, r.command_level_fallthroughs)

  def testFromDataWithDisplayNameHook(self):
    data = {'name': 'location',
            'help_text': 'group help',
            'spec': {'name': 'zone', 'collection': 'foo.projects.zones',
                     'attributes': [
                         {'parameter_name': 'projectsId',
                          'attribute_name': 'project',
                          'help': 'help1'},
                         {'parameter_name': 'zonesId',
                          'attribute_name': 'zone',
                          'help': 'help2'}]},
            'display_name_hook': 'path.to:Hook'}
    mock_hook = self.StartObjectPatch(util.Hook, 'FromPath',
                                      return_value='hook')
    resource_arg = resource_arg_schema.YAMLConceptArgument.FromData(data)
    self.assertEqual(resource_arg.display_name_hook, 'hook')
    mock_hook.assert_called_once_with('path.to:Hook')


class MultitypeTests(base.Base, parameterized.TestCase):

  def SetUp(self):
    self._zone_spec = {
        'name': 'zone', 'collection': 'foo.projects.zones',
        'attributes': [
            {'parameter_name': 'projectsId',
             'attribute_name': 'project',
             'help': 'help1'},
            {'parameter_name': 'zonesId',
             'attribute_name': 'zone',
             'help': 'help2'}]}
    self._region_spec = {
        'name': 'region', 'collection': 'foo.projects.regions',
        'attributes': [
            {'parameter_name': 'projectsId',
             'attribute_name': 'project',
             'help': 'help1'},
            {'parameter_name': 'regionsId',
             'attribute_name': 'region',
             'help': 'help3'}]}
    self._instance_spec = {
        'name': 'instance', 'collection': 'foo.projects.zones.instances',
        'attributes': [
            {'parameter_name': 'projectsId',
             'attribute_name': 'project',
             'help': 'help1'},
            {'parameter_name': 'zonesId',
             'attribute_name': 'zone',
             'help': 'help2'},
            {'parameter_name': 'instancesId',
             'attribute_name': 'instance',
             'help': 'help3'}]}
    self._no_zone_instance_spec = {
        'name': 'instance', 'collection': 'foo.projects.instances',
        'attributes': [
            {'parameter_name': 'projectsId',
             'attribute_name': 'project',
             'help': 'help1'},
            {'parameter_name': 'instancesId',
             'attribute_name': 'instance',
             'help': 'help3'}]}

  @parameterized.named_parameters(
      ('Resource',
       {'name': 'x', 'collection': 'foo.bar', 'attributes': []},
       resource_arg_schema.YAMLResourceArgument),
      ('MultitypeResource',
       {'name': 'x', 'resources': []},
       resource_arg_schema.YAMLMultitypeResourceArgument))
  def testConceptArgFromData(self, resource_spec, expected_type):
    spec = {'name': 'location',
            'help_text': 'group help',
            'spec': resource_spec}
    resource_arg = resource_arg_schema.YAMLConceptArgument.FromData(spec)
    self.assertTrue(isinstance(resource_arg, expected_type))

  def testMultitypeResourceArg(self):
    self.MockCRUDMethods(('foo.projects.zones', True),
                         ('foo.projects.regions', True))
    r = resource_arg_schema.YAMLMultitypeResourceArgument.FromData(
        {
            'name': 'location',
            'help_text': 'group help',
            'spec': {
                'name': 'region-or-zone',
                'resources': [self._zone_spec, self._region_spec]}})
    self.assertEqual(r.group_help, 'group help')
    self.assertEqual(r.removed_flags, [])
    self.assertEqual(r.is_positional, None)

    spec = r.GenerateResourceSpec()
    project_attr, zone_attr, region_attr = [spec.attributes[0],
                                            spec.attributes[1],
                                            spec.attributes[2]]
    self.assertEqual(project_attr.name, 'project')
    self.assertEqual(project_attr.help_text, 'help1')
    self.assertEqual(
        project_attr.fallthroughs,
        concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG.fallthroughs)
    self.assertEqual(zone_attr.name, 'zone')
    self.assertEqual(zone_attr.help_text, 'help2')
    self.assertEqual(zone_attr.fallthroughs, [])
    self.assertEqual(region_attr.name, 'region')
    self.assertEqual(region_attr.help_text, 'help3')
    self.assertEqual(region_attr.fallthroughs, [])
    self.assertTrue(spec.disable_auto_completers)

  def testMultitypeResourceArg_ParentChild(self):
    self.MockCRUDMethods(('foo.projects.zones', True),
                         ('foo.projects.zones.instances', True))
    r = resource_arg_schema.YAMLMultitypeResourceArgument.FromData(
        {
            'name': 'instance',
            'help_text': 'group help',
            'spec': {
                'name': 'instance-or-zone',
                'resources': [self._zone_spec, self._instance_spec]}})
    self.assertEqual(r.group_help, 'group help')
    self.assertEqual(r.removed_flags, [])
    self.assertEqual(r.is_positional, None)

    spec = r.GenerateResourceSpec()
    project_attr, zone_attr, instance_attr = [spec.attributes[0],
                                              spec.attributes[1],
                                              spec.attributes[2]]
    self.assertEqual(project_attr.name, 'project')
    self.assertEqual(project_attr.help_text, 'help1')
    self.assertEqual(
        project_attr.fallthroughs,
        concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG.fallthroughs)
    self.assertEqual(zone_attr.name, 'zone')
    self.assertEqual(zone_attr.help_text, 'help2')
    self.assertEqual(zone_attr.fallthroughs, [])
    self.assertEqual(instance_attr.name, 'instance')
    self.assertEqual(instance_attr.help_text, 'help3')
    self.assertEqual(instance_attr.fallthroughs, [])
    self.assertTrue(spec.disable_auto_completers)

  def testMultitypeResourceArg_ExtraAttribute(self):
    self.MockCRUDMethods(('foo.projects.zones.instances', True),
                         ('foo.projects.instances', True))
    r = resource_arg_schema.YAMLMultitypeResourceArgument.FromData(
        {
            'name': 'location',
            'help_text': 'group help',
            'spec': {
                'name': 'region-or-zone',
                'resources': [self._instance_spec,
                              self._no_zone_instance_spec]}})
    self.assertEqual(r.group_help, 'group help')
    self.assertEqual(r.removed_flags, [])
    self.assertEqual(r.is_positional, None)

    spec = r.GenerateResourceSpec()
    project_attr, zone_attr, instance_attr = [spec.attributes[0],
                                              spec.attributes[1],
                                              spec.attributes[2]]
    self.assertEqual(project_attr.name, 'project')
    self.assertEqual(project_attr.help_text, 'help1')
    self.assertEqual(
        project_attr.fallthroughs,
        concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG.fallthroughs)
    self.assertEqual(zone_attr.name, 'zone')
    self.assertEqual(zone_attr.help_text, 'help2')
    self.assertEqual(zone_attr.fallthroughs, [])
    self.assertEqual(instance_attr.name, 'instance')
    self.assertEqual(instance_attr.help_text, 'help3')
    self.assertEqual(instance_attr.fallthroughs, [])
    self.assertTrue(spec.disable_auto_completers)

  def testMultitypeResourceArgOptions(self):
    self.MockCRUDMethods(('foo.projects.zones', True),
                         ('foo.projects.regions', True))
    r = resource_arg_schema.YAMLMultitypeResourceArgument.FromData(
        {
            'name': 'location',
            'is_positional': False,
            'help_text': 'group help',
            'removed_flags': ['region'],
            'command_level_fallthroughs': {
                'region': [{'arg_name': 'other-region'}]},
            'spec': {
                'name': 'region-or-zone',
                'plural_name': 'regions-or-zones',
                'resources': [self._zone_spec, self._region_spec]}})
    self.assertEqual(r.group_help, 'group help')
    self.assertEqual(r.removed_flags, ['region'])
    self.assertEqual(r.is_positional, False)
    self.assertEqual(r.command_level_fallthroughs,
                     {'region': ['--other-region']})
    self.assertEqual(r._plural_name, 'regions-or-zones')

  def testMultitypeResourceArgMismatchedCollection(self):
    self.MockCRUDMethods(('foo.projects.zones', True),
                         ('foo.projects.regions', True))
    r = resource_arg_schema.YAMLMultitypeResourceArgument.FromData(
        {
            'name': 'location',
            'is_positional': False,
            'help_text': 'group help',
            'spec': {
                'name': 'region-or-zone',
                'resources': [self._zone_spec, self._region_spec]}})
    collection_info = resource_util.CollectionInfo(
        'bar', 'v1', '', '', 'projects.zones',
        'projects/{projectsId}/zones/{zonesId}',
        {'': 'projects/{projectsId}/zones/{zonesId}'},
        ['projectsId', 'zonesId'])
    with self.assertRaisesRegex(
        util.InvalidSchemaError,
        re.escape(
            'Collection names do not match for resource argument specification '
            '[region-or-zone]. Expected [bar.projects.zones version v1], and '
            'no contained resources matched. Given collections: '
            '[foo.projects.regions None, foo.projects.zones None]')):
      r.GenerateResourceSpec(collection_info)

  def testFromDataWithDisplayNameHook(self):
    data = {'name': 'location',
            'help_text': 'group help',
            'spec': {'name': 'zone',
                     'resources': [self._zone_spec, self._region_spec]},
            'display_name_hook': 'path.to:Hook'}
    mock_hook = self.StartObjectPatch(util.Hook, 'FromPath',
                                      return_value='hook')
    resource_arg = resource_arg_schema.YAMLConceptArgument.FromData(data)
    self.assertEqual(resource_arg.display_name_hook, 'hook')
    mock_hook.assert_called_once_with('path.to:Hook')


class CollectionValidationTests(base.Base, parameterized.TestCase):

  @parameterized.parameters(itertools.product(
      [True, False],
      [('get', ['projectsId', 'instancesId'], True),
       ('get', ['instancesId'], True),
       ('get', [], False),
       ('get', ['junk'], False),
       ('get', ['projectsId', 'instancesId', 'extra'], False),
       ('list', ['projectsId'], True),
       ('list', [], True),
       ('list', ['junk'], False),
       ('list', ['projectsId', 'extra'], False),
      ]))
  def testGenerateAttributes(self, is_atomic, data):
    method, fields, success = data
    self.MockCRUDMethods(('foo.projects.instances', is_atomic))
    method = registry.GetMethod('foo.projects.instances', method)

    r = resource_arg_schema.YAMLResourceArgument(
        {
            'name': 'instance',
            'collection': method.resource_argument_collection.full_name,
            'attributes': [
                {'parameter_name': f, 'attribute_name': f.lower(), 'help': 'h'}
                for f in fields]
        },
        group_help='group_help')
    if success:
      r.GenerateResourceSpec(method.resource_argument_collection)
    else:
      with self.assertRaises(concepts.InvalidResourceArgumentLists):
        r.GenerateResourceSpec(method.resource_argument_collection)

  def testWithParentResource(self):
    self.MockCRUDMethods(('foo.projects.instances', False))
    method = registry.GetMethod('foo.projects.instances', 'create')

    r = resource_arg_schema.YAMLResourceArgument(
        {
            'name': 'instance',
            'collection': 'foo.projects',
            'attributes': [
                {'parameter_name': 'projectsId', 'attribute_name': 'project',
                 'help': 'h'}],
        },
        group_help='group_help', is_parent_resource=True)

    r.GenerateResourceSpec(method.resource_argument_collection)

  def testUnspecifiedCollection(self):
    self.MockCRUDMethods(('foo.projects.instances', True))
    r = resource_arg_schema.YAMLResourceArgument(
        {'name': 'instance', 'api_version': 'v1',
         'collection': 'foo.projects.instances', 'attributes': [
             {'parameter_name': 'instancesId', 'attribute_name': 'instance',
              'help': 'h'}]},
        group_help='group_help')
    r.GenerateResourceSpec()

    # Same test but use the default API version.
    r = resource_arg_schema.YAMLResourceArgument(
        {'name': 'instance',
         'collection': 'foo.projects.instances', 'attributes': [
             {'parameter_name': 'instancesId', 'attribute_name': 'instance',
              'help': 'h'}]},
        group_help='group_help')
    r.GenerateResourceSpec()

  def testCollectionErrors(self):
    self.MockCRUDMethods(('foo.projects.instances', True))
    method = registry.GetMethod('foo.projects.instances', 'get')

    r = resource_arg_schema.YAMLResourceArgument(
        {'name': 'instance', 'collection': 'asdf', 'attributes': []},
        group_help='group_help')

    with self.assertRaisesRegex(
        util.InvalidSchemaError,
        r'Collection names do not match for resource argument specification '
        r'\[instance\]. Expected \[foo.projects.instances\], found \[asdf\]'):
      r.GenerateResourceSpec(method.collection)

    r = resource_arg_schema.YAMLResourceArgument(
        {'name': 'instance', 'api_version': 'foo',
         'collection': 'foo.projects.instances', 'attributes': []},
        group_help='group_help')

    with self.assertRaisesRegex(
        util.InvalidSchemaError,
        r'API versions do not match for resource argument specification '
        r'\[instance\]. Expected \[v1\], found \[foo\]'):
      r.GenerateResourceSpec(method.collection)

  def testCollectionOverride(self):
    self.MockCRUDMethods(('foo.projects.instances', True),
                         ('bar.instances', True))
    method = registry.GetMethod('foo.projects.instances', 'get')

    r = resource_arg_schema.YAMLResourceArgument(
        {'name': 'instance', 'collection': 'bar.instances',
         'attributes': [
             {'parameter_name': 'instancesId', 'attribute_name': 'instance',
              'help': 'h'}]},
        group_help='group_help', override_resource_collection=True)

    r.GenerateResourceSpec(method.collection)

if __name__ == '__main__':
  sdk_test_base.main()
