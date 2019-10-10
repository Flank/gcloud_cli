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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import properties
from tests.lib import test_case


class SettingsTest(test_case.Base):

  def testApiKey(self):
    key = 'newkey'
    header = 'X-Google-Project-Override'
    prop = properties.VALUES.core.api_key

    prop.Set(key)
    client = apis.GetClientInstance('compute', 'v1', no_http=True)
    self.assertEqual(key, client.global_params.key)
    self.assertIn(header, client.additional_http_headers)

    prop.Set('')
    client = apis.GetClientInstance('compute', 'v1', no_http=True)
    self.assertEqual(None, client.global_params.key)
    self.assertNotIn(header, client.additional_http_headers)
