# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Tests for 'clusters get-credentials' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib.surface.container import base


class CreateTestGA(base.GATestBase, base.ClustersTestBase):
  """gcloud GA track using container v1 API."""

  def testGetCredentials(self):
    self.ExpectGetCluster(self._RunningCluster(name=self.CLUSTER_NAME))
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' get-credentials {0}'.format(self.CLUSTER_NAME))
    self.AssertOutputEquals('')
    self.AssertErrContains('kubeconfig entry generated for {0}'.format(
        self.CLUSTER_NAME))

  def testGetCredentialsRegional(self):
    self.ExpectGetCluster(
        self._RunningCluster(name=self.CLUSTER_NAME, zone=self.REGION),
        zone=self.REGION)
    self.Run(
        self.regional_clusters_command_base.format(self.REGION) +
        ' get-credentials {0}'.format(self.CLUSTER_NAME))
    self.AssertOutputEquals('')
    self.AssertErrContains('kubeconfig entry generated for {0}'.format(
        self.CLUSTER_NAME))


# Mixin class must come in first to have the correct multi-inheritance behavior.
class CreateTestBeta(base.BetaTestBase, CreateTestGA):
  """gcloud Beta track using container v1beta1 API."""


# Mixin class must come in first to have the correct multi-inheritance behavior.
class CreateTestAlpha(base.AlphaTestBase, CreateTestBeta):
  """gcloud Alpha track using container v1alpha1 API."""
