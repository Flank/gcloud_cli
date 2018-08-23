# -*- coding: utf-8 -*- #
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

"""Tests for the 'gcloud container policy namespaces describe' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io

from googlecloudsdk.core.resource import resource_printer
from tests.lib import test_case
from tests.lib.surface.container.policy.namespaces import base
from tests.lib.surface.container.policy.namespaces import util


class Describe(base.NamespacesUnitTestBase):

  def testDescribe(self):
    test_namespace = util.GetManagedNamespace()
    self.mock_client.projects_namespaces.Get.Expect(
        self.messages.KubernetespolicyProjectsNamespacesGetRequest(
            name=test_namespace.name),
        test_namespace)

    result = self.RunNamespaces('describe', test_namespace.name)
    self.assertEqual(test_namespace, result)

    expected_output = io.StringIO()
    resource_printer.Print(
        test_namespace, 'yaml', out=expected_output, single=True)
    self.AssertOutputContains(expected_output.getvalue())
    expected_output.close()

if __name__ == '__main__':
  test_case.main()
