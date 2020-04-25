# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Initializes gcloud test package."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys

# The google package has a .pth file in site-package folder, which is loaded by
# the python interpreter before running gcloud code. Because of this early
# loading, gcloud's bundled google package is not used. If there is difference
# between these two copies, tests could fail.
#
# When users run gcloud on terminal, we use the '-S' option of python
# interpreter to disable the early loading. We remove the
# site-package from sys.path in run_pytest.py, reloading here will
# load the right copy.
if 'google' in sys.modules:
  import google  # pylint:disable=g-import-not-at-top
  try:
    reload(google)
  except NameError:
    import importlib  # pylint:disable=g-import-not-at-top
    importlib.reload(google)
