# Copyright 2015 Google Inc. All Rights Reserved.
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

"""Tests for gcloud app instances."""

from __future__ import absolute_import
from googlecloudsdk.api_lib.app import instances_util
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.app import instances_base
from six.moves import map  # pylint: disable=redefined-builtin


class InstanceTest(test_case.TestCase):

  PROJECT = 'fakeproject'

  def testFromResourcePath(self):
    from_resource_path = instances_util.Instance.FromResourcePath
    expected = instances_util.Instance('a', 'b', 'c')
    self.assertEqual(from_resource_path('a/b/c'), expected)
    self.assertEqual(from_resource_path('b/c', service='a'), expected)
    self.assertEqual(from_resource_path('c', service='a', version='b'),
                     expected)

  def testFromResourcePath_OverSpecified(self):
    from_resource_path = instances_util.Instance.FromResourcePath
    expected = instances_util.Instance('b', 'c', 'd')
    self.assertEqual(from_resource_path('b/c/d', service='b'),
                     expected)
    self.assertEqual(from_resource_path('b/c/d', service='b', version='c'),
                     expected)
    self.assertEqual(from_resource_path('c/d', service='b', version='c'),
                     expected)

  def testFromResourcePath_InvalidSpecification(self):
    with self.assertRaisesRegex(
        instances_util.InvalidInstanceSpecificationError,
        r'Instance resource path is incorrectly specified\.'):
      instances_util.Instance.FromResourcePath('a/b/c/d')

  def testFromResourcePath_UnderSpecified(self):
    self.assertEqual(instances_util.Instance.FromResourcePath('b/c'),
                     instances_util.Instance(None, 'b', 'c'))
    self.assertEqual(
        instances_util.Instance.FromResourcePath('c', service='a'),
        instances_util.Instance('a', None, 'c'))

  def testFromResourcePath_EmptyComponent(self):
    self.assertEqual(instances_util.Instance.FromResourcePath('a//c'),
                     instances_util.Instance('a', '', 'c'))


class FilterInstancesTest(test_case.TestCase):

  PROJECT = 'fakeproject'

  def SetUp(self):
    all_instances = list(map(instances_util.Instance.FromResourcePath,
                             ['service1/v1/i1',
                              'service1/v1/i2',
                              'service1/v2/i1',
                              'service2/v1/i1']))
    # Map of instance ID to instance name, for easy in-test reference
    self.instances = dict((str(i), i) for i in all_instances)

  def testFilterInstances_NoFilter(self):
    self.assertEqual(
        set(instances_util.FilterInstances(list(self.instances.values()))),
        set(self.instances.values()))

  def testFilterInstances_FilterService(self):
    self.assertEqual(
        set(instances_util.FilterInstances(list(self.instances.values()),
                                           service='service1')),
        set([self.instances['service1/v1/i1'],
             self.instances['service1/v1/i2'],
             self.instances['service1/v2/i1']]))
    self.assertEqual(
        set(instances_util.FilterInstances(list(self.instances.values()),
                                           service='service2')),
        set([self.instances['service2/v1/i1']]))

  def testFilterInstances_FilterServiceBadService(self):
    self.assertEqual(
        set(instances_util.FilterInstances(list(self.instances.values()),
                                           service='badservice')),
        set())

  def testFilterInstances_FilterVersion(self):
    self.assertEqual(
        set(instances_util.FilterInstances(list(self.instances.values()),
                                           version='v1')),
        set([self.instances['service1/v1/i1'],
             self.instances['service1/v1/i2'],
             self.instances['service2/v1/i1']]))
    self.assertEqual(
        set(instances_util.FilterInstances(list(self.instances.values()),
                                           version='v2')),
        set([self.instances['service1/v2/i1']]))

  def testFilterInstances_FilterVersionBadVersion(self):
    self.assertEqual(
        set(instances_util.FilterInstances(list(self.instances.values()),
                                           version='badversion')),
        set())

  def testFilterInstances_FilterServiceAndVersion(self):
    self.assertEqual(
        set(instances_util.FilterInstances(list(self.instances.values()),
                                           service='service1', version='v1')),
        set([self.instances['service1/v1/i1'],
             self.instances['service1/v1/i2']]))
    self.assertEqual(
        set(instances_util.FilterInstances(list(self.instances.values()),
                                           service='service1', version='v2')),
        set([self.instances['service1/v2/i1']]))
    self.assertEqual(
        set(instances_util.FilterInstances(list(self.instances.values()),
                                           service='service2', version='v1')),
        set([self.instances['service2/v1/i1']]))

  def testFilterInstances_FilterServiceAndInstance(self):
    self.assertEqual(
        set(instances_util.FilterInstances(list(self.instances.values()),
                                           service='service1',
                                           instance='i1')),
        set([self.instances['service1/v1/i1'],
             self.instances['service1/v2/i1']]))
    self.assertEqual(
        set(instances_util.FilterInstances(list(self.instances.values()),
                                           service='service1',
                                           instance='i2')),
        set([self.instances['service1/v1/i2']]))
    self.assertEqual(
        set(instances_util.FilterInstances(list(self.instances.values()),
                                           service='service2',
                                           instance='i1')),
        set([self.instances['service2/v1/i1']]))
    self.assertEqual(
        set(instances_util.FilterInstances(list(self.instances.values()),
                                           service='service2',
                                           instance='i2')),
        set())

  def testFilterInstances_FilterBothNoMatch(self):
    # service and version are both good, but don't match anything
    self.assertEqual(
        set(instances_util.FilterInstances(list(self.instances.values()),
                                           service='service2', version='v2')),
        set())

  def testFilterInstances_FilterInstanceName(self):
    self.assertEqual(
        set(instances_util.FilterInstances(list(self.instances.values()),
                                           instance='i2')),
        set([self.instances['service1/v1/i2']]))

  def testFilterInstances_FilterInstanceResourcePath(self):
    for instance in self.instances.values():
      self.assertEqual(
          set(instances_util.FilterInstances(list(self.instances.values()),
                                             instance=str(instance))),
          set([]))


class PromptPhase(object):
  """Represents a phase of the interactive query to identify an instance.

  Encompasses the following expected behavior:
  * What the user is selecting at this phase (ex. 'instance', 'service',
    'version').
  * Whether to show a prompt at all (i.e. the phase has more than one option).
  * If prompted, what value to return (ex. simulating what the user's response
    was)
  * What text to display, whether or not a prompt was shown.

  Attributes:
    attribute: str, what the user is selecting at this phase (ex. 'instance',
        'service', 'version').
    choices: list of str, the choices the user should be prompted with for the
        given attribute (ex. ['service1', 'service2'] or
        ['version1', 'version2']).
    idx: int or None. If given, simulates the user selecting the given index
        from the choices (ex. 1 would indicate choosing 'service2' from the
        choices ['service1', 'service2']).
  """

  def __init__(self, attribute, choices, idx=None):
    self.attribute = attribute
    self.choices = choices
    self.idx = idx

  def ShowPrompt(self):
    """Return True if at this phase a prompt should be shown."""
    return self.idx is not None

  def SkipPromptText(self):
    """Returns the text that indicates that this prompt was skipped."""
    return 'Choosing [{0}] for {1}.'.format(self.choices[0], self.attribute)

  def PromptText(self):
    """Returns the text that the prompt should display."""
    return 'Which {0}?'.format(self.attribute)


class SelectInstanceInteractiveTest(sdk_test_base.WithOutputCapture):

  PROJECT = 'fakeproject'

  def SetUp(self):
    properties.VALUES.core.project.Set(self.PROJECT)
    # These instances have a couple of properties useful for testing
    # interactive selection:
    #
    # * One instance uniquely identified by a service, and one service with
    #   multiple instances
    # * One instance uniquely identified by a version, and one version with
    #   multiple instances
    #
    # This means that by having a test that selects each instance for each
    # filtering method (ex. interactive or via the keyword arguments), we get
    # very good coverage of the combinations of filtering mechanisms.
    all_instances = list(map(instances_util.Instance.FromResourcePath,
                             ['service1/v1/i1',
                              'service1/v1/i2',
                              'service1/v2/i3',
                              'service2/v1/i4']))
    # Map of instance ID to instance name, for easy in-test reference
    self.instances = dict((i.id, i) for i in all_instances)

  def testSelectInstanceInteractive_NoPrompts(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.addCleanup(properties.VALUES.core.disable_prompts.Set, None)

    with self.assertRaisesRegex(
        instances_util.SelectInstanceError,
        r'Cannot interactively select instances with prompts disabled'):
      instances_util.SelectInstanceInteractive([])

  def testSelectInstanceInteractive_NoInstances(self):
    with self.assertRaisesRegex(
        instances_util.SelectInstanceError,
        r'No instances were found for the current project \[fakeproject\]\.'):
      instances_util.SelectInstanceInteractive([])

  def testSelectInstanceInteractive_NoMatchingInstances(self):
    with self.assertRaisesRegex(
        instances_util.SelectInstanceError,
        r'No instances could be found matching the given criteria\.'):
      instances_util.SelectInstanceInteractive(list(self.instances.values()),
                                               service='badservice')
    with self.assertRaisesRegex(
        instances_util.SelectInstanceError,
        r'No instances could be found matching the given criteria\.'):
      instances_util.SelectInstanceInteractive(list(self.instances.values()),
                                               service='badservice',
                                               version='badversion')
    with self.assertRaisesRegex(
        instances_util.SelectInstanceError,
        r'No instances could be found matching the given criteria\.'):
      # A valid service and version, but no instance that matches both
      instances_util.SelectInstanceInteractive(list(self.instances.values()),
                                               service='service2', version='v2')

  def RunTest(self, prompt_phases, kwargs=None, expected_instance=None):
    """Run a standard-conditions test of SelectInstanceInteractive.

    1. Mock out console_io.PromptChoice
    2. Run the test, with the provided (optional) keyword arguments passed to
       the function under test.
    3. Make sure that the expected PromptChoice calls were made, and that the
       expected skipped prompts have corresponding output.
    4. Make sure that the ultimately selected instance is the correct one.

    Do this all in an environment that doesn't interfere with other tests.

    An example call:

    >>> self.RunTest([PromptPhase('service', ['service1', 'service2'], 0),
    ...               PromptPhase('version', ['v1', 'v2'], 1),
    ...               PromptPhase('instance', [self.instances['i3']])],
    ...              expected_instance='service1/v2/i3')

    This means that the interaction being simulated should look something like
    this (note the conversion between 0- and 1-indexes):

        Which service?
         [1] service1
         [2] service2
        Please enter your numeric choice:  1

        Which version?
         [1] v1
         [2] v2
        Please enter your numeric choice:  2

        Choosing [service1/v2/i3] for instance.

    The ultimately selected instance should be given by the resource path
    [service1/v2/i3].

    Args:
      prompt_phases: list of PromptPhase, a list of the expected interactive
        phases for the SelectInstanceInteractive call.
      kwargs: dict. If given, the keyword arguments to pass to the
        SelectInstanceInteractive call.
      expected_instance: string, a resource path representing the expected
        selected instance.
    """
    kwargs = kwargs or {}
    self.ClearErr()
    prompt_mock = self.StartObjectPatch(console_io, 'PromptChoice')
    prompt_mock.side_effect = [p.idx for p in prompt_phases
                               if p.idx is not None]

    result = instances_util.SelectInstanceInteractive(
        list(self.instances.values()), **kwargs)

    # Since the calls don't map 1-to-1 to the phases, keep a separate iterator
    calls = iter(prompt_mock.call_args_list)
    for phase in prompt_phases:
      if phase.ShowPrompt():
        # Check that an appropriate call to console_io.PromptChoice was made
        (args,), kwargs = next(calls)
        self.assertEqual(args, phase.choices)
        self.assertEqual(kwargs['message'], phase.PromptText())
        # Check that the text to indicate a skipped prompt was NOT displayed
        self.AssertErrNotContains(phase.SkipPromptText())
      else:
        # Check that the appropriate text to indicate a skipped prompt was
        # displayed
        self.AssertErrContains(phase.SkipPromptText())
    # Check that there are no more calls to PromptChoice than expected
    self.assertRaises(StopIteration, next, calls)

    self.assertEqual(
        result,
        instances_util.Instance.FromResourcePath(expected_instance))

  def testSelectInstanceInteractive_NoFilters(self):
    self.RunTest([PromptPhase('service', ['service1', 'service2'], 0),
                  PromptPhase('version', ['v1', 'v2'], 0),
                  PromptPhase('instance', [self.instances['i1'],
                                           self.instances['i2']], 0)],
                 expected_instance='service1/v1/i1')
    self.RunTest([PromptPhase('service', ['service1', 'service2'], 0),
                  PromptPhase('version', ['v1', 'v2'], 0),
                  PromptPhase('instance', [self.instances['i1'],
                                           self.instances['i2']], 1)],
                 expected_instance='service1/v1/i2')
    self.RunTest([PromptPhase('service', ['service1', 'service2'], 0),
                  PromptPhase('version', ['v1', 'v2'], 1),
                  PromptPhase('instance', [self.instances['i3']])],
                 expected_instance='service1/v2/i3')
    self.RunTest([PromptPhase('service', ['service1', 'service2'], 1),
                  PromptPhase('version', ['v1']),
                  PromptPhase('instance', [self.instances['i4']])],
                 expected_instance='service2/v1/i4')

  def testSelectInstanceInteractive_FilterService(self):
    self.RunTest([PromptPhase('service', ['service1']),
                  PromptPhase('version', ['v1', 'v2'], 0),
                  PromptPhase('instance', [self.instances['i1'],
                                           self.instances['i2']], 0)],
                 expected_instance='service1/v1/i1',
                 kwargs={'service': 'service1'})
    self.RunTest([PromptPhase('service', ['service1']),
                  PromptPhase('version', ['v1', 'v2'], 0),
                  PromptPhase('instance', [self.instances['i1'],
                                           self.instances['i2']], 1)],
                 expected_instance='service1/v1/i2',
                 kwargs={'service': 'service1'})
    self.RunTest([PromptPhase('service', ['service1']),
                  PromptPhase('version', ['v1', 'v2'], 1),
                  PromptPhase('instance', [self.instances['i3']])],
                 expected_instance='service1/v2/i3',
                 kwargs={'service': 'service1'})
    self.RunTest([PromptPhase('service', ['service2']),
                  PromptPhase('version', ['v1']),
                  PromptPhase('instance', [self.instances['i4']])],
                 expected_instance='service2/v1/i4',
                 kwargs={'service': 'service2'})

  def testSelectInstanceInteractive_FilterVersion(self):
    self.RunTest([PromptPhase('service', ['service1', 'service2'], 0),
                  PromptPhase('version', ['v1']),
                  PromptPhase('instance', [self.instances['i1'],
                                           self.instances['i2']], 0)],
                 expected_instance='service1/v1/i1',
                 kwargs={'version': 'v1'})
    self.RunTest([PromptPhase('service', ['service1', 'service2'], 0),
                  PromptPhase('version', ['v1']),
                  PromptPhase('instance', [self.instances['i1'],
                                           self.instances['i2']], 1)],
                 expected_instance='service1/v1/i2',
                 kwargs={'version': 'v1'})
    self.RunTest([PromptPhase('service', ['service1', 'service2'], 1),
                  PromptPhase('version', ['v1']),
                  PromptPhase('instance', [self.instances['i4']])],
                 expected_instance='service2/v1/i4',
                 kwargs={'version': 'v1'})
    self.RunTest([PromptPhase('service', ['service1']),
                  PromptPhase('version', ['v2']),
                  PromptPhase('instance', [self.instances['i3']])],
                 expected_instance='service1/v2/i3',
                 kwargs={'version': 'v2'})

  def testSelectInstanceInteractive_FilterBoth(self):
    self.RunTest([PromptPhase('service', ['service1']),
                  PromptPhase('version', ['v1']),
                  PromptPhase('instance', [self.instances['i1'],
                                           self.instances['i2']], 0)],
                 expected_instance='service1/v1/i1',
                 kwargs={'service': 'service1', 'version': 'v1'})
    self.RunTest([PromptPhase('service', ['service1']),
                  PromptPhase('version', ['v1']),
                  PromptPhase('instance', [self.instances['i1'],
                                           self.instances['i2']], 1)],
                 expected_instance='service1/v1/i2',
                 kwargs={'service': 'service1', 'version': 'v1'})
    self.RunTest([PromptPhase('service', ['service1']),
                  PromptPhase('version', ['v2']),
                  PromptPhase('instance', [self.instances['i3']])],
                 expected_instance='service1/v2/i3',
                 kwargs={'service': 'service1', 'version': 'v2'})
    self.RunTest([PromptPhase('service', ['service2']),
                  PromptPhase('version', ['v1']),
                  PromptPhase('instance', [self.instances['i4']])],
                 expected_instance='service2/v1/i4',
                 kwargs={'service': 'service2', 'version': 'v1'})


class GetMatchingInstanceTest(test_case.TestCase):

  PROJECT = 'fakeproject'

  def SetUp(self):
    properties.VALUES.core.project.Set(self.PROJECT)
    all_instances = list(map(instances_util.Instance.FromResourcePath,
                             ['service1/v1/i1',
                              'service1/v1/i2',
                              'service1/v2/i3',
                              'service2/v1/i4']))
    # Map of instance ID to instance name, for easy in-test reference
    self.instances = dict((i.id, i) for i in all_instances)
    self.select_mock = self.StartObjectPatch(instances_util,
                                             'SelectInstanceInteractive')

  def testGetMatchingInstance_NonInteractiveTooManyMatches(self):
    # In order to generate more than one match, we need more than one instance
    # with the same ID. We don't have that in self.instances because it makes
    # the other tests more difficult to write.
    instances = [
        instances_util.Instance.FromResourcePath('service1/v1/abcd'),
        instances_util.Instance.FromResourcePath('service1/v2/abcd')
    ]
    with self.assertRaisesRegex(
        instances_util.InvalidInstanceSpecificationError,
        r'More than one instance matches the given specification\.\n\n'
        r"Matching instances: \['service1/v1/abcd', 'service1/v2/abcd'\]"):
      instances_util.GetMatchingInstance(instances, instance='abcd')

  def testGetMatchingInstance_NonInteractiveNoMatches(self):
    with self.assertRaisesRegex(
        instances_util.InvalidInstanceSpecificationError,
        r'No instances match the given specification\.\n\n'
        r"All instances: \['service1/v1/i1', 'service1/v1/i2', "
        r"'service1/v2/i3', 'service2/v1/i4'\]"):
      instances_util.GetMatchingInstance(list(self.instances.values()),
                                         instance='bad')

  def testGetMatchingInstance_NonInteractive(self):
    for instance_id, instance in self.instances.items():
      self.assertEqual(
          instances_util.GetMatchingInstance(list(self.instances.values()),
                                             instance=instance_id),
          instance)

  def testGetMatchingInstance_Interactive(self):
    self.select_mock.return_value = self.instances['i1']

    self.assertEqual(
        instances_util.GetMatchingInstance(list(self.instances.values())),
        self.instances['i1'])

    self.select_mock.assert_called_once_with(list(self.instances.values()),
                                             service=None, version=None)

  def testGetMatchingInstance_InteractiveWithFilters(self):
    self.select_mock.return_value = self.instances['i1']

    self.assertEqual(
        instances_util.GetMatchingInstance(list(self.instances.values()),
                                           service='service1', version='v1'),
        self.instances['i1'])

    self.select_mock.assert_called_once_with(list(self.instances.values()),
                                             service='service1', version='v1')


class InstancesDeleteTest(instances_base.InstancesTestBase):

  def testDelete_Interactive(self):
    """Tests deletion of an instance through the interactive path."""
    prompt_mock_continue = self.StartObjectPatch(console_io, 'PromptContinue')
    prompt_mock_continue.return_value = True

    self._ExpectDeleteInstanceCall('default', 'v1', 'bbbb')
    self.Run('app instances delete -s default -v v1 bbbb')
    self.AssertErrContains('Deleting the instance [default/v1/bbbb].')

  def testDelete_NonInteractive(self):
    """Tests deletion of an instance without user interaction."""
    properties.VALUES.core.disable_prompts.Set(True)

    self._ExpectDeleteInstanceCall('default', 'v1', 'bbbb')
    self.Run('app instances delete -s default -v v1 bbbb')
    self.AssertErrContains('Deleting the instance [default/v1/bbbb].')
    self.AssertErrNotContains('Do you want to continue (Y/n)?')


class InstancesEnableDebugTest(instances_base.InstancesTestBase):

  COMPUTE_INSTANCES = dict([
      # _MakeInstance('default', 'v1', 'i1'),
      # _MakeInstance('default', 'v1', 'i2'),
      # _MakeInstance('default', 'v2', 'i1'),
      # _MakeInstance('service1', 'v1', 'i1')
  ])

  def SetUp(self):
    self.select_instance_mock = self.StartObjectPatch(
        instances_util, 'SelectInstanceInteractive')

  def AssertDebugCalled(self, service, version, instance, retries=0):
    self.AssertErrContains(
        'About to enable debug mode for instance [{0}/{1}/{2}]'
        .format(service, version, instance))
    self.AssertErrContains(
        'Enabling debug mode for instance [{0}/{1}/{2}]'
        .format(service, version, instance))

  def testEnableDebug_NoMatches(self):
    self._ExpectCalls([
        ('default', [
            ('v1_flex', ['i1', 'i2']),
            ('v2_flex', ['i1'])
        ]),
        ('service1', [
            ('v1_flex', ['i1'])])
    ])
    with self.assertRaisesRegex(
        instances_util.InvalidInstanceSpecificationError,
        r'No instances match the given specification\.'):
      self.Run('app instances enable-debug bad')

  def testEnableDebug_TooManyMatches(self):
    self._ExpectCalls([
        ('default', [
            ('v1_flex', ['i1', 'i2']),
            ('v2_flex', ['i1'])
        ]),
        ('service1', [
            ('v1_flex', ['i1'])])
    ])
    with self.assertRaisesRegex(
        instances_util.InvalidInstanceSpecificationError,
        r'More than one instance matches the given specification\.'):
      self.Run('app instances enable-debug i1')

  def testEnableDebug(self):
    self._ExpectCalls([
        ('default', [
            ('v1_flex', ['i1', 'i2']),
            ('v2_flex', ['i1'])
        ]),
        ('service1', [
            ('v1_flex', ['i1'])])
    ])
    self._ExpectDebugInstanceCall('default', 'v1_flex', 'i2')
    self.Run('app instances enable-debug i2')
    self.AssertDebugCalled('default', 'v1_flex', 'i2')

  def testEnableDebug_MixedEnvironments(self):
    """Ensures that mvm, flex are working and standard ignored."""
    self._ExpectCalls([
        ('default', [
            ('v1_mvm', ['i1', 'i2']),
            ('v2_flex', ['i1'])
        ]),
        ('service1', [
            ('v1_standard', None)])
    ])
    self._ExpectDebugInstanceCall('default', 'v1_mvm', 'i2')
    self.Run('app instances enable-debug i2')
    self.AssertDebugCalled('default', 'v1_mvm', 'i2')

  def testEnableDebug_FilterService(self):
    self._ExpectCalls([
        ('default', []),
        ('service1', [
            ('v1_flex', ['i1'])])
    ])
    self._ExpectDebugInstanceCall('service1', 'v1_flex', 'i1')
    self.Run('app instances enable-debug --service service1 i1')
    self.AssertDebugCalled('service1', 'v1_flex', 'i1')

  def testEnableDebug_FilterVersion(self):
    self._ExpectCalls([
        ('default', [
            ('v1_flex', []),
            ('v2_flex', ['i1'])
        ]),
        ('service1', [
            ('v1_flex', [])])
    ])
    self._ExpectDebugInstanceCall('default', 'v2_flex', 'i1')
    self.Run('app instances enable-debug --version v2_flex i1')
    self.AssertDebugCalled('default', 'v2_flex', 'i1')

  def testEnableDebug_FilterBoth(self):
    self._ExpectCalls([
        ('default', [
            ('v1_flex', ['i1', 'i2']),
            ('v2_flex', [])
        ]),
        ('service1', [])
    ])
    self._ExpectDebugInstanceCall('default', 'v1_flex', 'i1')
    self.Run(
        'app instances enable-debug --service default --version v1_flex i1')
    self.AssertDebugCalled('default', 'v1_flex', 'i1')

  def testEnableDebug_ResourcePath(self):
    self._ExpectCalls([
        ('default', [
            ('v1_flex', ['i1', 'i2']),
            ('v2_flex', ['i1'])
        ]),
        ('service1', [
            ('v1_flex', ['i1'])])
    ])
    with self.assertRaisesRegex(
        instances_util.InvalidInstanceSpecificationError,
        r'No instances match the given specification\.'):
      self.Run('app instances enable-debug default/v1/i1')

  def testEnableDebug_Interactive(self):
    self._ExpectCalls([
        ('default', [
            ('v1_flex', ['i1', 'i2']),
            ('v2_flex', ['i1'])
        ]),
        ('service1', [
            ('v1_flex', ['i1'])])
    ])
    instances = [
        self._MakeUtilInstance('default', 'v1_flex', 'i1'),
        self._MakeUtilInstance('default', 'v1_flex', 'i2'),
        self._MakeUtilInstance('default', 'v2_flex', 'i1'),
        self._MakeUtilInstance('service1', 'v1_flex', 'i1')
    ]
    instance = instances[0]  # chosen arbitrarily
    self.select_instance_mock.return_value = instance

    self._ExpectDebugInstanceCall(instance.service, instance.version,
                                  instance.id)

    self.Run('app instances enable-debug')

    self.AssertDebugCalled(instance.service, instance.version, instance.id)
    self.select_instance_mock.assert_called_once_with(instances,
                                                      service=None,
                                                      version=None)

  def testEnableDebug_InteractiveFilter(self):
    self._ExpectCalls([
        ('default', [
            ('v1_flex', ['i1', 'i2']),
            ('v2_flex', [])
        ]),
        ('service1', [])
    ])
    instances = [
        self._MakeUtilInstance('default', 'v1_flex', 'i1'),
        self._MakeUtilInstance('default', 'v1_flex', 'i2')
    ]
    instance = instances[0]  # chosen arbitrarily
    self.select_instance_mock.return_value = instance

    self._ExpectDebugInstanceCall(instance.service, instance.version,
                                  instance.id)

    self.Run(
        'app instances enable-debug --service {0} --version {1}'.format(
            instance.service, instance.version))

    self.AssertDebugCalled(instance.service, instance.version, instance.id)
    self.select_instance_mock.assert_called_once_with(instances,
                                                      service=instance.service,
                                                      version=instance.version)
