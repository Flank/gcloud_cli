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
"""Test base for the backend services update subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources


class UpdateTestBase(test_base.BaseTest):
  """Test base for the backend services update subcommand."""

  def SetUp(self):
    self.SelectApi(self.api_version)

    self._backend_services = test_resources.BACKEND_SERVICES_V1

    self._http_backend_services_with_legacy_health_check = (
        test_resources.HTTP_BACKEND_SERVICES_WITH_LEGACY_HEALTH_CHECK_V1)
    self._https_backend_services_with_legacy_health_check = (
        test_resources.HTTPS_BACKEND_SERVICES_WITH_LEGACY_HEALTH_CHECK_V1)

    self._http_backend_services_with_health_check = (
        test_resources.HTTP_BACKEND_SERVICES_WITH_HEALTH_CHECK_V1)
    self._https_backend_services_with_health_check = (
        test_resources.HTTPS_BACKEND_SERVICES_WITH_HEALTH_CHECK_V1)

  def RunUpdate(self, command, use_global=True):
    suffix = ' --global' if use_global else ''
    self.Run('compute backend-services update ' + command + suffix)
