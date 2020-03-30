# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
# Lint as: python3
"""Tests for google3.third_party.py.tests.unit.command_lib.container.hub.api_util."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from apitools.base.py import exceptions as api_exceptions
from apitools.base.py.testing import mock as apimock
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.command_lib.container.hub import api_util
from googlecloudsdk.core import exceptions
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case

import mock

# Commonly used exceptions in tests
_http_404_exception = api_exceptions.HttpNotFoundError({'status': 404}, '', '')
_http_500_exception = api_exceptions.HttpError({'status': 500}, '', '')


class SubstringValidator(object):
  """Validates that a string contains another string as a substring."""

  def __init__(self, substring):
    self.substring = substring

  def __eq__(self, other):
    return self.substring in other


class GKEClusterSelfLinkTest(sdk_test_base.SdkBase, parameterized.TestCase):

  def SetUp(self):
    self.mock_old_kubernetes_client = self.StartPatch(
        'googlecloudsdk.command_lib.container.hub.kube_util.OldKubernetesClient'
    )()

    self.mock_kubernetes_client = self.StartPatch(
        'googlecloudsdk.command_lib.container.hub.kube_util.KubernetesClient')()

    compute_api = 'compute'
    compute_api_version = core_apis.ResolveVersion(compute_api)
    self.compute_messages = core_apis.GetMessagesModule(compute_api,
                                                        compute_api_version)
    self.mock_compute_client = apimock.Client(
        client_class=core_apis.GetClientClass(compute_api, compute_api_version))
    self.mock_compute_client.Mock()
    self.addCleanup(self.mock_compute_client.Unmock)
    self.StartPatch(
        'googlecloudsdk.command_lib.container.hub.api_util._ComputeClient'
    ).return_value = self.mock_compute_client

  # TODO(b/145953996): Remove this method once
  # gcloud.container.memberships.* has been ported
  def testNoInstanceIDOld(self):
    self.mock_old_kubernetes_client.GetResourceField.return_value = (None, None)
    self.assertIsNone(
        api_util.GKEClusterSelfLink(self.mock_old_kubernetes_client))

    self.mock_old_kubernetes_client.GetResourceField.assert_has_calls([
        mock.call(
            mock.ANY, mock.ANY,
            SubstringValidator('container\\.googleapis\\.com/instance_id')),
    ])

    self.assertEqual(
        self.mock_old_kubernetes_client.GetResourceField.call_count, 1)

  def testErrorGettingInstanceID(self):
    self.mock_old_kubernetes_client.GetResourceField.return_value = (None,
                                                                     'error')
    api_util.GKEClusterSelfLink(self.mock_old_kubernetes_client)

  def testNoProviderID(self):
    self.mock_old_kubernetes_client.GetResourceField.side_effect = [
        ('instance_id', None),
        (None, None),
    ]

    self_link = None
    with self.assertRaisesRegex(exceptions.Error, 'provider ID'):
      self_link = api_util.GKEClusterSelfLink(self.mock_old_kubernetes_client)
    self.assertIsNone(self_link)

    self.mock_old_kubernetes_client.GetResourceField.assert_has_calls([
        mock.call(
            mock.ANY, mock.ANY,
            SubstringValidator(
                'annotations.container\\.googleapis\\.com/instance_id')),
        mock.call(mock.ANY, mock.ANY, SubstringValidator('spec.providerID')),
    ])

    self.assertEqual(
        self.mock_old_kubernetes_client.GetResourceField.call_count, 2)

  def testErrorGettingProviderID(self):
    self.mock_old_kubernetes_client.GetResourceField.side_effect = [
        ('instance_id', None),
        (None, 'error'),
    ]
    with self.assertRaisesRegex(exceptions.Error, 'provider ID'):
      api_util.GKEClusterSelfLink(self.mock_old_kubernetes_client)

  @parameterized.parameters(
      'invalid',
      'gce:///bad',
      'gce://project',
      'gce://project/',
      'gce://project/location',
      'gce://project/location/',
  )
  def testErrorsParsingProviderID(self, provider_id):
    self.mock_old_kubernetes_client.GetResourceField.side_effect = [
        ('instance_id', None),
        (provider_id, None),
    ]
    with self.assertRaisesRegex(exceptions.Error, 'parsing.*provider ID'):
      api_util.GKEClusterSelfLink(self.mock_old_kubernetes_client)

  def testInstanceWithoutMetadataFromComputeAPIRequest(self):
    self.mock_old_kubernetes_client.GetResourceField.side_effect = [
        ('instance_id', None),
        ('gce://project-id/vm_zone/vm-name', None),
    ]

    self.mock_compute_client.instances.Get.Expect(
        request=self.compute_messages.ComputeInstancesGetRequest(
            instance='instance_id', zone='vm_zone', project='project-id'),
        response=self.compute_messages.Instance())

    with self.assertRaisesRegex(exceptions.Error, 'empty metadata'):
      api_util.GKEClusterSelfLink(self.mock_old_kubernetes_client)

  def testInstanceWithoutClusterNameFromComputeAPIRequest(self):
    self.mock_old_kubernetes_client.GetResourceField.side_effect = [
        ('instance_id', None),
        ('gce://project-id/vm_zone/instance_id', None),
    ]

    item = self.compute_messages.Metadata.ItemsValueListEntry

    self.mock_compute_client.instances.Get.Expect(
        request=self.compute_messages.ComputeInstancesGetRequest(
            instance='instance_id', zone='vm_zone', project='project-id'),
        response=self.compute_messages.Instance(
            metadata=self.compute_messages.Metadata(
                items=[item(key='foo', value='bar')])))

    with self.assertRaisesRegex(exceptions.Error, 'cluster name'):
      api_util.GKEClusterSelfLink(self.mock_old_kubernetes_client)

  def testInstanceWithoutClusterLocationFromComputeAPIRequest(self):
    self.mock_old_kubernetes_client.GetResourceField.side_effect = [
        ('instance_id', None),
        ('gce://project-id/vm_zone/instance_id', None),
    ]

    item = self.compute_messages.Metadata.ItemsValueListEntry

    self.mock_compute_client.instances.Get.Expect(
        request=self.compute_messages.ComputeInstancesGetRequest(
            instance='instance_id', zone='vm_zone', project='project-id'),
        response=self.compute_messages.Instance(
            metadata=self.compute_messages.Metadata(items=[
                item(key='foo', value='bar'),
                item(key='cluster-name', value='cluster'),
            ])))

    with self.assertRaisesRegex(exceptions.Error, 'cluster location'):
      api_util.GKEClusterSelfLink(self.mock_old_kubernetes_client)

  def testGetSelfLink(self):
    self.mock_old_kubernetes_client.GetResourceField.side_effect = [
        ('instance_id', None),
        ('gce://project-id/vm_zone/instance_id', None),
    ]

    item = self.compute_messages.Metadata.ItemsValueListEntry

    self.mock_compute_client.instances.Get.Expect(
        request=self.compute_messages.ComputeInstancesGetRequest(
            instance='instance_id', zone='vm_zone', project='project-id'),
        response=self.compute_messages.Instance(
            metadata=self.compute_messages.Metadata(items=[
                item(key='foo', value='bar'),
                item(key='cluster-name', value='cluster'),
                item(key='cluster-location', value='location'),
            ])))

    self.assertEqual(
        api_util.GKEClusterSelfLink(self.mock_old_kubernetes_client),
        '//container.googleapis.com/projects/project-id/locations/location/clusters/cluster'
    )

  # TODO(b/145953996): Remove this method once
  # gcloud.container.memberships.* has been ported
  def testComputeAPIErrorOld(self):
    self.mock_kubernetes_client.GetResourceField.side_effect = [
        ('instance_id', None),
        ('gce://project_id/vm_zone/instance_id', None),
    ]

    self.mock_compute_client.instances.Get.Expect(
        request=self.compute_messages.ComputeInstancesGetRequest(
            instance='instance_id', zone='vm_zone', project='project_id'),
        exception=api_exceptions.HttpError({'status': 404}, '', ''))

    self_link = None
    with self.assertRaises(api_exceptions.HttpError):
      self_link = api_util.GKEClusterSelfLink(self.mock_kubernetes_client)
    self.assertIsNone(self_link)


class ParseBucketIssuerURLTest(sdk_test_base.SdkBase, parameterized.TestCase):

  @parameterized.parameters(
      # Empty
      '',
      # Bogus
      'invalid',
      # No https
      'http://storage.googleapis.com/gke-issuer-0',
      # Not storage.googleapis.com
      'https://iss.example.com/gke-issuer-0',
      # Empty path component
      'https://storage.googleapis.com/',
      # Too many path segments
      'https://storage.googleapis.com/gke-issuer-0/bar',
      # Only gke-issuer- prefix
      'https://storage.googleapis.com/gke-issuer-',
      # Not gke-issuer- prefix
      'https://storage.googleapis.com/gke-0',
  )
  def testErrors(self, issuer_url):
    with self.assertRaisesRegex(exceptions.Error,
                                'invalid bucket-based issuer URL: '
                                '{}'.format(issuer_url)):
      api_util._ParseBucketIssuerURL(issuer_url)

  @parameterized.parameters(
      ('https://storage.googleapis.com/gke-issuer-0', 'gke-issuer-0'),
      ('https://storage.googleapis.com/gke-issuer-0/', 'gke-issuer-0'),
  )
  def testOk(self, issuer_url, expect):
    name = api_util._ParseBucketIssuerURL(issuer_url)
    self.assertEqual(name, expect)


class WorkloadIdentityBucketTest(sdk_test_base.SdkBase, parameterized.TestCase):

  def SetUp(self):
    storage_api = 'storage'
    storage_api_version = 'v1'
    self.storage_messages = core_apis.GetMessagesModule(storage_api,
                                                        storage_api_version)
    self.mock_storage_client = apimock.Client(
        client_class=core_apis.GetClientClass(storage_api, storage_api_version))
    self.mock_storage_client.Mock()
    self.addCleanup(self.mock_storage_client.Unmock)
    self.StartPatch(
        'googlecloudsdk.command_lib.container.hub.api_util._StorageClient'
    ).return_value = self.mock_storage_client

  def testCreateBucketNotExists(self):
    m = self.storage_messages
    bucket_name = 'gke-issuer-0'
    project = 'project'

    self.mock_storage_client.buckets.Insert.Expect(
        request=m.StorageBucketsInsertRequest(
            bucket=m.Bucket(
                iamConfiguration=m.Bucket.IamConfigurationValue(
                    uniformBucketLevelAccess=m.Bucket.IamConfigurationValue
                    .UniformBucketLevelAccessValue(enabled=True)),
                name=bucket_name),
            project=project),
        response=m.Bucket(name=bucket_name))

    api_util._CreateBucketIfNotExists(self.mock_storage_client,
                                      bucket_name, project)

  def testCreateBucketExists(self):
    m = self.storage_messages
    bucket_name = 'gke-issuer-0'
    project = 'project'

    self.mock_storage_client.buckets.Insert.Expect(
        request=m.StorageBucketsInsertRequest(
            bucket=m.Bucket(
                iamConfiguration=m.Bucket.IamConfigurationValue(
                    uniformBucketLevelAccess=m.Bucket.IamConfigurationValue
                    .UniformBucketLevelAccessValue(enabled=True)),
                name=bucket_name),
            project=project),
        exception=api_exceptions.HttpConflictError({'status': 409}, '', ''))
    self.mock_storage_client.buckets.Get.Expect(
        request=m.StorageBucketsGetRequest(bucket=bucket_name),
        response=m.Bucket(name=bucket_name))

    api_util._CreateBucketIfNotExists(self.mock_storage_client,
                                      bucket_name, project)

  def testCreateBucketException(self):
    m = self.storage_messages
    bucket_name = 'gke-issuer-0'
    project = 'project'

    self.mock_storage_client.buckets.Insert.Expect(
        request=m.StorageBucketsInsertRequest(
            bucket=m.Bucket(
                iamConfiguration=m.Bucket.IamConfigurationValue(
                    uniformBucketLevelAccess=m.Bucket.IamConfigurationValue
                    .UniformBucketLevelAccessValue(enabled=True)),
                name=bucket_name),
            project=project),
        exception=_http_500_exception)

    with self.assertRaisesRegex(exceptions.Error,
                                'Unable to create bucket '
                                '{}'.format(bucket_name)):
      api_util._CreateBucketIfNotExists(self.mock_storage_client,
                                        bucket_name, project)

  @parameterized.parameters(
      ([],),
      ([('foo', 'roles/bar')],),
  )
  def testSetPublicBucket(self, bindings):
    m = self.storage_messages
    bucket_name = 'gke-issuer-0'
    policy_bindings = [m.Policy.BindingsValueListEntry(
        members=[b[0]], role=b[1]) for b in bindings]

    set_policy_bindings = policy_bindings + [m.Policy.BindingsValueListEntry(
        members=['allUsers'], role='roles/storage.objectViewer')]

    self.mock_storage_client.buckets.GetIamPolicy.Expect(
        request=m.StorageBucketsGetIamPolicyRequest(bucket=bucket_name),
        response=m.Policy(bindings=policy_bindings))
    self.mock_storage_client.buckets.SetIamPolicy.Expect(
        request=m.StorageBucketsSetIamPolicyRequest(
            bucket=bucket_name,
            policy=m.Policy(bindings=set_policy_bindings)),
        # response=None without exception can cause real method call
        response=m.Policy())

    api_util._SetPublicBucket(self.mock_storage_client, bucket_name)

  @parameterized.parameters(
      (_http_500_exception, None),
      (None, _http_500_exception),
  )
  def testSetPublicBucketException(self, get_exception, set_exception):
    m = self.storage_messages
    bucket_name = 'gke-issuer-0'

    set_policy_bindings = [m.Policy.BindingsValueListEntry(
        members=['allUsers'], role='roles/storage.objectViewer')]
    get_request = m.StorageBucketsGetIamPolicyRequest(bucket=bucket_name)
    set_request = m.StorageBucketsSetIamPolicyRequest(
        bucket=bucket_name,
        policy=m.Policy(bindings=set_policy_bindings))

    if get_exception:
      self.mock_storage_client.buckets.GetIamPolicy.Expect(
          request=get_request, exception=get_exception)
    else:
      self.mock_storage_client.buckets.GetIamPolicy.Expect(
          request=get_request, response=m.Policy(bindings=[]))

    if not get_exception:
      if set_exception:
        self.mock_storage_client.buckets.SetIamPolicy.Expect(
            request=set_request, exception=set_exception)
      else:
        self.mock_storage_client.buckets.SetIamPolicy.Expect(
            # response=None without exception can cause real method call
            request=set_request, response=m.Policy())

    with self.assertRaisesRegex(exceptions.Error,
                                'Unable to configure {} '
                                'as a public bucket'.format(bucket_name)):
      api_util._SetPublicBucket(self.mock_storage_client, bucket_name)

  def testUploadToBucket(self):
    m = self.storage_messages
    bucket_name = 'gke-issuer-0'
    object_name = 'foo/bar'
    str_data = '{"foo":"bar"}'
    content_type = 'application/json'
    cache_control = 'Cache-Control: public, max-age=3600'

    self.mock_storage_client.objects.Insert.Expect(
        request=m.StorageObjectsInsertRequest(
            bucket=bucket_name, name=object_name,
            object=m.Object(contentType=content_type,
                            cacheControl=cache_control)),
        response=m.Object())

    api_util._UploadToBucket(self.mock_storage_client, bucket_name, object_name,
                             str_data, content_type, cache_control)

  def testUploadToBucketException(self):
    m = self.storage_messages
    bucket_name = 'gke-issuer-0'
    object_name = 'foo/bar'
    str_data = '{"foo":"bar"}'
    content_type = 'application/json'
    cache_control = 'Cache-Control: public, max-age=3600'

    self.mock_storage_client.objects.Insert.Expect(
        request=m.StorageObjectsInsertRequest(
            bucket=bucket_name, name=object_name,
            object=m.Object(contentType=content_type,
                            cacheControl=cache_control)),
        exception=_http_500_exception)

    with self.assertRaisesRegex(exceptions.Error,
                                'Unable to upload object to bucket '
                                '{} at {}'.format(bucket_name, object_name)):
      api_util._UploadToBucket(self.mock_storage_client, bucket_name,
                               object_name, str_data, content_type,
                               cache_control)

  # Test that it deletes objects before attempting to delete bucket
  @parameterized.parameters(
      ([],),
      (['foo/bar', 'foo/baz', 'quux'],),
  )
  def testDeleteBucket(self, objects):
    m = self.storage_messages
    bucket_name = 'gke-issuer-0'

    list_response = m.Objects(items=[m.Object(name=n) for n in objects])
    self.mock_storage_client.objects.List.Expect(
        request=m.StorageObjectsListRequest(bucket=bucket_name),
        response=list_response)

    for o in list_response.items:
      self.mock_storage_client.objects.Delete.Expect(
          request=m.StorageObjectsDeleteRequest(bucket=bucket_name,
                                                object=o.name),
          response=m.StorageObjectsDeleteResponse())

    self.mock_storage_client.buckets.Delete.Expect(
        request=m.StorageBucketsDeleteRequest(bucket=bucket_name),
        response=m.StorageBucketsDeleteResponse())

    api_util._DeleteBucket(self.mock_storage_client, bucket_name)

  @parameterized.parameters(
      (_http_500_exception, None, None),
      (None, _http_500_exception, None),
      (None, None, _http_500_exception),
  )
  def testDeleteBucketException(self, list_e, obj_e, bucket_e):
    # Exceptions from:
    # - list
    # - delete object
    # - delete bucket
    m = self.storage_messages
    bucket_name = 'gke-issuer-0'

    list_response = m.Objects(items=[m.Object(name='foo'),
                                     m.Object(name='bar')])
    if list_e:
      self.mock_storage_client.objects.List.Expect(
          request=m.StorageObjectsListRequest(bucket=bucket_name),
          exception=_http_500_exception)
    else:
      self.mock_storage_client.objects.List.Expect(
          request=m.StorageObjectsListRequest(bucket=bucket_name),
          response=list_response)

    if not list_e:
      if obj_e:
        self.mock_storage_client.objects.Delete.Expect(
            request=m.StorageObjectsDeleteRequest(
                bucket=bucket_name, object=list_response.items[0].name),
            exception=_http_500_exception)
      else:
        for o in list_response.items:
          self.mock_storage_client.objects.Delete.Expect(
              request=m.StorageObjectsDeleteRequest(bucket=bucket_name,
                                                    object=o.name),
              response=m.StorageObjectsDeleteResponse())

    if not list_e and not obj_e:
      if bucket_e:
        self.mock_storage_client.buckets.Delete.Expect(
            request=m.StorageBucketsDeleteRequest(bucket=bucket_name),
            exception=_http_500_exception)
      else:
        self.mock_storage_client.buckets.Delete.Expect(
            request=m.StorageBucketsDeleteRequest(bucket=bucket_name),
            response=m.StorageBucketsDeleteResponse())

    with self.assertRaisesRegex(exceptions.Error,
                                'Unable to delete bucket '
                                '{}'.format(bucket_name)):
      api_util._DeleteBucket(self.mock_storage_client, bucket_name)

  @parameterized.parameters(
      (None, None, None, None),
      ('Oops!', None, None, None),
      (None, 'Oops!', None, None),
      (None, None, 'Oops!', None),
      (None, None, None, 'Oops!'),
  )
  @mock.patch.object(api_util, '_ParseBucketIssuerURL',
                     return_value='gke-issuer-0')
  @mock.patch.object(api_util, '_CreateBucketIfNotExists')
  @mock.patch.object(api_util, '_SetPublicBucket')
  @mock.patch.object(api_util, '_UploadToBucket')
  def testCreateWorkloadIdentityBucket(
      self, upload_e, set_pub_e, create_e, parse_e,
      upload, set_pub, create, parse):
    project = 'project'
    issuer_url = 'https://storage.googleapis.com/gke-issuer-0'
    issuer_name = 'gke-issuer-0'
    config_name = '.well-known/openid-configuration'
    keyset_name = 'openid/v1/jwks'
    cache_control = 'public, max-age=3600'
    config_content_type = 'application/json'
    keyset_content_type = 'application/jwk-set+json'
    openid_config_json = '{"config":"foo"}'
    openid_keyset_json = '{"keyset":"foo"}'

    if parse_e:
      parse.side_effect = Exception(parse_e)
    if create_e:
      create.side_effect = Exception(create_e)
    if set_pub_e:
      set_pub.side_effect = Exception(set_pub_e)
    if upload_e:
      upload.side_effect = Exception(upload_e)

    if parse_e or create_e or set_pub_e or upload_e:
      with self.assertRaisesRegex(
          exceptions.Error,
          'Failed to configure bucket for Workload Identity: Oops!'):
        api_util.CreateWorkloadIdentityBucket(
            project, issuer_url, openid_config_json, openid_keyset_json)
    else:
      api_util.CreateWorkloadIdentityBucket(
          project, issuer_url, openid_config_json, openid_keyset_json)

    parse.assert_called_once_with(issuer_url)
    if parse_e:
      return

    create.assert_called_once_with(
        self.mock_storage_client, issuer_name, project)
    if create_e:
      return

    set_pub.assert_called_once_with(self.mock_storage_client, issuer_name)
    if set_pub_e:
      return

    if upload_e:
      upload.assert_called_once_with(self.mock_storage_client, issuer_name,
                                     config_name, openid_config_json,
                                     config_content_type, cache_control)
    else:
      upload.assert_has_calls(
          [
              mock.call(self.mock_storage_client, issuer_name, config_name,
                        openid_config_json, config_content_type, cache_control),
              mock.call(self.mock_storage_client, issuer_name, keyset_name,
                        openid_keyset_json, keyset_content_type, cache_control)
          ])

  @parameterized.parameters(
      (None, None),
      (Exception('Oops!'), None),
      (_http_404_exception, None),
      (None, Exception('Oops!')),
  )
  @mock.patch.object(api_util, '_ParseBucketIssuerURL',
                     return_value='gke-issuer-0')
  @mock.patch.object(api_util, '_DeleteBucket')
  def testDeleteWorkloadIdentityBucket(
      self, delete_e, parse_e,
      delete, parse):
    issuer_url = 'https://storage.googleapis.com/gke-issuer-0'
    issuer_name = 'gke-issuer-0'

    if parse_e:
      parse.side_effect = parse_e
    if delete_e:
      delete.side_effect = delete_e

    if parse_e or delete_e and \
        not isinstance(delete_e, api_exceptions.HttpNotFoundError):
      with self.assertRaisesRegex(
          exceptions.Error,
          'Failed to delete bucket for Workload Identity: Oops!'):
        api_util.DeleteWorkloadIdentityBucket(issuer_url)
    else:
      api_util.DeleteWorkloadIdentityBucket(issuer_url)

    parse.assert_called_once_with(issuer_url)
    if parse_e:
      return

    delete.assert_called_once_with(self.mock_storage_client, issuer_name)


if __name__ == '__main__':
  test_case.main()

