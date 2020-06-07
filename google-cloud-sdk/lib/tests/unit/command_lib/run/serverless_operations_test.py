# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Tests of the Serverless API Client."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import datetime
import functools
from apitools.base.protorpclite import messages
from apitools.base.py import exceptions as api_exceptions
from googlecloudsdk.api_lib.run import condition
from googlecloudsdk.api_lib.run import configuration
from googlecloudsdk.api_lib.run import domain_mapping
from googlecloudsdk.api_lib.run import k8s_object
from googlecloudsdk.api_lib.run import revision
from googlecloudsdk.api_lib.run import service
from googlecloudsdk.api_lib.services import enable_api
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.command_lib.run import config_changes
from googlecloudsdk.command_lib.run import exceptions as serverless_exceptions
from googlecloudsdk.command_lib.run import name_generator
from googlecloudsdk.command_lib.run import serverless_operations
from googlecloudsdk.command_lib.run import stages
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import config
from googlecloudsdk.core import exceptions
from googlecloudsdk.core.console import progress_tracker
from googlecloudsdk.core.resource import resource_lex
from googlecloudsdk.core.util import retry
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.run import base

import mock as unittest_mock


_FAKE_MANIFEST = {
    'server.js': {
        'sourceUrl': 'https://storage.googleapis.com/serversource',
        'sha1Sum': 'dab488784477c82618c17cbfa08a506fc6842580'
    }
}

_FAKE_APP_ENGINE_JSON = {
    'deployment': {
        'files': _FAKE_MANIFEST
    },
    'handlers': [{
        'script': {
            'scriptPath': 'server.js'
        },
        'securityLevel': 'SECURE_OPTIONAL',
        'urlRegex': '/.*'
    }],
    'id': 'current',
    'runtime': 'nodejs8',
    'threadsafe': True
}


_Cond = collections.namedtuple(
    '_Cond', ['type', 'status', 'message', 'reason', 'severity'])


class _FakeResource(object):

  def __init__(self, conditions):
    self.conditions = conditions


def _Stagify(keys):
  return [progress_tracker.Stage(k) for k in keys]


def _MakeMockTracker(stage_names):
  tracker = progress_tracker.NoOpStagedProgressTracker(_Stagify(stage_names))
  ret = unittest_mock.Mock(wraps=tracker)
  # HACK: Mock isn't iterable, even if it's wrapping an iterable thing. Give it
  # the iterable nature explicitly.
  ret.__iter__ = lambda _: iter(tracker)
  return ret


class ConditionPollerTest(test_case.TestCase):
  """Tests for the ConditionPoller class itself.

  Mostly to be sure we update the progress tracker right.
  """

  def _ResourceGetter(self):
    """Use self.conditions_series as a basis for a series of FakeResources."""
    return _FakeResource(next(self.conditions_series))

  def _ResetMockTracker(self, mocked_tracker):
    """Reset the mock of all relevant methods on the mocked tracker."""
    mocked_tracker.StartStage.reset_mock()
    mocked_tracker.CompleteStage.reset_mock()
    mocked_tracker.FailStage.reset_mock()
    mocked_tracker.UpdateHeaderMessage.reset_mock()

  def testTwoConditionsSuccess(self):
    """Test the normal path of going from unknown to done, no deps."""
    tracker = _MakeMockTracker(['one', 'two'])
    # Condition one goes to True immediately.
    # Condition two goes from Unknown to True, along with Ready
    self.conditions_series = iter([
        condition.Conditions([
            _Cond('Ready', 'Unknown', 'Not yet', '', None),
            _Cond('one', 'True', None, None, None),
            _Cond('two', 'Unknown', 'Not yet', '', None),
        ], ready_condition='Ready'),
        condition.Conditions([
            _Cond('Ready', 'True', None, None, None),
            _Cond('one', 'True', None, None, None),
            _Cond('two', 'True', None, None, None),
        ], ready_condition='Ready')])
    poller = serverless_operations.ConditionPoller(
        self._ResourceGetter, tracker)
    tracker.StartStage.assert_any_call('one')
    tracker.StartStage.assert_any_call('two')
    self.assertEqual(tracker.StartStage.call_count, 2)
    tracker.CompleteStage.assert_not_called()
    self._ResetMockTracker(tracker)
    poller.Poll(None)
    tracker.StartStage.assert_not_called()
    tracker.CompleteStage.assert_called_once_with('one', None)
    self._ResetMockTracker(tracker)
    poller.Poll(None)
    tracker.CompleteStage.assert_called_once_with('two', None)
    tracker.UpdateHeaderMessage.assert_any_call('Done.')

  def testTwoConditionsFailure(self):
    """Test showing failures right."""
    tracker = _MakeMockTracker(['one', 'two'])
    # Condition one goes to True immediately.
    # Condition two goes from Unknown to False, along with Ready
    self.conditions_series = iter([
        condition.Conditions([
            _Cond('Ready', 'Unknown', 'Not yet', '', None),
            _Cond('one', 'True', None, None, None),
            _Cond('two', 'Unknown', 'Not yet', '', None),
        ], ready_condition='Ready'),
        condition.Conditions([
            _Cond('Ready', 'False', 'Oops.', '', None),
            _Cond('one', 'True', None, None, None),
            _Cond('two', 'False', 'Oops.', '', None),
        ], ready_condition='Ready')])
    poller = serverless_operations.ConditionPoller(
        self._ResourceGetter, tracker)
    tracker.StartStage.assert_any_call('one')
    tracker.StartStage.assert_any_call('two')
    self.assertEqual(tracker.StartStage.call_count, 2)
    tracker.CompleteStage.assert_not_called()
    self._ResetMockTracker(tracker)
    poller.Poll(None)
    tracker.StartStage.assert_not_called()
    tracker.CompleteStage.assert_called_once_with('one', None)
    tracker.FailStage.assert_not_called()
    self._ResetMockTracker(tracker)
    with self.assertRaises(exceptions.Error):
      poller.Poll(None)
    tracker.FailStage.assert_called_once()
    tracker.UpdateHeaderMessage.assert_any_call('Oops.')

  def testTwoConditionsSuccessWithDeps(self):
    """Test when one stage is dependent on another to start."""
    tracker = _MakeMockTracker(['one', 'two'])
    # Make sure condition two doesn't Start until condition One is marked True
    self.conditions_series = iter([
        condition.Conditions([
            _Cond('Ready', 'Unknown', 'Not yet', '', None),
            _Cond('one', 'True', None, None, None),
            _Cond('two', 'Unknown', 'Not yet', '', None),
        ], ready_condition='Ready'),
        condition.Conditions([
            _Cond('Ready', 'True', None, None, None),
            _Cond('one', 'True', None, None, None),
            _Cond('two', 'True', None, None, None),
        ], ready_condition='Ready')])
    poller = serverless_operations.ConditionPoller(
        self._ResourceGetter, tracker,
        dependencies={'two': {'one'}})
    tracker.StartStage.assert_called_once_with('one')
    tracker.CompleteStage.assert_not_called()
    self._ResetMockTracker(tracker)
    poller.Poll(None)
    tracker.StartStage.assert_called_once_with('two')
    tracker.CompleteStage.assert_called_once_with('one', None)
    self._ResetMockTracker(tracker)
    poller.Poll(None)
    tracker.CompleteStage.assert_called_once_with('two', None)
    tracker.UpdateHeaderMessage.assert_any_call('Done.')

  def testTwoConditionsSuccessWithDepsOutOfOrder(self):
    """Test when one stage is dependent on another to start.

    In this case, test that the stages are all still tracked correctly even
    if they are completed outside of the dependency ordering.
    """
    tracker = _MakeMockTracker(['one', 'two'])
    # Make sure condition two doesn't Start until condition one is marked True
    self.conditions_series = iter([
        condition.Conditions([
            _Cond('Ready', 'Unknown', 'Not yet', '', None),
            _Cond('one', 'Unknown', 'Not yet', '', None),
            _Cond('two', 'True', None, None, None),
        ], ready_condition='Ready'),
        condition.Conditions([
            _Cond('Ready', 'True', None, None, None),
            _Cond('one', 'True', None, None, None),
            _Cond('two', 'True', None, None, None),
        ], ready_condition='Ready')])
    poller = serverless_operations.ConditionPoller(
        self._ResourceGetter, tracker,
        dependencies={'two': {'one'}})
    tracker.StartStage.assert_called_once_with('one')
    tracker.CompleteStage.assert_not_called()
    self._ResetMockTracker(tracker)
    poller.Poll(None)
    tracker.CompleteStage.assert_not_called()
    self._ResetMockTracker(tracker)
    poller.Poll(None)
    tracker.StartStage.assert_called_once_with('two')
    tracker.CompleteStage.assert_any_call('one', None)
    tracker.CompleteStage.assert_any_call('two', None)
    tracker.UpdateHeaderMessage.assert_any_call('Done.')

  def testDontStartTilUnblockedPrevTrue(self):
    """One stage dependent on another to start, and True before that happens."""
    tracker = _MakeMockTracker(['one', 'two'])
    # Condition one goes Unknown -> True -> True
    # Condition two goes True -> Unknown -> True
    # Because of the dependencies, two should not Start until the second poll.
    self.conditions_series = iter([
        condition.Conditions([
            _Cond('Ready', 'Unknown', 'Not yet', '', None),
            _Cond('one', 'Unknown', 'Not yet', '', None),
            _Cond('two', 'True', None, None, None),
        ], ready_condition='Ready'),
        condition.Conditions([
            _Cond('Ready', 'Unknown', 'Not yet.', None, None),
            _Cond('one', 'True', None, None, None),
            _Cond('two', 'Unknown', 'Working.', None, None),
        ], ready_condition='Ready'),
        condition.Conditions([
            _Cond('Ready', 'True', None, None, None),
            _Cond('one', 'True', None, None, None),
            _Cond('two', 'True', None, None, None),
        ], ready_condition='Ready')])
    poller = serverless_operations.ConditionPoller(
        self._ResourceGetter, tracker, dependencies={
            'two': {'one'},
            'one': set(),
        })
    tracker.StartStage.assert_called_once_with('one')
    tracker.CompleteStage.assert_not_called()
    self._ResetMockTracker(tracker)
    poller.Poll(None)
    tracker.StartStage.assert_not_called()
    tracker.CompleteStage.assert_not_called()
    self._ResetMockTracker(tracker)
    poller.Poll(None)
    tracker.StartStage.assert_called_once_with('two')
    tracker.CompleteStage.assert_called_once_with('one', None)
    self._ResetMockTracker(tracker)
    poller.Poll(None)
    tracker.CompleteStage.assert_called_once_with('two', None)
    tracker.UpdateHeaderMessage.assert_any_call('Done.')

  def testNotDoneTilReady(self):
    """Update top line to "Done." only when we are Ready."""
    tracker = _MakeMockTracker(['one', 'two'])
    # Ready spends the first round at Unknown while both conditions are True.
    self.conditions_series = iter([
        condition.Conditions([
            _Cond('Ready', 'Unknown', 'Not yet.', None, None),
            _Cond('one', 'True', None, None, None),
            _Cond('two', 'True', None, None, None),
        ], ready_condition='Ready'),
        condition.Conditions([
            _Cond('Ready', 'True', None, None, None),
            _Cond('one', 'True', None, None, None),
            _Cond('two', 'True', None, None, None),
        ], ready_condition='Ready')])
    poller = serverless_operations.ConditionPoller(
        self._ResourceGetter, tracker)
    tracker.StartStage.assert_any_call('one')
    tracker.StartStage.assert_any_call('two')
    self.assertEqual(tracker.StartStage.call_count, 2)
    self._ResetMockTracker(tracker)
    poller.Poll(None)
    tracker.CompleteStage.assert_any_call('one', None)
    tracker.CompleteStage.assert_any_call('two', None)
    self.assertEqual(tracker.CompleteStage.call_count, 2)
    tracker.UpdateHeaderMessage.assert_called_once_with('Not yet.')
    self._ResetMockTracker(tracker)
    poller.Poll(None)
    tracker.UpdateHeaderMessage.assert_called_once_with('Done.')

  def testStagesNotBlockedByCompletedStages(self):
    """Test when one stage is dependent on another to start.

    In this case, test that the dependent stage is started immediately if the
    stage its waiting on is already complete where initializing the poller.
    """
    tracker = _MakeMockTracker(['one', 'two'])
    # Condition one completes early, outside the poller
    tracker.CompleteStage('one')
    self._ResetMockTracker(tracker)
    # Make sure condition two starts immediately
    self.conditions_series = iter([
        condition.Conditions([
            _Cond('Ready', 'Unknown', 'Not yet', '', None),
            _Cond('one', 'True', None, None, None),
            _Cond('two', 'Unknown', 'Not yet', '', None),
        ], ready_condition='Ready'),
        condition.Conditions([
            _Cond('Ready', 'True', None, None, None),
            _Cond('one', 'True', None, None, None),
            _Cond('two', 'True', None, None, None),
        ], ready_condition='Ready')])
    poller = serverless_operations.ConditionPoller(
        self._ResourceGetter, tracker,
        dependencies={'two': {'one'}})
    tracker.StartStage.assert_called_once_with('two')
    tracker.CompleteStage.assert_not_called()
    self._ResetMockTracker(tracker)
    poller.Poll(None)
    tracker.CompleteStage.assert_not_called()
    self._ResetMockTracker(tracker)
    poller.Poll(None)
    tracker.CompleteStage.assert_any_call('two', None)
    tracker.UpdateHeaderMessage.assert_any_call('Done.')


class ServiceConditionPollerGetIfProbablyNewerTest(base.ServerlessBase):
  """Tests for ServiceConditionPoller's GetIfProbablyNewer."""

  _tracker = _MakeMockTracker(['one', 'two'])

  def _NewService(self, last_transition_time):
    metadata = k8s_object.MakeMeta(self.serverless_messages)
    conditions = [self.serverless_messages.GoogleCloudRunV1Condition(
        lastTransitionTime=last_transition_time, status='True', type=u'Ready')]
    status = self.serverless_messages.ServiceStatus(conditions=conditions)
    serv = self.serverless_messages.Service(
        apiVersion='1', metadata=metadata, status=status)
    return service.Service(serv, self.serverless_messages)

  def testServiceNotFound(self):
    getter = lambda: None
    with unittest_mock.patch.object(
        stages, 'ServiceDependencies', side_effect=None):
      poller = serverless_operations.ServiceConditionPoller(
          getter, self._tracker, None)
      self.assertIsNone(poller.GetConditions())

  def testNotChanged(self):
    orig = self._NewService('2019-07-23T20:10:11Z')
    getter = lambda: orig
    poller = serverless_operations.ServiceConditionPoller(
        getter, self._tracker, dependencies=None, serv=orig)
    self.assertIsNone(poller.GetConditions())

  def testChanged(self):
    orig = self._NewService('2019-07-23T20:10:11Z')
    changed = self._NewService('2019-07-23T20:10:12Z')
    getter = lambda: changed
    poller = serverless_operations.ServiceConditionPoller(
        getter, self._tracker, dependencies=None, serv=orig)
    self.assertEqual(changed.conditions, poller.GetConditions())

  def testSixSeconds(self):
    orig = self._NewService('2019-07-23T20:10:11Z')
    getter = lambda: orig
    with unittest_mock.patch.object(
        serverless_operations.ServiceConditionPoller,
        'HaveFiveSecondsPassed', side_effect=[True]):

      poller = serverless_operations.ServiceConditionPoller(
          getter, self._tracker, serv=orig)
      self.assertEqual(orig.conditions, poller.GetConditions())


class ServerlessConfigurationWaitTest(base.ServerlessBase):
  """Tests for polling and waiting for updating configuration."""

  def SetUp(self):
    self.cond_class = self.serverless_messages.GoogleCloudRunV1Condition
    self.poller_class = serverless_operations.ConditionPoller
    self.readiness_type = configuration.Configuration.READY_CONDITION
    self.orig_timeout = serverless_operations.MAX_WAIT_MS
    serverless_operations.MAX_WAIT_MS = 5000  # smaller timeout for faster test

  def _MockPoller(self):
    return serverless_operations.ConditionPoller(
        unittest_mock.Mock,
        _MakeMockTracker([
            stages.SERVICE_CONFIGURATIONS_READY,
            stages.SERVICE_ROUTES_READY]))

  def TearDown(self):
    serverless_operations.MAX_WAIT_MS = self.orig_timeout

  def testWaitSuccess(self):
    """Test the happy path of a wait."""
    pending_cond = condition.Conditions(
        [self.cond_class(type=self.readiness_type, status='Unknown')],
        ready_condition=self.readiness_type,
    )
    terminal_cond = condition.Conditions(
        [self.cond_class(type=self.readiness_type, status='True')],
        ready_condition=self.readiness_type,
    )
    with unittest_mock.patch.object(
        self.poller_class, 'GetConditions',
        side_effect=[pending_cond, terminal_cond]):
      self.serverless_client.WaitForCondition(self._MockPoller())
      self.assertEqual(2, self.poller_class.GetConditions.call_count)

  def testWaitNoneGuard(self):
    """Test waiting guards against no object to wait on."""
    pending_cond = None
    terminal_cond = condition.Conditions(
        [self.cond_class(type=self.readiness_type, status='True')],
        ready_condition=self.readiness_type,
    )
    with unittest_mock.patch.object(
        self.poller_class, 'GetConditions',
        side_effect=[pending_cond, terminal_cond]):
      self.serverless_client.WaitForCondition(self._MockPoller())
      self.assertEqual(2, self.poller_class.GetConditions.call_count)

  def testWaitFail_withReadyTypeCondition(self):
    """Test error raising with ready type condition present."""
    expected_error_message = 'Latest re failed to be ready'
    terminal_cond = condition.Conditions(
        [self.cond_class(
            type=self.readiness_type, status='False',
            message=expected_error_message)],
        ready_condition=self.readiness_type,
    )
    with unittest_mock.patch.object(
        self.poller_class, 'GetConditions', side_effect=[terminal_cond]):
      with self.assertRaisesRegexp(
          exceptions.Error,
          expected_error_message):
        self.serverless_client.WaitForCondition(self._MockPoller())

  def testWaitTimeout_WithReadyTypeCondition(self):
    """Test error of polling timeout while returning ready type condition."""
    pending_cond = condition.Conditions(
        [self.cond_class(type=self.readiness_type,
                         status='Unknown', message='This is why it fail'),
         self.cond_class(type=stages.SERVICE_CONFIGURATIONS_READY,
                         status='False')],
        ready_condition=self.readiness_type)
    with unittest_mock.patch.object(
        self.poller_class, 'GetConditions', side_effect=[pending_cond] * 4):
      with self.assertRaises(exceptions.Error):
        self.serverless_client.WaitForCondition(self._MockPoller())

  def testWaitTimeout_WithNoService(self):
    """Test error of polling timeout while returning no Service."""
    self.StartObjectPatch(
        waiter, 'PollUntilDone',
        side_effect=retry.WaitException(None, None, None))
    with unittest_mock.patch.object(
        self.poller_class, 'GetConditions', return_value=None):
      with self.assertRaises(retry.WaitException):
        self.serverless_client.WaitForCondition(self._MockPoller())


class ServerlessOperationsTest(base.ServerlessBase, parameterized.TestCase):

  def SetUp(self):
    # Mock enabling services
    self.enable_mock = self.StartObjectPatch(enable_api, 'EnableService')
    self.nonce = 'itsthenoncelol'
    self.revision_suffix = 'myrevision'
    self.StartObjectPatch(
        name_generator, 'GenerateName', return_value=self.revision_suffix)
    self.serverless_client.WaitForCondition = unittest_mock.Mock()
    dummy_config = configuration.Configuration.New(self.mock_serverless_client,
                                                   self.Project())
    self.fake_image = 'gcr.io/my-image'
    self.fake_deployable = config_changes.ImageChange(self.fake_image)
    self.old_gcloud_version = config.CLOUD_SDK_VERSION
    config.CLOUD_SDK_VERSION = 'test_version'
    self.poller = self.StartObjectPatch(
        serverless_operations, 'ServiceConditionPoller')
    self.poller.GetConditions.return_value = condition.Conditions([])
    # Prevent timeouts from tests running slowly
    self.StartObjectPatch(retry.Retryer, '_GetTimeToWait', return_value=0)

  def TearDown(self):
    config.CLOUD_SDK_VERSION = self.old_gcloud_version

  def _ExpectRevisionsList(self, serv_name, limit, cont, ret_cont):
    """List call for two revisions against the Serverless API."""

    request = (
        self.
        serverless_messages.RunNamespacesRevisionsListRequest(
            parent=self.namespace.RelativeName(),
            labelSelector='serving.knative.dev/service = {}'.format(
                serv_name),
        ))
    if cont is not None:
      request.continue_ = cont
    if limit is not None:
      request.limit = limit
    else:
      request.limit = 100

    def _GetLabels():
      return k8s_object.Meta(self.serverless_messages).LabelsValue(
          additionalProperties=[
              k8s_object.Meta(self.serverless_messages).LabelsValue.
              AdditionalProperty(key='serving.knative.dev/service', value='s1')
          ])

    def _GetMetadata(i):
      return k8s_object.MakeMeta(
          self.serverless_messages,
          name='r{}'.format(i),
          creationTimestamp=datetime.datetime.utcfromtimestamp(i).isoformat() +
          'Z',
          labels=_GetLabels())

    revisions_responses = self.serverless_messages.ListRevisionsResponse(
        items=[
            self.serverless_messages.Revision(metadata=_GetMetadata(i))
            for i in range(2)
        ],
        metadata=k8s_object.ListMeta(self.serverless_messages)())
    if ret_cont is not None:
      revisions_responses.metadata.continue_ = ret_cont

    self.mock_serverless_client.namespaces_revisions.List.Expect(
        request, response=revisions_responses)

  def _DeleteResponse(self):
    return self.serverless_messages.Status()

  def testListServices(self):
    """Test the list services api call."""
    expected_request = (
        self.serverless_messages.RunNamespacesServicesListRequest(
            parent='namespaces/{}'.format(self.namespace.namespacesId)))

    expected_response = self.serverless_messages.ListServicesResponse(
        items=[self.serverless_messages.Service(apiVersion='1')])
    self.mock_serverless_client.namespaces_services.List.Expect(
        expected_request, expected_response)

    services = self.serverless_client.ListServices(self.namespace)

    self.assertListEqual(
        [s.Message() for s in services],
        [self.serverless_messages.Service(apiVersion='1')])

  def testDeleteService(self):
    """Test the delete services api call."""
    expected_request = (
        self.serverless_messages.RunNamespacesServicesDeleteRequest(
            name=self._ServiceRef('s1').RelativeName()))

    expected_response = self._DeleteResponse()
    self.mock_serverless_client.namespaces_services.Delete.Expect(
        expected_request, expected_response)

    delete_response = self.serverless_client.DeleteService(
        self._ServiceRef('s1'))

    self.assertIsNone(delete_response)

  def testDeleteServiceNotFound(self):
    """Test the delete services api call with a non-existent service name."""
    expected_request = (
        self.serverless_messages.RunNamespacesServicesDeleteRequest(
            name=self._ServiceRef('s1').RelativeName()))

    self.mock_serverless_client.namespaces_services.Delete.Expect(
        expected_request,
        exception=api_exceptions.HttpNotFoundError(None, None, None))

    with self.assertRaises(serverless_exceptions.ServiceNotFoundError):
      self.serverless_client.DeleteService(self._ServiceRef('s1'))

  def testListRevisions(self):
    """Test the list revisions call against the Serverless API."""
    self._ExpectRevisionsList('default', None, None, None)
    revisions = list(self.serverless_client.ListRevisions(
        self.namespace, 'default'))

    self.assertEqual(revisions[0].metadata.name, 'r0')
    self.assertEqual(revisions[1].metadata.name, 'r1')

  def testListRevisionsCont(self):
    """Test the list revisions call against the Serverless API."""
    self._ExpectRevisionsList('default', 2, None, 'bar')
    self._ExpectRevisionsList('default', 2, 'bar', None)
    revisions = list(self.serverless_client.ListRevisions(
        self.namespace, 'default', None, 2))
    self.assertEqual(len(revisions), 4)

    self.assertEqual(revisions[0].metadata.name, 'r0')
    self.assertEqual(revisions[1].metadata.name, 'r1')

  def testListRevisionsLimit(self):
    """Test the list revisions call against the Serverless API."""
    self._ExpectRevisionsList('default', 2, None, 'bar')
    revisions = list(self.serverless_client.ListRevisions(
        self.namespace, 'default', 2, 2))
    self.assertEqual(len(revisions), 2)

    self.assertEqual(revisions[0].metadata.name, 'r0')
    self.assertEqual(revisions[1].metadata.name, 'r1')

  def testDeleteRevision(self):
    """Test the delete revision api call."""
    revision_ref = self._RevisionRef('r0')
    expected_request = (
        self.serverless_messages.RunNamespacesRevisionsDeleteRequest(
            name=revision_ref.RelativeName()))

    expected_response = self._DeleteResponse()
    self.mock_serverless_client.namespaces_revisions.Delete.Expect(
        expected_request, expected_response)

    delete_response = self.serverless_client.DeleteRevision(revision_ref)

    self.assertEqual(delete_response, None)

  def testDeleteRevisionNotFound(self):
    """Test the delete revision api call with a non-existent revision name."""
    revision_ref = self._RevisionRef('r0')
    expected_request = (
        self.serverless_messages.RunNamespacesRevisionsDeleteRequest(
            name=revision_ref.RelativeName()))
    self.mock_serverless_client.namespaces_revisions.Delete.Expect(
        expected_request,
        exception=api_exceptions.HttpNotFoundError(None, None, None))
    with self.assertRaises(serverless_exceptions.RevisionNotFoundError):
      self.serverless_client.DeleteRevision(revision_ref)

  def testReleaseServiceFresh(self):
    """Test the release flow for a new service."""
    fake_deployable = config_changes.ImageChange('gcr.io/fakething')
    self._ExpectCreate(
        image='gcr.io/fakething',
        annotations={
            revision.USER_IMAGE_ANNOTATION: 'gcr.io/fakething'})

    self.serverless_client.ReleaseService(
        self._ServiceRef('foo'),
        [fake_deployable])

  def testReleaseServiceFreshPrefetch(self):
    """Test the release flow for a new service."""
    fake_deployable = config_changes.ImageChange('gcr.io/fakething')
    self._ExpectCreate(
        image='gcr.io/fakething',
        annotations={
            revision.USER_IMAGE_ANNOTATION: 'gcr.io/fakething'})
    ref = self._ServiceRef('foo')
    self.serverless_client.ReleaseService(
        ref,
        [fake_deployable], prefetch=self.serverless_client.GetService(ref))

  def testReleaseServiceAllowUnauthenticatedNew(self):
    """Test the release flow for a new service with unauthenticated access."""
    fake_deployable = config_changes.ImageChange('gcr.io/fakething')
    self._ExpectCreate(
        image='gcr.io/fakething',
        annotations={
            revision.USER_IMAGE_ANNOTATION: 'gcr.io/fakething'})
    self._ExpectGetIamPolicy('foo', bindings=[])
    binding = self.serverless_messages.Binding(
        members=['allUsers'], role='roles/run.invoker')
    self._ExpectSetIamPolicy(service='foo', bindings=[binding])

    self.serverless_client.ReleaseService(
        self._ServiceRef('foo'),
        [fake_deployable],
        allow_unauthenticated=True)

  def testReleaseServiceAllowUnauthenticatedRemoval(self):
    """Test the release flow for removing unauthenticated access from a service."""
    fake_deployable = config_changes.ImageChange('gcr.io/fakething')
    self._ExpectCreate(
        image='gcr.io/fakething',
        annotations={
            revision.USER_IMAGE_ANNOTATION: 'gcr.io/fakething'})
    self._ExpectGetIamPolicy('foo', bindings=[self.serverless_messages.Binding(
        members=['allUsers'], role='roles/run.invoker')])
    self._ExpectSetIamPolicy(service='foo', bindings=[])

    self.serverless_client.ReleaseService(
        self._ServiceRef('foo'),
        [fake_deployable],
        allow_unauthenticated=False)

  def testReleaseServiceAllowUnauthenticatedSetIamFail(self):
    """Test the release flow for a new service with unauthenticated access."""
    fake_deployable = config_changes.ImageChange('gcr.io/fakething')
    self._ExpectCreate(
        image='gcr.io/fakething',
        annotations={
            revision.USER_IMAGE_ANNOTATION: 'gcr.io/fakething'})
    self._ExpectGetIamPolicy('foo', bindings=[])
    binding = self.serverless_messages.Binding(
        members=['allUsers'], role='roles/run.invoker')
    self._ExpectSetIamPolicy(
        service='foo',
        bindings=[binding],
        exception=api_exceptions.HttpError(None, None, None))
    with progress_tracker.StagedProgressTracker(
        'Deloying...',
        stages.ServiceStages(True),
        failure_message='Deployment failed',
        suppress_output=False) as tracker:
      self.serverless_client.ReleaseService(
          self._ServiceRef('foo'),
          [fake_deployable],
          tracker=tracker,
          allow_unauthenticated=True)
    self.AssertErrContains('"status": "WARNING"')
    self.assertIn(
        stages.SERVICE_IAM_POLICY_SET, tracker._completed_with_warnings_stages)

  def testReleaseServiceNotFound(self):
    """Test the flow for a configuration update on a nonexistent service."""
    env_changes = config_changes.EnvVarLiteralChanges(
        env_vars_to_update=collections.OrderedDict([('key1', 'value1.2'),
                                                    ('key2', 'value2')]))
    # Expect that it does not exist.
    self.mock_serverless_client.namespaces_services.Get.Expect(
        (self.serverless_messages.
         RunNamespacesServicesGetRequest(
             name=self._ServiceRef('foo').RelativeName())),
        exception=api_exceptions.HttpNotFoundError(None, None, None),
    )
    with self.assertRaises(serverless_exceptions.ServiceNotFoundError):
      self.serverless_client.ReleaseService(
          self._ServiceRef('foo'),
          [env_changes])

  def testReleaseServicePrivateEndpointNew(self):
    """Test the flow for releasing a new service with private endpoint."""
    endpoint_change = config_changes.EndpointVisibilityChange(True)
    self._ExpectCreate(
        image=self.fake_image,
        annotations={revision.USER_IMAGE_ANNOTATION: 'gcr.io/my-image'},
        labels={service.ENDPOINT_VISIBILITY: service.CLUSTER_LOCAL})

    self.serverless_client.ReleaseService(
        self._ServiceRef('foo'), [self.fake_deployable, endpoint_change])

  def testReleaseServicePublicEndpointNew(self):
    """Test the flow for releasing a new service with public endpoint."""
    endpoint_change = config_changes.EndpointVisibilityChange(False)
    self._ExpectCreate(
        image=self.fake_image,
        annotations={
            revision.USER_IMAGE_ANNOTATION: 'gcr.io/my-image'})

    self.serverless_client.ReleaseService(
        self._ServiceRef('foo'), [self.fake_deployable, endpoint_change])

  def testReleaseServicePublicEndpoint(self):
    """Test the flow for updating a service from private to public."""
    endpoint_change = config_changes.EndpointVisibilityChange(False)
    self._ExpectExisting(
        image='gcr.io/oldthing',
        annotations={revision.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'},
        labels={service.ENDPOINT_VISIBILITY: service.CLUSTER_LOCAL})

    self._ExpectBaseRevision(
        image='gcr.io/oldthing',
        imageDigest='gcr.io/newthing@sha256:abcdef',
        annotations={revision.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'})

    self._ExpectUpdate(
        image='gcr.io/newthing@sha256:abcdef',
        annotations={revision.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'})

    self.serverless_client.ReleaseService(
        self._ServiceRef('foo'), [endpoint_change])

  def testReleaseServicePrivateEndpoint(self):
    """Test the flow for updating a service from public to private."""
    endpoint_change = config_changes.EndpointVisibilityChange(True)
    self._ExpectExisting(
        image='gcr.io/my-image',
        annotations={
            revision.USER_IMAGE_ANNOTATION: 'gcr.io/my-image'})

    self._ExpectBaseRevision(
        image='gcr.io/oldthing',
        imageDigest='gcr.io/newthing@sha256:abcdef',
        annotations={revision.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'})

    self._ExpectUpdate(
        image='gcr.io/newthing@sha256:abcdef',
        annotations={revision.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'},
        labels={service.ENDPOINT_VISIBILITY: service.CLUSTER_LOCAL})

    self.serverless_client.ReleaseService(
        self._ServiceRef('foo'), [endpoint_change])

  def testUpdateEnvVars(self):
    """Test updating existing and create new env vars on an existing service."""
    self._ExpectExisting(
        image='gcr.io/oldthing',
        annotations={revision.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'},
        **{'template.env_vars.literals': {'key1': 'value1'}})
    self._ExpectBaseRevision(
        image='gcr.io/oldthing',
        imageDigest='gcr.io/newthing@sha256:abcdef',
        annotations={revision.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'})

    self._ExpectUpdate(
        image='gcr.io/newthing@sha256:abcdef',
        annotations={revision.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'},
        **{'template.env_vars.literals': collections.OrderedDict(
            [('key1', 'value1.2'), ('key2', 'value2')])})

    env_changes = config_changes.EnvVarLiteralChanges(
        env_vars_to_update=collections.OrderedDict([('key1', 'value1.2'),
                                                    ('key2', 'value2')]))
    self.serverless_client.ReleaseService(
        self._ServiceRef('foo'),
        [env_changes])

  def testUpdateEnvVarsPrefetch(self):
    """Test updating existing and create new env vars on an existing service."""
    self._ExpectExisting(
        image='gcr.io/oldthing',
        annotations={revision.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'},
        **{'template.env_vars.literals': {'key1': 'value1'}})
    self._ExpectBaseRevision(
        image='gcr.io/oldthing',
        imageDigest='gcr.io/newthing@sha256:abcdef',
        annotations={revision.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'})

    self._ExpectUpdate(
        image='gcr.io/newthing@sha256:abcdef',
        annotations={revision.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'},
        **{'template.env_vars.literals': collections.OrderedDict(
            [('key1', 'value1.2'), ('key2', 'value2')])})

    env_changes = config_changes.EnvVarLiteralChanges(
        env_vars_to_update=collections.OrderedDict([('key1', 'value1.2'),
                                                    ('key2', 'value2')]))
    ref = self._ServiceRef('foo')
    self.serverless_client.ReleaseService(
        ref,
        [env_changes], prefetch=self.serverless_client.GetService(ref))

  def testRemoveEnvVars(self):
    """Test removing env vars from an existing service.

    This tests that removing an existing env var actually works, and that
    attempting to remove a non-existent env var doesn't cause the entire
    command to fail.
    """
    self._ExpectExisting(
        image='gcr.io/oldthing',
        **{'template.env_vars.literals': collections.OrderedDict([
            ('key-to-delete', 'value1'), ('key-to-preserve', 'value1')])})
    self._ExpectBaseRevision(
        image='gcr.io/oldthing',
        imageDigest='gcr.io/newthing@sha256:abcdef',
        annotations={revision.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'})

    self._ExpectUpdate(
        image='gcr.io/newthing@sha256:abcdef',
        annotations={revision.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'},
        **{'template.env_vars.literals': collections.OrderedDict(
            [('key-to-preserve', 'value1')])})

    env_changes = config_changes.EnvVarLiteralChanges(
        env_vars_to_remove=['key-to-delete', 'dummy-key-should-be-ignored'])
    self.serverless_client.ReleaseService(
        self._ServiceRef('foo'),
        [env_changes])

  def testReleaseServiceAddRevisionName(self):
    self._ExpectExisting(
        name='foo',
        revision_name=None,
        image='gcr.io/oldthing',
        latestCreatedRevisionName='foo-old',
        annotations={revision.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'})
    self._ExpectBaseRevision(
        name_polls=0,
        name=None,
        latestCreatedRevisionName='foo-old',
        image='gcr.io/oldthing',
        imageDigest='gcr.io/newthing@sha256:abcdef',
        annotations={revision.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'})
    self._ExpectUpdate(
        name='foo',
        revision_name='foo-v2',
        image='gcr.io/newthing@sha256:abcdef',
        latestCreatedRevisionName='foo-old',
        annotations={revision.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'})
    revision_name_changes = config_changes.RevisionNameChanges('v2')
    self.serverless_client.ReleaseService(
        self._ServiceRef('foo'),
        [revision_name_changes])

  def testReleaseServiceUpdateRevisionName(self):
    self._ExpectExisting(
        name='foo',
        revision_name='foo-v1',
        image='gcr.io/oldthing',
        annotations={revision.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'})
    self._ExpectBaseRevision(
        name='foo-v1',
        image='gcr.io/oldthing',
        imageDigest='gcr.io/newthing@sha256:abcdef',
        annotations={revision.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'})
    self._ExpectUpdate(
        name='foo',
        revision_name='foo-v2',
        image='gcr.io/newthing@sha256:abcdef',
        annotations={revision.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'})
    revision_name_changes = config_changes.RevisionNameChanges('v2')
    self.serverless_client.ReleaseService(
        self._ServiceRef('foo'),
        [revision_name_changes])

  def testReleaseServiceBadImage(self):
    """Test the delete services api call with a non-existent service name."""
    fake_deployable = config_changes.ImageChange('badimage')
    self._ExpectExisting(image='gcr.io/oldthing')
    self._ExpectUpdate(
        exception=http_error.MakeDetailedHttpError(
            400,
            url='https://dummy_url.com/',
            content={
                'error': {
                    'code': 400,
                    'message': 'The request has errors.',
                    'status': 'INVALID_ARGUMENT',
                    'details': [{
                        '@type': 'type.googleapis.com/google.rpc.BadRequest',
                        'fieldViolations': [{
                            'field':
                                'spec.revisionTemplate.spec.container.image',
                            'description': 'standin error string',
                        }]}]}}),
        image='badimage',
        annotations={'client.knative.dev/user-image': 'badimage'})

    with self.assertRaisesRegexp(
        serverless_exceptions.HttpError,
        '^standin error string$'):
      self.serverless_client.ReleaseService(
          self._ServiceRef('foo'), [fake_deployable])

  def testReleaseServiceExisting(self):
    """Test the release flow when the service already exists."""

    self._ExpectExisting(
        image='gcr.io/oldthing',
        annotations={revision.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'})
    self._ExpectUpdate(
        image='gcr.io/newthing',
        annotations={revision.USER_IMAGE_ANNOTATION: 'gcr.io/newthing'})

    self.serverless_client.ReleaseService(
        self._ServiceRef('foo'),
        [config_changes.ImageChange('gcr.io/newthing')])

  def testReleaseServiceNewApi(self):
    """Test the release flow when the service already exists."""

    self._ExpectExisting(
        new_api=True,
        image='gcr.io/oldthing',
        annotations={revision.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'})
    self._ExpectUpdate(
        new_api=True,
        image='gcr.io/newthing',
        annotations={revision.USER_IMAGE_ANNOTATION: 'gcr.io/newthing'})

    self.serverless_client.ReleaseService(
        self._ServiceRef('foo'),
        [config_changes.ImageChange('gcr.io/newthing')])

  def testListDomainMappings(self):
    """Test the list domainmappings api call."""
    expected_request = (
        self.serverless_messages.RunNamespacesDomainmappingsListRequest(
            parent='namespaces/{}'.format(self.namespace.namespacesId)))
    expected_response = self.serverless_messages.ListDomainMappingsResponse(
        items=[self.serverless_messages.DomainMapping()])
    self.mock_serverless_client.namespaces_domainmappings.List.Expect(
        expected_request, expected_response)

    domainmappings = self.serverless_client.ListDomainMappings(self.namespace)
    self.assertListEqual(
        [dm.Message() for dm in domainmappings],
        [self.serverless_messages.DomainMapping()])

  def testCreateDomainMappings(self):
    """Test the create domainmappings api call."""
    new_domain_mapping = domain_mapping.DomainMapping.New(
        self.mock_serverless_client, self.namespace.namespacesId)
    new_domain_mapping.name = 'foo'
    new_domain_mapping.route_name = 'myapp'
    new_domain_mapping.force_override = False

    gotten_domain_mapping = domain_mapping.DomainMapping.New(
        self.mock_serverless_client, self.namespace.namespacesId)
    gotten_domain_mapping.name = 'foo'
    gotten_domain_mapping.route_name = 'myapp'
    gotten_domain_mapping.force_override = False
    gotten_domain_mapping.status.resourceRecords.append(
        self.serverless_messages.ResourceRecord(
            rrdata='216.239.32.21',
            type=self.serverless_messages.ResourceRecord.TypeValueValuesEnum.A))

    create_request = (
        self.serverless_messages.
        RunNamespacesDomainmappingsCreateRequest(
            parent=self.namespace.RelativeName(),
            domainMapping=new_domain_mapping.Message()))
    self.mock_serverless_client.namespaces_domainmappings.Create.Expect(
        create_request,
        response=new_domain_mapping.Message())

    domain_mapping_name = self._registry.Parse(
        'foo',
        params={'namespacesId': 'fake-project'},
        collection='run.namespaces.domainmappings').RelativeName()
    # Model one unready GET and one GET with the resource ready.
    get_request = (
        self.serverless_messages.
        RunNamespacesDomainmappingsGetRequest(name=domain_mapping_name))
    self.mock_serverless_client.namespaces_domainmappings.Get.Expect(
        get_request,
        response=new_domain_mapping.Message())
    self.mock_serverless_client.namespaces_domainmappings.Get.Expect(
        get_request,
        response=gotten_domain_mapping.Message())
    mapping = self.serverless_client.CreateDomainMapping(
        self._DomainmappingRef('foo'), 'myapp')
    self.assertEqual(mapping.records[0].rrdata, '216.239.32.21')

  def testUpdateLabels(self):
    """Test updating labels on an existing service."""
    label_changes = config_changes.LabelChanges(
        labels_util.Diff(additions={'key2': 'value2'}))
    self._ExpectExisting(
        image='gcr.io/oldthing',
        annotations={revision.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'},
        labels=collections.OrderedDict([('key1', 'value1')]),
        revision_labels=collections.OrderedDict([('key1', 'value1')]))
    self._ExpectBaseRevision(
        image='gcr.io/oldthing',
        imageDigest='gcr.io/newthing@sha256:abcdef',
        annotations={revision.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'})
    self._ExpectUpdate(
        image='gcr.io/newthing@sha256:abcdef',
        annotations={revision.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'},
        labels=collections.OrderedDict([('key1', 'value1'),
                                        ('key2', 'value2')]),
        revision_labels=collections.OrderedDict([('key1', 'value1'),
                                                 ('key2', 'value2')]))
    self.serverless_client.ReleaseService(
        self._ServiceRef('foo'), [label_changes])

  def testReleaseServiceMalformedLabel(self):
    """Test release services api call with a bad label key."""
    fake_label_changes = config_changes.LabelChanges(
        labels_util.Diff(additions={'_BAD/LABEL_': 'somevalue'}))
    self._ExpectExisting(image='gcr.io/oldthing')
    self._ExpectBaseRevision(
        image='gcr.io/oldthing',
        imageDigest='gcr.io/newthing@sha256:abcdef',
        annotations={revision.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'})
    self._ExpectUpdate(
        exception=http_error.MakeDetailedHttpError(
            400,
            url='https://dummy_url.com/',
            content={
                'error': {
                    'code': 400,
                    'message': 'The request has errors.',
                    'status': 'INVALID_ARGUMENT',
                    'details': [{
                        '@type': 'type.googleapis.com/google.rpc.BadRequest',
                        'fieldViolations': [{
                            'field': 'label',
                            'description': 'standin error string',
                        }]}]}}),
        image='gcr.io/newthing@sha256:abcdef',
        annotations={revision.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'},
        labels={'_BAD/LABEL_': 'somevalue'},
        revision_labels={'_BAD/LABEL_': 'somevalue'})

    with self.assertRaisesRegexp(
        serverless_exceptions.HttpError,
        '^standin error string$'):
      self.serverless_client.ReleaseService(
          self._ServiceRef('foo'), [fake_label_changes])

  def testDeleteDomainMappings(self):
    """Test the delete domainmappings api call."""
    expected_request = (
        self.serverless_messages.RunNamespacesDomainmappingsDeleteRequest(
            name=self._DomainmappingRef('dm1').RelativeName()))
    expected_response = self._DeleteResponse()
    self.mock_serverless_client.namespaces_domainmappings.Delete.Expect(
        expected_request, expected_response)
    delete_response = self.serverless_client.DeleteDomainMapping(
        self._DomainmappingRef('dm1'))

    self.assertEqual(delete_response, None)

  @parameterized.parameters([1, 2, 5])
  def testUpdateNoRevisionNameWithNonce(self, nonce_polls):
    """Test the update flow when the service has no revision name but has a nonce."""
    self._ExpectExisting(
        image='gcr.io/oldthing',
        annotations={revision.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'},
        revision_name=None,
        revision_labels={revision.NONCE_LABEL: self.nonce},
        **{'template.env_vars.literals': {
            'key1': 'value1'
        }})

    self._ExpectBaseRevision(
        name_polls=0,
        nonce_polls=nonce_polls,
        labels={revision.NONCE_LABEL: self.nonce},
        image='gcr.io/oldthing',
        imageDigest='gcr.io/newthing@sha256:abcdef',
        annotations={revision.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'})

    self._ExpectUpdate(
        image='gcr.io/newthing@sha256:abcdef',
        annotations={revision.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'},
        **{
            'template.env_vars.literals':
                collections.OrderedDict([('key1', 'value1.2'),
                                         ('key2', 'value2')])
        })

    env_changes = config_changes.EnvVarLiteralChanges(
        env_vars_to_update=collections.OrderedDict([(
            'key1', 'value1.2'), ('key2', 'value2')]))
    self.serverless_client.ReleaseService(
        self._ServiceRef('foo'), [env_changes])

  @parameterized.parameters([(1, 2), (2, 1), (2, 5), (5, 2)])
  def testUpdateRevisionNotFoundByNameWithNonce(self, name_polls, nonce_polls):
    """Test the update flow when the revision is not found by name but is by nonce."""
    self._ExpectExisting(
        image='gcr.io/oldthing',
        annotations={revision.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'},
        revision_labels={revision.NONCE_LABEL: self.nonce},
        **{'template.env_vars.literals': {
            'key1': 'value1'
        }})

    self._ExpectBaseRevision(
        name_polls=name_polls,
        found_by_name=False,
        nonce_polls=nonce_polls,
        labels={revision.NONCE_LABEL: self.nonce},
        image='gcr.io/oldthing',
        imageDigest='gcr.io/newthing@sha256:abcdef',
        annotations={revision.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'})

    self._ExpectUpdate(
        image='gcr.io/newthing@sha256:abcdef',
        annotations={revision.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'},
        **{
            'template.env_vars.literals':
                collections.OrderedDict([('key1', 'value1.2'),
                                         ('key2', 'value2')])
        })

    env_changes = config_changes.EnvVarLiteralChanges(
        env_vars_to_update=collections.OrderedDict([(
            'key1', 'value1.2'), ('key2', 'value2')]))
    self.serverless_client.ReleaseService(
        self._ServiceRef('foo'), [env_changes])

  def testUpdateNoRevisionNameNoNonce(self):
    """Test the update flow when the service has no revision name or nonce."""
    self._ExpectExisting(
        image='gcr.io/oldthing',
        revision_name=None,
        generation=5,
        annotations={revision.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'},
        latestCreatedRevisionName='foo-00005-old',
        **{'template.env_vars.literals': {
            'key1': 'value1'
        }})

    self._ExpectBaseRevision(
        name_polls=0,
        nonce_polls=0,
        name=None,
        latestCreatedRevisionName='foo-00005-old',
        image='gcr.io/oldthing',
        imageDigest='gcr.io/newthing@sha256:abcdef',
        annotations={revision.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'})

    self._ExpectUpdate(
        image='gcr.io/newthing@sha256:abcdef',
        generation=5,
        revision_name='foo-00006-myrevision',
        latestCreatedRevisionName='foo-00005-old',
        annotations={revision.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'},
        **{
            'template.env_vars.literals':
                collections.OrderedDict([('key1', 'value1.2'),
                                         ('key2', 'value2')])
        })

    env_changes = config_changes.EnvVarLiteralChanges(
        env_vars_to_update=collections.OrderedDict([(
            'key1', 'value1.2'), ('key2', 'value2')]))
    self.serverless_client.ReleaseService(
        self._ServiceRef('foo'), [env_changes])

  @parameterized.parameters([(1, 0), (1, 2), (2, 5), (5, 5)])
  def testUpdateNoRevisionNameNotFoundByNonce(self, nonce_polls, nonce_results):
    """Test the update flow when the service has no revision name and is not found by nonce.

    This tests both for no revisions found with nonce label and more than 1
    with nonce label, both of which mean "not found" in this case.

    Args:
      nonce_polls: int, number of polls by nonce label
      nonce_results: int, number of revisions to find by nonce label on the
        final poll.
    """
    self._ExpectExisting(
        image='gcr.io/oldthing',
        revision_name=None,
        generation=5,
        annotations={revision.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'},
        revision_labels={revision.NONCE_LABEL: self.nonce},
        latestCreatedRevisionName='foo-00005-old',
        **{'template.env_vars.literals': {
            'key1': 'value1'
        }})

    self._ExpectBaseRevision(
        name_polls=0,
        nonce_polls=nonce_polls,
        nonce_results=nonce_results,
        name=None,
        labels={revision.NONCE_LABEL: self.nonce},
        latestCreatedRevisionName='foo-00005-old',
        image='gcr.io/oldthing',
        imageDigest='gcr.io/newthing@sha256:abcdef',
        annotations={revision.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'})

    self._ExpectUpdate(
        image='gcr.io/newthing@sha256:abcdef',
        generation=5,
        revision_name='foo-00006-myrevision',
        latestCreatedRevisionName='foo-00005-old',
        annotations={revision.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'},
        **{
            'template.env_vars.literals':
                collections.OrderedDict([('key1', 'value1.2'),
                                         ('key2', 'value2')])
        })

    env_changes = config_changes.EnvVarLiteralChanges(
        env_vars_to_update=collections.OrderedDict([(
            'key1', 'value1.2'), ('key2', 'value2')]))
    self.serverless_client.ReleaseService(
        self._ServiceRef('foo'), [env_changes])

  @parameterized.parameters([1, 2, 5])
  def testUpdateNotFoundByRevisionNameNoNonce(self, name_polls):
    """Test the update flow when the revision is not found by name and has no nonce."""
    self._ExpectExisting(
        image='gcr.io/oldthing',
        generation=5,
        annotations={revision.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'},
        latestCreatedRevisionName='foo-00005-old',
        **{'template.env_vars.literals': {
            'key1': 'value1'
        }})

    self._ExpectBaseRevision(
        name_polls=name_polls,
        found_by_name=False,
        latestCreatedRevisionName='foo-00005-old',
        image='gcr.io/oldthing',
        imageDigest='gcr.io/newthing@sha256:abcdef',
        annotations={revision.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'})

    self._ExpectUpdate(
        image='gcr.io/newthing@sha256:abcdef',
        generation=5,
        revision_name='foo-00006-myrevision',
        latestCreatedRevisionName='foo-00005-old',
        annotations={revision.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'},
        **{
            'template.env_vars.literals':
                collections.OrderedDict([('key1', 'value1.2'),
                                         ('key2', 'value2')])
        })

    env_changes = config_changes.EnvVarLiteralChanges(
        env_vars_to_update=collections.OrderedDict([(
            'key1', 'value1.2'), ('key2', 'value2')]))
    self.serverless_client.ReleaseService(
        self._ServiceRef('foo'), [env_changes])

  @parameterized.parameters([(1, 2), (2, 1), (2, 5), (5, 2)])
  def testUpdateNotFoundByRevisionNameNotFoundByNonce(self, name_polls,
                                                      nonce_polls):
    """Test the update flow when the revision is not found by name or nonce."""
    self._ExpectExisting(
        image='gcr.io/oldthing',
        generation=5,
        annotations={revision.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'},
        revision_labels={revision.NONCE_LABEL: self.nonce},
        latestCreatedRevisionName='foo-00005-old',
        **{'template.env_vars.literals': {
            'key1': 'value1'
        }})

    self._ExpectBaseRevision(
        name_polls=name_polls,
        found_by_name=False,
        nonce_polls=nonce_polls,
        nonce_results=0,
        labels={revision.NONCE_LABEL: self.nonce},
        latestCreatedRevisionName='foo-00005-old',
        image='gcr.io/oldthing',
        imageDigest='gcr.io/newthing@sha256:abcdef',
        annotations={revision.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'})

    self._ExpectUpdate(
        image='gcr.io/newthing@sha256:abcdef',
        generation=5,
        revision_name='foo-00006-myrevision',
        latestCreatedRevisionName='foo-00005-old',
        annotations={revision.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'},
        **{
            'template.env_vars.literals':
                collections.OrderedDict([('key1', 'value1.2'),
                                         ('key2', 'value2')])
        })

    env_changes = config_changes.EnvVarLiteralChanges(
        env_vars_to_update=collections.OrderedDict([(
            'key1', 'value1.2'), ('key2', 'value2')]))
    self.serverless_client.ReleaseService(
        self._ServiceRef('foo'), [env_changes])

  def _MakeService(self, new_api=False, **kwargs):
    """Set specified attributes of the service.

    If the given attribute does not exist on the root service, it will be
    applied to service's metadata, template, or status if the attribute is found
    to exist there.

    You can manually apply the attribute to somewhere other than the root
    service with dot notation in your key. For example, to modify the 'name'
    attribute of the service's template, pass 'template.name' as the key.

    Args:
      new_api: bool, True if service uses the new api
      **kwargs: named attributes and their values

    Returns:
      The created service.Service
    """
    new_service = service.Service.New(
        self.mock_serverless_client, self.namespace.namespacesId)
    new_service.name = 'foo'
    new_service.revision_name = 'foo-00001-{}'.format(self.revision_suffix)
    new_service.annotations[
        serverless_operations._CLIENT_NAME_ANNOTATION] = 'gcloud'
    new_service.template.annotations[
        serverless_operations._CLIENT_NAME_ANNOTATION] = 'gcloud'
    new_service.annotations[
        serverless_operations._CLIENT_VERSION_ANNOTATION] = 'test_version'
    new_service.template.annotations[
        serverless_operations._CLIENT_VERSION_ANNOTATION] = 'test_version'
    for k, v in kwargs.items():
      obj = new_service
      parsed_key = resource_lex.Lexer(k).Key()
      key = parsed_key[0]
      if len(parsed_key) > 1:
        while len(parsed_key) > 1:
          obj = getattr(obj, parsed_key[0])
          key = parsed_key[1]
          parsed_key = parsed_key[1:]
      else:
        if hasattr(new_service, key):
          pass
        elif hasattr(new_service.metadata, key):
          obj = new_service.metadata  # key is a metadata attribute
        elif hasattr(new_service.template, key):
          obj = new_service.template  # key is a template attribute
        elif hasattr(new_service.status, key):
          obj = new_service.status  # key is a status attribute
      if isinstance(v, dict):
        dict_like = getattr(obj, key)
        for kk, vv in v.items():
          dict_like[kk] = vv
      else:
        setattr(obj, key, v)
    if revision.USER_IMAGE_ANNOTATION in new_service.annotations:
      new_service.template.annotations[revision.USER_IMAGE_ANNOTATION] = (
          new_service.annotations[revision.USER_IMAGE_ANNOTATION])
    return new_service

  def _MakeRevision(self, **kwargs):
    """Make a new Revision with the fields listed in kwargs set.

    Note that the kwargs fields are the leaf field names; if you want to modify
    a field that exists with the same name in multiple places in the field
    structure, this helper won't do. But for everything else it is convenient.

    Ex: _MakeRevision(name='foo', image='gcr.io/foo/bar') makes a new Revision
    with metadata.name and container.image set.

    Args:
      **kwargs: fields to set

    Returns:
      A new Revision with the fields set.
    """

    def _SeekAndModify(msg, name, value):
      """Go change given field somewhere deep in the message object.

      Arguments:
        msg: Message, the message object.
        name: str, Name of the field.
        value: Any, Value of the field.
      Returns:
        True if we found-and-modified the field.
      """
      if not msg:
        return False
      # TODO(b/120510499): Disambiguate between identical nested field names.
      # For now, set the field with lowest number that matches 'name'.
      for i in range(1, len(type(msg).all_fields()) + 1):
        field = type(msg).field_by_number(i)
        if field.name == name:
          setattr(msg, name, value)
          return True
        if not field.repeated and isinstance(field, messages.MessageField):
          if _SeekAndModify(getattr(msg, field.name), name, value):
            return True
        elif field.repeated:
          items = getattr(msg, field.name)
          if len(items) == 1 and isinstance(items[0], messages.Message):
            if _SeekAndModify(items[0], name, value):
              return True
      return False

    rev = revision.Revision.New(
        self.mock_serverless_client, self.namespace.namespacesId)
    rev.name = 'foo-00001-{}'.format(self.revision_suffix)
    for k, v in kwargs.items():
      if isinstance(v, dict):
        dict_like = getattr(rev, k)
        for kk, vv in v.items():
          dict_like[kk] = vv
      else:
        done = _SeekAndModify(rev.Message(), k, v)
        assert done, 'Failed to set field {}'.format(k)
    return rev

  def _ExpectCreate(self, **kwargs):
    # Expect that it does not exist.
    self.mock_serverless_client.namespaces_services.Get.Expect(
        (self.serverless_messages.
         RunNamespacesServicesGetRequest(
             name=self._ServiceRef('foo').RelativeName())),
        exception=api_exceptions.HttpNotFoundError(None, None, None),
    )
    # Expect creation.
    new_service = self._MakeService(**kwargs)
    create_request = (
        self.serverless_messages.
        RunNamespacesServicesCreateRequest(
            parent=self.namespace.RelativeName(),
            service=new_service.Message()))
    self.mock_serverless_client.namespaces_services.Create.Expect(
        create_request,
        response=new_service.Message())

  def _ExpectUpdate(self, exception=None, **kwargs):
    """Expect that the service will be updated with these values.

    See _MakeService for valid args.

    Args:
      exception: http_error to throw on update request
      **kwargs: keyword arguments that define service attributes
    """
    # Make sure the generation is set
    if 'generation' not in kwargs and 'metadata.generation' not in kwargs:
      kwargs['metadata.generation'] = 0
    new_service = self._MakeService(**kwargs)
    update_request = (
        self.serverless_messages.
        RunNamespacesServicesReplaceServiceRequest(
            service=new_service.Message(),
            name=self._ServiceRef('foo').RelativeName()))
    if exception:
      self.mock_serverless_client.namespaces_services.ReplaceService.Expect(
          update_request,
          exception=exception)
    else:
      self.mock_serverless_client.namespaces_services.ReplaceService.Expect(
          update_request,
          response=new_service.Message())

  def _ExpectExisting(self, **kwargs):
    """Expect that a service already exists with these values.

    See _MakeService for valid args.

    Args:
      **kwargs: keyword arguments that define service attributes
    """
    # Make sure the generation is set
    if 'generation' not in kwargs and 'metadata.generation' not in kwargs:
      kwargs['metadata.generation'] = 0
    old_service = self._MakeService(**kwargs)
    self.mock_serverless_client.namespaces_services.Get.Expect(
        (self.serverless_messages.
         RunNamespacesServicesGetRequest(
             name=self._ServiceRef('foo').RelativeName())),
        response=old_service.Message(),
    )

  def _PollUntilDonePatch(self, retrial_exception_counts):
    """Override waiter.PollUntilDone to gracefully handle timeouts.

    Args:
      retrial_exception_counts: List[int], for each call to
        waiter.PollUntilDone, how many calls to the underlying function to allow
        before raising retry.RetryException (alternatively, the number of
        retrials + 1). If the given value is 0, then no retry limit will be
        imposed for that call to waiter.PollUntilDone.

    Returns:
      A patch function for waiter.PollUntilDone that implements the retry-limit
        mechanism.
    """
    self.poll_call_count = 0
    poll_waiters = []
    for count in retrial_exception_counts:
      # Add a poll function with a built-in max count if specified
      if count == 0:
        poll_waiters.append(waiter.PollUntilDone)
      else:
        poll_waiters.append(
            functools.partial(waiter.PollUntilDone, max_retrials=(count - 1)))

    def _PollUntilDone(*args, **kwargs):
      self.poll_call_count += 1
      try:
        return poll_waiters[self.poll_call_count - 1](*args, **kwargs)
      except IndexError:
        raise ValueError('PollUntilDone patch limit reached. '
                         'Not enough patches specified.')

    return _PollUntilDone

  # pylint:disable=invalid-name
  def _ExpectBaseRevision(self,
                          name_polls=1,
                          found_by_name=True,
                          nonce_polls=0,
                          nonce_results=1,
                          latestCreatedRevisionName=None,
                          **kwargs):
    """Treat the server as having the given base revision.

    Mimics by first checking revision name, then nonce, then
    latestCreatedRevisionName depending on the polling amounts passed as
    arguments.

    Args:
      name_polls: int, Number of times the client polls for a revision with the
        given name before the server "has" the revision.
      found_by_name: bool, True if the revision should be found by revision name
        or False if additional requests are are necessary after polling by name.
      nonce_polls: int, Number of time the client polls for a revision with the
        given nonce before the server "has" the revision.
      nonce_results: int, Number of copies of revisions with the listed nonce
        the server pretends to have.
      latestCreatedRevisionName: str, the latest created revision name to poll
        with when name polling and nonce polling fail
      **kwargs: Fields for the revision to have
    """
    rev = self._MakeRevision(**kwargs)
    retrial_exception_counts = []
    # Poll by revision name
    for i in range(name_polls):
      response = None
      exception = None
      if i < name_polls - 1 or not found_by_name:
        exception = api_exceptions.HttpNotFoundError(None, None, None)
      else:
        response = rev.Message()
      self.mock_serverless_client.namespaces_revisions.Get.Expect(
          (self.serverless_messages.RunNamespacesRevisionsGetRequest(
              name=self._RevisionRef(rev.name).RelativeName())),
          response=response,
          exception=exception)
    # Specify retry limits if applicable
    if name_polls > 0:
      retrial_exception_counts.append(name_polls if not found_by_name else 0)
    # Poll by nonce
    for i in range(nonce_polls):
      self.mock_serverless_client.namespaces_revisions.List.Expect(
          (self.serverless_messages.RunNamespacesRevisionsListRequest(
              parent=self.namespace.RelativeName(),
              labelSelector='{} = {}'.format(revision.NONCE_LABEL,
                                             self.nonce))),
          response=(self.serverless_messages.ListRevisionsResponse(
              items=([] if i < nonce_polls - 1 else [rev.Message()] *
                     nonce_results))))
    # Specify retry limits if applicable
    if nonce_polls > 0:
      retrial_exception_counts.append(nonce_polls if nonce_results != 1 else 0)
    # We fall back to getting a revision by latestCreatedRevisionName
    if (latestCreatedRevisionName is not None and
        (name_polls == 0 or not found_by_name) and
        (nonce_polls == 0 or nonce_results != 1)):
      self.mock_serverless_client.namespaces_revisions.Get.Expect(
          self.serverless_messages.RunNamespacesRevisionsGetRequest(
              name=self._RevisionRef(latestCreatedRevisionName).RelativeName()),
          response=rev.Message())
    self.StartObjectPatch(
        waiter,
        'PollUntilDone',
        side_effect=self._PollUntilDonePatch(retrial_exception_counts))
  # pylint:enable=invalid-name


class ServerlessOperationsTestV1(ServerlessOperationsTest):

  API_VERSION = 'v1'

  def _MakeService(self, new_api=False, **kwargs):
    return super(ServerlessOperationsTestV1, self)._MakeService(
        new_api=True, **kwargs)

  def _ExpectBaseRevision(self,
                          name_polls=1,
                          found_by_name=True,
                          nonce_polls=0,
                          nonce_results=1,
                          latestCreatedRevisionName=None,
                          **kwargs):
    return super(ServerlessOperationsTestV1, self)._ExpectBaseRevision(
        name_polls=name_polls,
        found_by_name=found_by_name,
        nonce_polls=nonce_polls,
        nonce_results=nonce_results,
        latestCreatedRevisionName=latestCreatedRevisionName,
        **kwargs)

  def _DeleteResponse(self):
    return self.serverless_messages.Status()

  def testUpdateNoNonce(self):
    pass


if __name__ == '__main__':
  test_case.main()
