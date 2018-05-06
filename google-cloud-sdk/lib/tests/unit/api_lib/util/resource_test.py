# -*- coding: utf-8 -*-
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

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.util import resource as resource_util
from tests.lib import test_case


class SplitUrlTest(test_case.Base):

  def testGoogleApis(self):
    domain = 'www.googleapis.com'
    api_name = 'sql'
    api_version = 'v1beta3'
    resource_path = 'path/to/resource'
    url = 'https://{0}/{1}/{2}/{3}'.format(
        domain, api_name, api_version, resource_path)
    self.assertEqual((api_name, api_version, resource_path),
                     resource_util.SplitDefaultEndpointUrl(url))

  def testGoogleApis_NoVersion_NoResource(self):
    domain = 'googleapis.com'
    api_name = 'ml'
    url = 'https://{0}.{1}/'.format(api_name, domain)
    self.assertEqual((api_name, None, ''),
                     resource_util.SplitDefaultEndpointUrl(url))

  def testGoogleApis_NoResource(self):
    domain = 'www.googleapis.com'
    api_name = 'sql'
    api_version = 'v1beta3'
    resource_path = ''
    url = 'https://{0}/{1}/{2}/{3}'.format(
        domain, api_name, api_version, resource_path)
    self.assertEqual((api_name, api_version, resource_path),
                     resource_util.SplitDefaultEndpointUrl(url))

  def testGoogleApis_ApiNameFirst(self):
    domain = 'googleapis.com'
    api_name = 'sql'
    api_version = 'v1beta3'
    resource_path = 'path/to/resource'
    url = 'https://{1}.{0}/{2}/{3}'.format(
        domain, api_name, api_version, resource_path)
    self.assertEqual((api_name, api_version, resource_path),
                     resource_util.SplitDefaultEndpointUrl(url))

  def testGoogleApis_ApiNameFirst_NoResource(self):
    domain = 'googleapis.com'
    api_name = 'sql'
    api_version = 'v1beta3'
    resource_path = ''
    url = 'https://{1}.{0}/{2}/{3}'.format(
        domain, api_name, api_version, resource_path)
    self.assertEqual((api_name, api_version, resource_path),
                     resource_util.SplitDefaultEndpointUrl(url))

  def testOtherDomain(self):
    domain = 'otherdomain.com'
    api_name = 'sql'
    api_version = 'v1beta3'
    resource_path = 'path/to/resource'
    url = 'https://{0}/{1}/{2}/{3}'.format(
        domain, api_name, api_version, resource_path)
    self.assertEqual((api_name, api_version, resource_path),
                     resource_util.SplitDefaultEndpointUrl(url))


class UriTemplateTests(test_case.Base):

  def testEmptyPath(self):
    self.assertEqual([], resource_util.GetParamsFromPath(''))

  def testPathWithNoParams(self):
    self.assertEqual([], resource_util.GetParamsFromPath('//a/b/c'))

  def testPathSingleParams(self):
    self.assertEqual(['bvalue'],
                     resource_util.GetParamsFromPath('//a/b/{bvalue}/c'))

  def testPathMultiParams(self):
    self.assertEqual(
        ['bvalue', 'cvalue'],
        resource_util.GetParamsFromPath('//a/b/{bvalue}/c/{cvalue}'))
    self.assertEqual(
        ['bvalue', 'cvalue'],
        resource_util.GetParamsFromPath('//a/b/{bvalue}/c/{cvalue}/d'))
    self.assertEqual(
        ['bvalue', 'cvalue'],
        resource_util.GetParamsFromPath('//a/b/{bvalue}/c/{cvalue}:custom'))
    self.assertEqual(
        ['bvalue', 'cvalue'],
        resource_util.GetParamsFromPath('//a/b/{bvalue}/c/{cvalue}/d:custom'))

  def testPathSingleOnlyParams(self):
    self.assertEqual(['bvalue'], resource_util.GetParamsFromPath('{+bvalue}'))
    self.assertEqual(['bvalue'],
                     resource_util.GetParamsFromPath('{+bvalue}:custom'))


class CollectionInfoTests(test_case.Base):

  def testDefaultSubcollection(self):
    collection_info = resource_util.CollectionInfo(
        'sql', 'v1beta3',
        base_url='http://base_url.com/v1beta3',
        docs_url='https://cloud.google.com/docs',
        name='backupRuns',
        path=('projects/{project}/instances/{instance}/'
              'backupRuns/{backupConfiguration}/dueTime/{dueTime}'),
        flat_paths=[],
        params=['project', 'instance', 'backupConfiguration', 'dueTime'])
    self.assertEqual(['project', 'instance', 'backupConfiguration', 'dueTime'],
                     collection_info.GetParams(''))
    self.assertEqual('projects/{project}/instances/{instance}/'
                     'backupRuns/{backupConfiguration}/dueTime/{dueTime}',
                     collection_info.GetPath(''))

