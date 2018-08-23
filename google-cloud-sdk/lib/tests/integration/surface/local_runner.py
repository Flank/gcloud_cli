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

"""Testing recorded sessions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from tests.lib import sdk_test_base
from tests.lib import session_test_base
from tests.lib import test_case
import six


class SessionTestMeta(type):
  """Metaclass generating a separate test* methods for every *.yaml file."""

  def __new__(mcs, name, bases, namespace):
    session_tests_root = sdk_test_base.SdkBase.Resource('tests', 'integration',
                                                        'surface')
    for root, unused_dirs, files in os.walk(session_tests_root):
      for f in [f for f in files if f.endswith('.yaml')]:
        path = os.path.join(root, f)
        test_name = 'test{}'.format(os.path.splitext(os.path.relpath(
            path, session_tests_root))[0].title().replace(
                '/', '').replace('-', '').replace('_', ''))
        namespace[test_name] = mcs.GetTest(path)

    return super(SessionTestMeta, mcs).__new__(mcs, name, bases, namespace)

  @classmethod
  def GetTest(mcs, path):
    def Test(self):
      with session_test_base.SessionManager(self, self.Resource(path)):
        self.Run(self.command)
    return Test


class SessionTest(
    six.with_metaclass(SessionTestMeta, session_test_base.SessionTestBase)):

  pass


if __name__ == '__main__':
  test_case.main()
