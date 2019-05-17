# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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
from apitools.base.protorpclite import messages
from apitools.base.py import exceptions as api_exceptions
from googlecloudsdk.api_lib.run import condition
from googlecloudsdk.api_lib.run import configuration
from googlecloudsdk.api_lib.run import domain_mapping
from googlecloudsdk.api_lib.run import revision
from googlecloudsdk.api_lib.run import service
from googlecloudsdk.api_lib.services import enable_api
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.command_lib.run import config_changes
from googlecloudsdk.command_lib.run import deployable as deployable_pkg
from googlecloudsdk.command_lib.run import exceptions as serverless_exceptions
from googlecloudsdk.command_lib.run import serverless_operations
from googlecloudsdk.command_lib.run import source_ref
from googlecloudsdk.command_lib.run import stages
from googlecloudsdk.core import exceptions
from googlecloudsdk.core.console import progress_tracker
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
    '_Cond', ['type', 'status', 'message', 'reason'])


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
            _Cond('Ready', 'Unknown', 'Not yet', ''),
            _Cond('one', 'True', None, None),
            _Cond('two', 'Unknown', 'Not yet', ''),
        ], ready_condition='Ready'),
        condition.Conditions([
            _Cond('Ready', 'True', None, None),
            _Cond('one', 'True', None, None),
            _Cond('two', 'True', None, None),
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
            _Cond('Ready', 'Unknown', 'Not yet', ''),
            _Cond('one', 'True', None, None),
            _Cond('two', 'Unknown', 'Not yet', ''),
        ], ready_condition='Ready'),
        condition.Conditions([
            _Cond('Ready', 'False', 'Oops.', ''),
            _Cond('one', 'True', None, None),
            _Cond('two', 'False', 'Oops.', ''),
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
            _Cond('Ready', 'Unknown', 'Not yet', ''),
            _Cond('one', 'True', None, None),
            _Cond('two', 'Unknown', 'Not yet', ''),
        ], ready_condition='Ready'),
        condition.Conditions([
            _Cond('Ready', 'True', None, None),
            _Cond('one', 'True', None, None),
            _Cond('two', 'True', None, None),
        ], ready_condition='Ready')])
    poller = serverless_operations.ConditionPoller(
        self._ResourceGetter, tracker,
        dependencies={'two': {'one'}, 'one': set()})
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

  def testDontStartTilUnblockedPrevTrue(self):
    """One stage dependent on another to start, and True before that happens."""
    tracker = _MakeMockTracker(['one', 'two'])
    # Condition one goes Unknown -> True -> True
    # Condition two goes True -> Unknown -> True
    # Because of the dependencies, two should not Start until the second poll.
    self.conditions_series = iter([
        condition.Conditions([
            _Cond('Ready', 'Unknown', 'Not yet', ''),
            _Cond('one', 'Unknown', 'Not yet', ''),
            _Cond('two', 'True', None, None),
        ], ready_condition='Ready'),
        condition.Conditions([
            _Cond('Ready', 'Unknown', 'Not yet.', None),
            _Cond('one', 'True', None, None),
            _Cond('two', 'Unknown', 'Working.', None),
        ], ready_condition='Ready'),
        condition.Conditions([
            _Cond('Ready', 'True', None, None),
            _Cond('one', 'True', None, None),
            _Cond('two', 'True', None, None),
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
            _Cond('Ready', 'Unknown', 'Not yet.', None),
            _Cond('one', 'True', None, None),
            _Cond('two', 'True', None, None),
        ], ready_condition='Ready'),
        condition.Conditions([
            _Cond('Ready', 'True', None, None),
            _Cond('one', 'True', None, None),
            _Cond('two', 'True', None, None),
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


class ServerlessConfigurationWaitTest(base.ServerlessBase):
  """Tests for polling and waiting for updating configuration."""

  def SetUp(self):
    self.cond_class = self.serverless_messages.ConfigurationCondition
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
    self.enable_mock = self.StartObjectPatch(enable_api,
                                             'EnableServiceIfDisabled')
    self.nonce = 'itsthenoncelol'
    self.StartObjectPatch(serverless_operations,
                          '_Nonce', return_value=self.nonce)
    self.serverless_client.WaitForCondition = unittest_mock.Mock()
    dummy_config = configuration.Configuration.New(self.mock_serverless_client,
                                                   self.Project())
    self.is_source_branch = hasattr(dummy_config.Message().spec, 'build')

    self.fake_image = 'gcr.io/my-image'
    fake_source_ref = unittest_mock.Mock(source_path=self.fake_image)
    self.fake_deployable = deployable_pkg.ServerlessContainer(fake_source_ref)

  def _ExpectRevisionsList(self, serv_name):
    """List call for two revisions against the Serverless API."""

    request = (
        self.
        serverless_messages.RunNamespacesRevisionsListRequest(
            parent=self.namespace.RelativeName(),
            labelSelector='serving.knative.dev/service = {}'.format(
                serv_name),
        ))

    def _GetLabels():
      return self.serverless_messages.ObjectMeta.LabelsValue(
          additionalProperties=[
              self.serverless_messages.ObjectMeta.LabelsValue.
              AdditionalProperty(key='serving.knative.dev/service', value='s1')
          ])

    def _GetMetadata(i):
      return self.serverless_messages.ObjectMeta(
          name='r{}'.format(i),
          creationTimestamp=datetime.datetime.utcfromtimestamp(i).isoformat() +
          'Z',
          labels=_GetLabels(),
      )

    revisions_responses = self.serverless_messages.ListRevisionsResponse(items=[
        self.serverless_messages.Revision(metadata=_GetMetadata(i))
        for i in range(2)
    ])

    self.mock_serverless_client.namespaces_revisions.List.Expect(
        request, response=revisions_responses)

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

    expected_response = self.serverless_messages.Empty()
    self.mock_serverless_client.namespaces_services.Delete.Expect(
        expected_request, expected_response)

    delete_response = self.serverless_client.DeleteService(
        self._ServiceRef('s1'))

    self.assertEquals(delete_response, None)

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
    self._ExpectRevisionsList('default')
    revisions = self.serverless_client.ListRevisions(self.namespace, 'default')
    # Most recently created revision comes first
    self.assertEqual(revisions[0].metadata.name, 'r1')
    self.assertEqual(revisions[1].metadata.name, 'r0')

  def testDeleteRevision(self):
    """Test the delete revision api call."""
    revision_ref = self._RevisionRef('r0')
    expected_request = (
        self.serverless_messages.RunNamespacesRevisionsDeleteRequest(
            name=revision_ref.RelativeName()))

    expected_response = self.serverless_messages.Empty()
    self.mock_serverless_client.namespaces_revisions.Delete.Expect(
        expected_request, expected_response)

    delete_response = self.serverless_client.DeleteRevision(revision_ref)

    self.assertEquals(delete_response, None)

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
    fake_source_ref = unittest_mock.Mock()
    fake_source_ref.source_path = 'gcr.io/fakething'
    fake_deployable = deployable_pkg.ServerlessContainer(fake_source_ref)
    self._ExpectCreate(
        image='gcr.io/fakething',
        annotations={
            configuration.USER_IMAGE_ANNOTATION: 'gcr.io/fakething'})

    self.serverless_client.ReleaseService(
        self._ServiceRef('foo'),
        [fake_deployable])

  def testReleaseServiceAllowUnauthenticated(self):
    """Test the release flow for a new service with unauthenticated access."""
    fake_source_ref = unittest_mock.Mock()
    fake_source_ref.source_path = 'gcr.io/fakething'
    fake_deployable = deployable_pkg.ServerlessContainer(fake_source_ref)
    self._ExpectCreate(
        image='gcr.io/fakething',
        annotations={
            configuration.USER_IMAGE_ANNOTATION: 'gcr.io/fakething'})
    self._ExpectGetIamPolicy('foo', bindings=[])
    binding = self.serverless_messages.Binding(
        members=['allUsers'], role='roles/run.invoker')
    self._ExpectSetIamPolicy(service='foo', bindings=[binding])

    self.serverless_client.ReleaseService(
        self._ServiceRef('foo'),
        [fake_deployable],
        allow_unauthenticated=True)

  def testReleaseServiceAllowUnauthenticatedSetIamFail(self):
    """Test the release flow for a new service with unauthenticated access."""
    fake_source_ref = unittest_mock.Mock()
    fake_source_ref.source_path = 'gcr.io/fakething'
    fake_deployable = deployable_pkg.ServerlessContainer(fake_source_ref)
    self._ExpectCreate(
        image='gcr.io/fakething',
        annotations={
            configuration.USER_IMAGE_ANNOTATION: 'gcr.io/fakething'})
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
    self.assertTrue(stages.SERVICE_IAM_POLICY_SET in
                    tracker._completed_with_warnings_stages)

  def testReleaseServiceNotFound(self):
    """Test the flow for a configuration update on a nonexistent service."""
    env_changes = config_changes.EnvVarChanges(
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
    self._ExpectCreate(
        image=self.fake_image,
        annotations={
            configuration.USER_IMAGE_ANNOTATION: 'gcr.io/my-image'},
        labels={
            service.ENDPOINT_VISIBILITY: service.CLUSTER_LOCAL})

    self.serverless_client.ReleaseService(
        self._ServiceRef('foo'), [self.fake_deployable], private_endpoint=True)

  def testReleaseServicePublicEndpointNew(self):
    """Test the flow for releasing a new service with public endpoint."""
    self._ExpectCreate(
        image=self.fake_image,
        annotations={
            configuration.USER_IMAGE_ANNOTATION: 'gcr.io/my-image'})

    self.serverless_client.ReleaseService(
        self._ServiceRef('foo'), [self.fake_deployable], private_endpoint=False)

  def testReleaseServicePublicEndpoint(self):
    """Test the flow for updating a service from private to public."""
    self._ExpectExisting(
        image='gcr.io/my-image',
        annotations={
            configuration.USER_IMAGE_ANNOTATION: 'gcr.io/my-image'},
        labels={service.ENDPOINT_VISIBILITY: service.CLUSTER_LOCAL})

    self._ExpectUpdate(
        image='gcr.io/my-image',
        annotations={
            configuration.USER_IMAGE_ANNOTATION: 'gcr.io/my-image'})

    self.serverless_client.ReleaseService(
        self._ServiceRef('foo'), [self.fake_deployable], private_endpoint=False)

  def testReleaseServiceVisibilityUnchangedPrivate(self):
    """Test the flow for leaving private visibility unchanged."""
    self._ExpectExisting(
        image='gcr.io/my-image',
        annotations={
            configuration.USER_IMAGE_ANNOTATION: 'gcr.io/my-image'},
        labels={service.ENDPOINT_VISIBILITY: service.CLUSTER_LOCAL})

    self._ExpectUpdate(
        image='gcr.io/my-image',
        annotations={
            configuration.USER_IMAGE_ANNOTATION: 'gcr.io/my-image'},
        labels={service.ENDPOINT_VISIBILITY: service.CLUSTER_LOCAL})

    self.serverless_client.ReleaseService(
        self._ServiceRef('foo'), [self.fake_deployable])

  def testReleaseServiceVisibilityUnchangedPublic(self):
    """Test the flow for leaving public visibility unchanged."""
    self._ExpectExisting(
        image='gcr.io/my-image',
        annotations={
            configuration.USER_IMAGE_ANNOTATION: 'gcr.io/my-image'})

    self._ExpectUpdate(
        image='gcr.io/my-image',
        annotations={
            configuration.USER_IMAGE_ANNOTATION: 'gcr.io/my-image'})

    self.serverless_client.ReleaseService(
        self._ServiceRef('foo'), [self.fake_deployable])

  def testUpdateNoNonce(self):
    """Test the flow for update when configuration has no nonce."""
    self._ExpectExisting(
        image='gcr.io/oldthing',
        annotations={
            configuration.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'},
        revision_labels={serverless_operations.NONCE_LABEL: None},
        latestCreatedRevisionName='last_revision.1',
        env_vars={'key1': 'value1'})

    self._ExpectBaseRevision(
        polls=0,
        name='last_revision.1',
        image='gcr.io/oldthing',
        imageDigest='gcr.io/newthing@sha256:abcdef',
        annotations={
            configuration.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'})

    self._ExpectUpdate(
        image='gcr.io/newthing@sha256:abcdef',
        annotations={
            configuration.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'},
        env_vars=collections.OrderedDict(
            [('key1', 'value1.2'), ('key2', 'value2')]),
        latestCreatedRevisionName='last_revision.1')

    env_changes = config_changes.EnvVarChanges(
        env_vars_to_update=collections.OrderedDict([('key1', 'value1.2'),
                                                    ('key2', 'value2')]))
    self.serverless_client.ReleaseService(
        self._ServiceRef('foo'),
        [env_changes])

  def testUpdateNoRevisionWithNonce(self):
    """Test update flow when no revision found with nonce."""
    self._ExpectExisting(
        image='gcr.io/oldthing',
        annotations={
            configuration.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'},
        latestCreatedRevisionName='last_revision.1',
        env_vars={'key1': 'value1'})

    self._ExpectBaseRevision(
        polls=0,
        name='last_revision.1',
        image='gcr.io/oldthing',
        imageDigest='gcr.io/newthing@sha256:abcdef',
        annotations={
            configuration.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'})

    self._ExpectUpdate(
        image='gcr.io/newthing@sha256:abcdef',
        annotations={
            configuration.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'},
        env_vars=collections.OrderedDict(
            [('key1', 'value1.2'), ('key2', 'value2')]),
        latestCreatedRevisionName='last_revision.1')

    env_changes = config_changes.EnvVarChanges(
        env_vars_to_update=collections.OrderedDict([('key1', 'value1.2'),
                                                    ('key2', 'value2')]))

    with unittest_mock.patch.object(waiter, 'PollUntilDone', side_effect=[
        retry.WaitException(unittest_mock.ANY,
                            unittest_mock.ANY, unittest_mock.ANY)]):
      self.serverless_client.ReleaseService(
          self._ServiceRef('foo'),
          [env_changes])

  # latestCreatedRevisionName is available on Service. Add (1, 2) to the params.
  @parameterized.parameters((1, 1), (2, 1))
  def testUpdateEnvVars(self, base_revision_polls, base_revision_results):
    """Test updating env vars on an existing service.

    This tests both updating an existing env var and creating a new env var.

    Args:
      base_revision_polls: Number of times to poll the nonce before results
      base_revision_results: Number of results polling the nonce eventually
        yields
    """
    self._ExpectExisting(
        image='gcr.io/oldthing',
        annotations={
            configuration.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'},
        env_vars={'key1': 'value1'})
    self._ExpectBaseRevision(
        polls=base_revision_polls,
        results=base_revision_results,
        name='foo.1',
        image='gcr.io/oldthing',
        imageDigest='gcr.io/newthing@sha256:abcdef',
        annotations={
            configuration.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'})

    self._ExpectUpdate(
        image='gcr.io/newthing@sha256:abcdef',
        annotations={
            configuration.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'},
        env_vars=collections.OrderedDict(
            [('key1', 'value1.2'), ('key2', 'value2')]))

    env_changes = config_changes.EnvVarChanges(
        env_vars_to_update=collections.OrderedDict([('key1', 'value1.2'),
                                                    ('key2', 'value2')]))
    self.serverless_client.ReleaseService(
        self._ServiceRef('foo'),
        [env_changes])

  def testRemoveEnvVars(self):
    """Test removing env vars from an existing service.

    This tests that removing an existing env var actually works, and that
    attempting to remove a non-existent env var doesn't cause the entire
    command to fail.
    """
    self._ExpectExisting(
        image='gcr.io/oldthing',
        env_vars=collections.OrderedDict([
            ('key-to-delete', 'value1'), ('key-to-preserve', 'value1')]))
    self._ExpectBaseRevision(
        name='foo.1',
        image='gcr.io/oldthing',
        imageDigest='gcr.io/newthing@sha256:abcdef',
        annotations={configuration.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'})

    self._ExpectUpdate(
        image='gcr.io/newthing@sha256:abcdef',
        annotations={
            configuration.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'},
        env_vars=collections.OrderedDict([('key-to-preserve', 'value1')]))

    env_changes = config_changes.EnvVarChanges(
        env_vars_to_remove=['key-to-delete', 'dummy-key-should-be-ignored'])
    self.serverless_client.ReleaseService(
        self._ServiceRef('foo'),
        [env_changes])

  def testDetect(self):
    """Adjust this test once build templates are real on the server."""
    # TODO(b/112662240): Remove conditional once the build field is public
    if not self.is_source_branch:
      return
    s_ref = source_ref.SourceRef(source_ref.SourceRef.SourceType.DIRECTORY,
                                 'foo/bar')
    dep = self.serverless_client.Detect(self.namespace, s_ref)
    self.assertEqual(dep.build_template.name, 'nodejs_8_9_4')
    self.assertEqual(dep.deployment_type, 'app')

  def testDetectContainer(self):
    """Make sure detection can tell when we have a container."""
    i_ref = source_ref.SourceRef(source_ref.SourceRef.SourceType.IMAGE,
                                 'gcr.io/foo/baz:bar')
    dep = self.serverless_client.Detect(self.namespace, i_ref)
    self.assertEqual(dep.deployment_type, 'container')

  def testDetectFunction(self):
    """Adjust this test once build templates are real on the server."""
    # TODO(b/112662240): Remove conditional once the build field is public
    if not self.is_source_branch:
      return
    s_ref = source_ref.SourceRef(source_ref.SourceRef.SourceType.DIRECTORY,
                                 'foo/bar')
    dep = self.serverless_client.Detect(self.namespace, s_ref,
                                        function_entrypoint='thing')
    self.assertEqual(dep.build_template.name, 'nodejs_8_9_4')
    self.assertEqual(dep.deployment_type, 'function')

  def testDetectContainerRaises(self):
    """A container deployable cannot take a runtime or entrypoint."""
    i_ref = source_ref.SourceRef(source_ref.SourceRef.SourceType.IMAGE,
                                 'gcr.io/adsf/asdfafdw:asfd')
    with self.assertRaises(serverless_exceptions.UnknownDeployableError):
      self.serverless_client.Detect(self.namespace, i_ref,
                                    function_entrypoint='helloworld')

  def testReleaseServiceBadImage(self):
    """Test the delete services api call with a non-existent service name."""
    fake_source_ref = unittest_mock.Mock()
    fake_source_ref.source_path = 'badimage'
    fake_deployable = deployable_pkg.ServerlessContainer(fake_source_ref)
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
        serverless_exceptions.BadImageError,
        '^standin error string$'):
      self.serverless_client.ReleaseService(
          self._ServiceRef('foo'), [fake_deployable])

  def testReleaseServiceExisting(self):
    """Test the release flow when the service already exists."""
    fake_source_ref = unittest_mock.Mock()
    fake_source_ref.source_path = 'gcr.io/newthing'
    fake_deployable = deployable_pkg.ServerlessContainer(fake_source_ref)

    self._ExpectExisting(
        image='gcr.io/oldthing',
        annotations={
            configuration.USER_IMAGE_ANNOTATION: 'gcr.io/oldthing'})
    self._ExpectUpdate(
        image='gcr.io/newthing',
        annotations={
            configuration.USER_IMAGE_ANNOTATION: 'gcr.io/newthing'})

    self.serverless_client.ReleaseService(
        self._ServiceRef('foo'), [fake_deployable])

  def testReleaseImageExistingApp(self):
    """Test the release flow when the service already exists."""
    # TODO(b/112662240): Remove conditional once the build field is public
    if not self.is_source_branch:
      return
    fake_source_ref = unittest_mock.Mock()
    fake_source_ref.source_path = 'gcr.io/newthing'
    fake_deployable = deployable_pkg.ServerlessContainer(fake_source_ref)

    self._ExpectExisting(
        image='gcr.io/oldthing',
        source_manifest='foobar',
        build_template_name='blug',
        build_template_arguments={'_IMAGE': 'gcr.io/oldthing'})
    self._ExpectUpdate(
        image='gcr.io/newthing',
        annotations={
            configuration.USER_IMAGE_ANNOTATION: 'gcr.io/newthing'})

    self.serverless_client.ReleaseService(
        self._ServiceRef('foo'), [fake_deployable])

  def testReleaseAppServiceFresh(self):
    """Test the release flow for a new service which is an app."""
    # TODO(b/112662240): Remove conditional once the build field is public
    if not self.is_source_branch:
      return
    from googlecloudsdk.command_lib.run import source_deployable  # pylint: disable=g-import-not-at-top
    fake_manifest_ref = unittest_mock.Mock()
    fake_manifest_ref.url = 'fake-manifest-url'
    fake_build_template = unittest_mock.Mock()
    fake_build_template.name = 'fake-build-template'
    fake_build_template.namespace = 'build-templates'

    fake_deployable = source_deployable.ServerlessApp(
        'fake_source_ref', fake_build_template)
    fake_deployable.manifest_ref = fake_manifest_ref

    self._ExpectCreate(
        source_manifest='fake-manifest-url',
        build_template_name='fake-build-template',
        build_template_arguments={'_IMAGE': 'gcr.io/fake-project/foo:1'},
        image='gcr.io/fake-project/foo:1',
        annotations={
            configuration.USER_IMAGE_ANNOTATION: 'gcr.io/fake-project/foo:1'})

    self.serverless_client.ReleaseService(
        self._ServiceRef('foo'),
        [fake_deployable])

  def testReleaseFunctionServiceFresh(self):
    """Test the release flow for a new service which is a function."""
    # TODO(b/112662240): Remove conditional once the build field is public
    if not self.is_source_branch:
      return
    from googlecloudsdk.command_lib.run import source_deployable  # pylint: disable=g-import-not-at-top
    fake_manifest_ref = unittest_mock.Mock()
    fake_manifest_ref.url = 'fake-manifest-url'
    fake_build_template = unittest_mock.Mock()
    fake_build_template.name = 'fake-build-template'
    fake_build_template.namespace = 'build-templates'

    fake_deployable = source_deployable.ServerlessFunction(
        'fake_source_ref', fake_build_template, 'entrypoint')
    fake_deployable.manifest_ref = fake_manifest_ref

    self._ExpectCreate(
        source_manifest='fake-manifest-url',
        build_template_name='fake-build-template',
        build_template_arguments=collections.OrderedDict(
            [('_IMAGE', 'gcr.io/fake-project/foo:1'),
             ('_ENTRY_POINT', 'entrypoint')]),
        image='gcr.io/fake-project/foo:1',
        annotations={
            configuration.USER_IMAGE_ANNOTATION: 'gcr.io/fake-project/foo:1'})

    self.serverless_client.ReleaseService(
        self._ServiceRef('foo'),
        [fake_deployable])

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

    gotten_domain_mapping = domain_mapping.DomainMapping.New(
        self.mock_serverless_client, self.namespace.namespacesId)
    gotten_domain_mapping.name = 'foo'
    gotten_domain_mapping.route_name = 'myapp'
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
    records = self.serverless_client.CreateDomainMapping(
        self._DomainmappingRef('foo'), 'myapp')
    self.assertEqual(records[0].rrdata, '216.239.32.21')

  def testDeleteDomainMappings(self):
    """Test the delete domainmappings api call."""
    expected_request = (
        self.serverless_messages.RunNamespacesDomainmappingsDeleteRequest(
            name=self._DomainmappingRef('dm1').RelativeName()))
    expected_response = self.serverless_messages.Empty()
    self.mock_serverless_client.namespaces_domainmappings.Delete.Expect(
        expected_request, expected_response)
    delete_response = self.serverless_client.DeleteDomainMapping(
        self._DomainmappingRef('dm1'))

    self.assertEqual(delete_response, None)

  def _MakeService(self, **kwargs):
    new_service = service.Service.New(
        self.mock_serverless_client, self.namespace.namespacesId)
    new_service.name = 'foo'
    new_conf = new_service.configuration
    new_conf.revision_labels[serverless_operations.NONCE_LABEL] = self.nonce
    for k, v in kwargs.items():
      obj = new_conf
      if hasattr(new_service.metadata, k):
        obj = new_service  # k is a metadata attribute, not a spec attribute
      elif hasattr(new_service.status, k):
        obj = new_service.status  # k is a status attribute not a spec attribute
      if isinstance(v, dict):
        dict_like = getattr(obj, k)
        for kk, vv in v.items():
          dict_like[kk] = vv
      else:
        setattr(obj, k, v)
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
      return False

    rev = revision.Revision.New(
        self.mock_serverless_client, self.namespace.namespacesId)
    for k, v in kwargs.items():
      if isinstance(v, dict):
        dict_like = getattr(rev, k)
        for kk, vv in v.items():
          dict_like[kk] = vv
      else:
        done = _SeekAndModify(rev.Message(), k, v)
        assert done, 'Failed to set field {}'.format(k)
    rev.labels[serverless_operations.NONCE_LABEL] = self.nonce
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
    old_service = self._MakeService(**kwargs)
    self.mock_serverless_client.namespaces_services.Get.Expect(
        (self.serverless_messages.
         RunNamespacesServicesGetRequest(
             name=self._ServiceRef('foo').RelativeName())),
        response=old_service.Message(),
    )

  def _ExpectBaseRevision(self, polls=1, results=1, **kwargs):
    """Treat the server as having the given base revision.

    Mimics returning it by nonce, and, if that doesn't work,
    by latestCreatedRevisionName

    Args:
      polls: int, Number of times the client polls before the server "has"
        the revision
      results: int, Number of copies of the listed nonce the server pretends to
        have.
      **kwargs: Fields for the revision to have
    """
    rev = self._MakeRevision(**kwargs)
    for i in range(polls):
      self.mock_serverless_client.namespaces_revisions.List.Expect(
          (self.serverless_messages.
           RunNamespacesRevisionsListRequest(
               parent=self.namespace.RelativeName(),
               labelSelector='{} = {}'.format(serverless_operations.NONCE_LABEL,
                                              self.nonce))),
          response=(
              self.serverless_messages.ListRevisionsResponse(
                  items=[] if i < polls - 1 else [rev.Message()] * results)))
    if not polls or results != 1:
      # We fall back to getting a revision
      self.mock_serverless_client.namespaces_revisions.Get.Expect(
          (self.serverless_messages.
           RunNamespacesRevisionsGetRequest(
               name=self._RevisionRef(rev.name).RelativeName())),
          response=rev.Message())


class UploadSourceTest(base.ServerlessBase):
  """Tests upload source calls."""

  def testUpload(self):

    fake_source_ref = unittest_mock.Mock()
    fake_source_ref.source_path = 'gcr.io/newthing'
    fake_deployable = deployable_pkg.ServerlessContainer(fake_source_ref)
    self.serverless_client.Upload(fake_deployable)


if __name__ == '__main__':
  test_case.main()
