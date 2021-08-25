# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Utilities for the cloud deploy rollout resource."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import operator

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.clouddeploy import client_util
from googlecloudsdk.api_lib.clouddeploy import rollout
from googlecloudsdk.command_lib.deploy import exceptions as cd_exceptions
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import resources

_ROLLOUT_COLLECTION = 'clouddeploy.projects.locations.deliveryPipelines.releases.rollouts'
PENDING_APPROVAL_FILTER_TEMPLATE = (
    'approvalState="NEEDS_APPROVAL" AND '
    'state="PENDING_APPROVAL" AND targetId="{}"')
DEPLOYED_ROLLOUT_FILTER_TEMPLATE = (
    '(approvalState!="REJECTED" AND '
    'approvalState!="NEEDS_APPROVAL") AND state="SUCCEEDED" AND targetId="{}"')
ROLLOUT_IN_TARGET_FILTER_TEMPLATE = 'targetId="{}"'
ROLLOUT_ID_TEMPLATE = '{}-to-{}-{:04d}'


def RolloutId(rollout_name_or_id):
  """Returns rollout ID.

  Args:
    rollout_name_or_id: str, rollout full name or ID.

  Returns:
    Rollout ID.
  """
  rollout_id = rollout_name_or_id
  if 'projects/' in rollout_name_or_id:
    rollout_id = resources.REGISTRY.ParseRelativeName(
        rollout_name_or_id, collection=_ROLLOUT_COLLECTION).Name()

  return rollout_id


def ListPendingRollouts(releases, target_ref):
  """Lists the rollouts in PENDING_APPROVAL state for the releases associated with the specified target.

  The rollouts must be approvalState=NEEDS_APPROVAL and
  state=PENDING_APPROVAL. The returned list is sorted by rollout's create
  time.

  Args:
    releases: releases objects.
    target_ref: target object.

  Returns:
    a sorted list of rollouts.
  """
  rollouts = []
  filter_str = PENDING_APPROVAL_FILTER_TEMPLATE.format(target_ref.Name())
  for release in releases:
    resp = rollout.RolloutClient().List(release.name, filter_str)
    if resp:
      rollouts.extend(resp.rollouts)

  return sorted(rollouts, key=operator.attrgetter('createTime'), reverse=True)


def GetSucceededRollout(releases, target_ref, index=0):
  """Gets a successfully deployed rollouts for the releases associated with the specified target and index.

  Args:
    releases: releases objects.
    target_ref: target object.
    index: the nth rollout in the list to be returned.

  Returns:
    a rollout object or None if no rollouts in the target.
  """
  rollouts = []
  filter_str = DEPLOYED_ROLLOUT_FILTER_TEMPLATE.format(target_ref.Name())
  for release in releases:
    resp = rollout.RolloutClient().List(release.name, filter_str)
    if resp:
      rollouts.extend(resp.rollouts)

  if rollouts:
    if not 0 <= index < len(rollouts):
      raise exceptions.Error(
          'total number of rollouts for target {} is {}, index {} out of range.'
          .format(target_ref.Name(), len(rollouts), index))

    return sorted(
        rollouts, key=operator.attrgetter('deployEndTime'), reverse=True)[index]

  return None


def CreateRollout(release_ref,
                  to_target,
                  rollout_id=None,
                  annotations=None,
                  labels=None):
  """Creates a rollout by calling the rollout create API and waits for the operation to finish.

  Args:
    release_ref: protorpc.messages.Message, release resource object.
    to_target: str, the target to create create the rollout in.
    rollout_id: str, rollout ID.
    annotations: dict[str,str], a dict of annotation (key,value) pairs that
      allow clients to store small amounts of arbitrary data in cloud deploy
      resources.
    labels: dict[str,str], a dict of label (key,value) pairs that can be used to
      select cloud deploy resources and to find collections of cloud deploy
      resources that satisfy certain conditions.

  Raises:
      ListRolloutsError: an error occurred calling rollout list API.
  """
  final_rollout_id = rollout_id
  if not final_rollout_id:
    filter_str = ROLLOUT_IN_TARGET_FILTER_TEMPLATE.format(to_target)
    try:
      list_resp = rollout.RolloutClient().List(release_ref.RelativeName(),
                                               filter_str)
      final_rollout_id = ComputeRolloutID(release_ref.Name(), to_target,
                                          list_resp.rollouts)
    except apitools_exceptions.HttpError:
      raise cd_exceptions.ListRolloutsError(release_ref.RelativeName())

  resource_dict = release_ref.AsDict()
  rollout_ref = resources.REGISTRY.Parse(
      final_rollout_id,
      collection=_ROLLOUT_COLLECTION,
      params={
          'projectsId': resource_dict.get('projectsId'),
          'locationsId': resource_dict.get('locationsId'),
          'deliveryPipelinesId': resource_dict.get('deliveryPipelinesId'),
          'releasesId': release_ref.Name(),
      })
  rollout_obj = client_util.GetMessagesModule().Rollout(
      name=rollout_ref.RelativeName(), targetId=to_target)

  operation = rollout.RolloutClient().Create(rollout_ref, rollout_obj,
                                             annotations, labels)
  operation_ref = resources.REGISTRY.ParseRelativeName(
      operation.name, collection='clouddeploy.projects.locations.operations')
  client_util.OperationsClient().WaitForOperation(
      operation, operation_ref,
      'Creating rollout {} in target {}'.format(rollout_ref.RelativeName(),
                                                to_target))


def ComputeRolloutID(release_id, target_id, rollouts):
  """Generates a rollout ID.

  Args:
    release_id: str, release ID.
    target_id: str, target ID.
    rollouts: [apitools.base.protorpclite.messages.Message], list of rollout
      messages.

  Returns:
    rollout ID.

  Raises:
    googlecloudsdk.command_lib.deploy.exceptions.RolloutIdExhaustedError: if
    there are more than 1000 rollouts with auto-generated ID.
  """
  rollout_ids = {RolloutId(r.name) for r in rollouts}
  for i in range(1, 1001):
    # If the rollout ID is too long, the resource will fail to be created.
    # It is up to the user to mitigate this by passing an explicit rollout ID
    # to use, instead.
    rollout_id = ROLLOUT_ID_TEMPLATE.format(release_id, target_id, i)
    if rollout_id not in rollout_ids:
      return rollout_id

  raise cd_exceptions.RolloutIDExhaustedError(release_id)
