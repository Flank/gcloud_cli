# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Unit tests for anthos file_parsers module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import copy

from googlecloudsdk.command_lib.anthos.common import file_parsers
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files
from tests.lib import parameterized
from tests.lib import sdk_test_base


V1_TEST_DATA = collections.OrderedDict({
    'apiVersion':
        'authentication.gke.io/v1alpha1',
    'kind':
        'ClientConfig',
    'metadata': {
        'creationTimestamp': '100001'
    },
    'spec':
        collections.OrderedDict({
            'certificateAuthorityData':
                'ABCD12345abcde',
            'name':
                'mycluster',
            'oidcConfig':
                collections.OrderedDict({
                    'certificateAuthorityData': 'msakdfjshsdjkfh123==',
                    'clientID': 'kubernetes',
                    'clientSecret': 'ULTRA_SECRET',
                    'cloudConsoleRedirectURI': '',
                    'extraParams': 'resource=CustomeKubernetesClaim',
                    'issuerURI': 'https://test.example-gcp.com/adfs',
                    'kubectlRedirectURI': 'http://127.0.0.1:6630/callback',
                    'scopes': 'allatclaim'
                }),
            'server':
                'https://127.0.0.1:443',
            'type':
                'oidc',
            'useHTTPProxy':
                'false'
        }),
    'status': {}
})

V2_TEST_DATA = collections.OrderedDict([
    ('apiVersion', 'authentication.gke.io/v2alpha1'), ('kind', 'ClientConfig'),
    ('metadata',
     collections.OrderedDict([
         ('annotations',
          collections.OrderedDict([('controller-gen.kubebuilder.io/version',
                                    'v0.2.4')])), ('creationTimestamp', None),
         ('name', 'clientconfig-sample'), ('namespace', 'default')
     ])),
    ('spec',
     collections.OrderedDict([
         ('authentication', [
             collections.OrderedDict([
                 ('name', 'basic'),
                 ('basic', collections.OrderedDict([('enabled', True)]))
             ]),
             collections.OrderedDict([
                 ('name', 'oidc1'),
                 ('oidc',
                  collections.OrderedDict([
                      ('clientID', 'clientconfigtest'),
                      ('extraParams',
                       'resource=k8s-group-claim,domain_hint=consumers'),
                      ('certificateAuthorityData', 'jsdhfsjdhf298347298374=='),
                      ('issuerURI', 'https://adfs.contoso.com/adfs'),
                      ('kubectlRedirectURI', 'http://redirect.kubectl.com/'),
                      ('cloudConsoleRedirectURI',
                       'http://redirect.console.cloud.google.com/'),
                      ('scopes', 'allatclaim,group'), ('userClaim', 'sub'),
                      ('groupsClaim', 'groups'),
                      ('deployCloudConsoleProxy', True)
                  ]))
             ]),
             collections.OrderedDict([
                 ('name', 'oidc2'),
                 ('proxy', 'https://user:password@127.0.0.1:8888'),
                 ('oidc',
                  collections.OrderedDict([
                      ('certificateAuthorityData', 'jsdhfsjdhf298347298374=='),
                      ('clientID', 'kubernetes'),
                      ('clientSecret', 'B27QBQU9Ghg92XCAsykC'),
                      ('cloudConsoleRedirectURI',
                       'http://console.cloud.google.com/kubernetes/oidc'),
                      ('extraParams', 'resource=CustomeKubernetesClaim'),
                      ('issuerURI', 'https://ad-fs1.example-gcp.com/adfs'),
                      ('kubectlRedirectURI', 'http://127.0.0.1:6630/callback'),
                      ('scopes', 'allatclaim'), ('userClaim', 'sub'),
                      ('groupsClaim', 'groups')
                  ]))
             ]),
             collections.OrderedDict([
                 ('name', 'ldap1'),
                 ('ldap',
                  collections.OrderedDict([
                      ('host', '192.168.0.2:389'),
                      ('connectionType', 'insecure'),
                      ('user',
                       collections.OrderedDict([
                           ('baseDN', 'CN=User,OU=People,DC=example,DC=com')
                       ]))
                  ]))
             ]),
             collections.OrderedDict([
                 ('name', 'ldap2'),
                 ('ldap',
                  collections.OrderedDict([
                      ('host', 'ldap.example.com'),
                      ('connectionType', 'startTLS'),
                      ('user',
                       collections.OrderedDict([
                           ('baseDN', 'CN=User,OU=People,DC=example,DC=com'),
                           ('userAttribute', 'UID'),
                           ('memberAttribute', 'memberOf')
                       ])),
                      ('certificateAuthorityData',
                       'LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tDQpNSUlEZnpDQ0FtZWdBd0lCQWdJUVlqRTByVHBCRDVwR1ZVeUM4MTc1eVRBTkJna3Foa2lHOXcwQkFRc0ZBREJTDQpNUk13RVFZS0NaSW1pWlB5TEdRQkdSWURZMjl0TVJzd0dRWUtDWkltaVpQeUxHUUJHUllMWlhoaGJYQnNaUzFuDQpZM0F4SGpBY0JnTlZCQU1URldWNFlXMXdiR1V0WjJOd0xVRkVMVVpUTVMxRFFUQWVGdzB4T1RBeE1qWXdNakEzDQpNemxhRncweU5EQXhNall3TWpFM016bGFNRkl4RXpBUkJnb0praWFKay9Jc1pBRVpGZ05qYjIweEd6QVpCZ29KDQpraWFKay9Jc1pBRVpGZ3RsZUdGdGNHeGxMV2RqY0RFZU1Cd0dBMVVFQXhNVlpYaGhiWEJzWlMxblkzQXRRVVF0DQpSbE14TFVOQk1JSUJJakFOQmdrcWhraUc5dzBCQVFFRkFBT0NBUThBTUlJQkNnS0NBUUVBcWQrT0JiSUpiRWYxDQpNZnUyNU9nMjl3dGJUZVZDZEtnMzJPajh6cGs0TGdmMVZLQ215ZjJnZTFaTW5FQnN3dlNlckYrSUtqQ1hJUTVxDQpVTncvTGVIaC9MQmxVYUp2S3NkcktrQ0l6K0dMdjNYWXJXRzMyUXQwa0JlKy9mcDBaT1pkWFhqU1pGbDRxN0NCDQpxZE1RckpSQm9Reng1QlpQeGQ1WkwwTUp4SWtFc2RGWUphSktGUXg2L2pNcTRBd3puTEZMQmtWeDc1b2ZDWk5oDQpobHU5dS9FSlV5dW1ydWVYeXJnM2ZOUVhpZzRRY3FIWUc3Y2RGU092eEdtZnNEa29uZkRqZXUvTmg4eDAvYzNBDQpIM1ByYTJmcFJTU3M1dkpmWWp2VHlpeHBldlVSMnVjc0Z5ak1ydUF2YS9OMG93aURNM29Pb2UzclNQTjF0eFZFDQpxSG0rVHpYRHFRSURBUUFCbzFFd1R6QUxCZ05WSFE4RUJBTUNBWVl3RHdZRFZSMFRBUUgvQkFVd0F3RUIvekFkDQpCZ05WSFE0RUZnUVVaekJGRG5DMUlmTlVCZHl5OHVEaEF2cjNVcmt3RUFZSkt3WUJCQUdDTnhVQkJBTUNBUUF3DQpEUVlKS29aSWh2Y05BUUVMQlFBRGdnRUJBQWFHSlFzTEsxWGs1RXNxdWlQSW5HY0hSRGFJaFo2VSt3QkM3TUg0DQp2UGZ3RGJhSGxQMVBuQlR3UXhBQUNvbzRhTlArdWVlTW05MktGWWFyUUZRMytDbHN1ZHdjbEZMeFFXeGJuWXZiDQpaejdvQ28yeXNqbUN3a01VVHNtMW1xM1lVMXE4cStndVFjNk8xTU54TVcvZHZBUHJjQjV2V1VRUE84OVorMkpUDQpGN2JqUVpOV2lkTkpZY25zQjA4eUVhS0xXRmFhV0NzOWk0THJBTkR6NWVRMmtSSGhhQ2JiQ2FXYkV4VnI2RW85DQo2TFhndkh2YkFzUjhham80ejZWMEhxYmYzNDJKU05GdFhDSHl1MjBMOS94a3dRcy9iakZBa3lrVWZZR2oyZ25xDQp4WEJmcXQ2Q0V4cC9Fckh6R1hyTHcvV1Nldy9TQjBBT25UaCtkSHJWdW9oNVV6bz0NCi0tLS0tRU5EIENFUlRJRklDQVRFLS0tLS0NCg=='
                      )
                  ]))
             ])
         ]),
         ('certificateAuthorityData',
          'TFMwdExTMUNSVWRKVGlCRFJWSlVTVVpKUTBGVVJTMHRMUzB0Q2sxSlNVUjRSRU5EUVhGNVowRjNTVUpCWjBsVlluQk9jVFJZYlVjME5YSnZjbU5NYUN0ME9WRldlWGhEUmxCUmQwUlJXVXBMYjFwSmFIWmpUa0ZSUlV3S1FsRkJkMkZFUlV4TlFXdEhRVEZWUlVKb1RVTldWazE0UkhwQlRrSm5UbFpDUVdkVVFtczVlVnBYWkhaaWFrVlNUVUU0UjBFeFZVVkNlRTFKVlVjNWVRcGtSM2hvWW0xUmVFVjZRVkpDWjA1V1FrRnZWRU5yZERGWmJWWjVZbTFXTUZwWVRYaERla0ZLUW1kT1ZrSkJjMVJCYTA1Q1RWSk5kMFZSV1VSV1VWRkVDa1YzY0V4a1YwcHNZMjAxYkdSSFZucE5RalJZUkZSRk5VMUVSWHBOVkVVelRVUkZkMDFHYjFoRVZFa3dUVVJGZWsxRVJUTk5SRVYzVFVadmQyRkVSVXdLVFVGclIwRXhWVVZDYUUxRFZsWk5lRVI2UVU1Q1owNVdRa0ZuVkVKck9YbGFWMlIyWW1wRlVrMUJPRWRCTVZWRlFuaE5TVlZIT1hsa1IzaG9ZbTFSZUFwRmVrRlNRbWRPVmtKQmIxUkRhM1F4V1cxV2VXSnRWakJhV0UxNFEzcEJTa0puVGxaQ1FYTlVRV3RPUWsxU1RYZEZVVmxFVmxGUlJFVjNjRXhrVjBwc0NtTnROV3hrUjFaNlRVbEpRa2xxUVU1Q1oydHhhR3RwUnpsM01FSkJVVVZHUVVGUFEwRlJPRUZOU1VsQ1EyZExRMEZSUlVFNE1uaEdUU3RxYUhkcGFGY0tWRXhrVDNwUldVMDVUeXRzT1dOc2NVVllWakZNYzNGdFExQlRiREZ0VlU1MU0zVkZlbXRpVFhGdGNXZEtSVE16T0ZsUE0xRkpVVE50VVZCdFEyUlBSUXBsZVc0clpHTmxWVk14WlV0SlpHMTZabGxFYTJSS2JrNXRXR1phZDFOc2NUZzBlSFpyT1dGU1VERkVkbTVxTWpocVEzVlZhakI1TTNCdlZUaHJhVVEzQ2xjeU1GZHZSbVJSVjJocWVqSlRSMDVKVEhWSlJtMHlLek5DU2tsWWNDdHFjelp6VG5ScVZuTTBObTEwUVVoMlVrazFORmg2V1dsdWIyMUJkRVZYV0dNS2NtUnpNVk12WkZWdE9HZEdaaTlUVXpCaFRrcG9kVTh6T1dGTlZqSjBWVkp4ZVZkNU9Fb3daRmMwWlN0dmN6VlFSa3RESzI5Q1lVVkpVRkYxTjBSeVNncGljazR2YVZwT1ZYRjJaRmswY21rNFdrRnFMMU5RUlU0NGRuaHJUVmRoZW5CeWRrdFFOV1pHVDFoMGFsUlRMMHhUV2poVWIxWklVSFphWkZWcGRIWTVDazFwWkhsNGQzQXZjWGRKUkVGUlFVSnZNbGwzV2tSQlQwSm5UbFpJVVRoQ1FXWTRSVUpCVFVOQlVWbDNSV2RaUkZaU01GUkJVVWd2UWtGbmQwSm5SVUlLTDNkSlFrRnFRV1JDWjA1V1NGRTBSVVpuVVZWT00xQnRMelV2ZWxkUU5UWXdabGRSU2xkRWJDOUtTbVY0Y2xWM1NIZFpSRlpTTUdwQ1FtZDNSbTlCVlFwT00xQnRMelV2ZWxkUU5UWXdabGRSU2xkRWJDOUtTbVY0Y2xWM1JGRlpTa3R2V2tsb2RtTk9RVkZGVEVKUlFVUm5aMFZDUVU1eFprUkVaR2gxU25sVkNrUlNkMEkxTW5WRlRtdElSSGhvVDB4c1FUZGxiWHBoVEVSVlZYWlRVbFJDVFdrM2VsUkNZVGRKVVc1b1ZHOTZha0pqWkZBeVdWVjJZbHBvTWtGT09FY0tOMUlyTlRkTU9VSkVTRzlIU2tJemEySXpaMmRvU214QmNuQTNSbTlqY3pOQmMyNUtlR2MyVURnMFRYRkpVV0ZLVTAwek4yOW1UbkZIT1ZSbVdHRnJRUW8wU2t4RFMzTnZRVEpIZEhad1NVUndjV3hpUVRod1NXYzFjakl2TUVoNmJFaDFWVGRVZG5VME9EVlFXVFF4UTBRclVXSnlObUZhT1U1RFRtUmxPR3hzQ2lzdlVHb3ZZV3A0V2l0RVMzTXhjSEpQZFdsb1dFcG9NbGRaSzA1NWQyOUNXVFI1T1hOdlpGbFFVWEIzZFRKbVduUjJMMUozZDFKUVVIb3dTU3Q1TnpZS2RXNDVTMU5ETmxKR05pdE5NbkZ5VDBwTlQyOUVRVmt2V0RBNVFYTkJiMDVZYURaS1JVTmphbkowWkZsdFRrbE9Va2hwUldoc1JqQnRWbFJrY1ZSc1NRcFJNRTVUZWk5Q1dEQk1ZejBLTFMwdExTMUZUa1FnUTBWU1ZFbEdTVU5CVkVVdExTMHRMUW89'
         ), ('name', 'testcluster'), ('server', 'https://192.168.0.1:6443'),
         ('preferredAuthentication', 'oidc1')
     ]))
])


class YamlConfigObjectTest(sdk_test_base.SdkBase, parameterized.TestCase):
  """Test for YamlConfigObject class."""

  def SetUp(self):
    self.config_object = file_parsers.YamlConfigObject(
        copy.deepcopy(V1_TEST_DATA))

  @parameterized.named_parameters(
      ('Top_Level_Value', 'apiVersion', 'authentication.gke.io/v1alpha1'),
      ('Nested_Value', 'metadata.creationTimestamp', '100001'),
      ('Nested_Object', 'spec.oidcConfig', V1_TEST_DATA['spec']['oidcConfig']),
      ('Nested_Object_Value', 'spec.oidcConfig.clientID', 'kubernetes'),
  )
  def testGet(self, path_to_fetch, expected):
    result = self.config_object[path_to_fetch]
    if not expected:
      self.assertIsNone(result)
    self.assertEqual(expected, result)

  @parameterized.named_parameters(
      ('Not_Found', 'spec.fooBar'),
      ('Too_Deep', 'metadata.creationTimestamp.foo'),
      ('MissingPath', None)
  )
  def testGet_Errors(self, path_to_fetch):
    with self.assertRaises(KeyError):
      _ = self.config_object[path_to_fetch]

  @parameterized.named_parameters(
      ('Top_Level_Value', 'apiVersion', 'version10'),
      ('Nested_Value', 'metadata.creationTimestamp', '4'),
      ('Nested_Object', 'spec.oidcConfig', {
          'name': 'inserted'
      }),
      ('Nested_Object_Value', 'spec.oidcConfig.clientID', 'gke'),
      ('New_Key', 'foo.Bar.NewKey', 'New Value'),
  )
  def testSet(self, path, new_value):
    self.config_object[path] = new_value
    self.assertEqual(self.config_object[path], new_value)

  @parameterized.named_parameters(
      ('Top_Level_Value', 'apiVersion'),
      ('Nested_Value', 'metadata.creationTimestamp'),
      ('Nested_Object', 'spec.oidcConfig'),
      ('Nested_Object_Value', 'spec.oidcConfig.clientID'),
  )
  def testDelete(self, path):
    self.assertIsNotNone(self.config_object[path])
    del self.config_object[path]
    with self.assertRaises(KeyError):
      _ = self.config_object[path]

  @parameterized.named_parameters(
      ('Missing', ''),
      ('Undefined', None),
      ('Not_Found', 'metadata.creationTimestamp.foo'),
  )
  def testDeleteErrors(self, path):
    with self.assertRaises(KeyError):
      del self.config_object[path]

  def testIter(self):
    for key in self.config_object:
      self.assertIn(key, V1_TEST_DATA)

  def testLen(self):
    self.assertEqual(len(self.config_object), 5)

  @parameterized.parameters(
      'apiVersion', 'kind', 'metadata', 'spec', 'status'
  )
  def testContains(self, key):
    self.assertIn(key, self.config_object)

  def testContainsFails(self):
    self.assertNotIn('MadeUp.Key', self.config_object)

  def testStr(self):
    expected = yaml.dump(V1_TEST_DATA, round_trip=True)
    actual = str(self.config_object)
    self.assertEqual(expected, actual)


class LoginConfigObjectTest(sdk_test_base.SdkBase, parameterized.TestCase):
  """LoginConfigObject Tests."""

  def SetUp(self):
    self.login_config = file_parsers.LoginConfigObject(
        copy.deepcopy(V2_TEST_DATA))
    self.login_config_v1 = file_parsers.LoginConfigObject(
        copy.deepcopy(V1_TEST_DATA))

  def testVersion(self):
    self.assertEqual(self.login_config.version,
                     'authentication.gke.io/v2alpha1')

  def testGetPreferredAuth(self):
    self.assertEqual(self.login_config.GetPreferredAuth(), 'oidc1')
    with self.assertRaises(file_parsers.YamlConfigObjectFieldError):
      self.login_config_v1.GetPreferredAuth()

  def testSetPreferredAuth(self):
    self.login_config.SetPreferredAuth('mynewauth')
    self.assertEqual(self.login_config.GetPreferredAuth(), 'mynewauth')

  def testSetPreferredAuthFails(self):
    with self.assertRaises(file_parsers.YamlConfigObjectFieldError):
      self.login_config_v1.SetPreferredAuth('bad_config_version')

  def testGetAuthProviders(self):
    # Test provider objects
    auth_objs = self.login_config.GetAuthProviders(name_only=False)
    self.assertEqual(len(auth_objs), 5)
    self.assertTrue(all((yaml.dict_like(i) for i in auth_objs)))

    # Test Provider Strings
    self.assertEqual(self.login_config.GetAuthProviders(),
                     ['basic', 'oidc1', 'oidc2', 'ldap1', 'ldap2'])

    # Test Providers fail for V1
    self.assertIsNone(self.login_config_v1.GetAuthProviders())
    del self.login_config[file_parsers.LoginConfigObject.AUTH_PROVIDERS_KEY]

    # Test Providers fail if not found
    self.assertIsNone(self.login_config.GetAuthProviders())

  def testIsLdap(self):
    # Test V2
    self.assertFalse(self.login_config.IsLdap())
    self.login_config.SetPreferredAuth('ldap1')
    self.assertTrue(self.login_config.IsLdap())
    # Test V2 not found
    self.login_config.SetPreferredAuth('mynewauth')
    self.assertFalse(self.login_config.IsLdap())

    # Test V1
    self.assertFalse(self.login_config_v1.IsLdap())


class YamlConfigFileTest(sdk_test_base.SdkBase, parameterized.TestCase):
  """YAMLConfigFile tests."""

  def SetUp(self):
    self.test_file_dir = self.Resource('tests', 'unit', 'command_lib', 'anthos',
                                       'testdata')
    self.config_path = self.Resource(self.test_file_dir,
                                     'auth-config-multiple-v2alpha1.yaml')
    self.config_contents = files.ReadFileContents(self.config_path)

    self.config_path_2 = self.Resource(self.test_file_dir,
                                       'auth-config-v2alpha1.yaml')
    self.config_contents_2 = files.ReadFileContents(self.config_path_2)

  def testFindMatchingItem(self):
    config_file = file_parsers.YamlConfigFile(
        item_type=file_parsers.LoginConfigObject,
        file_path=self.config_path)
    found_config = config_file.FindMatchingItem(
        file_parsers.LoginConfigObject.CLUSTER_NAME_KEY, 'testcluster-2')[0]
    self.assertEqual(found_config.GetPreferredAuth(), 'ldap2')

  def testFindMatchingItemData(self):
    config_file = file_parsers.YamlConfigFile(
        item_type=file_parsers.LoginConfigObject,
        file_path=self.config_path)
    found_clusters = config_file.FindMatchingItemData(
        file_parsers.LoginConfigObject.CLUSTER_NAME_KEY)
    self.assertCountEqual(found_clusters,
                          ['testcluster-1', 'testcluster-2', 'testcluster-3'])

  def testSetMatchingItem(self):
    config_file = file_parsers.YamlConfigFile(
        item_type=file_parsers.LoginConfigObject,
        file_path=self.config_path)
    config_file.SetMatchingItemData(
        file_parsers.LoginConfigObject.CLUSTER_NAME_KEY, 'testcluster-2',
        file_parsers.LoginConfigObject.CLUSTER_NAME_KEY, 'updated_cluster',
        persist=False)
    self.assertIsNotNone(config_file.FindMatchingItem(
        file_parsers.LoginConfigObject.CLUSTER_NAME_KEY, 'updated_cluster'))

  def testSetMatchingItemWithPersist(self):
    # copy config to a temp directory
    config_file = file_parsers.YamlConfigFile(
        item_type=file_parsers.LoginConfigObject,
        file_path=self.config_path)
    temp_config_path = self.Touch(self.temp_path, name='temp_config.yaml',
                                  contents=config_file.yaml)
    new_config_file = file_parsers.YamlConfigFile(
        item_type=file_parsers.LoginConfigObject, file_path=temp_config_path)
    # mutate copied config and confirm temp file is changed on disk
    new_config_file.SetMatchingItemData(
        file_parsers.LoginConfigObject.CLUSTER_NAME_KEY, 'testcluster-2',
        file_parsers.LoginConfigObject.CLUSTER_NAME_KEY, 'updated_cluster')
    self.AssertFileContains('updated_cluster', temp_config_path)

  def testPathNotFound(self):
    # No file_contents provided.
    with self.assertRaises(file_parsers.YamlConfigFileError):
      file_parsers.YamlConfigFile(item_type=file_parsers.YamlConfigObject,
                                  file_path='NOT_FOUND')

  def testEq(self):
    config_file = file_parsers.YamlConfigFile(
        item_type=file_parsers.LoginConfigObject,
        file_path=self.config_path)
    config_file_2 = file_parsers.YamlConfigFile(
        item_type=file_parsers.LoginConfigObject,
        file_path=self.config_path_2)
    config_file3 = file_parsers.YamlConfigFile(
        item_type=file_parsers.LoginConfigObject,
        file_path=self.config_path)
    self.assertNotEqual(config_file, config_file_2)
    self.assertEqual(config_file, config_file3)

  def testItemType(self):
    config_file = file_parsers.YamlConfigFile(
        item_type=file_parsers.LoginConfigObject,
        file_path=self.config_path)
    self.assertEqual(config_file.item_type, file_parsers.LoginConfigObject)

  # No source file nor contents provided should throw exception.
  def testNoContentsNorFileProvided(self):
    with self.assertRaises(file_parsers.YamlConfigFileError):
      file_parsers.YamlConfigFile(item_type=file_parsers.LoginConfigObject)

  # Providing URL with no file_contents should throw exception.
  def testURLWithNoContents(self):
    with self.assertRaises(file_parsers.YamlConfigFileError):
      file_parsers.YamlConfigFile(item_type=file_parsers.LoginConfigObject,
                                  file_path='http://www.example.com')

  # Trying to write to disk with no file path specified should throw exception.
  def testWriteToDiskNoFilePath(self):
    with self.assertRaises(file_parsers.YamlConfigFileError):
      login_config = file_parsers.YamlConfigFile(
          item_type=file_parsers.LoginConfigObject,
          file_contents=self.config_contents)
      login_config.WriteToDisk()

  # Test equality in loading from file_path and from file_contents.
  def testEqLoadFromContents(self):
    # Read from file 1.
    config_file = file_parsers.YamlConfigFile(
        item_type=file_parsers.LoginConfigObject,
        file_path=self.config_path)
    # Read from file 2.
    config_file_2 = file_parsers.YamlConfigFile(
        item_type=file_parsers.LoginConfigObject,
        file_path=self.config_path_2)
    # Load from pre-read contents of file 1.
    config_file3 = file_parsers.YamlConfigFile(
        item_type=file_parsers.LoginConfigObject,
        file_contents=self.config_contents)
    self.assertNotEqual(config_file3, config_file_2)
    self.assertEqual(config_file3, config_file)

  # Test file_contents property is stored.
  def testFileContentsProperty(self):
    # Read from file 1.
    config_file = file_parsers.YamlConfigFile(
        item_type=file_parsers.LoginConfigObject,
        file_contents=self.config_contents,
        file_path=self.config_path)
    self.assertEqual(self.config_contents, config_file.file_contents)


if __name__ == '__main__':
  sdk_test_base.main().main()
