# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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

"""A pytest plugin for silencing tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


class SilenceTestPlugin(object):
  """A pytest plugin for silencing tests.

  A silenced test will run, but will not cause the entire job to fail if it
  fails. You can silence a test with:
    @pytest.mark.silence(reason='test skip reason')
  """

  def pytest_runtest_logreport(self, report):
    """Modify XML output for silenced tests.

    Add a `silenced` prop to all silenced tests.
    Mark failed silenced tests as skipped and save failure text in prop.

    Args:
      report: Pytest test report.
    """
    # Keywords can be a dict or a tuple of pairs.
    keywords = dict(report.keywords)
    if keywords.get('silence'):
      report.xml_properties['silenced'] = 'True'
      if report.outcome == 'failed':
        failure_text = (
            '{existing}{when} failure:\n{failure}\n'.format(
                existing=report.xml_properties.get('failure', ''),
                when=report.when, failure=report.longrepr))
        # Encode to preserve newlines, decode to make it unicode.
        report.xml_properties['failure'] = failure_text.encode(
            'unicode_escape').decode()
        report.outcome = 'skipped'
        # Mark the test as an expected failure. This will show as 'xfailed' in
        # pytest output.
        report.wasxfail = 'skip expected failure'


def pytest_configure(config):
  config.pluginmanager.register(SilenceTestPlugin())
