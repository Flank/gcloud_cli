# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Tests for googlecloudsdk.command_lib.util.args.repeated."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.args import resource_args
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from tests.lib import test_case


class ResourceArgsTest(test_case.TestCase):

  def SetUp(self):
    self.spec_data = {
        'collection': 'bigquery.tables',
        'attributes': [{
            'parameter_name': 'projectId',
            'attribute_name': 'project',
            'help': 'The project ID.'
        },
                       {
                           'parameter_name': 'datasetId',
                           'attribute_name': 'dataset',
                           'help': 'The id of the BigQuery dataset.'
                       },
                       {
                           'parameter_name': 'tableId',
                           'attribute_name': 'table',
                           'help': 'The id of the BigQuery table.'
                       }],
        'disable_auto_completers': False,
        'name': 'table'
    }
    self.table_attribute = concepts.ResourceParameterAttributeConfig(
        name='table', help_text='The id of the BigQuery {resource}.')
    self.dataset_attribute = concepts.ResourceParameterAttributeConfig(
        name='dataset', help_text='The id of the BigQuery {resource}.')

  def testGetResourcePresentationSpec(self):
    expected = presentation_specs.ResourcePresentationSpec(
        '--table',
        concepts.ResourceSpec(
            'bigquery.tables',
            resource_name='table',
            datasetId=self.dataset_attribute,
            tableId=self.table_attribute,
            projectId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
            disable_auto_completers=False),
        'The table to create.',
        required=False,
        prefixes=True)

    result = resource_args.GetResourcePresentationSpec('table', 'to create',
                                                       self.spec_data)
    self.assertEqual(expected.attribute_to_args_map,
                     result.attribute_to_args_map)
    self.assertEqual(expected.group_help,
                     result.group_help)

  def testGetResourcePresentationSpecAllArgs(self):
    self.table_attribute.attribute_name = 'source'
    expected = presentation_specs.ResourcePresentationSpec(
        'table',
        concepts.ResourceSpec(
            'bigquery.tables',
            resource_name='table',
            datasetId=self.dataset_attribute,
            tableId=self.table_attribute,
            projectId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
            disable_auto_completers=False),
        'A New help text for table to create.',
        required=True,
        prefixes=False)
    result = resource_args.GetResourcePresentationSpec(
        'table',
        'to create',
        self.spec_data,
        required=True,
        prefixes=False,
        help_text='A New help text for {name} {verb}.',
        attribute_overrides={'table': 'source'},
        positional=True)
    self.assertEqual(expected.attribute_to_args_map,
                     result.attribute_to_args_map)
    self.assertEqual(expected.group_help,
                     result.group_help)
