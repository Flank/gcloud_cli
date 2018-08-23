# -*- coding: utf-8 -*- #
# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Tests for googlecloudsdk/command_lib/category_manager/iam_lib."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.category_manager import store
from googlecloudsdk.api_lib.category_manager import utils
from googlecloudsdk.command_lib.category_manager import iam_lib
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import resources
from tests.lib import sdk_test_base
from tests.lib import test_case


class IamLibTest(sdk_test_base.WithFakeAuth):
  """Tests for iam_lib, which calls api_lib/category_manager."""

  def SetUp(self):
    self.messages = utils.GetMessagesModule()
    self.policy = self.messages.Policy(bindings=[
        self.messages.Binding(
            role='role/categorymanager.admin',
            members=[
                'user:admin@gmail.com',
                'serviceAccount:account@test-project.googleservice.com'
            ]),
        self.messages.Binding(
            role='role/categorymanager.reader',
            members=['user:user1@gmail.com', 'user:user2@gmail.com'])
    ])
    self.store_ref = resources.REGISTRY.Create(
        'categorymanager.taxonomyStores', taxonomyStoresId='111')
    self.store_getiam_mock = self.StartObjectPatch(
        store, 'GetIamPolicy', autospec=True, return_value=self.policy)
    self.store_setiam_mock = self.StartObjectPatch(
        store, 'SetIamPolicy', autospec=True)

  def testAddIamPolicyBinding(self):
    iam_lib.AddIamPolicyBinding(
        resource_resource=self.store_ref,
        role='role/categorymanager.admin',
        member='user:admin2@gmail.com',
        module=store)
    self.store_getiam_mock.assert_called_once_with(self.store_ref)
    self.store_setiam_mock.assert_called_once_with(self.store_ref, self.policy)
    self.assertEqual([
        self.messages.Binding(
            role='role/categorymanager.admin',
            members=[
                'user:admin@gmail.com',
                'serviceAccount:account@test-project.googleservice.com',
                'user:admin2@gmail.com',
            ]),
        self.messages.Binding(
            role='role/categorymanager.reader',
            members=['user:user1@gmail.com', 'user:user2@gmail.com'])
    ], self.policy.bindings)

  def testAddIamPolicyBindingAddNewRoles(self):
    iam_lib.AddIamPolicyBinding(
        resource_resource=self.store_ref,
        role='role/categorymanager.tagReader',
        member='user:user3@gmail.com',
        module=store)
    self.store_getiam_mock.assert_called_once_with(self.store_ref)
    self.store_setiam_mock.assert_called_once_with(self.store_ref, self.policy)
    self.assertEqual([
        self.messages.Binding(
            role='role/categorymanager.admin',
            members=[
                'user:admin@gmail.com',
                'serviceAccount:account@test-project.googleservice.com',
            ]),
        self.messages.Binding(
            role='role/categorymanager.reader',
            members=['user:user1@gmail.com', 'user:user2@gmail.com']),
        self.messages.Binding(
            role='role/categorymanager.tagReader',
            members=['user:user3@gmail.com'])
    ], self.policy.bindings)

  def testAddIamPolicyBindingWithDuplicateEntry(self):
    iam_lib.AddIamPolicyBinding(
        resource_resource=self.store_ref,
        role='role/categorymanager.admin',
        member='user:admin@gmail.com',
        module=store)
    self.store_getiam_mock.assert_called_once_with(self.store_ref)
    self.store_setiam_mock.assert_called_once_with(self.store_ref, self.policy)
    self.assertEqual([
        self.messages.Binding(
            role='role/categorymanager.admin',
            members=[
                'user:admin@gmail.com',
                'serviceAccount:account@test-project.googleservice.com',
            ]),
        self.messages.Binding(
            role='role/categorymanager.reader',
            members=['user:user1@gmail.com', 'user:user2@gmail.com'])
    ], self.policy.bindings)

  def testRemoveIamPolicyBinding(self):
    iam_lib.RemoveIamPolicyBinding(
        resource_resource=self.store_ref,
        role='role/categorymanager.reader',
        member='user:user1@gmail.com',
        module=store)
    self.store_getiam_mock.assert_called_once_with(self.store_ref)
    self.store_setiam_mock.assert_called_once_with(self.store_ref, self.policy)
    self.assertEqual([
        self.messages.Binding(
            role='role/categorymanager.admin',
            members=[
                'user:admin@gmail.com',
                'serviceAccount:account@test-project.googleservice.com',
            ]),
        self.messages.Binding(
            role='role/categorymanager.reader',
            members=['user:user2@gmail.com'])
    ], self.policy.bindings)

  def testRemoveIamPolicyBindingRaisesWhenUserNotFoundInBindings(self):
    self.assertRaises(
        core_exceptions.Error,
        iam_lib.RemoveIamPolicyBinding,
        resource_resource=self.store_ref,
        role='role/categorymanager.reader',
        member='user:nosuchuser@gmail.com',
        module=store)
    self.store_getiam_mock.assert_called_once_with(self.store_ref)
    self.assertEqual(0, self.store_setiam_mock.call_count)

  def testRemoveIamPolicyBindingRaisesWhenRoleNotFoundInBindings(self):
    self.assertRaises(
        core_exceptions.Error,
        iam_lib.RemoveIamPolicyBinding,
        resource_resource=self.store_ref,
        role='role/categorymanager.fakeReader',
        member='user:user1@gmail.com',
        module=store)
    self.store_getiam_mock.assert_called_once_with(self.store_ref)
    self.assertEqual(0, self.store_setiam_mock.call_count)


if __name__ == '__main__':
  test_case.main()
