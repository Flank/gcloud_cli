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
"""Tests for google3.third_party.py.tests.e2e.core.proxy.

See go/cloud-sdk-proxy-testing for more information.

Proxy instances running
---------
sudo docker run -dit --restart unless-stopped -p 8080:8080
  mosajjal/pproxy:latest -l http://:8080 -vv;
sudo docker run -dit --restart unless-stopped -p 8081:8081
  mosajjal/pproxy:latest -l http://:8081#user:pass -vv;

sudo docker run -dit --restart unless-stopped -p 8082:8082
  mosajjal/pproxy:latest -l socks4://:8082 -vv;

sudo docker run -dit --restart unless-stopped -p 8083:8083
  mosajjal/pproxy:latest -l socks5://:8083 -vv;
sudo docker run -dit --restart unless-stopped -p 8084:8084
  mosajjal/pproxy:latest -l socks5://:8084#user:pass -vv;
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties

from tests.lib import e2e_base
from tests.lib import exec_utils
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case

PROXY_HOST = '10.128.0.8'


def MakeProxyParams(protocol, proxy_port, with_pass=False):
  params = {
      'protocol': protocol,
      'host': PROXY_HOST,
      'port': proxy_port,
  }
  if with_pass:
    params['user'] = 'user'
    params['password'] = 'pass'

  return params


@test_case.Filters.RunOnlyWithEnv('RUN_PROXY_TESTS',
                                  ('Only run in cloudsdk/periodic/'
                                   '[windows_proxy.bat|ubuntu_proxy.sh]'))
class ProxyTest(sdk_test_base.BundledBase, e2e_base.WithServiceAuth,
                parameterized.TestCase):

  def setProxyViaProps(self, proxy_params):
    properties.VALUES.proxy.proxy_type.Set(proxy_params['protocol'])
    properties.VALUES.proxy.address.Set(proxy_params['host'])
    properties.VALUES.proxy.port.Set(proxy_params['port'])
    if 'user' in proxy_params:
      properties.VALUES.proxy.username.Set(proxy_params['user'])
    if 'password' in proxy_params:
      properties.VALUES.proxy.password.Set(proxy_params['password'])

  def setProxyViaEnv(self, proxy_params):
    proxy_type = proxy_params['protocol']
    proxy_address = proxy_params['host']
    proxy_port = proxy_params['port']
    proxy_rdns = True
    proxy_user = proxy_params.get('user')
    proxy_pass = proxy_params.get('password')

    if proxy_type == 'socks4':
      proxy_scheme = 'socks4a' if proxy_rdns else 'socks4'
    elif proxy_type == 'socks5':
      proxy_scheme = 'socks5h' if proxy_rdns else 'socks5'
    elif proxy_type == 'http':
      proxy_scheme = 'https'

    proxy_auth = ''
    if proxy_user or proxy_pass:
      proxy_auth = ':'.join(x or '' for x in (proxy_user, proxy_pass))
      proxy_auth += '@'
    else:
      proxy_auth = ''

    proxy = '{}://{}{}:{}'.format(proxy_scheme, proxy_auth, proxy_address,
                                  proxy_port)

    self.StartEnvPatch({'HTTPS_PROXY': proxy})

  def testNoProxyDoesNotConnect(self):
    self.Run('compute instances list --limit=1')
    with self.assertRaises(exec_utils.ExecutionError) as cm:
      results = self.ExecuteScript(
          'gcloud',
          ['compute', 'instances', 'list', '--limit', '1'])
      # The above should have thrown, if it did not, print the result so we can
      # see what happened.
      print(results)
    self.assertIn(
        'This may be due to network connectivity issues',
        cm.exception.result.stderr, msg='no network connection issue')

  @parameterized.parameters([
      # http no password
      (MakeProxyParams('http', 8080, with_pass=False), True),
      (MakeProxyParams('http', 8080, with_pass=False), False),
      (MakeProxyParams('http', 8081, with_pass=True), True),
      (MakeProxyParams('http', 8081, with_pass=True), False),
      (MakeProxyParams('socks4', 8082, with_pass=False), True),
      (MakeProxyParams('socks4', 8082, with_pass=False), False),

      (MakeProxyParams('socks5', 8083, with_pass=False), True),
      (MakeProxyParams('socks5', 8083, with_pass=False), False),

      (MakeProxyParams('socks5', 8084, with_pass=True), True),
      (MakeProxyParams('socks5', 8084, with_pass=True), False),
  ])
  def testProxyConnects(self, proxy_params, set_using_props):
    if set_using_props:
      self.setProxyViaProps(proxy_params)
    else:
      self.setProxyViaEnv(proxy_params)

    results = self.ExecuteScript(
        'gcloud',
        ['compute', 'instances', 'list', '--limit', '1'])
    self.assertEqual(0, results.return_code)


if __name__ == '__main__':
  test_case.main()
