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

"""Base class for gcloud app logs tests."""
from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


PROJECT = 'fakeproject'


class LogsTestBase(cli_test_base.CliTestBase, sdk_test_base.WithFakeAuth):
  """Base class for logs command group tests."""

  def SetUp(self):
    properties.VALUES.core.project.Set(PROJECT)
    self.log_name_filter = (
        u'logName=('
        '"projects/{project}/logs/appengine.googleapis.com%2Fcrash.log" OR '
        '"projects/{project}/logs/appengine.googleapis.com%2Fnginx.request" '
        'OR '
        '"projects/{project}/logs/appengine.googleapis.com%2Frequest_log" OR '
        '"projects/{project}/logs/appengine.googleapis.com%2Fstderr" OR '
        '"projects/{project}/logs/appengine.googleapis.com%2Fstdout")'
        .format(project=PROJECT))
    self.resource_filter = 'resource.type="gae_app"'
    self.default_filter = self.resource_filter + ' AND ' + self.log_name_filter
    self.messages = apis.GetMessagesModule('logging', 'v2')
    self.v2_client = mock.Client(apis.GetClientClass('logging', 'v2'))
    self.v2_client.Mock()
    self.addCleanup(self.v2_client.Unmock)

  def _CreateRequest(self, log_filter=None, page_token=None, page_size=200,
                     order_by=u'timestamp desc'):
    """Simply an internal wrapper method to create request objects.

    Args:
        log_filter: An advanced filter to use, or the default filter if None.
        page_token: Page token for continued requests.
        page_size: Page size requested.
        order_by: String that will sort logs by time.

    Returns:
        A request message object with the relevant parameters set.
    """
    if log_filter is None:
      log_filter = self.default_filter
    return self.messages.ListLogEntriesRequest(
        filter=log_filter.format(project=unicode(PROJECT)),
        orderBy=order_by,
        pageSize=page_size,
        pageToken=page_token,
        resourceNames=[u'projects/{}'.format(unicode(PROJECT))])
