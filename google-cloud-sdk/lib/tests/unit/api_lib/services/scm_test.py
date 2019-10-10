# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Tests of the scm module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.services import exceptions
from googlecloudsdk.api_lib.services import scm
from tests.lib.apitools import http_error
from tests.lib.surface.services import unit_test_base


class ServiceConsumerManagementTest(unit_test_base.SCMUnitTestBase):
  """Unit tests for scm module."""
  OPERATION_NAME = 'operations/123'
  OVERRIDE_ID = 'hello-override'

  def testListQuotaMetrics(self):
    """Test ListQuotaMetrics returns metrics when successful."""
    want = [self.mutate_quota_metric, self.default_quota_metric]
    self.ExpectListQuotaMetricsCall(want)

    got = scm.ListQuotaMetrics(self.DEFAULT_SERVICE, self.DEFAULT_CONSUMER)
    self.assertEqual([v for v in got], want)

  def testCreateQuotaOverrideCall(self):
    want = self.services_messages.Operation(
        name=self.OPERATION_NAME, done=False)
    self.ExpectListQuotaMetricsCall(
        [self.mutate_quota_metric, self.default_quota_metric])
    self.ExpectCreateQuotaOverrideCall(self.mutate_limit_name,
                                       self.mutate_metric, self.unit, 666,
                                       self.OPERATION_NAME)

    dimensions = None
    got = scm.CreateQuotaOverrideCall(self.DEFAULT_SERVICE,
                                      self.DEFAULT_CONSUMER, self.mutate_metric,
                                      self.unit, dimensions, 666)

    self.assertEqual(got, want)

  def testCreateQuotaOverrideCall_WithDimensions(self):
    want = self.services_messages.Operation(
        name=self.OPERATION_NAME, done=False)
    self.ExpectListQuotaMetricsCall(
        [self.mutate_quota_metric, self.default_quota_metric])
    self.ExpectCreateQuotaOverrideCall(
        self.mutate_limit_name,
        self.mutate_metric,
        self.unit,
        666,
        self.OPERATION_NAME,
        dimensions=[('regions', 'us-central1')],
        force=True)

    got = scm.CreateQuotaOverrideCall(
        self.DEFAULT_SERVICE,
        self.DEFAULT_CONSUMER,
        self.mutate_metric,
        self.unit, {'regions': 'us-central1'},
        666,
        force=True)

    self.assertEqual(got, want)

  def testCreateQuotaOverrideCall_failed(self):
    self.ExpectListQuotaMetricsCall(
        [self.mutate_quota_metric, self.default_quota_metric])
    server_error = http_error.MakeDetailedHttpError(code=403, message='Error.')
    self.ExpectCreateQuotaOverrideCall(
        self.mutate_limit_name,
        self.mutate_metric,
        self.unit,
        666,
        None,
        error=server_error)

    with self.assertRaisesRegex(
        exceptions.CreateQuotaOverridePermissionDeniedException, r'Error.'):
      dimensions = None
      scm.CreateQuotaOverrideCall(self.DEFAULT_SERVICE, self.DEFAULT_CONSUMER,
                                  self.mutate_metric, self.unit, dimensions,
                                  666)

  def testUpdateQuotaOverrideCall(self):
    want = self.services_messages.Operation(
        name=self.OPERATION_NAME, done=False)
    self.ExpectListQuotaMetricsCall(
        [self.mutate_quota_metric, self.default_quota_metric])
    self.ExpectUpdateQuotaOverrideCall(self.mutate_limit_name,
                                       self.mutate_metric, self.unit,
                                       self.OVERRIDE_ID, 666,
                                       self.OPERATION_NAME)

    dimensions = None
    got = scm.UpdateQuotaOverrideCall(self.DEFAULT_SERVICE,
                                      self.DEFAULT_CONSUMER, self.mutate_metric,
                                      self.unit, self.OVERRIDE_ID, dimensions,
                                      666)

    self.assertEqual(got, want)

  def testUpdateQuotaOverrideCall_WithDimensions(self):
    want = self.services_messages.Operation(
        name=self.OPERATION_NAME, done=False)
    self.ExpectListQuotaMetricsCall(
        [self.mutate_quota_metric, self.default_quota_metric])
    self.ExpectUpdateQuotaOverrideCall(
        self.mutate_limit_name,
        self.mutate_metric,
        self.unit,
        self.OVERRIDE_ID,
        666,
        self.OPERATION_NAME,
        dimensions=[('regions', 'us-central1')],
        force=True)

    got = scm.UpdateQuotaOverrideCall(
        self.DEFAULT_SERVICE,
        self.DEFAULT_CONSUMER,
        self.mutate_metric,
        self.unit,
        self.OVERRIDE_ID, {'regions': 'us-central1'},
        666,
        force=True)

    self.assertEqual(got, want)

  def testUpdateQuotaOverrideCall_failed(self):
    self.ExpectListQuotaMetricsCall(
        [self.mutate_quota_metric, self.default_quota_metric])
    server_error = http_error.MakeDetailedHttpError(code=403, message='Error.')
    self.ExpectUpdateQuotaOverrideCall(
        self.mutate_limit_name,
        self.mutate_metric,
        self.unit,
        self.OVERRIDE_ID,
        666,
        None,
        error=server_error)

    with self.assertRaisesRegex(
        exceptions.UpdateQuotaOverridePermissionDeniedException, r'Error.'):
      dimensions = None
      scm.UpdateQuotaOverrideCall(self.DEFAULT_SERVICE, self.DEFAULT_CONSUMER,
                                  self.mutate_metric, self.unit,
                                  self.OVERRIDE_ID, dimensions, 666)

  def testDeleteQuotaOverrideCall(self):
    want = self.services_messages.Operation(
        name=self.OPERATION_NAME, done=False)
    self.ExpectListQuotaMetricsCall(
        [self.mutate_quota_metric, self.default_quota_metric])
    self.ExpectDeleteQuotaOverrideCall(self.mutate_limit_name,
                                       self.mutate_metric, self.unit,
                                       self.OVERRIDE_ID, self.OPERATION_NAME)

    got = scm.DeleteQuotaOverrideCall(self.DEFAULT_SERVICE,
                                      self.DEFAULT_CONSUMER, self.mutate_metric,
                                      self.unit, self.OVERRIDE_ID)

    self.assertEqual(got, want)

  def testDeleteQuotaOverrideCall_WithDimensions(self):
    want = self.services_messages.Operation(
        name=self.OPERATION_NAME, done=False)
    self.ExpectListQuotaMetricsCall(
        [self.mutate_quota_metric, self.default_quota_metric])
    self.ExpectDeleteQuotaOverrideCall(
        self.mutate_limit_name,
        self.mutate_metric,
        self.unit,
        self.OVERRIDE_ID,
        self.OPERATION_NAME,
        force=True)

    got = scm.DeleteQuotaOverrideCall(
        self.DEFAULT_SERVICE,
        self.DEFAULT_CONSUMER,
        self.mutate_metric,
        self.unit,
        self.OVERRIDE_ID,
        force=True)

    self.assertEqual(got, want)

  def testDeleteQuotaOverrideCall_failed(self):
    self.ExpectListQuotaMetricsCall(
        [self.mutate_quota_metric, self.default_quota_metric])
    server_error = http_error.MakeDetailedHttpError(code=403, message='Error.')
    self.ExpectDeleteQuotaOverrideCall(
        self.mutate_limit_name,
        self.mutate_metric,
        self.unit,
        self.OVERRIDE_ID,
        None,
        error=server_error)

    with self.assertRaisesRegex(
        exceptions.DeleteQuotaOverridePermissionDeniedException, r'Error.'):
      scm.DeleteQuotaOverrideCall(self.DEFAULT_SERVICE, self.DEFAULT_CONSUMER,
                                  self.mutate_metric, self.unit,
                                  self.OVERRIDE_ID)

  def testGetOperation_Success(self):
    """Test GetOperation returns operation when successful."""
    want = self.services_messages.Operation(name=self.OPERATION_NAME, done=True)
    self.ExpectOperation(self.OPERATION_NAME, 0)

    got = scm.GetOperation(self.OPERATION_NAME)

    self.assertEqual(got, want)

  def testGetOperation_PermissionDenied(self):
    """Test GetOperation raises exception when server returns 403 error."""
    server_error = http_error.MakeDetailedHttpError(code=403, message='Error.')
    self.ExpectOperation(self.OPERATION_NAME, 0, error=server_error)

    with self.assertRaisesRegex(exceptions.OperationErrorException, r'Error.'):
      scm.GetOperation(self.OPERATION_NAME)
