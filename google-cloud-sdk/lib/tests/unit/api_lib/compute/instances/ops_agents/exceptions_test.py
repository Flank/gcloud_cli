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
"""Unit Tests for ops_agents.exceptions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute.instances.ops_agents import exceptions
from tests.lib import test_case

import six

ERROR_MESSAGE_1 = 'At most one agent with type [logging] is allowed.'
ERROR_MESSAGE_2 = (
    'The agent version [1] is not allowed. Expected values: [latest], '
    '[current-major], or anything in the format of '
    '[MAJOR_VERSION.MINOR_VERSION.PATCH_VERSION] or [MAJOR_VERSION.*.*].')
ERROR_MESSAGE_3 = (
    'An agent can not be pinned to the specific version [5.3.1] when '
    '[enable-autoupgrade] is set to true for that agent.')
MULTI_ERROR_MESSAGE = '{} | {} | {}'.format(
    ERROR_MESSAGE_1, ERROR_MESSAGE_2, ERROR_MESSAGE_3)


class PolicyValidationMultiErrorTest(test_case.TestCase):

  def testErrorMessage(self):
    errors = [
        exceptions.PolicyValidationError(ERROR_MESSAGE_1),
        exceptions.PolicyValidationError(ERROR_MESSAGE_2),
        exceptions.PolicyValidationError(ERROR_MESSAGE_3),
    ]
    multi_error = exceptions.PolicyValidationMultiError(errors)
    self.assertEqual(MULTI_ERROR_MESSAGE, six.text_type(multi_error))
