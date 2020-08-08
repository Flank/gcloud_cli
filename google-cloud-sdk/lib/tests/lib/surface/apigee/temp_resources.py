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
"""Context managers for temporary Apigee resources."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib
import os
import time
from xml.sax import saxutils
import zipfile

from googlecloudsdk.command_lib.apigee import request
from googlecloudsdk.core.util import files
from tests.lib import e2e_utils

import six
from six.moves import urllib

_API_REVISION_XML_TEMPLATE = """<APIProxy revision={revision} name={name}>
    <DisplayName></DisplayName>
    <Description></Description>
    <CreatedAt>1588958425357</CreatedAt>
    <LastModifiedAt>1588958425357</LastModifiedAt>
    <BasePaths>{basepath}</BasePaths>
    <Policies></Policies>
    <ProxyEndpoints>
        <ProxyEndpoint>default</ProxyEndpoint>
    </ProxyEndpoints>
    <Resources></Resources>
    <TargetServers></TargetServers>
    <TargetEndpoints>
        <TargetEndpoint>default</TargetEndpoint>
    </TargetEndpoints>
</APIProxy>
"""

_PROXY_XML_TEMPLATE = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<ProxyEndpoint name="default">
  <PreFlow name="PreFlow">
    <Request/>
    <Response/>
  </PreFlow>
  <Flows/>
  <PostFlow name="PostFlow">
    <Request/>
    <Response/>
  </PostFlow>
  <HTTPProxyConnection>
    <BasePath>{basepath}</BasePath>
  </HTTPProxyConnection>
  <RouteRule name="default">
    <TargetEndpoint>default</TargetEndpoint>
  </RouteRule>
</ProxyEndpoint>
"""

_TARGET_XML_TEMPLATE = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<TargetEndpoint name="default">
  <PreFlow name="PreFlow">
    <Request/>
    <Response/>
  </PreFlow>
  <Flows/>
  <PostFlow name="PostFlow">
    <Request/>
    <Response/>
  </PostFlow>
  <HTTPTargetConnection>
    <URL>{target_url}</URL>
  </HTTPTargetConnection>
</TargetEndpoint>
"""


@contextlib.contextmanager
def _APIProxyArchive(name, revision, basepath, target_url):
  """Creates a simple API proxy config archive.

  Args:
    name: the name of the API proxy to be configured.
    revision: the API proxy revision to be configured.
    basepath: the path where users would send requests to the API proxy.
    target_url: the URL to which the API proxy should send requests.

  Yields:
    a temporary ZIP archive of the proxy configuration which will be deleted
    upon exiting the context.
  """
  format_params = {
      "name": saxutils.quoteattr(name),
      "revision": saxutils.quoteattr(six.text_type(revision)),
      "basepath": saxutils.escape(basepath),
      "target_url": saxutils.escape(target_url)
  }
  with files.TemporaryDirectory() as archive_dir:
    with files.ChDir(archive_dir):
      files.MakeDir("apiproxy")
      manifest_filename = os.path.join("apiproxy", name + ".xml")
      with open(manifest_filename, "w") as top_xml:
        top_xml.write(_API_REVISION_XML_TEMPLATE.format(**format_params))

      proxies_dir = os.path.join("apiproxy", "proxies")
      proxies_filename = os.path.join(proxies_dir, "default.xml")
      files.MakeDir(proxies_dir)
      with open(proxies_filename, "w") as proxy_xml:
        proxy_xml.write(_PROXY_XML_TEMPLATE.format(**format_params))

      targets_dir = os.path.join("apiproxy", "targets")
      targets_filename = os.path.join(targets_dir, "default.xml")
      files.MakeDir(targets_dir)
      with open(targets_filename, "w") as target_xml:
        target_xml.write(_TARGET_XML_TEMPLATE.format(**format_params))

      archive_file = open("config.zip", "wb+")
      with zipfile.ZipFile(archive_file, "w") as archive:
        archive.write(manifest_filename)
        archive.write(proxies_filename)
        archive.write(targets_filename)
      archive_file.flush()
      archive_file.seek(0)
      try:
        yield archive_file
      finally:
        archive_file.close()


# TODO(b/157082792): Use gcloud commands, not direct ResponseToApiRequest calls.
# Commands to create and delete environments, API proxies, and revisions are not
# yet part of the `gcloud apigee` command surface. If and when such commands are
# added, these helper methods should be modified to use them.


def _IsTimestampStale(timestamp_str):
  """Returns whether timestamp_str is more than twelve hours old."""
  current_timestamp = int(time.time()*1000)
  return current_timestamp - int(timestamp_str) > (12*60*60*1000)


def CleanUpOldResources(organization):
  """Cleans up deployments, proxies, and environments more than 12 hours old.

  This function is intended to be called as a pre-test environment cleaner, and
  thus will avoid adding to the flakiness potential of subsequent tests, even
  when doing so risks ignoring important errors. If one attempt to remove an old
  resource fails, no matter the reason, it will continue to try to remove the
  others and exit without raising any exceptions.

  Args:
    organization: the name of the organization whose resources should be cleaned
      up.
  """
  identifiers = {"organizationsId": organization}
  try:
    deployments = request.ResponseToApiRequest(
        identifiers, ["organization"], "deployment")
    if "deployments" in deployments:
      for deployment in deployments["deployments"]:
        try:
          if _IsTimestampStale(deployment["deployStartTime"]):
            # More than 12 hours old. Its associated test certainly couldn't be
            # running anymore.
            deployment_identifiers = {
                "organizationsId": organization,
                "environmentsId": deployment["environment"],
                "apisId": deployment["apiProxy"],
                "revisionsId": deployment["revision"]
            }
            request.ResponseToApiRequest(
                deployment_identifiers,
                ["organization", "environment", "api", "revision"],
                "deployment", method="DELETE")
        except Exception:  # pylint: disable=broad-except
          # Even if this deployment is broken or malformed somehow, don't let
          # that prevent cleanup of the others.
          continue
  except Exception:  # pylint: disable=broad-except
    pass

  try:
    apis = request.ResponseToApiRequest(identifiers, ["organization"], "api")
    if "proxies" in apis:
      for api in apis["proxies"]:
        try:
          revision_identifiers = identifiers.copy()
          revision_identifiers["apisId"] = api["name"]
          api = request.ResponseToApiRequest(
              revision_identifiers, ["organization", "api"])
          if _IsTimestampStale(api["metaData"]["createdAt"]):
            request.ResponseToApiRequest(
                revision_identifiers, ["organization", "api"], method="DELETE")
        except Exception:  # pylint: disable=broad-except
          # Even if this API is broken or malformed somehow, don't let that
          # prevent cleanup of the others.
          continue
  except Exception:  # pylint: disable=broad-except
    pass


@contextlib.contextmanager
def APIProxy(organization, name_prefix, message=None, basepath_suffix=None):
  """Creates a temporary Apigee API proxy.

  The API proxy will have a basepath of /proxy_name/suffix, and will be
  automatically cleaned up upon exiting the context.

  Args:
    organization: the Apigee organization in which to create the API proxy.
    name_prefix: a string to include at the beginning of the API proxy's name.
    message: the message the API proxy should return when called.
    basepath_suffix: a suffix to add to the API proxy's basepath.

  Yields:
    the name of the created API proxy.
  """
  name = next(e2e_utils.GetResourceNameGenerator(name_prefix))
  basepath = "/" + name + ("/" + basepath_suffix if basepath_suffix else "")

  query_string = urllib.parse.urlencode({"user": message}) if message else ""
  url_tuple = ("https", "mocktarget.apigee.net", "/user", "", query_string, "")
  target_url = urllib.parse.urlunparse(url_tuple)
  with _APIProxyArchive(name, 1, basepath, target_url) as archive:
    identifiers = {"organizationsId": organization}
    request.ResponseToApiRequest(
        identifiers, ["organization"],
        "api",
        method="POST",
        body_mimetype="application/octet-stream",
        body=archive,
        query_params={
            "name": name,
            "action": "import"
        })

  try:
    yield name
  finally:
    identifiers["apisId"] = name
    request.ResponseToApiRequest(
        identifiers, ["organization", "api"], method="DELETE")


@contextlib.contextmanager
def Revision(organization,
             api_proxy,
             revision,
             message=None,
             basepath_suffix=None):
  """Creates a temporary Apigee API proxy revision.

  The revision will have a basepath of /proxy_name/suffix, and will be
  automatically cleaned up upon exiting the context.

  Args:
    organization: the Apigee organization in which to create the API proxy.
    api_proxy: the name of the existing API proxy to which the revision should
      be added.
    message: the message the API proxy should return when called.
    basepath_suffix: a suffix to add to the API proxy's basepath.

  Yields:
    the revision number of the created revision.
  """
  basepath = "/" + api_proxy
  if basepath_suffix:
    basepath += "/" + basepath_suffix

  query_string = urllib.parse.urlencode({"user": message}) if message else ""
  url_tuple = ("https", "mocktarget.apigee.net", "/user", "", query_string, "")
  target_url = urllib.parse.urlunparse(url_tuple)
  with _APIProxyArchive(api_proxy, revision, basepath, target_url) as archive:
    identifiers = {
        "organizationsId": organization,
        "apisId": api_proxy,
        "revisionsId": six.text_type(revision)
    }

    request.ResponseToApiRequest(
        identifiers, ["organization"],
        "api",
        method="POST",
        body_mimetype="application/octet-stream",
        body=archive,
        query_params={
            "name": api_proxy,
            "action": "import"
        })

  try:
    yield revision
  finally:
    request.ResponseToApiRequest(
        identifiers, ["organization", "api", "revision"], method="DELETE")
