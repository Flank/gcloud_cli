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
"""Integration tests for creating/deleting firewalls."""

import os
import subprocess
import time

from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import e2e_utils
from tests.lib import sdk_test_base
from tests.lib.surface.compute import e2e_test_base


SSL_CONFIG_FILE_CONTENTS = """
#
# SSLeay example configuration file.
#

[ req ]
distinguished_name      = req_distinguished_name
prompt                  = no

[ req_distinguished_name ]
commonName                      = @HostName@

[ v3_req ]
basicConstraints        = CA:FALSE
"""


class HttpsLoadBalancingTestBase(e2e_test_base.BaseTest):

  GSUTIL_BUCKET_PREFIX = 'gs://'

  # Arbitrary base64url encoded 128-bit key.
  # Generated using:
  # base64.urlsafe_b64encode(bytearray(os.urandom(16)))
  SIGNED_URL_KEY1 = 'a8UDvh668LDUIykP3hnznQ=='
  SIGNED_URL_KEY2 = 'SCfA_VWzIi3hzOziLJozkQ=='

  def UniqueName(self, name):
    return e2e_utils.GetResourceNameGenerator(
        prefix='compute-https-lb-test-' + name).next()

  def SetUp(self):
    self.backend_bucket_names_used = []
    self.backend_service_names_used = []
    self.gcs_bucket_names_used = []
    self.https_health_check_names_used = []
    self.https_rule_names_used = []
    self.ssl_cert_names_used = []
    self.ssl_policy_names_used = []
    self.url_map_names_used = []
    self.web_https_proxy_names_used = []
    self.ssl_config_fname = os.path.join(self.CreateTempDir(), 'ssl.cnf')
    self.key_fname = os.path.join(self.CreateTempDir(), 'foo.key')
    self.crt_fname = os.path.join(self.CreateTempDir(), 'foo.crt')

    ssl_config_file = open(self.ssl_config_fname, 'w')
    ssl_config_file.write(SSL_CONFIG_FILE_CONTENTS)
    ssl_config_file.close()

    self.assertEqual(
        subprocess.call(
            ['openssl', 'req', '-x509', '-nodes', '-days', '365',
             '-newkey', 'rsa:2048', '-batch',
             '-subj', '/C=US/CN=Alon',
             '-keyout', self.key_fname,
             '-out', self.crt_fname,
             '-rand', '/dev/zero',  # sounds pretty random
             '-config', self.ssl_config_fname]),
        0)

  @sdk_test_base.Retry(
      why=('gsutil may return a 409 even if bucket creation succeeds'),
      max_retrials=3,
      sleep_ms=300)
  def CreateGcsBucket(self):
    name = self.UniqueName('gcs-bucket')
    storage_api.StorageClient().CreateBucketIfNotExists(name, self.Project())
    self.gcs_bucket_names_used.append(name)
    return name

  def DeleteGcsBucket(self, name):
    bucket_ref = storage_util.BucketReference.FromBucketUrl(
        '{0}{1}/'.format(self.GSUTIL_BUCKET_PREFIX, name))
    storage_api.StorageClient().DeleteBucket(bucket_ref)

  def GetResourceName(self):
    # Make sure the name used is different on each retry, and make sure all
    # names used are cleaned up
    self.backend_bucket_name = self.UniqueName('backend-bucket')
    self.backend_service_name = self.UniqueName('web-service')
    self.https_health_check_name = self.UniqueName('https-health-checks')
    self.https_rule_name = self.UniqueName('https-rule')
    self.ssl_cert_name = self.UniqueName('www-ssl-cert')
    self.ssl_policy_name_1 = self.UniqueName('www-ssl-polcy-1')
    self.ssl_policy_name_2 = self.UniqueName('www-ssl-polcy-2')
    self.url_map_name = self.UniqueName('url-map')
    self.web_https_proxy_name = self.UniqueName('web-https-proxy')
    self.backend_bucket_names_used.append(self.backend_bucket_name)
    self.backend_service_names_used.append(self.backend_service_name)
    self.https_health_check_names_used.append(self.https_health_check_name)
    self.https_rule_names_used.append(self.https_rule_name)
    self.ssl_cert_names_used.append(self.ssl_cert_name)
    self.ssl_policy_names_used.append(self.ssl_policy_name_1)
    self.ssl_policy_names_used.append(self.ssl_policy_name_2)
    self.url_map_names_used.append(self.url_map_name)
    self.web_https_proxy_names_used.append(self.web_https_proxy_name)

  def HttpsLbCreateTests(self):
    self.GetResourceName()
    self.Run('compute ssl-certificates create {0} '
             '--certificate {1} --private-key {2}'.format(
                 self.ssl_cert_name, self.crt_fname, self.key_fname))

    self.Run('compute ssl-policies create {}'.format(self.ssl_policy_name_1))
    self.Run('compute ssl-policies create {}'.format(self.ssl_policy_name_2))

    self.Run('compute https-health-checks create {0}'.format(
        self.https_health_check_name))

    self.Run('compute backend-services create {0} '
             '--global '
             '--protocol HTTPS '
             '--https-health-checks {1}'.format(self.backend_service_name,
                                                self.https_health_check_name))

    gcs_bucket_name = self.CreateGcsBucket()
    self.Run('compute backend-buckets create {0} '
             '--gcs-bucket-name {1} '.format(self.backend_bucket_name,
                                             gcs_bucket_name))

    self.Run('compute url-maps create {0} '
             '--default-service {1}'.format(self.url_map_name,
                                            self.backend_service_name))

    self.Run('compute url-maps add-path-matcher {0} '
             '--default-service {1} '
             '--path-matcher-name bucket-matcher '
             '--backend-bucket-path-rules=/static/*={2}'.format(
                 self.url_map_name,
                 self.backend_service_name,
                 self.backend_bucket_name))

    self.Run('compute target-https-proxies create {0} '
             '--url-map {1}  --ssl-certificates {2} --ssl-policy {3}'.format(
                 self.web_https_proxy_name, self.url_map_name,
                 self.ssl_cert_name, self.ssl_policy_name_1))

    self.Run('compute target-https-proxies update {0} '
             '--ssl-certificates {1}'.format(self.web_https_proxy_name,
                                             self.ssl_cert_name))

    self.Run('compute target-https-proxies update {0} '
             '--url-map {1}'.format(self.web_https_proxy_name,
                                    self.url_map_name))

    self.Run('compute target-https-proxies update {0} '
             '--url-map {1}  --ssl-certificates {2}'.format(
                 self.web_https_proxy_name, self.url_map_name,
                 self.ssl_cert_name))

    # Update the associated SSL policy.
    self.Run('compute target-https-proxies update {} '
             '--ssl-policy {}'.format(self.web_https_proxy_name,
                                      self.ssl_policy_name_2))
    result = self.Run('compute target-https-proxies describe {}'.format(
        self.web_https_proxy_name))
    self.assertTrue(result.sslPolicy.endswith(self.ssl_policy_name_2))

    # Clear the associated SSL policy.
    self.Run('compute target-https-proxies update {} '
             '--clear-ssl-policy'.format(self.web_https_proxy_name))
    result = self.Run('compute target-https-proxies describe {}'.format(
        self.web_https_proxy_name))
    self.assertEqual(None, result.sslPolicy)

    self.Run('compute forwarding-rules create {0} --global '
             '--target-https-proxy {1} '
             '--port-range 443 '.format(self.https_rule_name,
                                        self.web_https_proxy_name))

  def EnableCdnTests(self):
    # Enable CDN for the backend service
    self.Run('compute backend-services update {0} --enable-cdn --global'.format(
        self.backend_service_name))
    result = self.Run('compute backend-services describe {0} --global'.format(
        self.backend_service_name))
    self.assertTrue(result.enableCDN)
    self.Run('compute backend-services update {0} --no-enable-cdn --global'.
             format(self.backend_service_name))
    result = self.Run('compute backend-services describe {0} --global'.format(
        self.backend_service_name))
    self.assertFalse(result.enableCDN)

    # Enable CDN for the backend bucket
    self.Run('compute backend-buckets update {0} --enable-cdn'.format(
        self.backend_bucket_name))
    result = self.Run('compute backend-buckets describe {0}'.format(
        self.backend_bucket_name))
    self.assertTrue(result.enableCdn)
    self.Run('compute backend-buckets update {0} --no-enable-cdn'.
             format(self.backend_bucket_name))
    result = self.Run('compute backend-buckets describe {0}'.format(
        self.backend_bucket_name))
    self.assertFalse(result.enableCdn)

  def CdnSignedUrlTestsBackendServices(self):
    """Tests for CDN Signed URL using backend services."""
    # Create the key files for the test keys.
    signed_url_key_file1 = self.Touch(
        self.temp_path, 'signed-url-key1.key', contents=self.SIGNED_URL_KEY1)
    signed_url_key_file2 = self.Touch(
        self.temp_path, 'signed-url-key2.key', contents=self.SIGNED_URL_KEY2)

    # Add CDN Signed URL keys to the backend service.
    result = self.Run('compute backend-services add-signed-url-key {0} '
                      '--key-name key1 --key-file {1}'.format(
                          self.backend_service_name, signed_url_key_file1))
    self.assertEqual(['key1'], result.cdnPolicy.signedUrlKeyNames)
    result = self.Run('compute backend-services describe {0} '
                      '--global'.format(self.backend_service_name))
    self.assertEqual(['key1'], result.cdnPolicy.signedUrlKeyNames)

    result = self.Run('compute backend-services add-signed-url-key {0} '
                      '--key-name key2 --key-file {1}'.format(
                          self.backend_service_name, signed_url_key_file2))
    self.assertEqual(['key1', 'key2'], result.cdnPolicy.signedUrlKeyNames)
    result = self.Run('compute backend-services describe {0} '
                      '--global'.format(self.backend_service_name))
    self.assertEqual(['key1', 'key2'], result.cdnPolicy.signedUrlKeyNames)

    # Delete CDN Signed URL keys from the backend service.
    result = self.Run('compute backend-services delete-signed-url-key {0} '
                      '--key-name key1'.format(self.backend_service_name))
    self.assertEqual(['key2'], result.cdnPolicy.signedUrlKeyNames)
    result = self.Run('compute backend-services describe {0} '
                      '--global'.format(self.backend_service_name))
    self.assertEqual(['key2'], result.cdnPolicy.signedUrlKeyNames)

    # Update CDN Signed URL Cache Max Age for the backend service.
    result = self.Run('compute backend-services update {0} '
                      '--signed-url-cache-max-age 987654 '
                      '--global'.format(self.backend_service_name))
    self.assertEqual(987654, result[0].cdnPolicy.signedUrlCacheMaxAgeSec)
    result = self.Run('compute backend-services describe {0} --global'.format(
        self.backend_service_name))
    self.assertEqual(987654, result.cdnPolicy.signedUrlCacheMaxAgeSec)

  def CdnSignedUrlTestsBackendBuckets(self):
    """Tests for CDN Signed URL using backend buckets."""
    # Create the key files for the test keys.
    signed_url_key_file1 = self.Touch(
        self.temp_path, 'signed-url-key1.key', contents=self.SIGNED_URL_KEY1)
    signed_url_key_file2 = self.Touch(
        self.temp_path, 'signed-url-key2.key', contents=self.SIGNED_URL_KEY2)

    # Add CDN Signed URL keys to the backend bucket.
    result = self.Run('compute backend-buckets add-signed-url-key {0} '
                      '--key-name key1 --key-file {1}'.format(
                          self.backend_bucket_name, signed_url_key_file1))
    self.assertEqual(['key1'], result.cdnPolicy.signedUrlKeyNames)
    result = self.Run(
        'compute backend-buckets describe {0}'.format(self.backend_bucket_name))
    self.assertEqual(['key1'], result.cdnPolicy.signedUrlKeyNames)

    result = self.Run('compute backend-buckets add-signed-url-key {0} '
                      '--key-name key2 --key-file {1}'.format(
                          self.backend_bucket_name, signed_url_key_file2))
    self.assertEqual(['key1', 'key2'], result.cdnPolicy.signedUrlKeyNames)
    result = self.Run(
        'compute backend-buckets describe {0}'.format(self.backend_bucket_name))
    self.assertEqual(['key1', 'key2'], result.cdnPolicy.signedUrlKeyNames)

    # Delete CDN Signed URL keys from the backend bucket.
    result = self.Run('compute backend-buckets delete-signed-url-key {0} '
                      '--key-name key1'.format(self.backend_bucket_name))
    self.assertEqual(['key2'], result.cdnPolicy.signedUrlKeyNames)
    result = self.Run(
        'compute backend-buckets describe {0}'.format(self.backend_bucket_name))
    self.assertEqual(['key2'], result.cdnPolicy.signedUrlKeyNames)

    # Update CDN Signed URL Cache Max Age for the backend bucket.
    result = self.Run('compute backend-buckets update {0} '
                      '--signed-url-cache-max-age 987654'.format(
                          self.backend_bucket_name))
    self.assertEqual(987654, result[0].cdnPolicy.signedUrlCacheMaxAgeSec)
    result = self.Run('compute backend-buckets describe {0}'.format(
        self.backend_bucket_name))
    self.assertEqual(987654, result.cdnPolicy.signedUrlCacheMaxAgeSec)

  def CacheInvalidationTests(self):
    self.Run('compute url-maps invalidate-cdn-cache {0} --path /a --async'.
             format(self.url_map_name))
    time.sleep(2)  # need invalidations to be at least 1 second apart.
    self.Run(
        'compute url-maps invalidate-cdn-cache {0} --host example.com --path '
        '/b --async'.format(self.url_map_name))
    result = list(
        self.Run('compute url-maps list-cdn-cache-invalidations {0} '
                 '--format=disable'.format(self.url_map_name)))
    self.assertEqual(len(result), 2)
    self.assertEqual(result[0]['description'], 'example.com/b')
    self.assertEqual(result[1]['description'], '/a')
    time.sleep(2)  # need invalidations to be at least 1 second apart.
    self.Run('compute url-maps invalidate-cdn-cache {0} --path /c --async'.
             format(self.url_map_name))
    result = list(
        self.Run('compute url-maps list-cdn-cache-invalidations {0} --limit 2 '
                 '--format=disable'.format(self.url_map_name)))
    self.assertEqual(len(result), 2)
    self.assertEqual(result[0]['description'], '/c')
    self.assertEqual(result[1]['description'], 'example.com/b')

  def HttpsLbDeleteTests(self):
    self.Run('compute forwarding-rules delete {0} --global '.format(
        self.https_rule_name))
    self.Run('compute target-https-proxies delete {0} '.format(
        self.web_https_proxy_name))
    self.Run('compute url-maps delete {0} '.format(self.url_map_name))
    self.Run('compute backend-services delete --global {0}'.format(
        self.backend_service_name))
    self.Run('compute backend-buckets delete {0}'.format(
        self.backend_bucket_name))
    self.Run('compute https-health-checks delete {0}'.format(
        self.https_health_check_name))
    self.Run('compute ssl-certificates delete {0} '.format(self.ssl_cert_name))

  def CustomKeysTests(self):
    """Tests for custom cache keys."""
    result = self.Run('compute backend-services describe --global {0}'.format(
        self.backend_service_name))
    self.assertIsNone(result.cdnPolicy)
    self.Run('compute backend-services update {0} '
             '--global '
             '--no-cache-key-include-protocol'.format(
                 self.backend_service_name))
    result = self.Run('compute backend-services describe --global {0}'.format(
        self.backend_service_name))
    self.assertEqual(False, result.cdnPolicy.cacheKeyPolicy.includeProtocol)

  def TearDown(self):
    for name in self.https_rule_names_used:
      self.CleanUpResource(name, 'forwarding-rules',
                           scope=e2e_test_base.EXPLICIT_GLOBAL)
    for name in self.web_https_proxy_names_used:
      self.CleanUpResource(name, 'target-https-proxies',
                           scope=e2e_test_base.GLOBAL)
    for name in self.url_map_names_used:
      self.CleanUpResource(name, 'url-maps',
                           scope=e2e_test_base.GLOBAL)
    for name in self.backend_service_names_used:
      self.CleanUpResource(name, 'backend-services',
                           scope=e2e_test_base.EXPLICIT_GLOBAL)
    for name in self.https_health_check_names_used:
      self.CleanUpResource(name, 'https-health-checks',
                           scope=e2e_test_base.GLOBAL)
    for name in self.ssl_cert_names_used:
      self.CleanUpResource(name, 'ssl-certificates',
                           scope=e2e_test_base.GLOBAL)
    for name in self.ssl_policy_names_used:
      self.CleanUpResource(name, 'ssl-policies',
                           scope=e2e_test_base.GLOBAL)

    # Delete the GCS Buckets
    self.DeleteResources(self.gcs_bucket_names_used,
                         self.DeleteGcsBucket,
                         'gcs bucket')


class HttpsLoadBalancingTestGA(HttpsLoadBalancingTestBase):

  def testHttpsLb(self):
    """Tests HTTPS LB using GA API."""
    self.HttpsLbCreateTests()
    self.EnableCdnTests()
    self.CacheInvalidationTests()
    self.HttpsLbDeleteTests()


class HttpsLoadBalancingTestAlpha(HttpsLoadBalancingTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    super(HttpsLoadBalancingTestAlpha, self).SetUp()

  def testHttpsLb(self):
    """Tests HTTPS LB using Alpha API."""
    self.HttpsLbCreateTests()
    self.EnableCdnTests()
    self.CustomKeysTests()
    self.CacheInvalidationTests()
    self.CdnSignedUrlTestsBackendServices()
    self.CdnSignedUrlTestsBackendBuckets()
    self.HttpsLbDeleteTests()


class HttpsLoadBalancingTestBeta(HttpsLoadBalancingTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    super(HttpsLoadBalancingTestBeta, self).SetUp()

  def testHttpsLb(self):
    """Tests HTTPS LB using Beta API."""
    self.HttpsLbCreateTests()
    self.EnableCdnTests()
    self.CustomKeysTests()
    self.CacheInvalidationTests()
    self.CdnSignedUrlTestsBackendServices()
    self.CdnSignedUrlTestsBackendBuckets()
    self.HttpsLbDeleteTests()


if __name__ == '__main__':
  e2e_test_base.main()
