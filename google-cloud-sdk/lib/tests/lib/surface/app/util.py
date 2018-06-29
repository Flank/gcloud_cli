# Copyright 2014 Google Inc. All Rights Reserved.
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

"""Module that just holds some test yaml data."""

from __future__ import absolute_import
from __future__ import unicode_literals
import cgi
import json
import os
import StringIO
import traceback
import urllib
import urllib2

from googlecloudsdk.api_lib.app import appengine_client
from googlecloudsdk.api_lib.app import util
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib.surface.app import api_test_util
from googlecloudsdk.third_party.appengine.tools import appengine_rpc_test_util


class WithFakeRPC(sdk_test_base.SdkBase):
  """Basic tests of the argument wiring between gcloud app and appcfg."""

  def SetUp(self):
    appengine_client.RpcServerClass = self.NewRpcServer
    self.responses = []
    self.strict = True
    self.rpcserver = None

  def NewRpcServer(self, server, *unused_args, **unused_kw):
    try:
      if self.rpcserver:
        return self.rpcserver
      self.rpcserver = appengine_rpc_test_util.TestRpcServer(
          server, lambda: ('testuser', 'testpass'),
          util.GetUserAgent(), util.GetSourceName())
    except Exception as e:
      traceback.print_exc()
      raise e
    self.rpcserver.set_strict(strict=self.strict)
    for (expected_url, handler) in self.responses:
      self.rpcserver.opener.AddResponse(expected_url, handler)
    return self.rpcserver

  def AddResponse(self, expected_url, expected_params=None, expected_body='',
                  response_code=200, response_body=''):
    """Adds a fake response for 'expected_url' to the TestRpcServer."""

    if expected_params is None:
      expected_params = {}

    def Handle(request):
      url = request.get_full_url()
      log.debug('Handling url: ' + url)
      query_string = ''
      if '?' in url:
        query_string = url.split('?', 1)[1]
      self.assertEqual(expected_params, cgi.parse_qs(query_string))
      self.assertEqual(expected_body, request.get_data())
      if response_code < 400:
        return appengine_rpc_test_util.TestRpcServer.MockResponse(
            response_body, response_code)
      else:
        raise urllib2.HTTPError('url', response_code, 'msg', {},
                                StringIO.StringIO(response_body))

    self.AddResponseHandler(expected_url, Handle)

  def AddStaticResponse(self, expected_url, body=''):
    f = lambda x: appengine_rpc_test_util.TestRpcServer.MockResponse(body)
    self.AddResponseHandler(expected_url, f)

  def AddResponseHandler(self, expected_url, func):
    self.responses.append((expected_url, func))

  def _MakeURL(self, url, params=None):
    if params:
      url += '?' + urllib.urlencode(sorted(params.items()))
    return url

  def _WasRequested(self, url):
    if not self.rpcserver:
      # Nothing was requested at all.
      return False
    for (request, _) in self.rpcserver.opener.requests:
      if url == request:
        return True
    return False

  def AssertRequested(self, url, params=None, requested=True, times=1):
    if not requested:
      return self.AssertNotRequested(url, params)
    url = self._MakeURL(url, params)
    if not self._WasRequested(url):
      all_requests = '\n\t'.join([str(req)
                                  for req in self.rpcserver.opener.requests])
      self.fail('URL [{0}] was never requested.\nAll requests:\n\t{1}'
                .format(url, all_requests))
    matching = [req for (req, _) in self.rpcserver.opener.requests
                if req == url]
    if len(matching) != times:
      self.fail('URL [{url}] was requested the wrong number of times.  '
                'Expected: [{expected}], Actual: [{actual}]'.format(
                    url=url, expected=times, actual=len(matching)))

  def AssertNotRequested(self, url, params=None):
    url = self._MakeURL(url, params)
    if self._WasRequested(url):
      self.fail('URL [{0}] was unexpectedly requested.'.format(url))


class WithAppData(sdk_test_base.WithOutputCapture):
  """A base class that lets you write common .yaml files for testing."""

  CRON_DATA = ('cron.yaml', """\
cron:
- description: test dispatch vs target
  url: /tasks/hello_module2
  schedule: every 1 mins
  target: module1
""")

  DISPATCH_DATA = ('dispatch.yaml', """\
dispatch:
- url: '*/tasks/hello_module2'
  service: module2
""")

  DOS_DATA = ('dos.yaml', """\
blacklist:
- subnet: 1.2.3.4
  description: a single IP address
""")

  INDEX_DATA = ('index.yaml', """\
indexes:
- kind: Cat
  ancestor: no
  properties:
  - name: name
  - name: age
    direction: desc
""")

  QUEUE_DATA = ('queue.yaml', """\
total_storage_limit: 120M
queue:
- name: foo
  rate: 35/s
""")

  APP_DATA = """\
api_version: 1
threadsafe: true

handlers:
- url: /
  script: home.app
"""
# pylint: disable=anomalous-backslash-in-string
  SKIP_FILES_DATA = """\
skip_files:
- ^.*\.zip$
"""
# pylint: enable=anomalous-backslash-in-string

  APP_DATA_VM_TRUE = """\
threadsafe: true
vm: true

handlers:
- url: /
  script: home.app
- url: /static
  static_dir: foo
"""

  APP_DATA_ENV_FLEX = """\
env: flex
threadsafe: true

handlers:
- url: /
  script: home.app
- url: /static
  static_dir: foo
"""

  APP_DATA_ENV2_RUNTIME = """\
threadsafe: true
env: 2
handlers:
- url: /
  script: home.app
"""

  APP_DATA_JAVA = """\
<?xml version="1.0" encoding="utf-8"?>
<appengine-web-app xmlns="http://appengine.google.com/ns/1.0">
  <module>{module}</module>
  <threadsafe>true</threadsafe>
  <staging>
    <enable-jar-classes>false</enable-jar-classes>
  <staging>
</appengine-web-app>
"""

  # Generated app.yaml from staging
  APP_DATA_JAVA_YAML = """\
runtime: java7
threadsafe: true
handlers:
- url: /
  script: home.app
"""

  APP_DATA_JAVA_VM = """\
<?xml version="1.0" encoding="utf-8"?>
<appengine-web-app xmlns="http://appengine.google.com/ns/1.0">
  <module>{module}</module>
  <threadsafe>true</threadsafe>
  <vm>true</vm>
</appengine-web-app>
"""

  APP_DATA_JAVA_WITH_VERSION = """\
<?xml version="1.0" encoding="utf-8"?>
<appengine-web-app xmlns="http://appengine.google.com/ns/1.0">
  <module>{module}</module>
  <version>2</version>
  <threadsafe>true</threadsafe>
</appengine-web-app>
"""

  WEB_XML_DATA = """\
<?xml version="1.0" encoding="utf-8"?>
<web-app xmlns="http://java.sun.com/xml/ns/javaee" version="2.5">
  <display-name>Hello World</display-name>
  <servlet>
    <servlet-name>hello</servlet-name>
    <servlet-class>org.example.HelloAppEngineServlet</servlet-class>
  </servlet>
  <servlet-mapping>
    <servlet-name>hello</servlet-name>
    <url-pattern>/helloappengine</url-pattern>
  </servlet-mapping>
</web-app>
"""

  # TODO(b/36050947): Remove all project & versions arguments from methods
  def MakeApp(self, project=None):
    self.WriteFile('start.py', '')
    return [
        self.WriteApp('app.yaml', service='default'),
        self.WriteApp('mod1.yaml', service='mod1'),
        self.WriteConfig(WithAppData.CRON_DATA, project),
        self.WriteConfig(WithAppData.DISPATCH_DATA, project),
        self.WriteConfig(WithAppData.DOS_DATA, project),
        self.WriteConfig(WithAppData.INDEX_DATA, project),
        self.WriteConfig(WithAppData.QUEUE_DATA, project),
    ]

  def WriteConfig(self, config, project=None):
    (file_name, data) = config
    if project:
      data = 'application: {0}\n'.format(project) + data
    return self.WriteFile(file_name, data)

  def WriteApp(self, file_name, project=None, version=None, service=None,
               data=None, secure=None, runtime=None, env=None,
               beta_settings=None, module=None, api_version=None):
    if data is None:
      data = self.APP_DATA
    default_runtime = ('python' if env in ['2', 'flex', 'flexible']
                       else 'python27')
    data = 'runtime: {0}\n'.format(runtime or default_runtime) + data
    if module:
      data = 'module: {0}\n'.format(module) + data
    if service:
      data = 'service: {0}\n'.format(service) + data
    if version:
      data = 'version: {0}\n'.format(version) + data
    if project:
      data = 'application: {0}\n'.format(project) + data
    if env is not None:
      data = 'env: {0}\n'.format(env) + data
    if secure is not None:
      data += '  secure: {0}\n'.format(secure)
    # beta_settings is another available configuration key in app.yaml similar
    # to other fields listed above.
    if beta_settings is not None:
      data += 'beta_settings: {0}\n'.format(beta_settings)
    if api_version:
      data += 'api_version: {0}\n'.format(api_version)

    return self.WriteFile(file_name, data)

  def WriteFlexRuntime(self, file_name, runtime, project=None,
                       version=None, module=None):
    return self.WriteApp(file_name, project, version, module,
                         self.APP_DATA_ENV_FLEX, runtime=runtime)

  def WriteVmRuntime(self, file_name, runtime, project=None,
                     version=None, module=None):
    return self.WriteApp(file_name, project, version, module,
                         self.APP_DATA_VM_TRUE, runtime=runtime)

  def WriteEnv2Runtime(self, file_name, runtime, project=None,
                       version=None, module=None):
    return self.WriteApp(file_name, project, version, module,
                         self.APP_DATA_ENV2_RUNTIME, runtime=runtime)

  def WriteJavaApp(self, module='default', directory=None, app_data=None):
    if app_data is None:
      app_data = self.APP_DATA_JAVA
    data = app_data.format(module=module)
    self.WriteFile('WEB-INF/appengine-web.xml', data, directory=directory)
    path = self.WriteFile('WEB-INF/web.xml', self.WEB_XML_DATA,
                          directory=directory)
    return os.path.dirname(os.path.dirname(path))

  def WriteJavaVMApp(self, module='default', directory=None):
    return self.WriteJavaApp(module, directory, self.APP_DATA_JAVA_VM)

  def FullPath(self, file_name, directory=None):
    if not directory:
      directory = self.temp_path
    return os.path.join(directory, file_name)

  def WriteFile(self, file_name, data, directory=None):
    file_path = self.FullPath(file_name, directory=directory)
    files.MakeDir(os.path.dirname(file_path))
    files.WriteFileContents(file_path, data)
    return file_path

  def WriteJSON(self, file_name, json_object):
    file_path = os.path.join(self.temp_path, file_name)
    self.Touch(self.temp_path, file_name, json.dumps(json_object))
    return file_path


class AppTestBase(cli_test_base.CliTestBase,
                  sdk_test_base.WithFakeAuth,
                  WithFakeRPC):
  """Basic tests of the argument wiring between gcloud app and appcfg."""

  PROJECT = 'fakeproject'

  def SetUp(self):
    properties.VALUES.core.project.Set(self.PROJECT)
    # Fake an API client.
    self.appengine_messages = core_apis.GetMessagesModule(
        'appengine',
        api_test_util.APPENGINE_API_VERSION)
