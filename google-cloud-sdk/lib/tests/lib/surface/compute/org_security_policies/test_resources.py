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


def MakeOrgSecurityPolicy(msgs, security_policy_ref):
  return msgs.SecurityPolicy(
      name=security_policy_ref.Name(),
      description='test-description',
      displayName='display-name',
      id=123,
      fingerprint=b'=g\313\0305\220\f\266',
      selfLink=security_policy_ref.SelfLink())
