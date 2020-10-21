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

"""Some YAML configs to test different scenarios."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

VALID_YAML = """
    queue:
    - name: processInput
      mode: push
      rate: 55/s
      bucket_size: 10
      max_concurrent_requests: 1
      retry_parameters:
        task_retry_limit: 7
        min_backoff_seconds: 10.45
        max_backoff_seconds: 200.2
        max_doublings: 2
        task_age_limit: 1h
    - name: pullqueue5
      mode: pull
      retry_parameters:
        task_retry_limit: 11
    """

BAD_YAML_PUSHQ_NO_RATE = """
    queue:
    - name: processInput
      mode: push
      bucket_size: 10
      max_concurrent_requests: 1
      retry_parameters:
        task_retry_limit: 7
        min_backoff_seconds: 10.45
        max_backoff_seconds: 200.2
        max_doublings: 2
        task_age_limit: 1h
    """

BAD_YAML_PUSHQ_HIGH_RATE = """
    queue:
    - name: processInput
      mode: push
      bucket_size: 10
      rate: 505/s
      max_concurrent_requests: 1
      retry_parameters:
        task_retry_limit: 7
        min_backoff_seconds: 10.45
        max_backoff_seconds: 200.2
        max_doublings: 2
        task_age_limit: 1h
    """

BAD_YAML_PUSHQ_NEGATIVE_RETRY_LIMIT = """
    queue:
    - name: processInput
      mode: push
      rate: 1000/d
      bucket_size: 5
      max_concurrent_requests: 1
      retry_parameters:
        task_retry_limit: -1
        min_backoff_seconds: 10.45
        max_backoff_seconds: 200.2
        max_doublings: 2
        task_age_limit: 1h
    """

BAD_YAML_PUSHQ_ZERO_TASK_AGE_LIMIT = """
    queue:
    - name: processInput
      mode: push
      bucket_size: 10
      rate: 100/m
      max_concurrent_requests: 1
      retry_parameters:
        task_retry_limit: 7
        min_backoff_seconds: 10.45
        max_backoff_seconds: 200.2
        max_doublings: 2
        task_age_limit: 0d
    """

BAD_YAML_PUSHQ_NEGATIVE_MIN_BACKOFF = """
    queue:
    - name: processInput
      mode: push
      bucket_size: 10
      rate: 100/m
      max_concurrent_requests: 1
      retry_parameters:
        task_retry_limit: 7
        min_backoff_seconds: -10.45
        max_backoff_seconds: 200.2
        max_doublings: 2
        task_age_limit: 1d
    """

BAD_YAML_PUSHQ_NEGATIVE_MAX_BACKOFF = """
    queue:
    - name: processInput
      mode: push
      bucket_size: 10
      rate: 100/m
      max_concurrent_requests: 1
      retry_parameters:
        task_retry_limit: 7
        min_backoff_seconds: 10.45
        max_backoff_seconds: -200.2
        max_doublings: 2
        task_age_limit: 1d
    """

BAD_YAML_PUSHQ_NEGATIVE_MAX_DOUBLINGS = """
    queue:
    - name: processInput
      mode: push
      bucket_size: 10
      rate: 100/m
      max_concurrent_requests: 1
      retry_parameters:
        task_retry_limit: 7
        min_backoff_seconds: 10.45
        max_backoff_seconds: 200.2
        max_doublings: -23
        task_age_limit: 1d
    """

BAD_YAML_PUSHQ_BAD_MIN_MAX_BACKOFF = """
    queue:
    - name: processInput
      mode: push
      bucket_size: 10
      rate: 100/m
      max_concurrent_requests: 1
      retry_parameters:
        task_retry_limit: 7
        min_backoff_seconds: 10.45
        max_backoff_seconds: 8.2
        max_doublings: 2
        task_age_limit: 1d
    """

BAD_YAML_PUSHQ_NEGATIVE_BUCKET_SIZE = """
    queue:
    - name: processInput
      mode: push
      bucket_size: -10
      rate: 100/m
      max_concurrent_requests: 1
      retry_parameters:
        task_retry_limit: 7
        min_backoff_seconds: 0.45
        max_backoff_seconds: 200.2
        max_doublings: 2
        task_age_limit: 1d
    """

BAD_YAML_PUSHQ_HIGH_BUCKET_SIZE = """
    queue:
    - name: processInput
      mode: push
      bucket_size: 2000
      rate: 100/m
      max_concurrent_requests: 1
      retry_parameters:
        task_retry_limit: 7
        min_backoff_seconds: 0.45
        max_backoff_seconds: 200.2
        max_doublings: 2
        task_age_limit: 1d
    """

BAD_YAML_PULLQ_RATE = """
    queue:
    - name: pullqueue5
      mode: pull
      rate: 100/m
      retry_parameters:
        task_retry_limit: 3
    """

BAD_YAML_PULLQ_NEGATIVE_RETRY_LIMIT = """
    queue:
    - name: pullqueue5
      mode: pull
      retry_parameters:
        task_retry_limit: -8
    """

BAD_YAML_PULLQ_TASK_AGE_LIMIT = """
    queue:
    - name: pullqueue5
      mode: pull
      retry_parameters:
        task_retry_limit: 3
        task_age_limit: 1d
    """

BAD_YAML_PULLQ_MIN_BACKOFF = """
    queue:
    - name: pullqueue5
      mode: pull
      retry_parameters:
        task_retry_limit: 3
        min_backoff_seconds: 0.45
    """

BAD_YAML_PULLQ_MAX_BACKOFF = """
    queue:
    - name: pullqueue5
      mode: pull
      retry_parameters:
        task_retry_limit: 3
        max_backoff_seconds: 0.45
    """

BAD_YAML_PULLQ_MAX_DOUBLINGS = """
    queue:
    - name: pullqueue5
      mode: pull
      retry_parameters:
        task_retry_limit: 3
        max_doublings: 2
    """

BAD_YAML_PULLQ_MAX_CONCURRENT_REQUESTS = """
    queue:
    - name: pullqueue5
      mode: pull
      max_concurrent_requests: 10
      retry_parameters:
        task_retry_limit: 3
    """

BAD_YAML_PULLQ_BUCKET_SIZE = """
    queue:
    - name: pullqueue5
      mode: pull
      bucket_size: 15
      retry_parameters:
        task_retry_limit: 3
    """

BAD_YAML_PULLQ_TARGET = """
    queue:
    - name: pullqueue5
      mode: pull
      target: beta
      retry_parameters:
        task_retry_limit: 3
    """
