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
"""Some tests for `gcloud app deploy queue.yaml` migration functions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections

from googlecloudsdk.api_lib.app import util
from googlecloudsdk.api_lib.app import yaml_parsing
from googlecloudsdk.api_lib.tasks import app_deploy_migration_util as mig_util
from googlecloudsdk.api_lib.tasks import task_queues_convertors as convertors
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.tasks import test_base
from tests.lib.surface.tasks import yaml_configs


class ValidateYamlFileTestBeta(test_base.CloudTasksTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.parser = yaml_parsing.ConfigYamlInfo.CONFIG_YAML_PARSERS.get('queue')

  def GetConfig(self, yaml_string):
    parsed = self.parser(yaml_string)
    config = yaml_parsing.ConfigYamlInfo('', config='queue', parsed=parsed)
    return config

  def testValidateYamlFile(self):
    config = self.GetConfig(yaml_configs.VALID_YAML)
    mig_util.ValidateYamlFileConfig(config)

  def testPushQueueNoRate(self):
    config = self.GetConfig(yaml_configs.BAD_YAML_PUSHQ_NO_RATE)
    err_msg = 'Refill rate must be specified for push-based queue'
    with self.assertRaisesRegex(util.RPCError, err_msg):
      mig_util.ValidateYamlFileConfig(config)

  def testPushQueueHighRate(self):
    config = self.GetConfig(yaml_configs.BAD_YAML_PUSHQ_HIGH_RATE)
    err_msg = 'Refill rate must not exceed'
    with self.assertRaisesRegex(util.RPCError, err_msg):
      mig_util.ValidateYamlFileConfig(config)

  def testPushQueueNegativeRetryLimit(self):
    config = self.GetConfig(yaml_configs.BAD_YAML_PUSHQ_NEGATIVE_RETRY_LIMIT)
    err_msg = 'Task retry limit must not be less than zero'
    with self.assertRaisesRegex(util.RPCError, err_msg):
      mig_util.ValidateYamlFileConfig(config)

  def testPushQueueNegativeTaskAgeLimit(self):
    config = self.GetConfig(yaml_configs.BAD_YAML_PUSHQ_ZERO_TASK_AGE_LIMIT)
    err_msg = 'Task age limit must be greater than zero'
    with self.assertRaisesRegex(util.RPCError, err_msg):
      mig_util.ValidateYamlFileConfig(config)

  def testPushQueueNegativeMinBackoff(self):
    config = self.GetConfig(yaml_configs.BAD_YAML_PUSHQ_NEGATIVE_MIN_BACKOFF)
    err_msg = 'Min backoff seconds must not be less than zero'
    with self.assertRaisesRegex(util.RPCError, err_msg):
      mig_util.ValidateYamlFileConfig(config)

  def testPushQueueNegativeMaxBackoff(self):
    config = self.GetConfig(yaml_configs.BAD_YAML_PUSHQ_NEGATIVE_MAX_BACKOFF)
    err_msg = 'Max backoff seconds must not be less than zero'
    with self.assertRaisesRegex(util.RPCError, err_msg):
      mig_util.ValidateYamlFileConfig(config)

  def testPushQueueNegativeMaxDoublings(self):
    config = self.GetConfig(yaml_configs.BAD_YAML_PUSHQ_NEGATIVE_MAX_DOUBLINGS)
    err_msg = 'Max doublings must not be less than zero'
    with self.assertRaisesRegex(util.RPCError, err_msg):
      mig_util.ValidateYamlFileConfig(config)

  def testPushQueueBadMinMaxBackoff(self):
    config = self.GetConfig(yaml_configs.BAD_YAML_PUSHQ_BAD_MIN_MAX_BACKOFF)
    err_msg = 'Min backoff sec must not be greater than than max backoff sec'
    with self.assertRaisesRegex(util.RPCError, err_msg):
      mig_util.ValidateYamlFileConfig(config)

  def testPushQueueNegativeBucketSize(self):
    config = self.GetConfig(yaml_configs.BAD_YAML_PUSHQ_NEGATIVE_BUCKET_SIZE)
    err_msg = 'Error updating queue "processInput": The queue rate is invalid'
    with self.assertRaisesRegex(util.RPCError, err_msg):
      mig_util.ValidateYamlFileConfig(config)

  def testPushQueueHighBucketSize(self):
    config = self.GetConfig(yaml_configs.BAD_YAML_PUSHQ_HIGH_BUCKET_SIZE)
    err_msg = 'Error updating queue "processInput": Maximum bucket size'
    with self.assertRaisesRegex(util.RPCError, err_msg):
      mig_util.ValidateYamlFileConfig(config)

  def testPullQueueRate(self):
    config = self.GetConfig(yaml_configs.BAD_YAML_PULLQ_RATE)
    err_msg = 'Refill rate must not be specified for pull-based queue'
    with self.assertRaisesRegex(util.RPCError, err_msg):
      mig_util.ValidateYamlFileConfig(config)

  def testPullQueueNegativeRetryLimit(self):
    config = self.GetConfig(yaml_configs.BAD_YAML_PULLQ_NEGATIVE_RETRY_LIMIT)
    err_msg = 'Task retry limit must not be less than zero'
    with self.assertRaisesRegex(util.RPCError, err_msg):
      mig_util.ValidateYamlFileConfig(config)

  def testPullQueueTaskAgeLimit(self):
    config = self.GetConfig(yaml_configs.BAD_YAML_PULLQ_TASK_AGE_LIMIT)
    err_msg = "Can't specify task_age_limit for a pull queue"
    with self.assertRaisesRegex(util.RPCError, err_msg):
      mig_util.ValidateYamlFileConfig(config)

  def testPullQueueMinBackoff(self):
    config = self.GetConfig(yaml_configs.BAD_YAML_PULLQ_MIN_BACKOFF)
    err_msg = "Can't specify min_backoff_seconds for a pull queue"
    with self.assertRaisesRegex(util.RPCError, err_msg):
      mig_util.ValidateYamlFileConfig(config)

  def testPullQueueMaxBackoff(self):
    config = self.GetConfig(yaml_configs.BAD_YAML_PULLQ_MAX_BACKOFF)
    err_msg = "Can't specify max_backoff_seconds for a pull queue"
    with self.assertRaisesRegex(util.RPCError, err_msg):
      mig_util.ValidateYamlFileConfig(config)

  def testPullQueueMaxDoublings(self):
    config = self.GetConfig(yaml_configs.BAD_YAML_PULLQ_MAX_DOUBLINGS)
    err_msg = "Can't specify max_doublings for a pull queue"
    with self.assertRaisesRegex(util.RPCError, err_msg):
      mig_util.ValidateYamlFileConfig(config)

  def testPullQueueMaxConcurrentRequests(self):
    config = self.GetConfig(yaml_configs.BAD_YAML_PULLQ_MAX_CONCURRENT_REQUESTS)
    err_msg = (
        'Max concurrent requests must not be specified for pull-based queue')
    with self.assertRaisesRegex(util.RPCError, err_msg):
      mig_util.ValidateYamlFileConfig(config)

  def testPullQueueBucketSize(self):
    config = self.GetConfig(yaml_configs.BAD_YAML_PULLQ_BUCKET_SIZE)
    err_msg = 'Bucket size must not be specified for pull-based queue'
    with self.assertRaisesRegex(util.RPCError, err_msg):
      mig_util.ValidateYamlFileConfig(config)

  def testPullQueueTarget(self):
    config = self.GetConfig(yaml_configs.BAD_YAML_PULLQ_TARGET)
    err_msg = 'Target must not be specified for pull-based queue'
    with self.assertRaisesRegex(util.RPCError, err_msg):
      mig_util.ValidateYamlFileConfig(config)


class ValidateConvertorFunctionsTestBeta(test_base.CloudTasksTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def testStringToCamelCase(self):
    combinations_to_test = (
        ('min_backoff', 'minBackoff'),
        ('max_retry_duration', 'maxRetryDuration'),
        ('max_retry_duration', 'maxRetryDuration'),  # Deliberate repeat
    )
    for snake_str, camel_str in combinations_to_test:
      self.assertEqual(convertors.ConvertStringToCamelCase(snake_str),
                       camel_str)

  def testConvertRate(self):
    combinations_to_test = (
        ('100/s', 100),
        ('60/m', 1),
        ('5400/h', 1.5),
        ('864000/d', 10),
    )
    for rate_str, rate_float in combinations_to_test:
      self.assertEqual(convertors.ConvertRate(rate_str), rate_float)

  def testCheckAndConvertStringToFloatIfApplicable(self):
    combinations_to_test = (
        ('2m', 120),
        ('1.5h', 5400),
        ('8.5s', 8.5),
        ('1d', 86400),
        ('max_retry_duration', 'max_retry_duration'),
        (17.4, 17.4),
    )
    for input_str, output in combinations_to_test:
      self.assertEqual(
          convertors.CheckAndConvertStringToFloatIfApplicable(input_str),
          output
      )

  def testConvertBackoffSeconds(self):
    combinations_to_test = (
        (1.3, '1.3s'),
        (10.74, '10.74s'),
    )
    for rate, rate_str in combinations_to_test:
      self.assertEqual(convertors.ConvertBackoffSeconds(rate), rate_str)

  def testConvertTaskAgeLimit(self):
    combinations_to_test = (
        ('2m', '120s'),
        ('1.5h', '5400s'),
        ('8.5s', '8s'),
        ('1d', '86400s'),
    )
    for time_with_units, time_in_sec in combinations_to_test:
      self.assertEqual(
          convertors.ConvertTaskAgeLimit(time_with_units), time_in_sec)

  def testConvertTarget(self):
    combinations_to_test = (
        ('alpha', collections.OrderedDict({'service': 'alpha'})),
        ('version.beta', collections.OrderedDict(
            {'service': 'beta', 'version': 'version'}))
    )
    for target, result in combinations_to_test:
      self.assertEqual(convertors.ConvertTarget(target), result)
    with self.AssertRaisesExceptionMatches(
        ValueError, 'Unsupported value received for target alpha.beta.omega'):
      convertors.ConvertTarget('alpha.beta.omega')


if __name__ == '__main__':
  test_case.main()
