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
"""Helpers for commands that shell out to kubectl.

In order to use kubectl, commands need to fetch GKE cluster credentials
and pod info. The helpers herein are shared by tests that verify these
interactions.
"""

from __future__ import absolute_import
from __future__ import unicode_literals
import six
from six.moves import range  # pylint: disable=redefined-builtin


class FakeExec(object):
  """Fake execution_utils.Exec method that facilitates verification of calls.

  We use this rather than mock.Mock.assert_has_calls because mock.Call
  imposes a strict requirement on the order of parameters, which makes
  the test more brittle. It also allows us to control the return value
  and write to the out_func.

  To use, register a callback for each invocation. The callback's return
  value will be returned to the caller. For example:
  fe = FakeExec(...)
  def cb_zero(args, **kwargs):
    if kwargs.get('out_func') is not None:
      kwargs['out_func']('foo')
    return 0
  fe.AddCallback(0, cb_zero)

  Note that the callback takes a positional arg called `args` which
  corresponds to the `args` list argument to execution_utils.Exec.
  This is in contrast to the common idiom of a tuple arg defined as
  `*args`.
  """

  def __init__(self):
    self.call_count = 0
    self.callbacks = []

  def AddCallback(self, call_number, cb):
    """Adds expected callback to FakeExec object.

    Args:
      call_number: The number of times callback should be expected.
      cb: Callback to call instead when FakeExec is called.

    Raises:
      ValueError: if negative call number is provided
    """
    if call_number < 0:
      raise ValueError(
          'call_number ({}) must be non-negative.'.format(call_number))

    if call_number < len(self.callbacks):
      self.callbacks[call_number] = cb
      return
    # Pad out callbacks until we the tail is long enough to append.
    while call_number > len(self.callbacks):
      self.callbacks.append(None)
    self.callbacks.append(cb)

  def __call__(self, args, **kwargs):
    if self.call_count >= len(self.callbacks):
      raise Exception('Unexpected call: Exec({}{})'.format(
          ', '.join(args), ', ' + ', '.join(
              '{}={}'.format(k, v) for k, v in six.iteritems(kwargs))))
    cb = self.callbacks[self.call_count]
    if cb is None:
      raise IndexError('No callback registered for {}-th execution_utils.Exec '
                       'call'.format(self.call_count))

    self.call_count += 1

    return cb(args, **kwargs)

  def Verify(self):
    assert self.call_count == len(self.callbacks)


class CredentialedExec(FakeExec):
  """Convenience test fake for calls to Exec after fetchign credentials.

  When shelling out to kubectl, it is currently always necessary to fetch
  cluster credentials first. This test fake for execution_utils.Exec
  allows its users to verify behavior that occurs after credentials
  have been obtained in a standardized way.

  Users of this class should add callbacks to verify Exec calls that
  follow credential acquisition. For example:

  credentialed_exec = CredentialedExec(...)
  def RunProxyCallback(args, **kwargs):
    # Verify that an appropriate Exec call for starting a web proxy
    # was made, following any calls needed to obtain GKE credentials.

  credentialed_exec.AddCallback(0, RunProxyCallback)

  See also the docs for FakeExec.
  """

  def __init__(self,
               test_case=None,
               project=None,
               location=None,
               gke_cluster=None,
               gcloud_path=None):
    if (test_case is None or project is None or location is None or
        gke_cluster is None or gcloud_path is None):
      raise ValueError('All args must be provided.')

    super(CredentialedExec, self).__init__()

    def _GetCredentialsCallback(args, **_):
      AssertListHasPrefix(
          test_case, args,
          [gcloud_path, 'container', 'clusters', 'get-credentials'])
      # TODO(b/63644138): Once zones are exposed via the API, the expected zone
      # should match what's in the environment.
      AssertContainsAllSublists(test_case, args, ['--project', project],
                                ['--zone', location + '-a'])
      test_case.assertIn(gke_cluster, args)
      return 0

    self.setup_calls = []
    self.setup_calls.append(_GetCredentialsCallback)

    for i, cb in enumerate(self.setup_calls):
      super(CredentialedExec, self).AddCallback(i, cb)

  def AddCallback(self, call_number, cb):
    super(CredentialedExec, self).AddCallback(
        call_number + len(self.setup_calls), cb)


def AssertListHasPrefix(test_case, lst, prefix):
  test_case.assertEquals(prefix, lst[:len(prefix)])


def AssertContainsAllSublists(test_case, lst, *sublists):
  for sublist in sublists:
    test_case.assertTrue(ContainsSublist(lst, sublist))


def ContainsSublist(lst, sublist):
  sublen = len(sublist)
  return any(sublist == lst[i:i + sublen] for i in range(len(lst) - sublen + 1))
