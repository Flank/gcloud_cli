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

import itertools

from googlecloudsdk.api_lib.util import resource as resource_util
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.apis import registry
from googlecloudsdk.command_lib.util.apis import resource_arg_schema
from googlecloudsdk.command_lib.util.apis import yaml_command_schema_util as util
from googlecloudsdk.core import resources
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib.command_lib.util.apis import base


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

    spec = r._GenerateResourceSpec(
        'foo.projects.zones', 'v1', ['projectsId', 'zonesId'])
    project_attr, zone_attr = spec.attributes[0], spec.attributes[1]
    self.assertEqual(project_attr.name, 'project')
    self.assertEqual(project_attr.help_text, 'help1')
    self.assertEqual(zone_attr.name, 'zone')
    self.assertEqual(zone_attr.help_text, concepts.ANCHOR_HELP)
    self.assertTrue(spec.disable_auto_completers)

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

    spec = r._GenerateResourceSpec(
        'foo.projects.zones', 'v1', ['projectsId', 'zonesId'])
    self.assertFalse(spec.disable_auto_completers)
    zone_attr = spec.attributes[1]
    self.assertEqual('zoneField', zone_attr.completion_id_field)
    self.assertEqual({'field1': 'value1'}, zone_attr.completion_request_params)

  def testRemovedFlagsValidation(self):
    with self.assertRaisesRegexp(
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

  @parameterized.parameters(True, False)
  def testGenerateAttributesValidation(self, is_atomic):
    with self.assertRaisesRegexp(
        resource_arg_schema.InvalidResourceArgumentLists,
        r'Invalid resource arguments: Expected \[\[projectsId\], instancesId\],'
        r' Found \[\]'):
      resource_arg_schema._GenerateAttributes(['projectsId', 'instancesId'], [])

    with self.assertRaisesRegexp(
        resource_arg_schema.InvalidResourceArgumentLists,
        r'Invalid resource arguments: Expected \[\[projectsId\], instancesId\],'
        r' Found \[junk\]'):
      resource_arg_schema._GenerateAttributes(
          ['projectsId', 'instancesId'],
          [{'parameter_name': 'junk', 'attribute_name': 'junk', 'help': 'h'}])

    with self.assertRaisesRegexp(
        resource_arg_schema.InvalidResourceArgumentLists,
        r'Invalid resource arguments: Expected \[\[projectsId\], instancesId\],'
        r' Found \[instancesId, extraId\]'):
      resource_arg_schema._GenerateAttributes(
          ['projectsId', 'instancesId'],
          [{'parameter_name': 'instancesId', 'attribute_name': 'instance',
            'help': 'h'},
           {'parameter_name': 'extraId', 'attribute_name': 'extra',
            'help': 'h'}])


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
    self.MockGetListCreateMethods(('foo.projects.instances', is_atomic))
    method = registry.GetMethod('foo.projects.instances', method)

    r = resource_arg_schema.YAMLResourceArgument(
        {
            'name': 'instance',
            'collection': method.resource_argument_collection.full_name,
            'attributes': [
                {'parameter_name': f, 'attribute_name': f, 'help': 'h'}
                for f in fields]
        },
        group_help='group_help')
    if success:
      r.GenerateResourceSpec(method.resource_argument_collection)
    else:
      with self.assertRaises(resource_arg_schema.InvalidResourceArgumentLists):
        r.GenerateResourceSpec(method.resource_argument_collection)

  def testWithParentResource(self):
    self.MockGetListCreateMethods(('foo.projects.instances', False))
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
    self.MockGetListCreateMethods(('foo.projects.instances', True))
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
    self.MockGetListCreateMethods(('foo.projects.instances', True))
    method = registry.GetMethod('foo.projects.instances', 'get')

    r = resource_arg_schema.YAMLResourceArgument(
        {'name': 'instance', 'collection': 'asdf', 'attributes': []},
        group_help='group_help')

    with self.assertRaisesRegexp(
        util.InvalidSchemaError,
        r'Collection names do not match for resource argument specification '
        r'\[instance\]. Expected \[foo.projects.instances\], found \[asdf\]'):
      r.GenerateResourceSpec(method.collection)

    r = resource_arg_schema.YAMLResourceArgument(
        {'name': 'instance', 'api_version': 'foo',
         'collection': 'foo.projects.instances', 'attributes': []},
        group_help='group_help')

    with self.assertRaisesRegexp(
        util.InvalidSchemaError,
        r'API versions do not match for resource argument specification '
        r'\[instance\]. Expected \[v1\], found \[foo\]'):
      r.GenerateResourceSpec(method.collection)


if __name__ == '__main__':
  sdk_test_base.main()
