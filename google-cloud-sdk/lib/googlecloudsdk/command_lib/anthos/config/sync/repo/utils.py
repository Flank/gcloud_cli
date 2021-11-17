# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Utils for running gcloud command and kubectl command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io
import os

from googlecloudsdk.api_lib.container import util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core.util import files

_KUBECONFIGENV = 'KUBECONFIG'
_DEFAULTKUBECONFIG = 'config_sync'


def KubeconfigForMembership(project, membership):
  """Get the kubeconfig of a membership.

  If the kubeconfig for the membership already exists locally, use it;
  Otherwise run a gcloud command to get the credential for it.

  Args:
    project: The project ID of the membership.
    membership: The name of the membership.

  Returns:
    None

  Raises:
      Error: The error occured when it failed to get credential for the
      membership.
  """
  context = 'connectgateway_{project}_{membership}'.format(
      project=project, membership=membership)
  command = ['config', 'use-context', context]
  _, err = RunKubectl(command)
  if err is None:
    return

  # kubeconfig for the membership doesn't exit locally
  # run a gcloud command to get the credential of the given
  # membership

  args = [
      'container', 'hub', 'memberships', 'get-credentials', membership,
      '--project', project
  ]
  _, err = _RunGcloud(args)
  if err:
    raise exceptions.Error(
        'Error getting credential for membership {}: {}'.format(
            membership, err))


def KubeconfigForCluster(project, region, cluster):
  """Get the kubeconfig of a GKE cluster.

  If the kubeconfig for the GKE cluster already exists locally, use it;
  Otherwise run a gcloud command to get the credential for it.

  Args:
    project: The project ID of the cluster.
    region: The region of the cluster.
    cluster: The name of the cluster.

  Returns:
    None

  Raises:
    Error: The error occured when it failed to get credential for the cluster.
  """
  context = 'gke_{project}_{region}_{cluster}'.format(
      project=project, region=region, cluster=cluster)
  command = ['config', 'use-context', context]
  _, err = RunKubectl(command)
  if err is None:
    return None
  # kubeconfig for the cluster doesn't exit locally
  # run a gcloud command to get the credential of the given
  # cluster
  args = [
      'container', 'clusters', 'get-credentials', cluster, '--region', region,
      '--project', project
  ]
  _, err = _RunGcloud(args)
  if err:
    raise exceptions.Error('Error getting credential for cluster {}: {}'.format(
        cluster, err))


def ListConfigControllerClusters(project):
  """Runs a gcloud command to list the clusters that host Config Controller.

  Currently the Config Controller only works in the region
  us-central1 according to Config Controller doc
  https://cloud.google.com/anthos-config-management/docs/how-to/config-controller-setup

  Args:
    project: project that the Config Controller is in.

  Returns:
    The list of (cluster, region) for Config Controllers.

  Raises:
    Error: The error occured when it failed to list clusters.
  """
  # TODO(b/202418506) Check if there is any library
  # function to list the clusters.
  args = [
      'container', 'clusters', 'list', '--project', project, '--filter',
      'name:krmapihost', '--format', 'table(name,location)'
  ]
  output, err = _RunGcloud(args)
  if err:
    raise exceptions.Error('Error listing clusters: {}'.format(err))

  clusters = []
  for cluster in output.split('\n'):
    c = _ParseClusterLocation(cluster)
    if c:
      clusters.append(c)
  return clusters


def ListMemberships(project):
  """List hte memberships from a given project.

  Args:
    project: project that the memberships are in.

  Returns:
    The memberships registered to the fleet hosted by the given project.

  Raises:
    Error: The error occured when it failed to list memberships.
  """
  # TODO(b/202418506) Check if there is any library
  # function to list the memberships.
  args = [
      'container', 'hub', 'memberships', 'list', '--format', 'table(name)',
      '--project', project
  ]
  output, err = _RunGcloud(args)
  if err:
    raise exceptions.Error('Error listing memberships: {}'.format(err))

  memberships = []
  for membership in output.replace('\n', ' ').split():
    if membership != 'NAME':
      memberships.append(membership)
  return memberships


def RunKubectl(args):
  """Runs a kubectl command with the cluster referenced by this client.

  Args:
    args: command line arguments to pass to kubectl

  Returns:
    The contents of stdout if the return code is 0, stderr (or a fabricated
    error if stderr is empty) otherwise
  """
  cmd = [util.CheckKubectlInstalled()]
  cmd.extend(args)
  out = io.StringIO()
  err = io.StringIO()
  env = _GetEnvs()
  returncode = execution_utils.Exec(
      cmd,
      no_exit=True,
      out_func=out.write,
      err_func=err.write,
      in_str=None,
      env=env)

  if returncode != 0 and not err.getvalue():
    err.write('kubectl exited with return code {}'.format(returncode))

  return out.getvalue() if returncode == 0 else None, err.getvalue(
  ) if returncode != 0 else None


def _RunGcloud(args):
  """Runs a gcloud command.

  Args:
    args: command line arguments to pass to gcloud

  Returns:
    The contents of stdout if the return code is 0, stderr (or a fabricated
    error if stderr is empty) otherwise
  """
  cmd = execution_utils.ArgsForGcloud()
  cmd.extend(args)
  out = io.StringIO()
  err = io.StringIO()
  env = _GetEnvs()
  returncode = execution_utils.Exec(
      cmd,
      no_exit=True,
      out_func=out.write,
      err_func=err.write,
      in_str=None,
      env=env)

  if returncode != 0 and not err.getvalue():
    err.write('gcloud exited with return code {}'.format(returncode))
  return out.getvalue() if returncode == 0 else None, err.getvalue(
  ) if returncode != 0 else None


def _GetEnvs():
  """Get the environment variables that should be passed to kubectl/gcloud commands.

  Returns:
    The dictionary that includes the environment varialbes.
  """
  env = dict(os.environ)
  if _KUBECONFIGENV not in env:
    env[_KUBECONFIGENV] = files.ExpandHomeDir(
        os.path.join('~', '.kube', _DEFAULTKUBECONFIG))
  return env


def _ParseClusterLocation(cluster_and_location):
  """Get the cluster and location for the Config Controller cluster.

  Args:
    cluster_and_location: The one line string that contains the Config
      Controller resource name and its location.

  Returns:
    The tuple of cluster and region.
  """
  if not cluster_and_location or cluster_and_location.startswith('NAME'):
    return None
  cluster = ''
  region = ''
  strings = cluster_and_location.split(' ')
  for s in strings:
    if s.startswith('krmapihost'):
      cluster = s
    elif s:
      region = s
  return (cluster, region)
