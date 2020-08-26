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
"""Resources that are shared by two or more tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis

alpha_messages = core_apis.GetMessagesModule('compute', 'alpha')

_COMPUTE_PATH = 'https://compute.googleapis.com/compute'


def MakeSslPolicies(msgs, api):
  """Make ssl policy test resources for the given api version."""
  prefix = _COMPUTE_PATH + '/' + api
  return [
      msgs.SslPolicy(
          name='ssl-policy-1',
          profile=msgs.SslPolicy.ProfileValueValuesEnum('COMPATIBLE'),
          minTlsVersion=msgs.SslPolicy.MinTlsVersionValueValuesEnum('TLS_1_0'),
          customFeatures=[],
          selfLink=(prefix +
                    '/projects/my-project/global/sslPolicies/ssl-policy-1'))
  ]


SSL_POLICIES_ALPHA = MakeSslPolicies(alpha_messages, 'alpha')
