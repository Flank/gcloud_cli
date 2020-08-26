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
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import contextlib
import datetime
import json
import os
import signal
import time

from googlecloudsdk.command_lib.code import skaffold_events
from googlecloudsdk.core.util import retry
from tests.lib import cli_test_base
from tests.lib import e2e_base
from tests.lib import sdk_test_base
from tests.lib import test_case
import six
import six.moves.urllib.request


class SkaffoldContext(object):
  """Context of running skaffold."""

  def __init__(self, events_port):
    self._events_port = events_port

  def GetLocalPort(self, service_name):
    """Get the local port of a port-forwarded kubernetes service."""
    with contextlib.closing(
        skaffold_events.OpenEventsStream(self._events_port)) as response:
      return next(skaffold_events.GetServiceLocalPort(response, service_name))


class TerminateWithSigInt(object):
  """Context manager that terminates a process with SIGINT."""

  def __init__(self,
               proc,
               timeout,
               check_interval=datetime.timedelta(seconds=5)):
    self._proc = proc
    self._timeout = timeout
    self._check_interval = check_interval

  def __enter__(self):
    return self

  def __exit__(self, exception_type, exception_value, traceback):
    self._proc.send_signal(signal.SIGINT)

    deadline = datetime.datetime.now() + self._timeout
    while _IsStillRunning(self._proc) and datetime.datetime.now() < deadline:
      time.sleep(self._check_interval.total_seconds())


def _IsStillRunning(proc):
  return proc.poll() is None


class DevOnMinikubeTest(sdk_test_base.BundledBase, cli_test_base.CliTestBase):

  MINIKUBE_PROFILE_PREFIX = 'gcloud-local-dev'

  def SetUp(self):
    self.ShowTestOutput()

    # Bump up the size limit to accomodate the docker image when it is stored
    # in the minikube image cache.
    self._dirs_size_limit_method = 2 << 29

  def TearDown(self):
    # If the minikube cluster was not properly torn down as part of the
    # gcloud local dev command, delete the cluster here.
    result = self.ExecuteLegacyScript('minikube',
                                      ['profile', 'list', '-o', 'json'])
    running_clusters = [
        cluster['Name']
        for cluster in json.loads(six.ensure_text(result.stdout))['valid']
        if cluster['Status'] == 'Running'
    ]
    if self.ClusterName() in running_clusters:
      self.ExecuteLegacyScript('minikube',
                               ['delete', '--purge', '-p',
                                self.ClusterName()])

  def ClusterName(self):
    return self.MINIKUBE_PROFILE_PREFIX + self.id().split('.')[-1]

  def assertIsUp(self, local_port):
    retryer = retry.Retryer()
    self.assertTrue(
        retryer.RetryOnException(self._IsUp, [local_port], sleep_ms=5000))

  @staticmethod
  def _IsUp(port):
    url = 'http://localhost:' + six.text_type(port) + '/'

    with contextlib.closing(six.moves.urllib.request.urlopen(url)) as response:
      return response.getcode() == 200

  def _GetServices(self, context, namespace=None):
    args = ['--context', context]
    if namespace:
      args += ['--namespace', namespace]
    args += ['get', 'services', '-o', 'name']

    result = self.ExecuteLegacyScript('kubectl', args)
    return six.ensure_text(result.stdout).splitlines()

  @contextlib.contextmanager
  def _RunDevelopmentServer(self,
                            service_name,
                            local_port,
                            additional_gcloud_flags=None):
    skaffold_event_port = self.GetPort()

    with e2e_base.RefreshTokenAuth() as auth:
      gcloud_args = [
          'alpha',
          'code',
          'dev',
          '--service-name=' + service_name,
          '--image=fake-image-name',
          '--stop-cluster',
          '--minikube-profile=%s' % self.ClusterName(),
          '--skaffold-events-port=%s' % skaffold_event_port,
          '--account=%s' % auth.Account(),
      ]
      gcloud_args.append('--local-port=%s' % local_port)
      if additional_gcloud_flags:
        gcloud_args += additional_gcloud_flags

      match_strings = ['Service available at http://localhost']

      with self.ExecuteLegacyScriptAsync(
          'gcloud', gcloud_args, match_strings=match_strings,
          timeout=450) as process_context:
        with TerminateWithSigInt(
            process_context.p, timeout=datetime.timedelta(minutes=2)):
          yield SkaffoldContext(skaffold_event_port)

  @test_case.Filters.RunOnlyOnLinux("other platforms don't support minikube")
  def testNamespace(self):
    dockerfile = os.path.relpath(
        self.Resource('tests', 'e2e', 'surface', 'code', 'testdata', 'hello',
                      'Dockerfile'), os.getcwd())

    local_port = self.GetPort()
    gcloud_flags = [
        '--namespace=my-namespace',
        '--dockerfile=%s' % dockerfile,
        '--source=%s' % os.path.dirname(dockerfile),
    ]
    with self._RunDevelopmentServer('myservice', local_port, gcloud_flags):
      self.assertIsUp(local_port)

      kube_context_name = self.ClusterName()
      self.assertIn('service/myservice',
                    self._GetServices(kube_context_name, 'my-namespace'))

  @test_case.Filters.RunOnlyOnLinux("other platforms don't support minikube")
  def testDev(self):
    dockerfile = os.path.relpath(
        self.Resource('tests', 'e2e', 'surface', 'code', 'testdata', 'hello',
                      'Dockerfile'), os.getcwd())
    local_port = self.GetPort()
    gcloud_flags = [
        '--dockerfile=%s' % dockerfile,
        '--source=%s' % os.path.dirname(dockerfile),
    ]
    with self._RunDevelopmentServer('myservice', local_port, gcloud_flags):
      self.assertIsUp(local_port)

  @test_case.Filters.RunOnlyOnLinux("other platforms don't support minikube")
  def testAppengineBuilder(self):
    app_root = os.path.relpath(
        os.path.dirname(
            self.Resource('tests', 'e2e', 'surface', 'code', 'testdata',
                          'hello_appengine', 'app.yaml')), os.getcwd())

    local_port = self.GetPort()
    gcloud_flags = [
        '--appengine',
        '--source=%s' % app_root,
    ]
    with self._RunDevelopmentServer('myservice', local_port, gcloud_flags):
      self.assertIsUp(local_port)


if __name__ == '__main__':
  test_case.main()
