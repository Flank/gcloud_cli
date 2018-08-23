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

"""Tests for the generator.py script."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.regen import resource_generator
from googlecloudsdk.api_lib.util import resource
from tests.lib import parameterized
from tests.lib import test_case


class ApiMapGeneratorTest(test_case.Base, parameterized.TestCase):

  @parameterized.parameters([
      # Normal case.
      ('projects.foos', 'projects/{projectsId}/foos/{foosId}',
       'projects', 'projects/{projectsId}'),
      # Normal, but non-dotted collection name
      ('foos', 'projects/{projectsId}/foos/{foosId}',
       'projects', 'projects/{projectsId}'),
      # Extra parameter, dotted collection.
      ('projects.foos', 'projects/{projectsId}/foos/{foosId}/{extra}',
       'projects', 'projects/{projectsId}'),
      # Extra parameter, but non-dotted collection name
      ('foos', 'projects/{projectsId}/foos/{foosId}/{extra}',
       'projects', 'projects/{projectsId}'),
      # Extra non-param.
      ('projects.foos', 'projects/{projectsId}/foos/extra/{foosId}',
       'projects', 'projects/{projectsId}'),
      # Extra non-param, but non-dotted collection name
      ('foos', 'projects/{projectsId}/foos/extra/{foosId}',
       'projects', 'projects/{projectsId}'),
      # Extra param in parent.
      ('projects.foos', 'projects/{projectsId}/{extra}/foos/{foosId}',
       'projects', 'projects/{projectsId}/{extra}'),
      # Extra param in parent, but non-dotted collection name
      ('foos', 'projects/{projectsId}/{extra}/foos/{foosId}',
       'projects', 'projects/{projectsId}/{extra}'),
      # Extra non-param in parent.
      ('projects.foos', 'projects/extra/{projectsId}/foos/{foosId}',
       'projects', 'projects/extra/{projectsId}'),
      # Extra non-param in parent.but non-dotted collection name
      ('foos', 'projects/extra/{projectsId}/foos/{foosId}',
       'extra', 'projects/extra/{projectsId}'),
      # Extra non-param in parent.
      ('projects.foos', '{extra}/{projectsId}/foos/{foosId}',
       None, None),
      # Extra non-param in parent.but non-dotted collection name
      ('foos', '{extra}/{projectsId}/foos/{foosId}',
       None, None),
      # No parent of a root thing.
      ('projects', 'projects/{projectsId}',
       None, None),
      # No parent of a thing with only params.
      ('projects', '{extra}/{projectsId}',
       None, None),
  ])
  def testGetParentCollection(self, collection_name, flat_path,
                              parent_name, parent_path):
    collection_info = resource.CollectionInfo(
        'api_name', 'api_version', 'base_url', 'docs_url', collection_name,
        'atomic_path', {'': flat_path}, [])
    self.assertEqual(resource_generator._GetParentCollection(collection_info),
                     (parent_name, parent_path))


if __name__ == '__main__':
  test_case.main()
