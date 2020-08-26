#!/usr/bin/python
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
"""Updates do-not-delete-knative-test-latest cluster to latest version."""

from __future__ import print_function

import subprocess
import sys

VERSION_BLACKLIST = ('1.14.6-gke.2', '1.14.6-gke.1', '1.14.3-gke.11')

CLUSTER_NAME = 'do-not-delete-knative-test-latest'

IS_GT_PY3 = sys.version_info.major >= 3


def Run(cmd):
  """Run a process.

  Args:
    cmd: (list[str]) command line command.

  Returns:
    A tuple of the return code, stdout as a str, and stderr as a str.
  """
  process = subprocess.Popen(
      cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  out, err = process.communicate()
  return process.returncode, out, err


def GetLatestVersion():
  """Get the latest available kubernetes cluster version."""
  code, out, err = Run([
      'gcloud', 'container', 'get-server-config', '--zone', 'us-central1-a',
      '--format=value(validMasterVersions)'
  ])
  if code:
    print(err, file=sys.stderr)
    raise Exception(err)

  if IS_GT_PY3:
    out = out.decode('utf-8')
  versions = out.strip().split(';')
  for version in versions:
    if version not in VERSION_BLACKLIST:
      return version

  return None


def GetCurrentVersion():
  """Get the current kubernetes cluster version."""
  code, out, err = Run([
      'gcloud', 'container', 'clusters', 'describe', CLUSTER_NAME,
      '--region=us-central1-a', '--format=value(currentMasterVersion)'
  ])
  if code:
    print(err, file=sys.stderr)
    raise Exception(err)

  return out.strip()


def IsLocalTest():
  """Check if the scenario test is run in local mode.

  Returns:
    Boolean value indicating if the test is run locally.
  """
  try:
    return GetCurrentAccount() == 'fake_account'
  except OSError:
    # Calling gcloud directly doesn't work on windows unit tests. Unit tests
    # are local tests.
    return True


def GetCurrentAccount():
  """Get the current user account."""
  code, out, err = Run(
      ['gcloud', 'config', 'list', 'account', '--format=value(core.account)'])
  if code:
    print(err, file=sys.stderr)
    raise Exception(err)

  account = out.strip()
  return account.decode('utf-8') if IS_GT_PY3 else account


def main():
  # If the current account is fake-account, then we are in local mode. Don't
  # run cluster update in local mode.
  if IsLocalTest():
    return

  latest_version = GetLatestVersion()
  current_version = GetCurrentVersion()
  if latest_version != current_version:
    code, _, err = Run([
        'gcloud', 'container', 'clusters', 'upgrade', CLUSTER_NAME, '--master',
        '--region=us-central1-a',
        '--cluster-version={version}'.format(version=latest_version), '--quiet'
    ])
    if code:
      print(err, file=sys.stderr)


if __name__ == '__main__':
  main()
