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

import collections
import contextlib
import datetime
import fnmatch
import json
import signal

from googlecloudsdk.command_lib.anthos.config.sync.repo import utils
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log


class RepoStatus:
  """RepoStatus represents an aggregated repo status after deduplication."""

  def __init__(self):
    self.synced = 0
    self.pending = 0
    self.error = 0
    self.stalled = 0
    self.reconciling = 0
    self.total = 0
    self.namespace = ''
    self.name = ''
    self.source = ''
    self.cluster_type = ''


class RepoResourceGroupPair:
  """RepoResourceGroupPair represents a RootSync|RepoSync and a ResourceGroup pair."""

  def __init__(self, repo, rg, cluster_type):
    self.repo = repo
    self.rg = rg
    self.cluster_type = cluster_type


class RawRepos:
  """RawRepos records all the RepoSync|RootSync CRs and ResourceGroups across multiple clusters."""

  def __init__(self):
    self.repos = collections.defaultdict(
        lambda: collections.defaultdict(RepoResourceGroupPair))

  def AddRepo(self, membership, repo, rg, cluster_type):
    key = _GetGitKey(repo)
    self.repos[key][membership] = RepoResourceGroupPair(repo, rg, cluster_type)

  def GetRepos(self):
    return self.repos


def ListRepos(project_id, status, namespace, membership, selector, targets):
  """List repos across clusters.

  Args:
    project_id: project id that the command should list the repo from.
    status: status of the repo that the list result should contain
    namespace: namespace of the repo that the command should list.
    membership: membership name that the repo should be from.
    selector: label selectors for repo. It applies to the RootSync|RepoSync CRs.
    targets: The targets from which to list the repos. The value should be one
      of "all", "fleet-clusters" and "config-controller".

  Returns:
    A list of RepoStatus.

  """
  if targets and targets not in ['all', 'fleet-clusters', 'config-controller']:
    raise exceptions.Error(
        '--targets must be one of "all", "fleet-clusters" and "config-controller"'
    )
  if targets != 'fleet-clusters' and membership:
    raise exceptions.Error(
        '--membership should only be specified when --targets=fleet-clusters')
  if status not in ['all', 'synced', 'error', 'pending', 'stalled']:
    raise exceptions.Error(
        '--status must be one of "all", "synced", "pending", "error", "stalled"'
    )
  selector_map, err = _ParseSelector(selector)
  if err:
    raise exceptions.Error(err)

  repo_cross_clusters = RawRepos()

  if targets == 'all' or targets == 'config-controller':
    # list the repos from Config Controller cluster
    clusters = []
    try:
      clusters = utils.ListConfigControllerClusters(project_id)
    except exceptions.Error as err:
      log.error(err)
    if clusters:
      for cluster in clusters:
        try:
          utils.KubeconfigForCluster(project_id, cluster[1], cluster[0])
          _AppendReposFromCluster(cluster[0], repo_cross_clusters,
                                  'Config Controller', namespace, selector_map)
        except exceptions.Error as err:
          log.error(err)

  if targets == 'all' or targets == 'fleet-clusters':
    # list the repos from membership clusters
    try:
      memberships = utils.ListMemberships(project_id)
    except exceptions.Error as err:
      raise err

    for member in memberships:
      if not _MembershipMatched(member, membership):
        continue
      try:
        utils.KubeconfigForMembership(project_id, member)
        _AppendReposFromCluster(member, repo_cross_clusters, 'Membership',
                                namespace, selector_map)
      except exceptions.Error as err:
        log.error(err)

  # aggregate all the repos
  return _AggregateRepoStatus(repo_cross_clusters, status)


def _AggregateRepoStatus(repos_cross_clusters, status):
  """Aggregate the repo status from multiple clusters.

  Args:
    repos_cross_clusters: The repos read from multiple clusters.
    status: The status used for filtering the list results.

  Returns:
    The list of RepoStatus after aggregation.
  """
  repos = []
  for git, rs in repos_cross_clusters.GetRepos().items():
    repo_status = _GetRepoStatus(rs, git)
    if not _StatusMatched(status, repo_status):
      continue
    repos.append(repo_status)
  return repos


def _GetRepoStatus(rs, git):
  """Get the status for a repo.

  Args:
    rs: The dictionary of a unique repo across multiple clusters.
        It contains the following data: {
           cluster-name-1: RepoSourceGroupPair,
           cluster-name-2: RepoSourceGroupPair }
    git: The string that represent the git spec of the repo.

  Returns:
    One RepoStatus that represents the aggregated
    status for the current repo.
  """
  repo_status = RepoStatus()
  repo_status.source = git
  for _, pair in rs.items():
    status = 'SYNCED'
    obj = pair.repo
    namespace, name = _GetObjectKey(obj)
    repo_status.namespace = namespace
    repo_status.name = name
    single_repo_status = _GetStatusForRepo(obj)
    status = single_repo_status.status
    if status == 'SYNCED':
      repo_status.synced += 1
    elif status == 'PENDING':
      repo_status.pending += 1
    elif status == 'ERROR':
      repo_status.error += 1
    elif status == 'STALLED':
      repo_status.stalled += 1
    elif status == 'RECONCILING':
      repo_status.reconciling += 1
    repo_status.total += 1
    repo_status.cluster_type = pair.cluster_type
  return repo_status


def _MembershipMatched(membership, target_membership):
  """Check if the current membership matches the specified memberships.

  Args:
    membership: string The current membership.
    target_membership: string The specified memberships.

  Returns:
    Returns True if matching; False otherwise.
  """
  if not target_membership:
    return True

  if target_membership and '*' in target_membership:
    return fnmatch.fnmatch(membership, target_membership)
  else:
    members = target_membership.split(',')
    for m in members:
      if m == membership:
        return True
    return False


def _LabelMatched(obj, selector_map):
  """Checked if the given object matched with the label selectors."""
  if not obj:
    return False
  if not selector_map:
    return True
  labels = _GetPathValue(obj, ['metadata', 'labels'])
  if not labels:
    return False
  for key in selector_map:
    value = selector_map[key]
    if key not in labels or labels[key] != value:
      return False
  return True


def _StatusMatched(status, repo_status):
  """Checked if the aggregaged repo status matches the given status."""
  if status.lower() == 'all':
    return True
  if status.lower() == 'pending':
    return repo_status.pending > 0
  if status.lower() == 'stalled':
    return repo_status.stalled > 0
  if status.lower() == 'error':
    return repo_status.error > 0
  if status.lower() == 'synced':
    return repo_status.synced == repo_status.total


def _GetConditionForType(obj, condition_type):
  """Return the object condition for the given type.

  Args:
    obj: The json object that represents a RepoSync|RootSync CR.
    condition_type: Condition type.

  Returns:
    The condition for the given type.
  """
  conditions = _GetPathValue(obj, ['status', 'conditions'])
  if not conditions:
    return False
  for condition in conditions:
    if condition['type'] == condition_type:
      return condition
  return None


def _GetPathValue(obj, paths, default_value=None):
  """Get the value at the given paths from the input json object.

  Args:
    obj: The json object that represents a RepoSync|RootSync CR.
    paths: [] The string paths in the json object.
    default_value: The default value to return if the path value is not found in
      the object.

  Returns:
    The field value of the given paths if found. Otherwise it returns None.
  """
  if not obj:
    return default_value
  for p in paths:
    if p in obj:
      obj = obj[p]
    else:
      return default_value
  return obj


def _GetObjectKey(obj):
  """Return the Object Key containing namespace and name."""
  namespace = obj['metadata']['namespace']
  name = obj['metadata']['name']
  return namespace, name


def _GetGitKey(obj):
  """Hash the Git specification for the given RepoSync|RootSync object."""
  repo = obj['spec']['git']['repo']
  branch = 'main'
  if 'branch' in obj['spec']['git']:
    branch = obj['spec']['git']['branch']
  directory = '.'
  if 'dir' in obj['spec']['git']:
    directory = obj['spec']['git']['dir']
  revision = ''
  if 'revision' in obj['spec']['git']:
    revision = obj['spec']['git']['revision']
  if not revision:
    return '{repo}//{dir}@{branch}'.format(
        repo=repo, dir=directory, branch=branch)
  else:
    return '{repo}//{dir}@{branch}:{revision}'.format(
        repo=repo, dir=directory, branch=branch, revision=revision)


def _ParseSelector(selector):
  """This function parses the selector flag."""
  if not selector:
    return None, None
  selectors = selector.split(',')
  selector_map = {}
  for s in selectors:
    items = s.split('=')
    if len(items) != 2:
      return None, '--selector should have the format key1=value1,key2=value2'
    selector_map[items[0]] = items[1]
  return selector_map, None


def _AppendReposFromCluster(membership, repos_cross_clusters, cluster_type,
                            namespaces, selector):
  """List all the RepoSync and RootSync CRs from the given cluster.

  Args:
    membership: The membership name or cluster name of the current cluster.
    repos_cross_clusters: The repos across multiple clusters.
    cluster_type: The type of the current cluster. It is either a Fleet-cluster
      or a Config-controller cluster.
    namespaces: The namespaces that the list should get RepoSync|RootSync from.
    selector: The label selector that the RepoSync|RootSync should match.

  Returns:
    None

  Raises:
    Error: errors that happen when listing the CRs from the cluster.
  """
  _GetConfigManagement(membership, cluster_type)

  params = []
  if not namespaces or '*' in namespaces:
    params = [['--all-namespaces']]
  else:

    params = [['-n', ns] for ns in namespaces.split(',')]
  all_repos = []
  errors = []
  for p in params:
    repos, err = utils.RunKubectl(['get', 'rootsync,reposync', '-o', 'json'] +
                                  p)
    if err:
      errors.append(err)
      continue
    if repos:
      obj = json.loads(repos)
      if 'items' in obj:
        if namespaces and '*' in namespaces:
          for item in obj['items']:
            ns = _GetPathValue(item, ['metadata', 'namespace'], '')
            if fnmatch.fnmatch(ns, namespaces):
              all_repos.append(item)
        else:
          all_repos += obj['items']
  if errors:
    raise exceptions.Error(
        'Error getting RootSync and RepoSync custom resources: {}'.format(
            errors))

  count = 0
  for repo in all_repos:
    if not _LabelMatched(repo, selector):
      continue
    repos_cross_clusters.AddRepo(membership, repo, None, cluster_type)
    count += 1
  if count > 0:
    log.status.Print('getting {} RepoSync and RootSync from {}'.format(
        count, membership))


def _AppendReposAndResourceGroups(membership, repos_cross_clusters,
                                  cluster_type, name, namespace, source):
  """List all the RepoSync,RootSync CRs and ResourceGroup CRs from the given cluster.

  Args:
    membership: The membership name or cluster name of the current cluster.
    repos_cross_clusters: The repos across multiple clusters.
    cluster_type: The type of the current cluster. It is either a Fleet-cluster
      or a Config-controller cluster.
    name: The name of the desired repo.
    namespace: The namespace of the desired repo.
    source: The source of the repo. It should be copied from the output of the
      list command.

  Returns:
    None

  Raises:
    Error: errors that happen when listing the CRs from the cluster.
  """
  _GetConfigManagement(membership, cluster_type)
  params = []
  if not namespace:
    params = ['--all-namespaces']
  else:
    params = ['-n', namespace]
  repos, err = utils.RunKubectl(
      ['get', 'rootsync,reposync,resourcegroup', '-o', 'json'] + params)
  if err:
    raise exceptions.Error(
        'Error getting RootSync,RepoSync,Resourcegroup custom resources: {}'
        .format(err))

  if not repos:
    return
  obj = json.loads(repos)
  if 'items' not in obj or not obj['items']:
    return

  repos = {}
  resourcegroups = {}
  for item in obj['items']:
    ns, nm = _GetObjectKey(item)
    if name and nm != name:
      continue
    key = ns + '/' + nm
    kind = item['kind']
    if kind == 'ResourceGroup':
      resourcegroups[key] = item
    else:
      repos[key] = item

  count = 0
  for key, repo in repos.items():
    repo_source = _GetGitKey(repo)
    if source and repo_source != source:
      continue
    rg = None
    if key in resourcegroups:
      rg = resourcegroups[key]
    repos_cross_clusters.AddRepo(membership, repo, rg, cluster_type)
    count += 1
  if count > 0:
    log.status.Print('getting {} RepoSync and RootSync from {}'.format(
        count, membership))


def _GetConfigManagement(membership, cluster_type):
  """Get ConfigManagement to check if multi-repo is enabled.

  Args:
    membership: The membership name or cluster name of the current cluster.
    cluster_type: The type of the current cluster. It is either a Fleet-cluster
      or a Config-controller cluster.

  Returns:
    None

  Raises:
    Error: errors that happen when getting the object from the cluster.
  """
  config_management = None
  err = None
  timed_out = True
  with Timeout(5):
    config_management, err = utils.RunKubectl([
        'get', 'configmanagements.configmanagement.gke.io/config-management',
        '-o', 'json'
    ])
    timed_out = False
  if timed_out and cluster_type != 'Config Controller':
    raise exceptions.Error(
        'Timed out getting ConfigManagement object. ' +
        'Make sure you have setup Connect Gateway for ' + membership +
        ' following the instruction from https://cloud.google.com/anthos/multicluster-management/gateway/setup'
    )
  if timed_out:
    raise exceptions.Error('Timed out getting ConfigManagement object from ' +
                           membership)

  if err:
    raise exceptions.Error(
        'Error getting ConfigManagement object from {}: {}\n'.format(
            membership, err))
  config_management_obj = json.loads(config_management)
  if 'enableMultiRepo' not in config_management_obj[
      'spec'] or not config_management_obj['spec']['enableMultiRepo']:
    raise exceptions.Error(
        'Legacy mode is used in {}. Please enable the multi-repo feature to use this command.'
        .format(membership))
  if 'status' not in config_management_obj:
    log.status.Print(
        'The ConfigManagement object is not reconciled in {}. Please check if the Config Management is running on it.'
        .format(membership))
  errors = config_management_obj.get('status', {}).get('errors')
  if errors:
    log.status.Print(
        'The ConfigManagement object contains errors in{}:\n{}'.format(
            membership, errors))


class DetailedStatus:
  """DetailedStatus represent a detailed status for a repo."""

  def __init__(self, source, commit, status, errors, clusters):
    self.source = source
    self.commit = commit
    self.status = status
    self.clusters = clusters
    self.errors = errors

  def EqualTo(self, result):
    return self.source == result.source and self.commit == result.commit and self.status == result.status


class ManagedResource:
  """ManagedResource represent a managed resource across multiple clusters."""

  def __init__(self, group, kind, namespace, name, status, conditions,
               clusters):
    if not conditions:
      self.conditions = None
    else:
      messages = []
      for condition in conditions:
        messages.append(condition['message'])
      self.conditions = messages
    self.group = group
    self.kind = kind
    self.namespace = namespace
    self.name = name
    self.status = status
    self.clusters = clusters


class DescribeResult:
  """DescribeResult represents the result of the describe command."""

  def __init__(self):
    self.detailed_status = []
    self.managed_resources = []

  def AppendDetailedStatus(self, status):
    for i in range(len(self.detailed_status)):
      s = self.detailed_status[i]
      if s.EqualTo(status):
        s.clusters.append(status.clusters[0])
        self.detailed_status[i] = s
        return
    self.detailed_status.append(status)

  def AppendManagedResources(self, resource, membership, status):
    """append a managed resource to the list."""
    if status.lower() != 'all' and resource['status'].lower() != status.lower():
      return

    for i in range(len(self.managed_resources)):
      r = self.managed_resources[i]
      if r.group == resource['group'] and r.kind == resource[
          'kind'] and r.namespace == resource[
              'namespace'] and r.name == resource[
                  'name'] and r.status == resource['status']:
        r.clusters.append(membership)
        self.managed_resources[i] = r
        return
    conditions = None
    if 'conditions' in resource:
      conditions = resource['conditions']
    mr = ManagedResource(resource['group'], resource['kind'],
                         resource['namespace'], resource['name'],
                         resource['status'], conditions, [membership])
    self.managed_resources.append(mr)


def DescribeRepo(project, name, namespace, source, managed_resources):
  """Describe a repo for the detailed status and managed resources.

  Args:
    project: The project id the repo is from.
    name: The name of the correspoinding RepoSync|RootSync CR.
    namespace: The namespace of the correspoinding RepoSync|RootSync CR.
    source: The source of the repo.
    managed_resources: The status to filter the managed resources for the
      output.

  Returns:
    It returns an instance of DescribeResult

  """
  if name and source or namespace and source:
    raise exceptions.Error(
        '--name and --namespace cannot be specified together with '
        '--source.')
  if name and not namespace or namespace and not name:
    raise exceptions.Error('--name and --namespace must be specified together.')
  if managed_resources not in [
      'all', 'current', 'inprogress', 'notfound', 'failed', 'unknown'
  ]:
    raise exceptions.Error(
        '--managed-resources must be one of all, current, inprogress, notfound, failed or unknown'
    )

  repo_cross_clusters = RawRepos()
  # Get repos from the Config Controller cluster
  clusters = []
  try:
    clusters = utils.ListConfigControllerClusters(project)
  except exceptions.Error as err:
    log.error(err)
  if clusters:
    for cluster in clusters:
      try:
        utils.KubeconfigForCluster(project, cluster[1], cluster[0])
        _AppendReposAndResourceGroups(cluster[0], repo_cross_clusters,
                                      'Config Controller', name, namespace,
                                      source)
      except exceptions.Error as err:
        log.error(err)

  # Get repos from memberships
  try:
    memberships = utils.ListMemberships(project)
  except exceptions.Error as err:
    raise err
  for membership in memberships:
    try:
      utils.KubeconfigForMembership(project, membership)
      _AppendReposAndResourceGroups(membership, repo_cross_clusters,
                                    'Membership', name, namespace, source)
    except exceptions.Error as err:
      log.error(err)
  # Describe the repo
  repo = _Describe(managed_resources, repo_cross_clusters)
  return repo


def _Describe(status_filter, repos_cross_clusters):
  """Describe the repo given the filter for managed resources and KRM resources.

  Args:
    status_filter: The status filter for managed resources.
    repos_cross_clusters: An instance of RawRepos that contains all the relevant
      KRM resources for a repo across multiple clusters.

  Returns:
    It returns an instance of DescribeResult.
  """
  describe_result = DescribeResult()
  for source_key, repos in repos_cross_clusters.GetRepos().items():
    for cluster, pair in repos.items():
      single_repo_status = _GetStatusForRepo(pair.repo)
      status = single_repo_status.GetStatus()
      errors = single_repo_status.GetErrors()
      commit = single_repo_status.GetCommit()
      for resource in pair.rg['status']['resourceStatuses']:
        describe_result.AppendManagedResources(resource, cluster, status_filter)
      status_result = DetailedStatus(source_key, commit, status, errors,
                                     [cluster])
      describe_result.AppendDetailedStatus(status_result)
  return describe_result


class SingleRepoStatus:
  """SingleRepoStatus represents a single repo status on a single cluster."""

  def __init__(self, status, errors, commit):
    self.status = status
    self.errors = errors
    self.commit = commit

  def GetStatus(self):
    return self.status

  def GetErrors(self):
    return self.errors

  def GetCommit(self):
    return self.commit


def _GetStatusForRepo(obj):
  """Get the status for a repo.

  Args:
    obj: The RepoSync|RootSync object.

  Returns:
    a SingleRepoStatus object that represents the RepoSync|RootSync object.
  """
  stalled = _GetConditionForType(obj, 'Stalled')
  if stalled and stalled['status'] == 'True':
    return SingleRepoStatus('STALLED', [stalled['message']], '')
  reconciling = _GetConditionForType(obj, 'Reconciling')
  if reconciling and reconciling['status'] == 'True':
    return SingleRepoStatus('RECONCILING', [], '')
  # When syncing condition is available for
  # Config Sync with version >= 1.10.0
  syncing = _GetConditionForType(obj, 'Syncing')
  if syncing:
    errs = _GetPathValue(syncing, ['errors'], [])
    commit = syncing['commit']
    if errs:
      return SingleRepoStatus('ERROR', _GetErrorMessages(errs), commit)
    if syncing['status'] == 'True':
      return SingleRepoStatus('PENDING', [], commit)
    return SingleRepoStatus('SYNCED', [], commit)
  # When syncing condition is not availalbe for
  # Config Sync with version < 1.10.0
  rendering = _GetPathValue(obj, ['status', 'rendering', 'commit'], '')
  source = _GetPathValue(obj, ['status', 'source', 'commit'], '')
  sync = _GetPathValue(obj, ['status', 'sync', 'commit'], '')
  status = ''
  # The field `.status.rendering` is in 1.9.0+.
  if not rendering:
    errors = []
    if not source and not sync:
      status = 'PENDING'
    elif source != sync:
      errors = _GetPathValue(obj, ['status', 'source', 'errors'], [])
      if errors:
        status = 'ERROR'
      else:
        status = 'PENDING'
    else:
      errors += _GetPathValue(obj, ['status', 'source', 'errors'], [])
      errors += _GetPathValue(obj, ['status', 'sync', 'errors'], [])
      if errors:
        status = 'ERROR'
      else:
        status = 'SYNCED'
    return SingleRepoStatus(status, _GetErrorMessages(errors), source)
  # The following logic applies to Config Sync versions between 1.9.0 and
  # 1.10.0 where .status.rendering status is present but syncing condition
  # is not supported.
  stalled_ts = _GetPathValue(stalled, ['lastUpdateTime'],
                             '2000-01-01T23:50:20Z')
  reconciling_ts = _GetPathValue(reconciling, ['lastUpdateTime'],
                                 '2000-01-01T23:50:20Z')
  rendering_ts = _GetPathValue(obj, ['status', 'rendering', 'lastUpdate'],
                               '2000-01-01T23:50:20Z')
  source_ts = _GetPathValue(obj, ['status', 'source', 'lastUpdate'],
                            '2000-01-01T23:50:20Z')
  sync_ts = _GetPathValue(obj, ['status', 'sync', 'lastUpdate'],
                          '2000-01-01T23:50:20Z')
  stalled_time = _TimeFromString(stalled_ts)
  reconciling_time = _TimeFromString(reconciling_ts)
  rendering_time = _TimeFromString(rendering_ts)
  source_time = _TimeFromString(source_ts)
  sync_time = _TimeFromString(sync_ts)
  if stalled_time > rendering_time and stalled_time > source_time and stalled_time > sync_time or reconciling_time > rendering_time and reconciling_time > source_time and stalled_time > sync_time:
    return SingleRepoStatus('PENDING', [], '')
  if rendering_time > source_time and rendering_time > sync_time:
    errors = _GetPathValue(obj, ['status', 'rendering', 'errors'], [])
    if errors:
      status = 'ERROR'
    else:
      status = 'PENDING'
    return SingleRepoStatus(status, _GetErrorMessages(errors), rendering)
  elif source_time > rendering_time and source_time > sync_time:
    errors = _GetPathValue(obj, ['status', 'source', 'errors'], [])
    if errors:
      status = 'ERROR'
    else:
      status = 'PENDING'
    return SingleRepoStatus(status, _GetErrorMessages(errors), source)
  else:
    errors = _GetPathValue(obj, ['status', 'sync', 'errors'], [])
    if errors:
      status = 'ERROR'
    else:
      status = 'SYNCED'
    return SingleRepoStatus(status, _GetErrorMessages(errors), sync)


def _GetErrorMessages(errors):
  """return the errorMessage list from a list of ConfigSync errors."""
  return_errors = []
  for err in errors:
    return_errors.append(err['errorMessage'])
  return return_errors


def _TimeFromString(timestamp):
  """return the datetime from a timestamp string."""
  return datetime.datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%SZ')


@contextlib.contextmanager
def Timeout(time):
  """set timeout for a python function."""
  # Register a function to raise a TimeoutError on the signal.
  signal.signal(signal.SIGALRM, RaiseTimeout)
  # Schedule the signal to be sent after ``time``
  signal.alarm(time)

  try:
    yield
  except KubectlTimeOutError:
    pass
  finally:
    # Unregister the signal so it won't be triggered
    # if the timeout is not reached.
    signal.signal(signal.SIGALRM, signal.SIG_IGN)


def RaiseTimeout(signum, frame):
  """Raise a timeout error."""
  raise KubectlTimeOutError


class KubectlTimeOutError(Exception):
  pass
