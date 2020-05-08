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
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.code import kubernetes
from surface.code import clean_up
from tests.lib import test_case
from tests.lib.calliope import util as test_util
import mock


class CleanUpTest(test_case.TestCase):

  def SetUp(self):
    self.parser = test_util.ArgumentParser()
    clean_up.CleanUp.Args(self.parser)

  def testDefaultCluster(self):
    args = self.parser.parse_args([])

    with mock.patch.object(kubernetes, 'DeleteMinikube') as delete_minikube:
      clean_up.CleanUp(None, None).Run(args)

    delete_minikube.assert_called_with(kubernetes.DEFAULT_CLUSTER_NAME)

  def testMinikubeProfile(self):
    args = self.parser.parse_args(['--minikube-profile', 'my-cluster'])

    with mock.patch.object(kubernetes, 'DeleteMinikube') as delete_minikube:
      clean_up.CleanUp(None, None).Run(args)

    delete_minikube.assert_called_with('my-cluster')

  def testKind(self):
    args = self.parser.parse_args(['--kind-cluster', 'my-cluster'])

    with mock.patch.object(kubernetes,
                           'DeleteKindClusterIfExists') as delete_kind_cluster:
      clean_up.CleanUp(None, None).Run(args)

    delete_kind_cluster.assert_called_with('my-cluster')
