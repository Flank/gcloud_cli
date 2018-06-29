# Copyright 2016 Google Inc. All Rights Reserved.
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

"""Tests for the debug API wrapper module."""

from __future__ import absolute_import
from __future__ import unicode_literals
import threading

from apitools.base.py.testing import mock as api_mock

from googlecloudsdk.api_lib.debug import debug
from googlecloudsdk.api_lib.debug import errors
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib.apitools import http_error
import six
from six.moves import range

# Some tests could potentially wait forever if the test is broken.
# GLOBAL_MAX_WAIT provides an upper limit in such cases. It should never be
# reached under normal circumstances.
GLOBAL_MAX_WAIT = 30


class UnsatisfiedExpectationError(Exception):

  def __init__(self, expectations):
    super(UnsatisfiedExpectationError, self).__init__(
        'Expected, but did not receive, Get requests (id, # expected) = {0}'
        .format(sorted(expectations)))


class UnexpectedIdError(Exception):

  def __init__(self, breakpointId, ids):
    super(UnexpectedIdError, self).__init__(
        'Breakpoint {0} not expected. Expected ids are: {1}'.format(
            breakpointId, sorted(ids)))


class _DebugMockApiTest(sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase):
  """Base class for all debug mock tests."""

  def SetUp(self):
    self.mocked_debug_client = api_mock.Client(
        core_apis.GetClientClass('clouddebugger', 'v2'))
    self.mocked_debug_client.Mock()
    self.debug_messages = core_apis.GetMessagesModule('clouddebugger', 'v2')
    self.mocked_resource_client = api_mock.Client(
        core_apis.GetClientClass('cloudresourcemanager', 'v1beta1'))
    self.resource_messages = core_apis.GetMessagesModule(
        'cloudresourcemanager', 'v1beta1')
    self.mocked_resource_client.Mock()
    self.addCleanup(self.mocked_debug_client.Unmock)
    self.addCleanup(self.mocked_resource_client.Unmock)

  def MakeDebuggeeLabels(self, labelmap):
    return self.debug_messages.Debuggee.LabelsValue(additionalProperties=[
        self.debug_messages.Debuggee.LabelsValue.AdditionalProperty(
            key=k, value=v)
        for k, v  in six.iteritems(labelmap)])

  def MakeDebuggees(self, label_formats, start_index=0, count=10,
                    description_format=None):
    result = []
    for i in range(start_index, start_index + count):
      debuggee_id = '0123456789abcd-0123-{0}'.format(i)
      description = description_format.format(i) if description_format else None
      label_properties = [
          self.debug_messages.Debuggee.LabelsValue.AdditionalProperty(
              key=key, value=value.format(i))
          for key, value in six.iteritems(label_formats)]
      result.append(
          debug.Debuggee(self.debug_messages.Debuggee(
              project='12345', id=debuggee_id, description=description,
              labels=self.debug_messages.Debuggee.LabelsValue(
                  additionalProperties=label_properties))))
    return result

  def MakeBreakpoints(self, label_formats=None, start_index=0, count=10,
                      id_format='0123456789abcdef-1234-{0}',
                      location_format=None, action=None):
    result = []
    location = None
    labels = None
    for i in range(start_index, start_index + count):
      breakpoint_id = id_format.format(i)
      if location_format:
        path, line = location_format.format(i).split(':')
        location = self.debug_messages.SourceLocation(path=path, line=int(line))
      if label_formats:
        labels = self.debug_messages.Breakpoint.LabelsValue(
            additionalProperties=[
                self.debug_messages.Debuggee.LabelsValue.AdditionalProperty(
                    key=key, value=value.format(i))
                for key, value in six.iteritems(label_formats)])
      result.append(self.debug_messages.Breakpoint(
          id=breakpoint_id, location=location, action=action, labels=labels))
    return result


class _DebugTestWithDebugger(_DebugMockApiTest):

  def SetUp(self):
    self.project_id = 'test_project'
    self.project_number = '12345'
    self.debugger = debug.Debugger(
        'test_project',
        debug_client=self.mocked_debug_client,
        debug_messages=self.debug_messages,
        resource_client=self.mocked_resource_client,
        resource_messages=self.resource_messages)


class _DebugTestWithDebuggee(_DebugTestWithDebugger):

  def SetUp(self):
    self.debuggee = debug.Debuggee(
        self.debug_messages.Debuggee(
            project=str(self.project_number),
            id='test-default-debuggee', uniquifier='unique-12345',
            labels=self.debug_messages.Debuggee.LabelsValue(
                additionalProperties=[
                    self.debug_messages.Debuggee.LabelsValue.AdditionalProperty(
                        key='module', value='test-gae-module'),
                    self.debug_messages.Debuggee.LabelsValue.AdditionalProperty(
                        key='minorversion', value='123456789')])),
        debug_client=self.mocked_debug_client,
        debug_messages=self.debug_messages,
        resource_client=self.mocked_resource_client,
        resource_messages=self.resource_messages)
    self.StartObjectPatch(self.debugger, 'DefaultDebuggee',
                          return_value=self.debuggee)


def _DummyHttpError(message='dummy_error_message'):
  return http_error.MakeHttpError(404, message=message, url='http://dummy/URL')


class _AttrDict(object):
  """Converts a dict to a set of read-only attributes.

  Unknown identifiers are mapped to None.
  """

  def __init__(self, d):
    self.members_ = d

  def __getattr__(self, attr):
    return self.members_.get(attr, None)


class FunctionalTests(_DebugMockApiTest):

  def testSplitLogExpressionsSimple(self):
    self.assertEqual(
        debug.SplitLogExpressions('a={a}, b={b}, c={c}'),
        ('a=$0, b=$1, c=$2', ['a', 'b', 'c']))

  def testSplitLogExpressionEscapedDollar(self):
    self.assertEqual(
        debug.SplitLogExpressions('$ {abc$}$ $0'),
        ('$$ $0$$ $$0', ['abc$']))

  def testSplitLogExpressionsRepeatedField(self):
    self.assertEqual(
        debug.SplitLogExpressions('a={a}, b={b}, a={a}, c={c}, b={b}'),
        ('a=$0, b=$1, a=$0, c=$2, b=$1', ['a', 'b', 'c']))

  def testSplitLogExpressionsNestedBraces(self):
    self.assertEqual(
        debug.SplitLogExpressions('a={{a} and {b}}, b={a{b{{cde}f}}g}'),
        ('a=$0, b=$1', ['{a} and {b}', 'a{b{{cde}f}}g']))

  def testSplitLogExpressionsTrailingNumbers(self):
    self.assertEqual(
        debug.SplitLogExpressions('a={abc}100'),
        ('a=$0 100', ['abc']))

  def testSplitLogExpressionsUnbalancedRight(self):
    with self.assertRaisesRegex(errors.InvalidLogFormatException,
                                'too many'):
      debug.SplitLogExpressions('a={abc}}')

  def testSplitLogExpressionsUnbalancedLeft(self):
    with self.assertRaisesRegex(errors.InvalidLogFormatException,
                                'too many'):
      debug.SplitLogExpressions('a={{a}')

  def testMergeLogExpressionsSimple(self):
    self.assertEqual('a={a}, b={b}, c={c}',
                     debug.MergeLogExpressions(
                         'a=$0, b=$1, c=$2', ['a', 'b', 'c']))

  def testMergeLogExpressionsRepeatedField(self):
    self.assertEqual('a={a}, b={b}, a={a}, c={c}, b={b}',
                     debug.MergeLogExpressions(
                         'a=$0, b=$1, a=$0, c=$2, b=$1', ['a', 'b', 'c']))

  def testMergeLogExpressionsEscapedDollar(self):
    self.assertEqual('{a} $0 ${a} {b$} $2',
                     debug.MergeLogExpressions(
                         '$0 $$0 $$$0 $1 $2', ['a', 'b$']))

  def testMergeLogExpressionsBogusFormat(self):
    self.assertEqual('}a={a}, b={b}, a={a}, c={c}, b={b}{',
                     debug.MergeLogExpressions(
                         '}a=$0, b=$1, a=$0, c=$2, b=$1{', ['a', 'b', 'c']))

  def testLogQueryV2StringNoText(self):
    self.assertEqual(
        'resource.type=gae_app '
        'logName:request_log '
        'resource.labels.module_id="test-svc" '
        'resource.labels.version_id="v1" '
        'severity=INFO',
        debug.LogQueryV2String(
            _AttrDict({'service': 'test-svc', 'version': 'v1'})))

  def testLogQueryV2StringWithText(self):
    self.assertEqual(
        'resource.type=gae_app '
        'logName:request_log '
        'resource.labels.module_id="test-svc" '
        'resource.labels.version_id="v1" '
        'severity=INFO '
        '"test string"',
        debug.LogQueryV2String(
            _AttrDict({
                'service': 'test-svc',
                'version': 'v1',
                'logLevel':
                    self.debug_messages.Breakpoint.LogLevelValueValuesEnum.INFO,
                'logMessageFormat': 'test string'
            })))

  def testLogQueryV2StringWithExpressions(self):
    self.assertEqual(
        'resource.type=gae_app '
        'logName:request_log '
        'resource.labels.module_id="test-svc" '
        'resource.labels.version_id="v1" '
        'severity=INFO '
        '"test string " " string2 " " string3 string 4"',
        debug.LogQueryV2String(
            _AttrDict({
                'service': 'test-svc',
                'version': 'v1',
                'logLevel':
                    self.debug_messages.Breakpoint.LogLevelValueValuesEnum.INFO,
                'logMessageFormat':
                    'test string {expression} string2 {expr2} string3 string 4'
            })))

  def testLogViewUrlNoText(self):
    self.assertEqual(
        'https://console.cloud.google.com/logs?project=test-project&'
        'advancedFilter='
        'resource.type%3Dgae_app%0A'
        'logName%3Arequest_log%0A'
        'resource.labels.module_id%3D%22test-svc%22%0A'
        'resource.labels.version_id%3D%22v1%22%0A'
        'severity%3DINFO%0A',
        debug.LogViewUrl(
            _AttrDict({
                'project': 'test-project',
                'service': 'test-svc',
                'version': 'v1'})))

  def testLogViewUrlWithText(self):
    self.assertEqual(
        'https://console.cloud.google.com/logs?project=test-project&'
        'advancedFilter='
        'resource.type%3Dgae_app%0A'
        'logName%3Arequest_log%0A'
        'resource.labels.module_id%3D%22test-svc%22%0A'
        'resource.labels.version_id%3D%22v1%22%0A'
        'severity%3DINFO%0A'
        '%22test+string%22%0A',
        debug.LogViewUrl(
            _AttrDict({
                'project': 'test-project',
                'service': 'test-svc',
                'version': 'v1',
                'logLevel':
                    self.debug_messages.Breakpoint.LogLevelValueValuesEnum.INFO,
                'logMessageFormat': 'test string'
            })))

  def testLogViewUrlWithExpressions(self):
    self.assertEqual(
        'https://console.cloud.google.com/logs?project=test-project&'
        'advancedFilter='
        'resource.type%3Dgae_app%0A'
        'logName%3Arequest_log%0A'
        'resource.labels.module_id%3D%22test-svc%22%0A'
        'resource.labels.version_id%3D%22v1%22%0A'
        'severity%3DINFO%0A'
        '%22test+string+%22+%22+string2+%22+%22+string3+string+4%22%0A',
        debug.LogViewUrl(
            _AttrDict({
                'project': 'test-project',
                'service': 'test-svc',
                'version': 'v1',
                'logLevel':
                    self.debug_messages.Breakpoint.LogLevelValueValuesEnum.INFO,
                'logMessageFormat':
                    'test string {expression} string2 {expr2} string3 string 4'
            })))


class DebuggeeTest(_DebugMockApiTest):

  def testDebuggeeId(self):
    debuggee = debug.Debuggee(self.debug_messages.Debuggee(
        project='567890',
        labels=self.MakeDebuggeeLabels({'module': 'testmodule',
                                        'version': 'testversion'})))
    self.assertEqual(debuggee.name, 'testmodule-testversion')

  def testDebuggeeIdModuleOnly(self):
    debuggee = debug.Debuggee(self.debug_messages.Debuggee(
        project='567890',
        labels=self.MakeDebuggeeLabels({'module': 'testmodule'})))
    self.assertEqual(debuggee.name, 'testmodule-' + debug.DEFAULT_VERSION)

  def testDebuggeeIdVersionOnly(self):
    debuggee = debug.Debuggee(self.debug_messages.Debuggee(
        project='567890',
        labels=self.MakeDebuggeeLabels({'version': 'testversion'})))
    self.assertEqual(debuggee.name, debug.DEFAULT_MODULE + '-testversion')

  def testDebuggeeIdNoLabels(self):
    debuggee = debug.Debuggee(self.debug_messages.Debuggee(
        project='567890', id='test-id', description='test-description'))
    self.assertEqual(debuggee.name, 'test-description')


class DebuggerTest(_DebugTestWithDebugger):

  def SetUp(self):
    self.maxDiff = 4000

  def testListDebuggees(self):
    debuggees = [
        self.debug_messages.Debuggee(id='debuggee{0}'.format(i),
                                     project=self.project_number)
        for i in range(0, 10)]
    self.mocked_debug_client.debugger_debuggees.List.Expect(
        request=self.debug_messages.ClouddebuggerDebuggerDebuggeesListRequest(
            project=self.project_id, includeInactive=False,
            clientVersion=debug.DebugObject.CLIENT_VERSION),
        response=self.debug_messages.ListDebuggeesResponse(debuggees=debuggees))
    result = list(self.debugger.ListDebuggees())
    expected = [
        debug.Debuggee(debuggee)
        for debuggee in debuggees]
    self.assertEqual(expected, result)

  def testListDebuggeesMultipleMinorVersions(self):
    response = [
        self.debug_messages.Debuggee(
            id='debuggee{0}-{1}'.format(module, minor),
            project=self.project_number,
            labels=self.MakeDebuggeeLabels({
                'module': 'noise{0}'.format(module),
                'minorversion': '{0}'.format(minor)}))
        for module in range(0, 10) for minor in range(5, 12)]
    self.mocked_debug_client.debugger_debuggees.List.Expect(
        request=self.debug_messages.ClouddebuggerDebuggerDebuggeesListRequest(
            project=self.project_id, includeInactive=False,
            clientVersion=debug.DebugObject.CLIENT_VERSION),
        response=self.debug_messages.ListDebuggeesResponse(debuggees=response))
    result = list(self.debugger.ListDebuggees())
    expected = [
        debug.Debuggee(self.debug_messages.Debuggee(
            id='debuggee{0}-11'.format(i), project=self.project_number,
            labels=self.MakeDebuggeeLabels({'module': 'noise{0}'.format(i),
                                            'minorversion': '11'})))
        for i in range(0, 10)]
    self.assertEqual(sorted(expected, key=lambda d: d.target_id),
                     sorted(result, key=lambda d: d.target_id))

  def testListDebuggeesMultipleMinorVersionsOneMissing(self):
    # Make one module instance with no minorversion. This will cause all minor
    # versions for that module to be returned
    response = [
        self.debug_messages.Debuggee(
            id='debuggee10', project=self.project_number,
            labels=self.MakeDebuggeeLabels({'module': 'noise10'}))]
    response += [
        self.debug_messages.Debuggee(
            id='debuggee10-{0}'.format(minor),
            project=self.project_number,
            labels=self.MakeDebuggeeLabels(
                {'module': 'noise10',
                 'minorversion': '{0}'.format(minor)}))
        for minor in range(0, 10)]
    self.mocked_debug_client.debugger_debuggees.List.Expect(
        request=self.debug_messages.ClouddebuggerDebuggerDebuggeesListRequest(
            project=self.project_id, includeInactive=False,
            clientVersion=debug.DebugObject.CLIENT_VERSION),
        response=self.debug_messages.ListDebuggeesResponse(debuggees=response))
    result = list(self.debugger.ListDebuggees())
    expected = [debug.Debuggee(debuggee) for debuggee in response]
    self.assertEqual(sorted(expected, key=lambda d: d.target_id),
                     sorted(result, key=lambda d: d.target_id))

  def testListDebuggeesMultipleMinorVersionsOneInvalid(self):
    # Make one module instance with no minorversion. This will cause all minor
    # versions for that module to be returned
    response = [
        self.debug_messages.Debuggee(
            id='debuggee10', project=self.project_number,
            labels=self.MakeDebuggeeLabels(
                {'module': 'noise10',
                 'minorversion': 'bogus_value'}))]
    response += [
        self.debug_messages.Debuggee(
            id='debuggee10-{0}'.format(minor),
            project=self.project_number,
            labels=self.MakeDebuggeeLabels(
                {'module': 'noise10',
                 'minorversion': '{0}'.format(minor)}))
        for minor in range(0, 10)]
    self.mocked_debug_client.debugger_debuggees.List.Expect(
        request=self.debug_messages.ClouddebuggerDebuggerDebuggeesListRequest(
            project=self.project_id, includeInactive=False,
            clientVersion=debug.DebugObject.CLIENT_VERSION),
        response=self.debug_messages.ListDebuggeesResponse(debuggees=response))
    result = list(self.debugger.ListDebuggees())
    expected = [debug.Debuggee(debuggee) for debuggee in response]
    self.assertEqual(sorted(expected, key=lambda d: d.target_id),
                     sorted(result, key=lambda d: d.target_id))

  def testListDebuggeesError(self):
    self.mocked_debug_client.debugger_debuggees.List.Expect(
        request=self.debug_messages.ClouddebuggerDebuggerDebuggeesListRequest(
            project=self.project_id, includeInactive=False,
            clientVersion=debug.DebugObject.CLIENT_VERSION),
        exception=_DummyHttpError())
    with self.AssertRaisesHttpExceptionMatches(
        'Resource not found API reason: dummy_error_message'):
      list(self.debugger.ListDebuggees())

  def testNoDefaultDebuggeeError(self):
    self.StartObjectPatch(debug.Debugger, 'ListDebuggees', return_value=[])
    with self.assertRaises(errors.NoDebuggeeError):
      self.debugger.DefaultDebuggee()

  def testDefaultDebuggeeMultipleModulesNoMinorVersionError(self):
    list_result = self.MakeDebuggees({'module': 'noise{0}'})
    self.StartObjectPatch(debug.Debugger, 'ListDebuggees',
                          return_value=list_result)
    with self.assertRaises(errors.MultipleDebuggeesError):
      self.debugger.DefaultDebuggee()

  def testDefaultDebuggeeMultipleModulesError(self):
    list_result = self.MakeDebuggees(
        {'module': 'noise{0}', 'minorversion': '1'})
    self.StartObjectPatch(debug.Debugger, 'ListDebuggees',
                          return_value=list_result)
    with self.assertRaises(errors.MultipleDebuggeesError):
      self.debugger.DefaultDebuggee()

  def testDefaultDebuggeeMultipleVersionError(self):
    list_result = self.MakeDebuggees(
        {'version': 'noise{0}', 'minorversion': '1'})
    self.StartObjectPatch(debug.Debugger, 'ListDebuggees',
                          return_value=list_result)
    with self.assertRaises(errors.MultipleDebuggeesError):
      self.debugger.DefaultDebuggee()

  def testFindDebuggeeDefaultOneDebuggee(self):
    expected = debug.Debuggee(self.debug_messages.Debuggee(
        project=self.project_number,
        labels=self.MakeDebuggeeLabels({'version': 'testversion'})))
    self.StartObjectPatch(debug.Debugger, 'ListDebuggees',
                          return_value=[expected])
    self.assertEqual(expected, self.debugger.FindDebuggee())

  def testFindDebuggeeByID(self):
    expected = debug.Debuggee(self.debug_messages.Debuggee(
        project=self.project_number, id='expected',
        labels=self.MakeDebuggeeLabels({'module': 'testmodule',
                                        'version': 'testversion'})))
    list_result = self.MakeDebuggees({'module': 'noise{0}'})
    list_result.append(expected)
    list_result.extend(self.MakeDebuggees({'module': 'noise{0}',
                                           'version': 'testversion{0}'},
                                          start_index=10))
    self.StartObjectPatch(debug.Debugger, 'ListDebuggees',
                          return_value=list_result)
    self.assertEqual(expected, self.debugger.FindDebuggee('expected'))

  def testFindDebuggeeByExactName(self):
    expected = debug.Debuggee(self.debug_messages.Debuggee(
        project=self.project_number, id='expected',
        labels=self.MakeDebuggeeLabels({'module': 'testmodule-with-pattern',
                                        'version': 'testversion'})))
    list_result = self.MakeDebuggees({'module': 'noise{0}'})
    list_result.append(expected)
    list_result.append(debug.Debuggee(self.debug_messages.Debuggee(
        project=self.project_number, id='expected',
        labels=self.MakeDebuggeeLabels({'module': 'testmodule-with-pattern',
                                        'version': 'testversion-nomatch'}))))
    list_result.extend(self.MakeDebuggees({'module': 'noise{0}',
                                           'version': 'testversion{0}'},
                                          start_index=10))
    self.StartObjectPatch(debug.Debugger, 'ListDebuggees',
                          return_value=list_result)
    self.assertEqual(
        expected,
        self.debugger.FindDebuggee('testmodule-with-pattern-testversion'))

  def testFindDebuggeeByNamePattern(self):
    expected = debug.Debuggee(self.debug_messages.Debuggee(
        project=self.project_number, id='expected',
        labels=self.MakeDebuggeeLabels({'module': 'testmodule-with-pattern',
                                        'version': 'testversion'})))
    list_result = self.MakeDebuggees({'module': 'noise{0}'})
    list_result.append(expected)
    list_result.extend(self.MakeDebuggees({'module': 'noise{0}',
                                           'version': 'testversion{0}'},
                                          start_index=10))
    self.StartObjectPatch(debug.Debugger, 'ListDebuggees',
                          return_value=list_result)
    self.assertEqual(expected, self.debugger.FindDebuggee('pat..rn'))

  def testFindDebuggeeByDescription(self):
    expected = debug.Debuggee(self.debug_messages.Debuggee(
        project=self.project_number, id='expected',
        description='desc_with_pattern_in_it',
        labels=self.MakeDebuggeeLabels({'module': 'testmodule',
                                        'version': 'testversion'})))
    list_result = self.MakeDebuggees({'module': 'noise{0}'},
                                     description_format='noisy description{0}')
    list_result.append(expected)
    list_result.extend(self.MakeDebuggees(
        {'module': 'noise{0}', 'version': 'testversion{0}'}, start_index=10,
        description_format='noisy description{0}'))
    self.StartObjectPatch(debug.Debugger, 'ListDebuggees',
                          return_value=list_result)
    self.assertEqual(expected, self.debugger.FindDebuggee('pat..rn'))

  def testFindDebuggeeStaleMinorVersionsById(self):
    response = [
        self.debug_messages.Debuggee(
            id='debuggee0-{0}'.format(minor),
            project=self.project_number,
            labels=self.MakeDebuggeeLabels({
                'module': 'noise0',
                'minorversion': '{0}'.format(minor)}))
        for minor in range(0, 2)]
    self.mocked_debug_client.debugger_debuggees.List.Expect(
        request=self.debug_messages.ClouddebuggerDebuggerDebuggeesListRequest(
            project=self.project_id, includeInactive=False,
            clientVersion=debug.DebugObject.CLIENT_VERSION),
        response=self.debug_messages.ListDebuggeesResponse(debuggees=[]))
    self.mocked_debug_client.debugger_debuggees.List.Expect(
        request=self.debug_messages.ClouddebuggerDebuggerDebuggeesListRequest(
            project=self.project_id, includeInactive=True,
            clientVersion=debug.DebugObject.CLIENT_VERSION),
        response=self.debug_messages.ListDebuggeesResponse(debuggees=response))
    self.assertEqual(debug.Debuggee(response[0]),
                     self.debugger.FindDebuggee('debuggee0-0'))

  def testFindDebuggeeStaleMinorVersionByPatternError(self):
    response = [
        self.debug_messages.Debuggee(
            id='debuggee0-{0}'.format(minor),
            project=self.project_number,
            labels=self.MakeDebuggeeLabels({
                'module': 'noise0',
                'minorversion': '{0}'.format(minor)}))
        for minor in range(0, 2)]
    self.mocked_debug_client.debugger_debuggees.List.Expect(
        request=self.debug_messages.ClouddebuggerDebuggerDebuggeesListRequest(
            project=self.project_id, includeInactive=False,
            clientVersion=debug.DebugObject.CLIENT_VERSION),
        response=self.debug_messages.ListDebuggeesResponse(debuggees=response))
    self.mocked_debug_client.debugger_debuggees.List.Expect(
        request=self.debug_messages.ClouddebuggerDebuggerDebuggeesListRequest(
            project=self.project_id, includeInactive=True,
            clientVersion=debug.DebugObject.CLIENT_VERSION),
        response=self.debug_messages.ListDebuggeesResponse(debuggees=[]))
    with self.assertRaises(errors.NoDebuggeeError):
      self.debugger.FindDebuggee('debuggee[0-9]-0')

  def testFindDebuggeeByPatternNoDebuggeesError(self):
    self.StartObjectPatch(debug.Debugger, 'ListDebuggees', return_value=[])
    with self.assertRaises(errors.NoDebuggeeError):
      self.debugger.FindDebuggee('bogus_pattern')

  def testFindDebuggeeNoMatchError(self):
    list_result = self.MakeDebuggees({'module': 'noise{0}'})
    self.StartObjectPatch(debug.Debugger, 'ListDebuggees',
                          return_value=list_result)
    try:
      self.debugger.FindDebuggee('bogus_pattern')
    except errors.NoDebuggeeError as e:
      message = str(e)
      self.assertRegexpMatches(message, r'No active.*bogus_pattern')
      for d in list_result:
        self.assertRegexpMatches(message, d.name)

  def testFindDebuggeeMultipleError(self):
    list_result = self.MakeDebuggees({'module': 'noise{0}'})
    self.StartObjectPatch(debug.Debugger, 'ListDebuggees',
                          return_value=list_result)
    try:
      self.debugger.FindDebuggee('noise[1-9].*')
    except errors.MultipleDebuggeesError as e:
      message = str(e)
      self.assertRegexpMatches(message,
                               r'Multiple possible.*noise\[1-9\]\.\*"')
      self.assertNotRegexpMatches(message, list_result[0].name)
      for i in range(1, 10):
        self.assertRegexpMatches(message, list_result[i].name)


class BreakpointTest(_DebugTestWithDebuggee):

  def testGetBreakpoint(self):
    breakpoint = self.debug_messages.Breakpoint(id='test_breakpoint')
    self.mocked_debug_client.debugger_debuggees_breakpoints.Get.Expect(
        request=(
            self.debug_messages.
            ClouddebuggerDebuggerDebuggeesBreakpointsGetRequest(
                breakpointId='test_breakpoint',
                debuggeeId=self.debuggee.target_id,
                clientVersion=debug.DebugObject.CLIENT_VERSION)),
        response=self.debug_messages.GetBreakpointResponse(
            breakpoint=breakpoint))
    result = self.debuggee.GetBreakpoint(breakpoint.id)
    self.assertEqual(self.debuggee.AddTargetInfo(breakpoint), result)

  def testGetBreakpointError(self):
    self.mocked_debug_client.debugger_debuggees_breakpoints.Get.Expect(
        request=(
            self.debug_messages.
            ClouddebuggerDebuggerDebuggeesBreakpointsGetRequest(
                breakpointId='test_breakpoint',
                debuggeeId=self.debuggee.target_id,
                clientVersion=debug.DebugObject.CLIENT_VERSION)),
        exception=_DummyHttpError())
    with self.AssertRaisesHttpExceptionMatches(
        'Resource not found API reason: dummy_error_message'):
      list(self.debuggee.GetBreakpoint('test_breakpoint'))

  def testDelete(self):
    self.mocked_debug_client.debugger_debuggees_breakpoints.Delete.Expect(
        request=(
            self.debug_messages.
            ClouddebuggerDebuggerDebuggeesBreakpointsDeleteRequest(
                breakpointId='test_breakpoint',
                debuggeeId=self.debuggee.target_id,
                clientVersion=debug.DebugObject.CLIENT_VERSION)),
        response=self.debug_messages.Empty())
    self.debuggee.DeleteBreakpoint('test_breakpoint')

  def testDeleteFailure(self):
    self.mocked_debug_client.debugger_debuggees_breakpoints.Delete.Expect(
        request=(
            self.debug_messages.
            ClouddebuggerDebuggerDebuggeesBreakpointsDeleteRequest(
                breakpointId='test_breakpoint',
                debuggeeId=self.debuggee.target_id,
                clientVersion=debug.DebugObject.CLIENT_VERSION)),
        exception=_DummyHttpError())
    with self.AssertRaisesHttpExceptionMatches(
        'Resource not found API reason: dummy_error_message'):
      self.debuggee.DeleteBreakpoint('test_breakpoint')

  def _doBreakpointsTest(self, restrict_to_type=None):
    snapshots = self.MakeBreakpoints(
        action=self.debug_messages.Breakpoint.ActionValueValuesEnum.CAPTURE)
    logpoints = self.MakeBreakpoints(
        action=self.debug_messages.Breakpoint.ActionValueValuesEnum.LOG,
        start_index=10)
    breakpoints = snapshots + logpoints
    self.mocked_debug_client.debugger_debuggees_breakpoints.List.Expect(
        request=(
            self.debug_messages.
            ClouddebuggerDebuggerDebuggeesBreakpointsListRequest(
                debuggeeId=self.debuggee.target_id, includeAllUsers=False,
                includeInactive=False,
                clientVersion=debug.DebugObject.CLIENT_VERSION)),
        response=self.debug_messages.ListBreakpointsResponse(
            breakpoints=breakpoints))
    result = self.debuggee.ListBreakpoints(restrict_to_type=restrict_to_type)
    if not restrict_to_type:
      expected = [self.debuggee.AddTargetInfo(breakpoint)
                  for breakpoint in breakpoints]
      self.assertEqual(expected, result)
    elif restrict_to_type == self.debuggee.SNAPSHOT_TYPE:
      expected = [self.debuggee.AddTargetInfo(breakpoint)
                  for breakpoint in snapshots]
      self.assertEqual(expected, result)
      for r in result:
        self.assertTrue('bp=' in r.consoleViewUrl)
    else:
      expected = [self.debuggee.AddTargetInfo(breakpoint)
                  for breakpoint in logpoints]
      self.assertEqual(expected, result)
      for r in result:
        self.assertTrue(self.debuggee.service in r.logViewUrl)

  def testListBreakpoints(self):
    self._doBreakpointsTest()
    self._doBreakpointsTest(self.debuggee.SNAPSHOT_TYPE)
    self._doBreakpointsTest(self.debuggee.LOGPOINT_TYPE)

  def testListBreakpointsError(self):
    self.mocked_debug_client.debugger_debuggees_breakpoints.List.Expect(
        request=(
            self.debug_messages.
            ClouddebuggerDebuggerDebuggeesBreakpointsListRequest(
                debuggeeId=self.debuggee.target_id, includeAllUsers=False,
                includeInactive=False,
                clientVersion=debug.DebugObject.CLIENT_VERSION)),
        exception=_DummyHttpError())
    with self.AssertRaisesHttpExceptionMatches(
        'Resource not found API reason: dummy_error_message'):
      self.debuggee.ListBreakpoints()

  def testListBreakpointsBadRegexError(self):
    with self.assertRaises(errors.InvalidLocationException):
      self.debuggee.ListBreakpoints(['*'])

  def testListBreakpointsEmptyList(self):
    breakpoints = self.MakeBreakpoints()
    self.mocked_debug_client.debugger_debuggees_breakpoints.List.Expect(
        request=(
            self.debug_messages.
            ClouddebuggerDebuggerDebuggeesBreakpointsListRequest(
                debuggeeId=self.debuggee.target_id, includeAllUsers=False,
                includeInactive=False,
                clientVersion=debug.DebugObject.CLIENT_VERSION)),
        response=self.debug_messages.ListBreakpointsResponse(
            breakpoints=breakpoints))
    expected = [self.debuggee.AddTargetInfo(b) for b in breakpoints]
    response = self.debuggee.ListBreakpoints()
    self.assertEqual(response, expected)

  def testListBreakpointsByID(self):
    breakpoints = self.MakeBreakpoints()
    # Set a couple to final state to ensure they get included
    breakpoints[1].isFinalState = True
    breakpoints[5].isFinalState = True

    # Make one of the breakpoints include an error
    breakpoints[1].status = self.debug_messages.StatusMessage(isError=True)

    self.mocked_debug_client.debugger_debuggees_breakpoints.List.Expect(
        request=(
            self.debug_messages.
            ClouddebuggerDebuggerDebuggeesBreakpointsListRequest(
                debuggeeId=self.debuggee.target_id, includeAllUsers=False,
                includeInactive=True,
                clientVersion=debug.DebugObject.CLIENT_VERSION)),
        response=self.debug_messages.ListBreakpointsResponse(
            breakpoints=breakpoints))
    expected = (
        [self.debuggee.AddTargetInfo(breakpoints[i])
         for i in [0, 1, 3, 5, 6, 7, 8]])
    response = self.debuggee.ListBreakpoints(
        resource_ids=[b.id for b in expected])
    self.assertEqual(response, expected)
    self.assertTrue('consoleViewUrl' in response[0])
    self.assertTrue('consoleViewUrl' not in response[1])
    self.assertTrue('consoleViewUrl' in response[2])

  def testListBreakpointsByIDAndPatterns(self):
    breakpoints = self.MakeBreakpoints(location_format='foo/bar:{0}')
    # Set a couple to final state to ensure they get included
    breakpoints[1].isFinalState = True
    breakpoints[5].isFinalState = True
    breakpoints[6].isFinalState = True

    # Make one of the breakpoints include an error
    breakpoints[1].status = self.debug_messages.StatusMessage(isError=True)

    self.mocked_debug_client.debugger_debuggees_breakpoints.List.Expect(
        request=(
            self.debug_messages.
            ClouddebuggerDebuggerDebuggeesBreakpointsListRequest(
                debuggeeId=self.debuggee.target_id, includeAllUsers=False,
                includeInactive=True,
                clientVersion=debug.DebugObject.CLIENT_VERSION)),
        response=self.debug_messages.ListBreakpointsResponse(
            breakpoints=breakpoints))
    # Note that 7 is in both lists, to ensure we don't get duplicates if a
    # breakpoint matches both ways. Also, 6 is in the by_pattern list, but
    # should not be returned because the pattern should not match against a
    # breakpoint that is in the final state.
    by_pattern = [3, '[67]', 8]
    by_id = [0, 1, 5, 7]
    expected = [self.debuggee.AddTargetInfo(breakpoints[i])
                for i in [0, 1, 3, 5, 7, 8]]
    response = self.debuggee.ListBreakpoints(
        ['foo/bar:{0}'.format(p) for p in by_pattern],
        resource_ids=[breakpoints[i].id for i in by_id])
    self.assertEqual(response, expected)
    self.assertTrue('consoleViewUrl' in response[0])
    self.assertTrue('consoleViewUrl' not in response[1])
    self.assertTrue('consoleViewUrl' in response[2])

  def testListBreakpointsMissingIDError(self):
    breakpoints = self.MakeBreakpoints()
    self.mocked_debug_client.debugger_debuggees_breakpoints.List.Expect(
        request=(
            self.debug_messages.
            ClouddebuggerDebuggerDebuggeesBreakpointsListRequest(
                debuggeeId=self.debuggee.target_id, includeAllUsers=False,
                includeInactive=True,
                clientVersion=debug.DebugObject.CLIENT_VERSION)),
        response=self.debug_messages.ListBreakpointsResponse(
            breakpoints=breakpoints))
    ids = [b.id for b in breakpoints]
    bad_ids = ['0123456789abcdef-1234-9999', '0123456789abcdef-1234-aaaa']
    try:
      self.debuggee.ListBreakpoints(resource_ids=ids + bad_ids)
      self.assertTrue(False, msg='ListBreakpoints did not fail as expected')
    except errors.BreakpointNotFoundError as e:
      message = str(e)
      for i in bad_ids:
        self.assertRegexpMatches(message, i + '([^0-9]|$)')
      for i in ids:
        self.assertNotRegexpMatches(message, i + '([^0-9]|$)')

  def testListBreakpointsInactivePatternError(self):
    breakpoints = self.MakeBreakpoints(location_format='foo/bar:{0}')
    self.mocked_debug_client.debugger_debuggees_breakpoints.List.Expect(
        request=(
            self.debug_messages.
            ClouddebuggerDebuggerDebuggeesBreakpointsListRequest(
                debuggeeId=self.debuggee.target_id, includeAllUsers=False,
                includeInactive=True,
                clientVersion=debug.DebugObject.CLIENT_VERSION)),
        response=self.debug_messages.ListBreakpointsResponse(
            breakpoints=breakpoints))
    breakpoints[1].isFinalState = True
    with self.assertRaises(errors.NoMatchError):
      self.debuggee.ListBreakpoints(
          ['foo/bar:1'],
          resource_ids=[b.id for b in breakpoints if b != breakpoints[1]])

  def testListBreakpointsByResourceURI(self):
    breakpoints = self.MakeBreakpoints()
    # Set a couple to final state to ensure they get included
    breakpoints[1].isFinalState = True
    breakpoints[5].isFinalState = True
    self.mocked_debug_client.debugger_debuggees_breakpoints.List.Expect(
        request=(
            self.debug_messages.
            ClouddebuggerDebuggerDebuggeesBreakpointsListRequest(
                debuggeeId=self.debuggee.target_id, includeAllUsers=False,
                includeInactive=True,
                clientVersion=debug.DebugObject.CLIENT_VERSION)),
        response=self.debug_messages.ListBreakpointsResponse(
            breakpoints=breakpoints))
    expected = [self.debuggee.AddTargetInfo(breakpoints[i*2])
                for i in range(0, len(breakpoints)//2)]
    response = self.debuggee.ListBreakpoints([], resource_ids=[
        'https://clouddebugger.googleapis.com/v2/debugger/'
        'debuggees/{0}/breakpoints/{1}'.format(self.debuggee.target_id, b.id)
        for b in expected])
    self.assertEqual(response, expected)

  def testListBreakpointsBadUrl(self):
    breakpoints = self.MakeBreakpoints()
    # Set a couple to final state to ensure they get included
    breakpoints[1].isFinalState = True
    breakpoints[5].isFinalState = True
    with self.assertRaises(resources.InvalidResourceException):
      self.debuggee.ListBreakpoints([], resource_ids=[
          'https://clouddebugger.googleapis.com/v2/debugger/'
          'debuggees/{0}/badcollection/bar'.format(self.debuggee.target_id)])

  def testListBreakpointsByFile(self):
    # Create at least 11 breakpoints to verify that bar:[15] doesn't match
    # bar:10
    breakpoints = self.MakeBreakpoints(location_format='foo/bar:{0}', count=201)
    # Set a couple to final state to ensure they do not get included
    breakpoints[1].isFinalState = True
    breakpoints[5].isFinalState = True
    self.mocked_debug_client.debugger_debuggees_breakpoints.List.Expect(
        request=(
            self.debug_messages.
            ClouddebuggerDebuggerDebuggeesBreakpointsListRequest(
                debuggeeId=self.debuggee.target_id, includeAllUsers=False,
                includeInactive=False,
                clientVersion=debug.DebugObject.CLIENT_VERSION)),
        response=self.debug_messages.ListBreakpointsResponse(
            breakpoints=breakpoints))
    expected = [self.debuggee.AddTargetInfo(breakpoints[i])
                for i in [2, 3, 4, 7, 8, 13, 15, 16, 17]]
    response = self.debuggee.ListBreakpoints(
        ['bar:[125]', 'bar:4', 'bar:[37]', 'foo/bar:8', 'bar:13|ar:14',
         '^foo/bar:15$', 'foo:?|bar:?16', '.*:17$', '.ar:[^0-35-9]'])
    self.assertEqual(response, expected)

  def testListBreakpointsIncludeInactive(self):
    breakpoints = self.MakeBreakpoints(location_format='foo/bar:{0}')
    # Set a couple to final state to ensure they get included
    breakpoints[1].isFinalState = True
    breakpoints[5].isFinalState = True
    self.mocked_debug_client.debugger_debuggees_breakpoints.List.Expect(
        request=(
            self.debug_messages.
            ClouddebuggerDebuggerDebuggeesBreakpointsListRequest(
                debuggeeId=self.debuggee.target_id, includeAllUsers=False,
                includeInactive=True,
                clientVersion=debug.DebugObject.CLIENT_VERSION)),
        response=self.debug_messages.ListBreakpointsResponse(
            breakpoints=breakpoints))
    expected = [self.debuggee.AddTargetInfo(breakpoints[i])
                for i in [1, 3, 4, 5, 7]]
    response = self.debuggee.ListBreakpoints(['bar:[15]', 'bar:4', 'bar:[37]'],
                                             include_inactive=True)
    self.assertEqual(response, expected)

  def testListBreakpointsNoMatch(self):
    breakpoints = self.MakeBreakpoints()
    self.mocked_debug_client.debugger_debuggees_breakpoints.List.Expect(
        request=(
            self.debug_messages.
            ClouddebuggerDebuggerDebuggeesBreakpointsListRequest(
                debuggeeId=self.debuggee.target_id, includeAllUsers=False,
                includeInactive=False,
                clientVersion=debug.DebugObject.CLIENT_VERSION)),
        response=self.debug_messages.ListBreakpointsResponse(
            breakpoints=breakpoints))
    with self.assertRaisesRegex(errors.NoMatchError, 'No breakpoint'):
      self.debuggee.ListBreakpoints(['not_there', 'me_either'])

  def testListMatchingSnapshotsNoMatch(self):
    breakpoints = self.MakeBreakpoints()
    self.mocked_debug_client.debugger_debuggees_breakpoints.List.Expect(
        request=(
            self.debug_messages.
            ClouddebuggerDebuggerDebuggeesBreakpointsListRequest(
                debuggeeId=self.debuggee.target_id, includeAllUsers=False,
                includeInactive=False,
                clientVersion=debug.DebugObject.CLIENT_VERSION)),
        response=self.debug_messages.ListBreakpointsResponse(
            breakpoints=breakpoints))
    with self.assertRaisesRegex(errors.NoMatchError, 'No snapshot'):
      self.debuggee.ListBreakpoints(
          ['not_there', 'me_either'],
          restrict_to_type=self.debuggee.SNAPSHOT_TYPE)

  def testListMatchingLogpointsNoMatch(self):
    breakpoints = self.MakeBreakpoints()
    self.mocked_debug_client.debugger_debuggees_breakpoints.List.Expect(
        request=(
            self.debug_messages.
            ClouddebuggerDebuggerDebuggeesBreakpointsListRequest(
                debuggeeId=self.debuggee.target_id, includeAllUsers=False,
                includeInactive=False,
                clientVersion=debug.DebugObject.CLIENT_VERSION)),
        response=self.debug_messages.ListBreakpointsResponse(
            breakpoints=breakpoints))
    with self.assertRaisesRegex(errors.NoMatchError, 'No logpoint'):
      self.debuggee.ListBreakpoints(
          ['not_there', 'me_either'],
          restrict_to_type=self.debuggee.LOGPOINT_TYPE)

  def testListWithFullDetails(self):
    breakpoints = self.MakeBreakpoints()
    breakpoints[0].isFinalState = True
    breakpoints[1].isFinalState = True
    breakpoints[2].isFinalState = True

    # Make one of the breakpoints include an error
    breakpoints[1].status = self.debug_messages.StatusMessage(isError=True)

    # Make one of them a logpoint
    breakpoints[2].action = (
        self.debug_messages.Breakpoint.ActionValueValuesEnum.LOG)

    self.mocked_debug_client.debugger_debuggees_breakpoints.List.Expect(
        request=(
            self.debug_messages.
            ClouddebuggerDebuggerDebuggeesBreakpointsListRequest(
                debuggeeId=self.debuggee.target_id, includeAllUsers=False,
                includeInactive=True,
                clientVersion=debug.DebugObject.CLIENT_VERSION)),
        response=self.debug_messages.ListBreakpointsResponse(
            breakpoints=breakpoints))
    self.mocked_debug_client.debugger_debuggees_breakpoints.Get.Expect(
        request=(
            self.debug_messages.
            ClouddebuggerDebuggerDebuggeesBreakpointsGetRequest(
                breakpointId=breakpoints[0].id,
                debuggeeId=self.debuggee.target_id,
                clientVersion=debug.DebugObject.CLIENT_VERSION)),
        response=self.debug_messages.GetBreakpointResponse(
            breakpoint=breakpoints[0]))

    expected = ([
        self.debuggee.AddTargetInfo(breakpoints[i]) for i in [0, 1, 2, 3]
    ])
    response = self.debuggee.ListBreakpoints(
        resource_ids=[b.id for b in expected], full_details=True)
    self.assertEqual(response, expected)

  def testCreateSnapshot(self):
    breakpoint = self.debug_messages.Breakpoint(id='dummy-response-id')
    self.mocked_debug_client.debugger_debuggees_breakpoints.Set.Expect(
        request=self.debug_messages.
        ClouddebuggerDebuggerDebuggeesBreakpointsSetRequest(
            debuggeeId=self.debuggee.target_id,
            breakpoint=self.debug_messages.Breakpoint(
                location=self.debug_messages.SourceLocation(path='myfile',
                                                            line=1234),
                condition='dummy condition', expressions=['expression1'],
                labels=self.debug_messages.Breakpoint.LabelsValue(
                    additionalProperties=[
                        self.debug_messages.Breakpoint.LabelsValue.
                        AdditionalProperty(key='hello', value='world')]),
                userEmail='me@mine.com',
                action=(self.debug_messages.Breakpoint.ActionValueValuesEnum.
                        CAPTURE)),
            clientVersion=debug.DebugObject.CLIENT_VERSION),
        response=self.debug_messages.SetBreakpointResponse(
            breakpoint=breakpoint))
    response = self.debuggee.CreateSnapshot(
        'myfile:1234', condition='dummy condition', expressions=['expression1'],
        user_email='me@mine.com', labels={'hello': 'world'})
    self.assertEqual(response, self.debuggee.AddTargetInfo(breakpoint))

  def testCreateSnapshotFailure(self):
    self.mocked_debug_client.debugger_debuggees_breakpoints.Set.Expect(
        request=self.debug_messages.
        ClouddebuggerDebuggerDebuggeesBreakpointsSetRequest(
            debuggeeId=self.debuggee.target_id,
            breakpoint=self.debug_messages.Breakpoint(
                location=self.debug_messages.SourceLocation(path='myfile',
                                                            line=1234),
                action=(self.debug_messages.Breakpoint.ActionValueValuesEnum.
                        CAPTURE)),
            clientVersion=debug.DebugObject.CLIENT_VERSION),
        exception=_DummyHttpError())
    with self.AssertRaisesHttpExceptionMatches(
        'Resource not found API reason: dummy_error_message'):
      self.debuggee.CreateSnapshot('myfile:1234')

  def testCreateLogpoint(self):
    breakpoint = self.debug_messages.Breakpoint(id='dummy-response-id')
    self.mocked_debug_client.debugger_debuggees_breakpoints.Set.Expect(
        request=self.debug_messages.
        ClouddebuggerDebuggerDebuggeesBreakpointsSetRequest(
            debuggeeId=self.debuggee.target_id,
            breakpoint=self.debug_messages.Breakpoint(
                location=self.debug_messages.SourceLocation(path='myfile',
                                                            line=1234),
                condition='dummy condition', expressions=['expression1'],
                logLevel=(
                    self.debug_messages.
                    Breakpoint.LogLevelValueValuesEnum.ERROR),
                logMessageFormat='foo=$0',
                labels=self.debug_messages.Breakpoint.LabelsValue(
                    additionalProperties=[
                        self.debug_messages.Breakpoint.LabelsValue.
                        AdditionalProperty(key='hello', value='world')]),
                userEmail='me@mine.com',
                action=(self.debug_messages.Breakpoint.ActionValueValuesEnum.
                        LOG)),
            clientVersion=debug.DebugObject.CLIENT_VERSION),
        response=self.debug_messages.SetBreakpointResponse(
            breakpoint=breakpoint))
    response = self.debuggee.CreateLogpoint(
        'myfile:1234', 'foo={expression1}', condition='dummy condition',
        user_email='me@mine.com', labels={'hello': 'world'}, log_level='error')
    self.assertEqual(response, self.debuggee.AddTargetInfo(breakpoint))

  def testCreateLogpointNoLocationFailure(self):
    with self.assertRaisesRegex(errors.InvalidLocationException,
                                'location must not be empty'):
      self.debuggee.CreateLogpoint('', 'dummy text')

  def testCreateLogpointBadLocationFailure(self):
    with self.assertRaisesRegex(errors.InvalidLocationException,
                                'must be of the form'):
      self.debuggee.CreateLogpoint('bogus_location', 'dummy text')

  def testCreateLogpointNoFormatFailure(self):
    with self.assertRaisesRegex(errors.InvalidLogFormatException,
                                'log format string must not be empty'):
      self.debuggee.CreateLogpoint('a:1', '')

  def testCreateLogpointRemoteFailure(self):
    self.mocked_debug_client.debugger_debuggees_breakpoints.Set.Expect(
        request=self.debug_messages.
        ClouddebuggerDebuggerDebuggeesBreakpointsSetRequest(
            debuggeeId=self.debuggee.target_id,
            breakpoint=self.debug_messages.Breakpoint(
                location=self.debug_messages.SourceLocation(path='myfile',
                                                            line=1234),
                logMessageFormat='dummy text',
                action=(self.debug_messages.Breakpoint.ActionValueValuesEnum.
                        LOG)),
            clientVersion=debug.DebugObject.CLIENT_VERSION),
        exception=_DummyHttpError())
    with self.AssertRaisesHttpExceptionMatches(
        'Resource not found API reason: dummy_error_message'):
      self.debuggee.CreateLogpoint('myfile:1234', 'dummy text')

  def testWaitWithImmediateSuccess(self):
    breakpoint = self.debug_messages.Breakpoint(
        id='fake_id',
        location=self.debug_messages.SourceLocation(path='myfile', line=1234),
        logMessageFormat='dummy text',
        action=(self.debug_messages.Breakpoint.ActionValueValuesEnum.LOG),
        isFinalState=True)
    request = (
        self.debug_messages.ClouddebuggerDebuggerDebuggeesBreakpointsGetRequest(
            breakpointId=breakpoint.id, debuggeeId=self.debuggee.target_id,
            clientVersion=debug.DebugObject.CLIENT_VERSION))
    self.mocked_debug_client.debugger_debuggees_breakpoints.Get.Expect(
        request=request, response=self.debug_messages.GetBreakpointResponse(
            breakpoint=breakpoint))
    response = self.debuggee.WaitForBreakpoint(breakpoint.id, 'myfile:1234')
    self.assertEqual(response, self.debuggee.AddTargetInfo(breakpoint))

  def testWaitWithDelayedSuccess(self):
    breakpoint = self.debug_messages.Breakpoint(
        id='fake_id',
        location=self.debug_messages.SourceLocation(path='myfile', line=1234),
        logMessageFormat='dummy text',
        action=(self.debug_messages.Breakpoint.ActionValueValuesEnum.LOG),
        isFinalState=False)
    final_breakpoint = self.debug_messages.Breakpoint(
        id='fake_id',
        location=self.debug_messages.SourceLocation(path='myfile', line=1234),
        logMessageFormat='dummy text',
        action=(self.debug_messages.Breakpoint.ActionValueValuesEnum.LOG),
        isFinalState=True)
    request = (
        self.debug_messages.ClouddebuggerDebuggerDebuggeesBreakpointsGetRequest(
            breakpointId=breakpoint.id, debuggeeId=self.debuggee.target_id,
            clientVersion=debug.DebugObject.CLIENT_VERSION))
    self.mocked_debug_client.debugger_debuggees_breakpoints.Get.Expect(
        request=request, response=self.debug_messages.GetBreakpointResponse(
            breakpoint=breakpoint))
    self.mocked_debug_client.debugger_debuggees_breakpoints.Get.Expect(
        request=request, response=self.debug_messages.GetBreakpointResponse(
            breakpoint=breakpoint))
    self.mocked_debug_client.debugger_debuggees_breakpoints.Get.Expect(
        request=request, response=self.debug_messages.GetBreakpointResponse(
            breakpoint=final_breakpoint))
    response = self.debuggee.WaitForBreakpointSet(breakpoint.id, 'myfile:1234')
    self.assertEqual(response,
                     self.debuggee.AddTargetInfo(final_breakpoint))

  def testWaitWithDifferentLocation(self):
    breakpoint = self.debug_messages.Breakpoint(
        id='fake_id',
        location=self.debug_messages.SourceLocation(path='myfile', line=1234),
        logMessageFormat='dummy text',
        action=(self.debug_messages.Breakpoint.ActionValueValuesEnum.LOG),
        isFinalState=False)
    adjusted_breakpoint = self.debug_messages.Breakpoint(
        id='fake_id',
        location=self.debug_messages.SourceLocation(path='myfile', line=1235),
        logMessageFormat='dummy text',
        action=(self.debug_messages.Breakpoint.ActionValueValuesEnum.LOG),
        isFinalState=False)
    request = (
        self.debug_messages.ClouddebuggerDebuggerDebuggeesBreakpointsGetRequest(
            breakpointId=breakpoint.id, debuggeeId=self.debuggee.target_id,
            clientVersion=debug.DebugObject.CLIENT_VERSION))
    self.mocked_debug_client.debugger_debuggees_breakpoints.Get.Expect(
        request=request, response=self.debug_messages.GetBreakpointResponse(
            breakpoint=breakpoint))
    self.mocked_debug_client.debugger_debuggees_breakpoints.Get.Expect(
        request=request, response=self.debug_messages.GetBreakpointResponse(
            breakpoint=breakpoint))
    self.mocked_debug_client.debugger_debuggees_breakpoints.Get.Expect(
        request=request, response=self.debug_messages.GetBreakpointResponse(
            breakpoint=adjusted_breakpoint))
    response = self.debuggee.WaitForBreakpointSet(breakpoint.id, 'myfile:1234')
    self.assertEqual(response,
                     self.debuggee.AddTargetInfo(adjusted_breakpoint))

  def testWaitWithTimeout(self):
    breakpoint = self.debug_messages.Breakpoint(
        id='fake_id',
        location=self.debug_messages.SourceLocation(path='myfile', line=1234),
        logMessageFormat='dummy text',
        action=(self.debug_messages.Breakpoint.ActionValueValuesEnum.LOG))
    request = (
        self.debug_messages.ClouddebuggerDebuggerDebuggeesBreakpointsGetRequest(
            breakpointId=breakpoint.id, debuggeeId=self.debuggee.target_id,
            clientVersion=debug.DebugObject.CLIENT_VERSION))
    self.mocked_debug_client.debugger_debuggees_breakpoints.Get.Expect(
        request=request, response=self.debug_messages.GetBreakpointResponse(
            breakpoint=breakpoint))
    response = self.debuggee.WaitForBreakpoint(breakpoint.id, timeout=0)
    self.assertFalse(response)

  def testWaitWithFailure(self):
    breakpoint = self.debug_messages.Breakpoint(
        id='fake_id',
        location=self.debug_messages.SourceLocation(path='myfile', line=1234),
        logMessageFormat='dummy text',
        action=(self.debug_messages.Breakpoint.ActionValueValuesEnum.LOG),
        isFinalState=False)
    request = (
        self.debug_messages.ClouddebuggerDebuggerDebuggeesBreakpointsGetRequest(
            breakpointId=breakpoint.id, debuggeeId=self.debuggee.target_id,
            clientVersion=debug.DebugObject.CLIENT_VERSION))
    self.mocked_debug_client.debugger_debuggees_breakpoints.Get.Expect(
        request=request, exception=_DummyHttpError())
    with self.AssertRaisesHttpExceptionMatches(
        'Resource not found API reason: dummy_error_message'):
      self.debuggee.WaitForBreakpoint(breakpoint.id)

  def testWaitNoRetry(self):
    # We don't currently use this case, but verify correctness in case
    # of future changes.
    breakpoint = self.debug_messages.Breakpoint(
        id='fake_id',
        location=self.debug_messages.SourceLocation(path='myfile', line=1234),
        logMessageFormat='dummy text',
        action=(self.debug_messages.Breakpoint.ActionValueValuesEnum.LOG))
    request = (
        self.debug_messages.ClouddebuggerDebuggerDebuggeesBreakpointsGetRequest(
            breakpointId=breakpoint.id, debuggeeId=self.debuggee.target_id,
            clientVersion=debug.DebugObject.CLIENT_VERSION))
    self.mocked_debug_client.debugger_debuggees_breakpoints.Get.Expect(
        request=request, response=self.debug_messages.GetBreakpointResponse(
            breakpoint=breakpoint))
    response = self.debuggee.WaitForBreakpoint(breakpoint.id, 'myfile:1234',
                                               completion_test=lambda _: True)
    self.assertFalse(response.isFinalState)


class BreakpointMultiWaitTest(_DebugTestWithDebuggee):
  """Tests for WaitForMultipleBreakpoints."""

  class _MockGetBreakpoint(object):

    def MakeBreakpoint(self, breakpoint_id, is_final_state):
      return self._parent.debug_messages.Breakpoint(id=breakpoint_id,
                                                    isFinalState=is_final_state)

    def __init__(self, parent):
      self._map_lock = threading.Lock()
      self._response_map = {}
      self._error_set = set()
      self._parent = parent

    def TearDown(self):
      unsatisfied = [(key, value + 1)
                     for key, value in six.iteritems(self._response_map)
                     if value >= 0]
      if unsatisfied:
        raise UnsatisfiedExpectationError(unsatisfied)

    def ExpectId(self, breakpoint_id, final_after_tries, raise_error=False):
      with self._map_lock:
        self._response_map[breakpoint_id] = final_after_tries
        if raise_error:
          self._error_set.add(breakpoint_id)
        else:
          self._error_set.discard(breakpoint_id)

    def __call__(self, request):
      if request.breakpointId not in self._response_map:
        raise UnexpectedIdError(request.breakpointId,
                                list(self._response_map.keys()))
      with self._map_lock:
        value = self._response_map[request.breakpointId]
        response = self._parent.debug_messages.GetBreakpointResponse(
            breakpoint=self.MakeBreakpoint(request.breakpointId, (value == 0)))
        if value == 0:
          self._response_map.pop(request.breakpointId)
          if request.breakpointId in self._error_set:
            raise _DummyHttpError()
        elif value > 0:
          self._response_map[request.breakpointId] -= 1
        return response

  def SetUp(self):
    self._orig_mock_get = (
        self.mocked_debug_client.debugger_debuggees_breakpoints.Get)
    self._mock_get = self._MockGetBreakpoint(self)
    self.mocked_debug_client.debugger_debuggees_breakpoints.Get = self._mock_get

  def TearDown(self):
    self._mock_get.TearDown()
    self.mocked_debug_client.debugger_debuggees_breakpoints.Get = (
        self._orig_mock_get)

  def testWithAllImmediateSuccess(self):
    ids = ['fake_id-{0}'.format(i) for i in range(0, 10)]
    # Set everything to complete immediately
    for i in ids:
      self._mock_get.ExpectId(i, 0)

    response = self.debuggee.WaitForMultipleBreakpoints(ids, wait_all=True,
                                                        timeout=GLOBAL_MAX_WAIT)
    self.assertEqual(response, [
        self.debuggee.AddTargetInfo(self._mock_get.MakeBreakpoint(i, True))
        for i in ids])

  def testWithOneImmediateSuccess(self):
    ids = ['fake_id-{0}'.format(i) for i in range(0, 10)]
    # Set everything to never complete
    for i in ids:
      self._mock_get.ExpectId(i, -1)

    # Adjust one breakpoint to succeed immediately.
    self._mock_get.ExpectId(ids[3], 0)

    response = self.debuggee.WaitForMultipleBreakpoints(ids,
                                                        timeout=GLOBAL_MAX_WAIT)
    self.assertEqual(response, [
        self.debuggee.AddTargetInfo(
            self._mock_get.MakeBreakpoint(ids[3], True))])

  def testWithOneDelayedSuccess(self):
    ids = ['fake_id-{0}'.format(i) for i in range(0, 10)]
    # Set everything to never complete
    for i in ids:
      self._mock_get.ExpectId(i, -1)

    # Adjust one breakpoint to succeed after 2 retries.
    self._mock_get.ExpectId(ids[3], 2)

    response = self.debuggee.WaitForMultipleBreakpoints(ids,
                                                        timeout=GLOBAL_MAX_WAIT)
    self.assertEqual(response, [
        self.debuggee.AddTargetInfo(
            self._mock_get.MakeBreakpoint(ids[3], True))])

  def testWithAllDelayedSuccess(self):
    ids = ['fake_id-{0}'.format(i) for i in range(0, 10)]
    # Set everything to complete after different numbers of retries
    for i in range(0, 10):
      self._mock_get.ExpectId(ids[i], 10 - i)

    response = self.debuggee.WaitForMultipleBreakpoints(ids, wait_all=True,
                                                        timeout=GLOBAL_MAX_WAIT)
    self.assertEqual(response, [
        self.debuggee.AddTargetInfo(self._mock_get.MakeBreakpoint(i, True))
        for i in ids])

  def testWithTimeout(self):
    ids = ['fake_id-{0}'.format(i) for i in range(0, 10)]
    # Set everything to never complete
    for i in ids:
      self._mock_get.ExpectId(i, -1)

    response = self.debuggee.WaitForMultipleBreakpoints(ids, timeout=1)
    self.assertFalse(response)

  def testPartialSuccessWithTimeout(self):
    ids = ['fake_id-{0}'.format(i) for i in range(0, 10)]
    # Set everything to never complete
    for i in ids:
      self._mock_get.ExpectId(i, -1)

    # Adjust one breakpoint to complete immediately.
    self._mock_get.ExpectId(ids[3], 0)
    response = self.debuggee.WaitForMultipleBreakpoints(ids, timeout=1,
                                                        wait_all=True)
    self.assertEqual(response, [
        self.debuggee.AddTargetInfo(
            self._mock_get.MakeBreakpoint(ids[3], True))])

  def testWithFailure(self):
    ids = ['fake_id-{0}'.format(i) for i in range(0, 10)]
    # Set everything to never complete
    for i in ids:
      self._mock_get.ExpectId(i, -1)

    # Adjust one breakpoint to fail.
    self._mock_get.ExpectId(ids[3], 2, raise_error=True)
    with self.AssertRaisesHttpExceptionMatches(
        'Resource not found API reason: dummy_error_message'):
      self.debuggee.WaitForMultipleBreakpoints(ids, wait_all=True,
                                               timeout=GLOBAL_MAX_WAIT)


if __name__ == '__main__':
  sdk_test_base.main()
