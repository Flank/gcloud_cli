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
"""e2e test for kuberun command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib

from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from tests.lib import e2e_utils
from tests.lib import sdk_test_base
from tests.lib.surface.compute import e2e_test_base


@sdk_test_base.Filters.RunOnlyInBundle
class ServicesTest(sdk_test_base.BundledBase, e2e_test_base.BaseTest):

  def PreSetUp(self):
    self.track = base.ReleaseTrack.ALPHA

  def SetUp(self):
    self.name_gen = e2e_utils.GetResourceNameGenerator(
        prefix='gcloud-kuberun-test-service', hash_len=4)
    self.cluster_args = (
        '--cluster crfa-productivity-kape-e2e '
        '--cluster-location us-central1-a '
        '--project cloud-sdk-integration-testing')
    self.test_image = 'gcr.io/cloudrun/hello'

  @contextlib.contextmanager
  def CreateService(self):
    properties.VALUES.kuberun.enable_experimental_commands.Set(True)
    name = next(self.name_gen)
    try:
      self.Run('kuberun core services deploy {} {} --image {}'
               .format(self.cluster_args, name, self.test_image), self.track)
      self.AssertNewErrContainsAll([
          'Service [{}]'.format(name),
          'has been deployed and is serving 100 percent of traffic'
      ])
      yield name
    finally:
      self.Run('kuberun core services delete {} {} --quiet'
               .format(self.cluster_args, name), self.track)
      self.AssertNewErrContains('Service is successfully deleted')

  @sdk_test_base.Filters.SkipOnWindows('not implemented', 'b/169948680')
  def testServiceCreateAndUpdate(self):
    with self.CreateService() as service_name:
      self.Run('kuberun core services list {}'
               .format(self.cluster_args), self.track)
      self.AssertNewOutputContainsAll([
          service_name,
          'http://{}.default.example.com'.format(service_name)
      ])
      self.Run('kuberun core services describe {} {}'
               .format(self.cluster_args, service_name), self.track)
      self.AssertNewOutputContainsAll([
          ('Service {} in namespace default').format(service_name),
          '100% LATEST (currently {}-00001-'.format(service_name)
      ])

      self.Run('kuberun core services update {} {} --cpu 0.1'
               .format(self.cluster_args, service_name), self.track)
      self.AssertErrContains('Service [{}] has been updated.'
                             .format(service_name))

      self.Run('kuberun core services describe {} {}'
               .format(self.cluster_args, service_name), self.track)
      self.AssertNewOutputContainsAll([
          '100% LATEST (currently {}-00002-'.format(service_name)
      ])

  @sdk_test_base.Filters.SkipOnWindows('not implemented', 'b/169948680')
  def testServiceUpdateTraffic(self):
    with self.CreateService() as service_name:
      self.Run('kuberun core services list {}'
               .format(self.cluster_args), self.track)
      self.AssertNewOutputContainsAll([
          service_name,
          'http://{}.default.example.com'.format(service_name)
      ])

      # Update with --no-traffic
      self.Run('kuberun core services update {} {} --cpu 0.2 '
               '--no-traffic'
               .format(self.cluster_args, service_name), self.track)
      self.AssertErrContains('Service [{}] has been updated.'
                             .format(service_name))

      self.Run('kuberun core services describe {} {}'
               .format(self.cluster_args, service_name), self.track)
      self.AssertNewOutputContainsAll([
          '100% {}-00001-'.format(service_name),
          'Revision {}-00002-'.format(service_name)
      ])

      # Update traffic back to latest
      self.Run('kuberun core services update-traffic {} {} '
               '--to-latest'.format(self.cluster_args, service_name),
               self.track)
      self.AssertErrContains('Service [{}] has been updated.'
                             .format(service_name))

      self.Run('kuberun core services describe {} {}'
               .format(self.cluster_args, service_name), self.track)
      self.AssertNewOutputContainsAll([
          '100% LATEST (currently {}-00002-'.format(service_name)
      ])
