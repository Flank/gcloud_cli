# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Set of utilities used in e2e tests involving gsutil."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib
import os

from googlecloudsdk.core import config
from googlecloudsdk.core.util import files


@contextlib.contextmanager
def ModifiedGsutilStateDir(account):
  """A contextmanager that modifies the gsutil state directory.

  This is useful when gsutil commands need to be called from within an
  integration test. By default, gsutil uses the home directory of the user
  running the command as the state directory. With this decorator, the BOTO
  config is overriden to use a temporary directory as the state directory.

  Args:
    account: The account the test will be running as.
  Yields:
    The path of the modified state directory.
  """
  boto_config_path = config.Paths().LegacyCredentialsGSUtilPath(account)
  # Ensure the containing directory for the boto config exists, in case this is
  # the first time the file is being accessed on the system.
  if not os.path.exists(os.path.dirname(boto_config_path)):
    os.makedirs(os.path.dirname(boto_config_path))

  with files.TemporaryDirectory() as temp_dir:
    new_config = '[GSUtil]\nstate_dir = {0}'.format(temp_dir)
    with open(boto_config_path, 'a') as boto_config:
      boto_config.write(new_config)
    yield temp_dir
