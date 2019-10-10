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
"""Unit tests for environments delete."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.composer import util as api_util
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.composer import util as command_util
from googlecloudsdk.core.console import console_io
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.composer import base


class EnvironmentsDeleteGATest(base.EnvironmentsUnitTest):

  def PreSetUp(self):
    self.SetTrack(calliope_base.ReleaseTrack.GA)

  def testSuccessfulDeleteSingle_synchronous(self):
    self.WriteInput('y\n')
    self._ExpectDeletionCalls(self.TEST_PROJECT, self.TEST_LOCATION,
                              self.TEST_ENVIRONMENT_ID,
                              self.TEST_OPERATION_UUID)

    self.RunEnvironments('delete', '--project', self.TEST_PROJECT, '--location',
                         self.TEST_LOCATION, self.TEST_ENVIRONMENT_ID)

  def testSuccessfulDeleteSingle_asynchronous(self):
    self.WriteInput('y\n')
    self._ExpectDeletionCalls(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        self.TEST_OPERATION_UUID,
        is_async=True)

    self.RunEnvironments('delete', '--project', self.TEST_PROJECT, '--location',
                         self.TEST_LOCATION, self.TEST_ENVIRONMENT_ID,
                         '--async')

  def testSuccessfulDeleteMultiple_asynchronous(self):
    self.WriteInput('y\n')
    deletions = [
        _Deletion(
            self.TEST_PROJECT,
            self.TEST_LOCATION,
            self.TEST_ENVIRONMENT_ID,
            self.TEST_OPERATION_UUID,
            is_async=True),
        _Deletion(
            self.TEST_PROJECT,
            self.TEST_LOCATION,
            self.TEST_ENVIRONMENT_ID2,
            self.TEST_OPERATION_UUID2,
            is_async=True)
    ]

    self._ExpectMultipleDeletionCalls(deletions)

    self.RunEnvironments('delete', '--project', self.TEST_PROJECT, '--location',
                         self.TEST_LOCATION, self.TEST_ENVIRONMENT_ID,
                         self.TEST_ENVIRONMENT_ID2, '--async')

  def testSuccessfulDeleteMultiple_synchronous(self):
    self.WriteInput('y\n')
    deletions = [
        _Deletion(self.TEST_PROJECT, self.TEST_LOCATION,
                  self.TEST_ENVIRONMENT_ID, self.TEST_OPERATION_UUID),
        _Deletion(self.TEST_PROJECT, self.TEST_LOCATION,
                  self.TEST_ENVIRONMENT_ID2, self.TEST_OPERATION_UUID2)
    ]

    self._ExpectMultipleDeletionCalls(deletions)

    self.RunEnvironments('delete', '--project', self.TEST_PROJECT, '--location',
                         self.TEST_LOCATION, self.TEST_ENVIRONMENT_ID,
                         self.TEST_ENVIRONMENT_ID2)

  def testSuccessfulDeleteMultipleWithSingleFastFailure_synchronous(self):
    self.WriteInput('y\n')
    deletions = [
        _Deletion(
            self.TEST_PROJECT,
            self.TEST_LOCATION,
            self.TEST_ENVIRONMENT_ID,
            self.TEST_OPERATION_UUID,
            deletion_exception=http_error.MakeHttpError(
                code=404, message='NOT_FOUND')),
        _Deletion(self.TEST_PROJECT, self.TEST_LOCATION,
                  self.TEST_ENVIRONMENT_ID2, self.TEST_OPERATION_UUID2)
    ]

    self._ExpectMultipleDeletionCalls(deletions)

    with self.AssertRaisesExceptionMatches(
        command_util.Error, 'Some requested deletions did not succeed.'):
      self.RunEnvironments('delete', '--project', self.TEST_PROJECT,
                           '--location', self.TEST_LOCATION,
                           self.TEST_ENVIRONMENT_ID, self.TEST_ENVIRONMENT_ID2)
    self.AssertErrMatches(r'Failed to delete environment \[{}\]'.format(
        self.TEST_ENVIRONMENT_NAME))
    self.AssertErrMatches(
        r'^{{"ux": "PROGRESS_TRACKER", "message": "Waiting for \[{}] to '
        r'be deleted'.format(self.TEST_ENVIRONMENT_NAME2))

  def testSuccessfulDeleteMultipleWithSingleSlowFailure_synchronous(self):
    failed_op_metadata = self.messages.OperationMetadata(
        state=self.messages.OperationMetadata.StateValueValuesEnum.FAILED,
        operationType=self.messages.OperationMetadata.
        OperationTypeValueValuesEnum.DELETE)
    failed_op = self.MakeOperation(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_OPERATION_UUID,
        done=True,
        error=self.messages.Status(),
        metadata=api_util.ParseOperationJsonMetadata(
            failed_op_metadata, self.messages.Operation.MetadataValue))

    self.WriteInput('y\n')

    deletions = [
        _Deletion(
            self.TEST_PROJECT,
            self.TEST_LOCATION,
            self.TEST_ENVIRONMENT_ID,
            self.TEST_OPERATION_UUID,
            get_operation_response=failed_op),
        _Deletion(self.TEST_PROJECT, self.TEST_LOCATION,
                  self.TEST_ENVIRONMENT_ID2, self.TEST_OPERATION_UUID2)
    ]

    self._ExpectMultipleDeletionCalls(deletions)

    with self.AssertRaisesExceptionMatches(
        command_util.Error, 'Some requested deletions did not succeed.'):
      self.RunEnvironments('delete', '--project', self.TEST_PROJECT,
                           '--location', self.TEST_LOCATION,
                           self.TEST_ENVIRONMENT_ID, self.TEST_ENVIRONMENT_ID2)
    self.AssertErrMatches(r'Failed to delete environment \[{}\]'.format(
        self.TEST_ENVIRONMENT_NAME))
    self.AssertErrMatches(
        r'^{{"ux": "PROGRESS_TRACKER", "message": "Waiting for \[{}] to be '
        'deleted"'.format(self.TEST_ENVIRONMENT_NAME2))

  def testSuccessfulDeleteMultipleWithSingleFastFailure_asynchronous(self):
    self.WriteInput('y\n')
    deletions = [
        _Deletion(
            self.TEST_PROJECT,
            self.TEST_LOCATION,
            self.TEST_ENVIRONMENT_ID,
            self.TEST_OPERATION_UUID,
            is_async=True,
            deletion_exception=http_error.MakeHttpError(
                code=404, message='NOT_FOUND')),
        _Deletion(
            self.TEST_PROJECT,
            self.TEST_LOCATION,
            self.TEST_ENVIRONMENT_ID2,
            self.TEST_OPERATION_UUID2,
            is_async=True)
    ]

    self._ExpectMultipleDeletionCalls(deletions)

    with self.AssertRaisesExceptionMatches(
        command_util.Error, 'Some requested deletions did not succeed.'):
      self.RunEnvironments('delete', '--project', self.TEST_PROJECT,
                           '--location', self.TEST_LOCATION,
                           self.TEST_ENVIRONMENT_ID, self.TEST_ENVIRONMENT_ID2,
                           '--async')
    self.AssertErrMatches(r'Failed to delete environment \[{}\]'.format(
        self.TEST_ENVIRONMENT_NAME))
    self.AssertErrMatches(r'^Delete in progress for environment \[{}]'
                          .format(self.TEST_ENVIRONMENT_NAME2))

  def testDeleteEnvironmentNotFound(self):
    self.WriteInput('y\n')
    self.ExpectEnvironmentDelete(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        exception=http_error.MakeHttpError(code=404, message='NOT_FOUND'))
    with self.AssertRaisesExceptionMatches(
        command_util.Error, 'Some requested deletions did not succeed.'):
      self.RunEnvironments('delete', '--project', self.TEST_PROJECT,
                           '--location', self.TEST_LOCATION,
                           self.TEST_ENVIRONMENT_ID)
    self.AssertErrMatches(r'Failed to delete environment \[{}]'.format(
        self.TEST_ENVIRONMENT_NAME))

  def testDeleteEnvironmentDecline(self):
    self.WriteInput('n\n')
    with self.AssertRaisesExceptionMatches(console_io.OperationCancelledError,
                                           'Deletion aborted by user'):
      self.RunEnvironments('delete', '--project', self.TEST_PROJECT,
                           '--location', self.TEST_LOCATION,
                           self.TEST_ENVIRONMENT_ID)

  def testDeleteInsufficentPermissions(self):
    self.WriteInput('y\n')
    self.ExpectEnvironmentDelete(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        exception=http_error.MakeHttpError(
            code=403, message='PERMISSION_DENIED'))
    with self.AssertRaisesExceptionMatches(
        command_util.Error, 'Some requested deletions did not succeed.'):
      self.RunEnvironments('delete', '--project', self.TEST_PROJECT,
                           '--location', self.TEST_LOCATION,
                           self.TEST_ENVIRONMENT_ID)
    self.AssertErrMatches(r'Failed to delete environment \[{}]'.format(
        self.TEST_ENVIRONMENT_NAME))

  def _ExpectDeletionCalls(self,
                           project,
                           location,
                           environment_id,
                           operation_uuid,
                           is_async=False,
                           exception=None):
    running_op = self.MakeOperation(
        project, location, operation_uuid, done=False)
    successful_op = self.MakeOperation(
        project, location, operation_uuid, done=True)
    self.ExpectEnvironmentDelete(
        project,
        location,
        environment_id,
        exception=exception,
        response=running_op if exception is None else None)
    if not is_async and exception is None:
      self.ExpectOperationGet(
          project, location, operation_uuid, response=successful_op)
    else:
      return running_op

  def _ExpectMultipleDeletionCalls(self, deletions):
    for deletion in deletions:
      running_op = self.MakeOperation(
          deletion.project,
          deletion.location,
          deletion.operation_uuid,
          done=False)
      self.ExpectEnvironmentDelete(
          deletion.project,
          deletion.location,
          deletion.environment_id,
          exception=deletion.deletion_exception,
          response=running_op if deletion.deletion_exception is None else None)
    for deletion in deletions:
      if not deletion.async_ and deletion.deletion_exception is None:
        successful_op = self.MakeOperation(
            deletion.project,
            deletion.location,
            deletion.operation_uuid,
            done=True)
        self.ExpectOperationGet(
            deletion.project,
            deletion.location,
            deletion.operation_uuid,
            response=(successful_op if deletion.get_operation_response is None
                      else deletion.get_operation_response))


class EnvironmentsDeleteBetaTest(EnvironmentsDeleteGATest):

  def PreSetUp(self):
    self.SetTrack(calliope_base.ReleaseTrack.BETA)


class EnvironmentsDeleteAlphaTest(EnvironmentsDeleteBetaTest):

  def PreSetUp(self):
    self.SetTrack(calliope_base.ReleaseTrack.ALPHA)


class _Deletion(object):

  def __init__(self,
               project,
               location,
               environment_id,
               operation_uuid,
               is_async=False,
               deletion_exception=None,
               get_operation_response=None):
    self.project = project
    self.location = location
    self.environment_id = environment_id
    self.operation_uuid = operation_uuid
    self.async_ = is_async
    self.deletion_exception = deletion_exception
    self.get_operation_response = get_operation_response


if __name__ == '__main__':
  test_case.main()
