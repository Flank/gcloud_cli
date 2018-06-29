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

"""Integration tests for creating/deleting IAM keys."""

from __future__ import absolute_import
from __future__ import unicode_literals

import os.path
import re
import tempfile

from tests.lib.surface.iam import e2e_test_base


def _GetTempFileName():
  file_obj = tempfile.NamedTemporaryFile()
  filename = file_obj.name
  # Windows platforms give permission denied errors if you try to use this
  # filename without closing the file object. Python doesn't have a way to
  # just generate a tempname. It's gnarly, but hey, it works.
  file_obj.close()
  return filename


# This test requires the 'Google Identity and Access Management' API to be
# enabled on the current project.
class KeysTest(e2e_test_base.ServiceAccountBaseTest):

  def testKeys(self):
    self.Run(
        'iam service-accounts create {0} '
        '--display-name "Keys Test"'.format(self.account_name))
    key_id = self.CreateKey()
    self.ListKeys(key_id)
    self.DeleteKey(key_id)

  def CreateKey(self):
    filename = _GetTempFileName()
    self.ClearOutput()
    self.RunFormat(
        'iam service-accounts keys create --iam-account={email} '
        '--key-file-type=json {0}',
        filename)

    key_id_match = re.search(r'created key \[([^\]]+)\]', self.GetErr())
    if not key_id_match:
      self.fail('Couldn\'t find a key id on stderr')
    key_id = key_id_match.group(1)

    self.AssertErrContains('created key [{0}]'.format(key_id))
    self.AssertErrContains('of type [json]')
    self.AssertErrContains('as [{0}]'.format(filename))
    self.AssertErrContains('for [{0}]'.format(self.email))

    if not os.path.exists(filename):
      self.fail('The key didn\'t get saved to the filesystem!')
    os.remove(filename)
    return key_id

  def ListKeys(self, key_id):
    self.ClearOutput()
    self.RunFormat(
        'iam service-accounts keys list --iam-account={email} '
        '--managed-by=user')
    self.AssertOutputContains('{0}'.format(key_id))

    self.ClearOutput()
    self.RunFormat(
        'iam service-accounts keys list --iam-account={email} '
        '--managed-by=system')
    self.AssertOutputNotContains('{0}'.format(key_id))

  def DeleteKey(self, key_id):
    self.ClearErr()
    self.ClearOutput()
    self.RunFormat('iam service-accounts keys delete '
                   '--iam-account={email} {0}',
                   key_id)
    self.AssertErrContains(
        'deleted key [{1}] for service account [{0}]'.format(
            self.email, key_id))


if __name__ == '__main__':
  e2e_test_base.main()
