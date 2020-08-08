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
    url = 'http://localhost:%s/v1/events' % self._events_port
    with contextlib.closing(six.moves.urllib.request.urlopen(url)) as response:
      for line in _ReadStreamingLines(response):
        try:
          payload = json.loads(line)
          if not isinstance(payload, dict):
            continue
          event = payload['result']['event']
          if ('portEvent' in event and
              event['portEvent']['resourceName'] == service_name):
            return event['portEvent']['localPort']
        except ValueError:
          # Some of the output will not be json. We don't care about those
          # lines. Ignore the line if the line is invalid json.
          pass
      return None


def _ReadStreamingLines(response, chunk_size_bytes=50):
  # The standard http response readline waits until either the buffer is full
  # or the connection closes. The connection to read the event stream
  # stays open forever until the client closes it. As a result, we can get
  # into a state where http readline() never returns because the buffer
  # is not full but the server is waiting for the test to do something
  # to generate more events.
  # This function will not block a buffer not being full. os.read() will
  # return data of any size if a response is received. This allows the test
  # to make progress.
  pending = None

  while True:
    chunk = six.ensure_text(os.read(response.fp.fileno(), chunk_size_bytes))
    if not chunk:
      break

    if pending is not None:
      chunk = pending + chunk
      pending = None

    lines = chunk.split('\n')
    if lines and lines[-1]:
      pending = lines.pop()

    for line in lines:
      yield line

  if pending:
    yield pending


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
                            dockerfile,
                            service_name,
                            local_port,
                            additional_gcloud_flags=None):
    skaffold_event_port = self.GetPort()

    with e2e_base.RefreshTokenAuth() as auth:
      additional_skaffold_flags = ('--enable-rpc,--rpc-http-port=%s' %
                                   skaffold_event_port)
      gcloud_args = [
          'alpha',
          'code',
          'dev',
          '--service-name=' + service_name,
          '--image=fake-image-name',
          '--dockerfile=' + dockerfile,
          '--stop-cluster',
          '--source=%s' % os.path.dirname(dockerfile),
          '--minikube-profile=%s' % self.ClusterName(),
          '--additional-skaffold-flags=%s' % additional_skaffold_flags,
          '--account=%s' % auth.Account(),
          '--local-port=%s' % str(local_port),
      ]
      if additional_gcloud_flags:
        gcloud_args += additional_gcloud_flags

      match_strings = ['Serving Flask app']

      with self.ExecuteLegacyScriptAsync(
          'gcloud', gcloud_args, match_strings=match_strings,
          timeout=450) as process_context:
        with TerminateWithSigInt(
            process_context.p, timeout=datetime.timedelta(minutes=2)):
          yield SkaffoldContext(skaffold_event_port)

  @test_case.Filters.RunOnlyOnLinux
  def testNamespace(self):
    dockerfile = os.path.relpath(
        self.Resource('tests', 'e2e', 'surface', 'code', 'testdata', 'hello',
                      'Dockerfile'), os.getcwd())

    gcloud_flags = ['--namespace', 'my-namespace']
    local_port = self.GetPort()
    with self._RunDevelopmentServer(
        dockerfile,
        'myservice',
        local_port=local_port,
        additional_gcloud_flags=gcloud_flags):
      self.assertIsUp(local_port)

      kube_context_name = self.ClusterName()
      self.assertIn('service/myservice',
                    self._GetServices(kube_context_name, 'my-namespace'))

  @test_case.Filters.RunOnlyOnLinux
  def testDev(self):
    dockerfile = os.path.relpath(
        self.Resource('tests', 'e2e', 'surface', 'code', 'testdata', 'hello',
                      'Dockerfile'), os.getcwd())

    local_port = self.GetPort()
    with self._RunDevelopmentServer(
        dockerfile, 'myservice', local_port=local_port):
      self.assertIsUp(local_port)


if __name__ == '__main__':
  test_case.main()
