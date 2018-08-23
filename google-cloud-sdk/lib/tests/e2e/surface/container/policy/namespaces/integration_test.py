# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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


"""Integration tests for the 'gcloud container policy namespaces' commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io

from googlecloudsdk.core.resource import resource_printer
from tests.lib.surface.container.policy.namespaces import base


class NamespacesTest(base.NamespacesE2ETest):

  def SetUp(self):
    test_k8s_name = 'do-not-delete-gcould-integration-test'
    self.test_namespace = self.messages.Namespace(
        name='projects/cloud-sdk-integration-testing/namespaces/{0}'.format(
            test_k8s_name),
        organization='organizations/433637338589',
        kubernetesName=test_k8s_name,
        parent='projects/cloud-sdk-integration-testing',
    )

  def testList(self):
    self.Run('alpha container policy namespaces list')
    expected_output = io.StringIO()
    resource_printer.Print(
        self.test_namespace, 'yaml', out=expected_output, single=True)
    self.AssertOutputContains(expected_output.getvalue())
    expected_output.close()

  def testDescribe(self):
    self.Run('alpha container policy namespaces describe {0}'.format(
        self.test_namespace.name))
    expected_output = io.StringIO()
    resource_printer.Print(
        self.test_namespace, 'yaml', out=expected_output, single=True)
    self.AssertOutputContains(expected_output.getvalue())
    expected_output.close()
