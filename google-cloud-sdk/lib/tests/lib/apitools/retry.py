# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""Utility for repeated apitools Expect method calls."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from six.moves import range


def ExpectWithRetries(method, request, response,
                      polling_method=None, polling_request=None,
                      final_response=None, num_retries=2):
  """Expects requests for a method, with retries if desired.

  Args:
    method: the initial method to expect on.
    request: the initial request.
    response: the initial response. Can be an exception.
    polling_method: the method to poll on if subsequent attempts are made,
        if different.
    polling_request: the request expected on subsequent attempts, if different.
    final_response: the last response expected, if different.
        Can be an exception.
    num_retries: the number of times the polling will happen after the initial
        request.
  """
  polling_method = polling_method or method
  polling_request = polling_request or request
  final_response = final_response or response

  for i in range(num_retries + 1):
    if i == 0:
      current_request = request
      current_method = method
    else:
      current_request = polling_request
      current_method = polling_method
    if i == num_retries:
      current_response = final_response
    else:
      current_response = response
    if isinstance(current_response, Exception):
      current_method.Expect(current_request, exception=current_response)
    else:
      current_method.Expect(current_request, response=current_response)
