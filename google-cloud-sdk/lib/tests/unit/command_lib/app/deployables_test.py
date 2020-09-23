# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Tests for deployable services and configs."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.api_lib.app import env as app_env
from googlecloudsdk.api_lib.app import yaml_parsing
from googlecloudsdk.command_lib.app import deployables
from googlecloudsdk.command_lib.app import exceptions
from googlecloudsdk.command_lib.app import staging
from tests.lib import sdk_test_base
from tests.lib import test_case


class AppInfoFake(object):
  """Fake app info for use with ServiceYamlInfo."""

  def __init__(self, filename, service, env=None, runtime='fake-runtime'):
    self.file = filename
    self.module = service
    self.service = service
    self.env = env or app_env.STANDARD
    self.runtime = runtime
    self.vm = False


class ServicesTest(test_case.TestCase):
  """Tests for deployables.Service and deployables.Services."""

  def SetUp(self):
    self.descriptor = 'app.yaml'
    self.parsed = AppInfoFake('staged/app.yaml', 'my-service')
    self.source = 'my-source'
    self.upload_dir = 'staged'
    self.info = yaml_parsing.ServiceYamlInfo('app.yaml', self.parsed)

    self.parsed2 = AppInfoFake('staged/s2.yaml', 'other-service')
    self.info2 = yaml_parsing.ServiceYamlInfo('s2.yaml', self.parsed2)

    self.s1 = deployables.Service(self.descriptor, self.source, self.info,
                                  self.upload_dir)
    self.s2 = deployables.Service(self.descriptor, self.source, self.info2,
                                  self.upload_dir)

  def testServiceConstructor(self):
    """Just check that the service has the right properties after creation."""
    self.assertEqual(self.s1.descriptor, self.descriptor)
    self.assertEqual(self.s1.source, self.source)
    self.assertEqual(self.s1.service_info, self.info)
    self.assertEqual(self.s1.upload_dir, self.upload_dir)

    self.assertEqual(self.s1.path, 'app.yaml')
    self.assertEqual(self.s1.service_id, 'my-service')

  def testMultipleServices(self):
    services = deployables.Services()
    services.Add(self.s1)
    services.Add(self.s2)
    s_all = services.GetAll()
    s_ids = [s.service_id for s in s_all]
    self.assertEqual(s_ids, ['my-service', 'other-service'])

  def testMultipleServicesConstructor(self):
    services = deployables.Services([self.s1, self.s2])
    s_all = services.GetAll()
    s_ids = [s.service_id for s in s_all]
    self.assertEqual(s_ids, ['my-service', 'other-service'])

  def testDuplicateServices(self):
    services = deployables.Services()
    services.Add(self.s1)
    with self.assertRaises(exceptions.DuplicateServiceError):
      services.Add(self.s1)


class ConfigsTest(test_case.TestCase):
  """Tests for deployables.Configs."""

  def SetUp(self):
    self.cron = yaml_parsing.ConfigYamlInfo('cron.yaml', 'cron', 'mock-parsed')
    self.dos = yaml_parsing.ConfigYamlInfo('dos.yaml', 'dos', 'mock-parsed')

  def testMultipleConfigs(self):
    configs = deployables.Configs()
    configs.Add(self.cron)
    configs.Add(self.dos)
    c_all = configs.GetAll()
    c_names = [c.name for c in c_all]
    self.assertEqual(c_names, ['cron', 'dos'])

  def testDuplicateConfigs(self):
    configs = deployables.Configs()
    configs.Add(self.cron)
    with self.assertRaises(exceptions.DuplicateConfigError):
      configs.Add(self.cron)


class TestGetDeployables(sdk_test_base.WithTempCWD,
                         test_case.WithOutputCapture):
  """Test detection and precedence of deployable detection."""

  def SetUp(self):
    self.cron = yaml_parsing.ConfigYamlInfo('cron.yaml', 'cron', 'mock-parsed')
    self.appinfo1 = AppInfoFake('app.yaml', 'my-service')
    self.stager = staging.GetNoopStager('staging-area')
    self.service_yaml_mock = self.StartPatch(
        'googlecloudsdk.api_lib.app.yaml_parsing.ServiceYamlInfo.FromFile')
    self.config_yaml_mock = self.StartPatch(
        'googlecloudsdk.api_lib.app.yaml_parsing.ConfigYamlInfo.FromFile')
    self.cwd_path = os.path.realpath(self.cwd_path)

  def testAppYaml(self):
    """Simple app.yaml passed as deployable."""
    self.service_yaml_mock.return_value = self.appinfo1
    self.config_yaml_mock.return_value = None
    self.Touch(self.cwd_path, name='app.yaml', contents='unused')
    services, configs = deployables.GetDeployables(
        ['app.yaml'], self.stager, deployables.GetPathMatchers())
    self.assertEqual(len(services), 1)
    s = services[0]
    self.assertEqual(s.descriptor, os.path.join(self.cwd_path, 'app.yaml'))
    self.assertEqual(s.service_id, 'my-service')
    self.assertEqual(s.upload_dir, self.cwd_path)
    self.assertEqual(configs, [])

  def testDirWithAppYaml(self):
    """Directory with app.yaml passed as deployable."""
    self.service_yaml_mock.return_value = self.appinfo1
    self.config_yaml_mock.return_value = None
    self.Touch(self.cwd_path, name='app.yaml', contents='unused')
    services, configs = deployables.GetDeployables(
        ['.'], self.stager, deployables.GetPathMatchers())
    self.assertEqual(len(services), 1)
    s = services[0]
    self.assertEqual(s.descriptor, os.path.join(self.cwd_path, 'app.yaml'))
    self.assertEqual(s.service_id, 'my-service')
    self.assertEqual(s.upload_dir, self.cwd_path)
    self.assertEqual(configs, [])

  def testDirWithAppYamlEmptyArgs(self):
    """Directory with nothing passed as deployable."""
    self.service_yaml_mock.return_value = self.appinfo1
    self.config_yaml_mock.return_value = None
    self.Touch(self.cwd_path, name='app.yaml', contents='unused')
    services, configs = deployables.GetDeployables(
        [], self.stager, deployables.GetPathMatchers())
    self.assertEqual(len(services), 1)
    s = services[0]
    self.assertEqual(s.descriptor, os.path.join(self.cwd_path, 'app.yaml'))
    self.assertEqual(s.service_id, 'my-service')
    self.assertEqual(s.upload_dir, self.cwd_path)
    self.assertEqual(configs, [])

  def testCronYaml(self):
    """cron.yaml passed as deployable."""
    self.config_yaml_mock.return_value = self.cron
    self.Touch(self.cwd_path, name='cron.yaml', contents='unused')
    services, configs = deployables.GetDeployables(
        ['cron.yaml'], self.stager, deployables.GetPathMatchers())
    self.assertEqual(services, [])
    self.assertEqual(len(configs), 1)
    c = configs[0]
    self.assertEqual(c.name, 'cron')

  def testDirWithOtherYaml(self):
    """Directory with other.yaml inside, should error."""
    self.config_yaml_mock.return_value = None
    self.Touch(self.cwd_path, name='other.yaml', contents='unused')
    with self.assertRaises(exceptions.UnknownSourceError):
      deployables.GetDeployables(
          ['.'], self.stager, deployables.GetPathMatchers())

  def testOtherYaml(self):
    """Simple other.yaml passed as deployable."""
    self.service_yaml_mock.return_value = self.appinfo1
    self.config_yaml_mock.return_value = None
    self.Touch(self.cwd_path, name='other.yaml', contents='unused')
    services, configs = deployables.GetDeployables(
        ['other.yaml'], self.stager, deployables.GetPathMatchers())
    self.assertEqual(len(services), 1)
    s = services[0]
    self.assertEqual(s.descriptor, os.path.join(self.cwd_path, 'other.yaml'))
    self.assertEqual(s.service_id, 'my-service')
    self.assertEqual(s.upload_dir, self.cwd_path)
    self.assertEqual(configs, [])

  def testCronYamlAndAppDir(self):
    """Directory with app.yaml passed as deployable."""
    self.service_yaml_mock.return_value = self.appinfo1
    self.config_yaml_mock.side_effect = [None, self.cron]
    self.Touch(self.cwd_path, name='app.yaml', contents='unused')
    self.Touch(self.cwd_path, name='cron.yaml', contents='unused')
    services, configs = deployables.GetDeployables(
        ['.', 'cron.yaml'], self.stager, deployables.GetPathMatchers())
    self.assertEqual(len(services), 1)
    s = services[0]
    self.assertEqual(s.descriptor, os.path.join(self.cwd_path, 'app.yaml'))
    self.assertEqual(s.service_id, 'my-service')
    self.assertEqual(s.upload_dir, self.cwd_path)
    self.assertEqual(len(configs), 1)
    c = configs[0]
    self.assertEqual(c.name, 'cron')

  def testDuplicateServices(self):
    """Duplicate services passed as deployable."""
    self.service_yaml_mock.return_value = self.appinfo1  # returned twice
    self.config_yaml_mock.return_value = None
    self.Touch(self.cwd_path, name='app.yaml', contents='unused')
    self.Touch(self.cwd_path, name='other.yaml', contents='unused')
    with self.assertRaises(exceptions.DuplicateServiceError):
      deployables.GetDeployables(['app.yaml', 'other.yaml'], self.stager,
                                 deployables.GetPathMatchers())

  def testDuplicateConfigs(self):
    """Two cron.yaml files passed as deployables."""
    self.config_yaml_mock.return_value = self.cron
    self.Touch(self.cwd_path, name='cron.yaml', contents='unused')
    self.Touch(os.path.join(self.cwd_path, 'sub'),
               name='cron.yaml', contents='unused', makedirs=True)
    with self.assertRaises(exceptions.DuplicateConfigError):
      deployables.GetDeployables(['cron.yaml', 'sub/cron.yaml'], self.stager,
                                 deployables.GetPathMatchers())

  def testAppengineWebXmlDir(self):
    """Directory with WEB_INF/appengine-web.xml passed as deployable."""
    self.service_yaml_mock.return_value = self.appinfo1  # synthesized app.yaml
    self.config_yaml_mock.return_value = None
    self.StartObjectPatch(staging.Stager, 'Stage', return_value='stage-dir')
    self.Touch(os.path.join(self.cwd_path, 'WEB-INF'), makedirs=True,
               name='appengine-web.xml', contents='unused')
    services, configs = deployables.GetDeployables(
        ['.'], self.stager, deployables.GetPathMatchers())
    self.assertEqual(len(services), 1)
    s = services[0]
    self.assertEqual(s.descriptor, os.path.join(self.cwd_path, 'WEB-INF',
                                                'appengine-web.xml'))
    self.assertEqual(s.service_id, 'my-service')
    self.assertEqual(s.upload_dir, 'stage-dir')
    self.assertEqual(configs, [])

  def testAppengineWebXml(self):
    """WEB_INF/appengine-web.xml passed as deployable."""
    self.service_yaml_mock.return_value = self.appinfo1  # synthesized app.yaml
    self.config_yaml_mock.return_value = None
    self.StartObjectPatch(staging.Stager, 'Stage', return_value='stage-dir')
    self.Touch(os.path.join(self.cwd_path, 'WEB-INF'), makedirs=True,
               name='appengine-web.xml', contents='unused')
    services, configs = deployables.GetDeployables(
        [os.path.join('WEB-INF', 'appengine-web.xml')],
        self.stager, deployables.GetPathMatchers())
    self.assertEqual(len(services), 1)
    s = services[0]
    self.assertEqual(s.descriptor, os.path.join(self.cwd_path, 'WEB-INF',
                                                'appengine-web.xml'))
    self.assertEqual(s.service_id, 'my-service')
    self.assertEqual(s.upload_dir, 'stage-dir')
    self.assertEqual(configs, [])

  def testAppengineWebXmlWithVersion(self):
    """WEB_INF/appengine-web.xml passed as deployable."""
    self.service_yaml_mock.return_value = self.appinfo1  # synthesized app.yaml
    self.config_yaml_mock.return_value = None
    self.StartObjectPatch(staging.Stager, 'Stage', return_value='stage-dir')
    self.Touch(
        os.path.join(self.cwd_path, 'WEB-INF'),
        makedirs=True,
        name='appengine-web.xml',
        contents='<version>test</version>')
    services, configs = deployables.GetDeployables(
        [os.path.join('WEB-INF', 'appengine-web.xml')], self.stager,
        deployables.GetPathMatchers())
    self.assertEqual(len(services), 1)
    s = services[0]
    self.assertEqual(
        s.descriptor, os.path.join(self.cwd_path, 'WEB-INF',
                                   'appengine-web.xml'))
    self.assertEqual(s.service_id, 'my-service')
    self.assertEqual(s.upload_dir, 'stage-dir')
    self.assertEqual(configs, [])

    self.AssertErrContains('WARNING: <application> and <version> elements in ' +
                           '`appengine-web.xml` are not respected')

  def testDirWithAppYamlAndAppengineWebXml(self):
    """Directory with both app.yaml and WEB-INF/appengine-web.xml.

    Here, we check that app.yaml takes precedence.
    """
    self.service_yaml_mock.return_value = self.appinfo1
    self.config_yaml_mock.return_value = None
    java_match_mock = self.StartObjectPatch(deployables, 'AppengineWebMatcher')
    self.Touch(self.cwd_path, name='app.yaml', contents='unused')
    self.Touch(os.path.join(self.cwd_path, 'WEB-INF'), makedirs=True,
               name='appengine-web.xml', contents='unused')
    services, configs = deployables.GetDeployables(
        ['.'], self.stager, deployables.GetPathMatchers())
    self.assertEqual(len(services), 1)
    s = services[0]
    self.assertEqual(s.descriptor, os.path.join(self.cwd_path, 'app.yaml'))
    self.assertEqual(s.service_id, 'my-service')
    self.assertEqual(s.upload_dir, self.cwd_path)
    self.assertEqual(configs, [])
    java_match_mock.assert_not_called()

  def testAppengineWebXmlNoStaging(self):
    """WEB_INF/appengine-web.xml passed but staging not defined.

    If staging is not defined for `java-xml`, ensure that we don't recognize
    the java descriptor at all. This is used for rolling out in beta.
    """
    self.service_yaml_mock.return_value = self.appinfo1  # synthesized app.yaml
    self.config_yaml_mock.return_value = None
    self.StartObjectPatch(staging.Stager, 'Stage', return_value=None)
    self.Touch(os.path.join(self.cwd_path, 'WEB-INF'), makedirs=True,
               name='appengine-web.xml', contents='unused')
    with self.assertRaises(exceptions.UnknownSourceError):
      deployables.GetDeployables(
          [os.path.join('WEB-INF', 'appengine-web.xml')],
          self.stager, deployables.GetPathMatchers())

  def testUnidentifiedDir(self):
    """An empty directory is supplied which should trigger fingerprint logic."""
    self.config_yaml_mock.return_value = None
    service = deployables.Service('/path/to/app.yaml', '/path/to/app.yaml',
                                  self.appinfo1, '/path/to')
    m = self.StartObjectPatch(deployables, 'UnidentifiedDirMatcher',
                              autospec=True, return_value=service)
    services, _ = deployables.GetDeployables(['.'], self.stager,
                                             deployables.GetPathMatchers())
    m.assert_called_once()
    self.assertEqual(len(services), 1)
    self.assertEqual(services[0].descriptor, '/path/to/app.yaml')

  @test_case.Filters.DoNotRunOnWindows("Windows doesn't support symlinks")
  def testLinkedAppYaml(self):
    """Symlinked app.yaml."""
    self.service_yaml_mock.return_value = self.appinfo1
    self.config_yaml_mock.return_value = None
    self.Touch(self.cwd_path, name='link_target', contents='unused')
    os.symlink(os.path.join(self.cwd_path, 'link_target'),
               os.path.join(self.cwd_path, 'app.yaml'))
    services, configs = deployables.GetDeployables(
        ['app.yaml'], self.stager, deployables.GetPathMatchers())
    self.assertEqual(len(services), 1)
    s = services[0]
    self.assertEqual(s.descriptor, os.path.join(self.cwd_path, 'app.yaml'))
    self.assertEqual(s.service_id, 'my-service')
    self.assertEqual(s.upload_dir, self.cwd_path)
    self.assertEqual(configs, [])

if __name__ == '__main__':
  test_case.main()
