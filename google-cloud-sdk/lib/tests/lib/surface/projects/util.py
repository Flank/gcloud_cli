# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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

"""Testing resources for Projects."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudresourcemanager import projects_util
import six


def GetTestActiveProjectsList():
  messages = projects_util.GetMessages()
  return [
      messages.Project(
          lifecycleState=messages.Project.LifecycleStateValueValuesEnum.ACTIVE,
          projectId='feisty-catcher-644',
          projectNumber=925276746377,
          name='My Project 5'),
      messages.Project(
          lifecycleState=messages.Project.LifecycleStateValueValuesEnum.ACTIVE,
          projectId='test-project-2',
          projectNumber=123002,
          name='test-project-2'),
      messages.Project(
          lifecycleState=messages.Project.LifecycleStateValueValuesEnum.ACTIVE,
          projectId='test-project-3',
          projectNumber=123003,
          name='Test Project 3')
  ]


def GetTestProjectWithLongNameAndMatchingId():
  messages = projects_util.GetMessages()
  return messages.Project(
      lifecycleState=messages.Project.LifecycleStateValueValuesEnum.ACTIVE,
      projectId='abcdefghijklmnopqrstuvwxyz',
      projectNumber=925276746377,
      name='AbcdefghijkLMNOpqrstuvwxyz ')  # needs to be at least 24 characters


def GetTestActiveProject(prefix=False):
  messages = projects_util.GetMessages()
  return messages.Project(
      lifecycleState=messages.Project.LifecycleStateValueValuesEnum.ACTIVE,
      projectId=('projects/feisty-catcher-644'
                 if prefix else 'feisty-catcher-644'),
      projectNumber=925276746377,
      name='My Project 5')


def GetTestActiveProjectWithSameNameAndId():
  messages = projects_util.GetMessages()
  return messages.Project(
      lifecycleState=messages.Project.LifecycleStateValueValuesEnum.ACTIVE,
      projectId='test-project-2',
      projectNumber=123002,
      name='test-project-2')


def GetTestActiveProjectWithFolderParent():
  messages = projects_util.GetMessages()
  return messages.Project(
      lifecycleState=messages.Project.LifecycleStateValueValuesEnum.ACTIVE,
      projectId='test-project-2',
      projectNumber=123002,
      name='test-project-2',
      parent=messages.ResourceId(id='12345', type='folder'))


def GetTestActiveProjectWithOrganizationParent():
  messages = projects_util.GetMessages()
  return messages.Project(
      lifecycleState=messages.Project.LifecycleStateValueValuesEnum.ACTIVE,
      projectId='test-project-2',
      projectNumber=123002,
      name='test-project-2',
      parent=messages.ResourceId(id='2048', type='organization'),
  )


def GetTestActiveProjectWithLabels(labels):
  messages = projects_util.GetMessages()
  labels_message = messages.Project.LabelsValue(
      additionalProperties=[
          messages.Project.LabelsValue.AdditionalProperty(key=key, value=value)
          for key, value in sorted(labels.items())
      ])
  return projects_util.GetMessages().Project(
      lifecycleState=messages.Project.LifecycleStateValueValuesEnum.ACTIVE,
      projectId='test-project-2',
      projectNumber=123002,
      name='test-project-2',
      labels=labels_message)


def GetTestIamPolicy(clear_fields=None):
  """Creates a test IAM policy.

  Args:
      clear_fields: list of policy fields to clear.
  Returns:
      IAM policy.
  """
  if clear_fields is None:
    clear_fields = []

  messages = projects_util.GetMessages()
  policy = projects_util.GetMessages().Policy(
      auditConfigs=[
          messages.AuditConfig(
              auditLogConfigs=[
                  messages.AuditLogConfig(logType=messages.AuditLogConfig.
                                          LogTypeValueValuesEnum.ADMIN_READ)
              ],
              service='allServices')
      ],
      bindings=[
          messages.Binding(
              members=['serviceAccount:123hash@developer.gserviceaccount.com'],
              role='roles/editor'),
          messages.Binding(
              members=['user:tester@gmail.com', 'user:slick@gmail.com'],
              role='roles/owner')
      ],
      etag=b'<< Unique versioning etag bytefield >>')

  for field in clear_fields:
    policy.reset(field)

  return policy


def GetLabelsFlagValue(labels):
  return ','.join(
      ['{0}={1}'.format(k, v) for k, v in sorted(six.iteritems(labels))])
