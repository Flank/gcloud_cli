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

"""Test of the functions surface deploy.trigger_util module."""

from googlecloudsdk.api_lib.functions import triggers
from googlecloudsdk.command_lib.functions.deploy import trigger_util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties
from tests.lib import sdk_test_base
from tests.lib import test_case


class TriggerUtilTest(sdk_test_base.SdkBase):

  def SetUp(self):
    properties.VALUES.core.project.Set('deploy-util-test-project')

  def _ProviderEventGenerator(self):

    class Stub(object):

      def __getattr__(self, item):
        return None

      def IsSpecified(self, arg):
        del arg
        return False

    for provider in triggers.INPUT_TRIGGER_PROVIDER_REGISTRY.providers:
      for event in provider.events:
        namespace = Stub()
        namespace.trigger_provider = provider.label
        namespace.trigger_event = event.label
        namespace.stage_bucket = 'buck'
        namespace.trigger_resource = 'generic'
        namespace.trigger_path = None
        # Additional field may be required if _CheckArgs is changed
        yield namespace

  def testPrepareResourceForProtoInternalErrorExhaustiveSearch(self):
    for provider_event in self._ProviderEventGenerator():
      trigger_util.ConvertTriggerArgsToRelativeName(
          provider_event.trigger_provider,
          provider_event.trigger_event,
          provider_event.trigger_resource)

  def testCheckArgsInternalErrorExhaustiveSearch(self):
    for args in self._ProviderEventGenerator():
      trigger_util.GetTriggerEventParams(
          args.trigger_http, args.trigger_bucket, args.trigger_topic,
          args.trigger_event, args.trigger_resource)

  def testCheckArgsInternalErrorFalseNegative(self):
    # get some content
    args = self._ProviderEventGenerator().next()
    # mock
    copy = triggers.INPUT_TRIGGER_PROVIDER_REGISTRY.providers
    try:
      triggers.INPUT_TRIGGER_PROVIDER_REGISTRY.providers = [
          triggers.TriggerProvider(args.trigger_provider, [
              triggers.TriggerEvent(args.trigger_event, {'path': None})
          ])
      ]
      with self.assertRaises(exceptions.InternalError):
        trigger_util.GetTriggerEventParams(
            args.trigger_http, args.trigger_bucket, args.trigger_topic,
            args.trigger_event, args.trigger_resource)
    finally:
      triggers.INPUT_TRIGGER_PROVIDER_REGISTRY.providers = copy

if __name__ == '__main__':
  test_case.main()
