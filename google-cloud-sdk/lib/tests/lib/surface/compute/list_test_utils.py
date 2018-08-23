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
"""Module with utils for testing lister.Invoke calls."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import copy

import sys

from googlecloudsdk.core import resources

import mock
import six


class Helper(object):
  """Helper class used by test_base.BaseTest."""

  def __init__(self):
    self.invoke_mock = None

    # Invariant: queue is empty iff invoke_replaying_mock is None
    #            otherwise invoke_replaying_mock is a started lister.Invoke mock
    self.call_queue = collections.deque()
    self.invoke_replaying_mock = None

  def Setup(self, add_cleanup):
    # Adds concept checks of lister.Invoke arguments in unit tests
    invoke_mock = mock.patch(
        'googlecloudsdk.api_lib.compute.lister.Invoke',
        new=_InvokeChecked)
    add_cleanup(invoke_mock.stop)
    self.invoke_mock = invoke_mock.start()

  def Teardown(self):
    if self.invoke_replaying_mock is not None:
      self.invoke_replaying_mock.stop()
      # Note: this replaces active exception (if present)
      if not sys.exc_info():
        raise AssertionError('Expected {} more calls to lister.Invoke but '
                             'unit test finished'.format(len(self.call_queue)))

  def ExpectListerInvoke(self, scope_set, filter_expr, max_results, result,
                         with_implementation):
    self._SetupInvokeForReplaying()
    self.call_queue.append(
        copy.deepcopy((scope_set, filter_expr, max_results, result,
                       with_implementation)))

  def _SetupInvokeForReplaying(self):
    if self.call_queue:
      return
    self.invoke_replaying_mock = mock.patch(
        'googlecloudsdk.api_lib.compute.lister.Invoke',
        new=self._InvokeReplaying)
    self.invoke_replaying_mock.start()

  def _InvokeReplaying(self, frontend, implementation):
    """lister.Invoke variant replaying recorded scenario."""
    _ImplementationConceptCheck(implementation)
    _FrontendConceptCheck(frontend)

    # Invariant: self.call_queue is not empty
    (scope_set, filter_expr, max_results, result,
     with_implementation) = self.call_queue.popleft()
    if not self.call_queue:
      self.invoke_replaying_mock.stop()
      self.invoke_replaying_mock = None

    if frontend.filter != filter_expr:
      raise AssertionError('frontend.filter is "{}", expected "{}"'.format(
          frontend.filter, filter_expr))
    if frontend.max_results != max_results:
      raise AssertionError('frontend.max_results is {}, expected {}'.format(
          frontend.max_results, max_results))
    if (with_implementation is not None and
        with_implementation != implementation):
      raise AssertionError('implementation is {}, expected {}'.format(
          implementation, with_implementation))
    _CheckScopeSet(frontend.scope_set, scope_set)
    return result


def _InvokeChecked(frontend, implementation):
  _ImplementationConceptCheck(implementation)
  _FrontendConceptCheck(frontend)

  return implementation(frontend)


def _ImplementationConceptCheck(implementation):
  if not callable(implementation):
    raise AssertionError('Implementation must be callable')


def _FrontendConceptCheck(frontend):
  """Checks if given object is a valid frontend."""
  sentinel = object()
  if not isinstance(
      getattr(frontend, 'filter', sentinel), (type(None), six.string_types)):
    raise AssertionError(
        'frontend must have filter property of type str or None')
  if not isinstance(getattr(frontend, 'max_results', None), (type(None), int)):
    raise AssertionError(
        'frontend must have max_results property of type int or None')
  scope_set = getattr(frontend, 'scope_set', sentinel)
  if scope_set is sentinel:
    raise AssertionError('frontend must have scope_set property')

  if getattr(scope_set, 'projects', sentinel) != sentinel:
    _AllScopesConceptCheck(scope_set)
  else:
    _ScopeSetConceptCheck(scope_set)


def _AllScopesConceptCheck(all_scopes):
  """Checks if given object is a valid AllScopes object."""
  if not isinstance(getattr(all_scopes, 'zonal', None), bool):
    raise AssertionError('frontend.scope_set of type AllScopes must have '
                         'zonal property of type bool')
  if not isinstance(getattr(all_scopes, 'regional', None), bool):
    raise AssertionError('frontend.scope_set of type AllScopes must have '
                         'regional property of type bool')
  try:
    projects = [p for p in all_scopes.projects]
  except TypeError:
    raise AssertionError('frontend.scope_set of type AllScopes must have '
                         'iterable projects property')
  for p in projects:
    if not isinstance(p, resources.Resource):
      raise AssertionError(
          'All projects must be of type Resource, got: {}'.format(type(p)))
    if p.Collection() != 'compute.projects':
      raise AssertionError(
          'All projects should have compute.projects collection')


def _ScopeSetConceptCheck(scope_set):
  """Checks if given object is a valid GlobalScope, ZoneSet or RegionSet."""
  try:
    scope_list = [s for s in scope_set]
  except TypeError:
    raise AssertionError('frontend.scope_set must be iterable or AllScopes')

  collection_set = set()
  for s in scope_list:
    if not isinstance(s, resources.Resource):
      raise AssertionError(
          'All elements of scope_set must be of type Resource, got: {}'.format(
              type(s)))
    collection_set.add(s.Collection())

  if len(collection_set) > 1:
    raise AssertionError('All elements in scope_set must have the same '
                         'resource collection, got: {}'.format(collection_set))
  if (collection_set and 'compute.projects' not in collection_set and
      'compute.zones' not in collection_set and
      'compute.regions' not in collection_set):
    raise AssertionError(
        'All elements in scope_set must have collection '
        'compute.projects or compute.zones or '
        'compute.regions, got: {}'.format(collection_set.pop()))


def _CheckScopeSet(actual_scope_set, expected_scope_set):
  sentinel = object()
  if getattr(actual_scope_set, 'projects', sentinel) != sentinel:
    if getattr(expected_scope_set, 'projects', sentinel) == sentinel:
      raise AssertionError(
          'frontend.scope_set has type AllScopes but expected {}'.format(
              _GetScopeSetType(expected_scope_set)))
    list_actual_projects = sorted([p for p in actual_scope_set.projects])
    list_expected_projects = sorted(list(expected_scope_set.projects))
    if list_actual_projects != list_expected_projects:
      raise AssertionError(
          'frontend.scope_set.projects is [{}]\nexpected [{}]'.format(
              '\n\t'.join([p.SelfLink() for p in list_actual_projects]),
              '\n\t'.join([p.SelfLink() for p in list_expected_projects])))
    if actual_scope_set.zonal != expected_scope_set.zonal:
      raise AssertionError('frontend.scope_set.zonal is {} expected {}'.format(
          actual_scope_set.zonal, expected_scope_set.zonal))
    if actual_scope_set.regional != expected_scope_set.regional:
      raise AssertionError(
          'frontend.scope_set.regional is {} expected {}'.format(
              actual_scope_set.regional, expected_scope_set.regional))
  else:
    if getattr(expected_scope_set, 'projects', sentinel) != sentinel:
      raise AssertionError(
          'frontend.scope_set has type {} but expected AllScopes'.format(
              _GetScopeSetType(actual_scope_set)))
    list_actual_scope_set = sorted(list(actual_scope_set))
    list_expected_scope_set = sorted(list(expected_scope_set))
    if list_actual_scope_set != list_expected_scope_set:
      raise AssertionError('fronted.scope_set is [{}]\nexpected [{}]'.format(
          '\n\t'.join([p.SelfLink() for p in list_actual_scope_set]),
          '\n\t'.join([p.SelfLink() for p in list_expected_scope_set])))


def _GetScopeSetType(scope_set):
  """Returns human-readable type of given scope set."""
  # Precondition:
  # scope_set is valid AllScopes, ZoneSet, RegionSet or GlobalScope
  sentinel = object()
  if getattr(scope_set, 'projects', sentinel) != sentinel:
    return 'AllScopes'
  list_scope_set = list(scope_set)
  if not list_scope_set:
    return '*Set'
  if list_scope_set[0].Collection() == 'compute.projects':
    return 'GlobalScope'
  if list_scope_set[0].Collection() == 'compute.zones':
    return 'ZoneSet'
  if list_scope_set[0].Collection() == 'compute.regions':
    return 'RegionSet'
