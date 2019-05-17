# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import resource as resource_util
from tests.lib import parameterized
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

  def testGoogleApis_K8sStyle(self):
    domain = 'googleapis.com'
    api_name = 'run'
    api_version = 'v1beta3'
    resource_path = 'path/to/resource'
    k8s_api = 'elephant.dev'
    url = 'https://{api}.{domain}/apis/{k8s_api}/{version}/{resource}'.format(
        domain=domain,
        api=api_name,
        k8s_api=k8s_api,
        version=api_version,
        resource=resource_path)
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

  def testGoogleStagingApi(self):
    url = 'https://www-googleapis-staging.sandbox.google.com/mock/v1/projects/your-stuff'
    self.assertEqual(('mock', 'v1', 'projects/your-stuff'),
                     resource_util.SplitDefaultEndpointUrl(url))


class SplitUrlTestWithDomainSplitting(test_case.Base, parameterized.TestCase):

  @parameterized.parameters('staging_v1', 'staging_alpha', 'staging_beta', 'v1',
                            'alpha', 'beta')
  def testOldStyleComputeApis(self, api_version):
    domain = 'www.googleapis.com'
    api_name = 'compute'
    resource_path = 'path/to/resource'
    url = 'https://{domain}/{api_name}/{api_version}/{resource_path}'.format(
        domain=domain,
        api_name=api_name,
        api_version=api_version,
        resource_path=resource_path)
    self.assertEqual((api_name, api_version, resource_path),
                     resource_util.SplitDefaultEndpointUrl(url))

  @parameterized.parameters('staging_v1', 'staging_alpha', 'staging_beta', 'v1',
                            'alpha', 'beta')
  def testComputeApis(self, api_version):
    domain = 'compute.googleapis.com'
    api_name = 'compute'
    resource_path = 'path/to/resource'
    url = 'https://{domain}/{api_name}/{api_version}/{resource_path}'.format(
        domain=domain,
        api_name=api_name,
        api_version=api_version,
        resource_path=resource_path)
    self.assertEqual((api_name, api_version, resource_path),
                     resource_util.SplitDefaultEndpointUrl(url))


class SplitUrlTestWithMalformedFormat(test_case.Base):
  # Ideally we don't need to support such case, but need to go over it again
  # before actually remove these test cases.
  # TODO(b/128616081): get rid of this test suite.

  def testGoogleApis_NoVersion_NoResource(self):
    domain = 'googleapis.com'
    api_name = 'ml'
    url = 'https://{0}.{1}/'.format(api_name, domain)
    self.assertEqual((api_name, None, ''),
                     resource_util.SplitDefaultEndpointUrl(url))

  def testGoogleApis_Malformed(self):
    url = 'https://bliggity-blah'
    _, v, p = resource_util.SplitDefaultEndpointUrl(url)
    self.assertEqual(v, None)
    self.assertEqual(p, '')

  def testGoogleApis_K8sStyleMalformed(self):
    domain = 'googleapis.com'
    api_name = 'run'
    url = 'https://{api}.{domain}/apis/blah blah blah'.format(
        domain=domain, api=api_name)
    _, v, p = resource_util.SplitDefaultEndpointUrl(url)
    self.assertEqual(v, None)
    self.assertEqual(p, '')


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
    self.assertEqual(
        'projects/{project}/instances/{instance}/'
        'backupRuns/{backupConfiguration}/dueTime/{dueTime}',
        collection_info.GetPath(''))


class IsApiVersionTests(test_case.Base, parameterized.TestCase):

  @parameterized.parameters('v1alpha', 'v1beta2', 'v2', 'v1', 'alpha', 'beta',
                            'v2beta3', 'v1p1beta1')
  def testProductionApis(self, api_version):
    self.assertTrue(resource_util.IsApiVersion(api_version))

  @parameterized.parameters('staging_v1', 'staging_alpha', 'staging_beta')
  def testStagingApis(self, api_version):
    self.assertTrue(resource_util.IsApiVersion(api_version))
