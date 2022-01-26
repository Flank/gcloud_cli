# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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
"""Code that's shared between multiple backend-services subcommands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding

from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


class CacheKeyQueryStringException(core_exceptions.Error):

  def __init__(self):
    super(CacheKeyQueryStringException, self).__init__(
        'cache-key-query-string-whitelist and '
        'cache-key-query-string-blacklist may only be set when '
        'cache-key-include-query-string is enabled.')


# TODO(b/35086027) - Remove this
def IsDefaultRegionalBackendServicePropertyNoneWarnOtherwise():
  """Warns if core/default_regional_backend_service property is set."""
  default_regional = (
      properties.VALUES.core.default_regional_backend_service.GetBool())
  if default_regional is not None:
    # Print a warning if it is set.
    log.warning(
        'core/default_regional_backend_service property is deprecated and '
        'has no meaning.')


# TODO(b/35086027) - Remove this
def GetDefaultScope():
  """Gets the default compute flags scope enum value."""
  IsDefaultRegionalBackendServicePropertyNoneWarnOtherwise()
  return None


def GetIAP(iap_arg, messages, existing_iap_settings=None):
  """Returns IAP settings from arguments."""

  # --iap is specified as str in flags.py.  We do that and then re-parse
  # here instead of just setting the flag to ArgDict in the first place
  # to fix the autogenerated help text.  TODO(b/34479878): Clean this up.
  subargs = iap_arg.split(',')
  iap_arg_parsed = {}
  for subarg in subargs:
    if not subarg:
      continue

    if '=' in subarg:
      subarg, value = subarg.split('=', 1)
    else:
      value = True

    def _Repr(s):
      r = repr(s)
      if r.startswith('u'):
        r = r[1:]
      return r

    if subarg in ('enabled', 'disabled', 'oauth2-client-id',
                  'oauth2-client-secret'):
      if subarg in iap_arg_parsed:
        raise exceptions.InvalidArgumentException(
            '--iap', 'Sub-argument %s specified multiple times' % _Repr(subarg))
      iap_arg_parsed[subarg] = value
    else:
      raise exceptions.InvalidArgumentException(
          '--iap', 'Invalid sub-argument %s' % _Repr(subarg))

  if not iap_arg_parsed or not iap_arg:
    raise exceptions.InvalidArgumentException(
        '--iap', 'Must provide value when specifying --iap')

  if 'enabled' in iap_arg_parsed and 'disabled' in iap_arg_parsed:
    raise exceptions.InvalidArgumentException(
        '--iap', 'Must specify only one of [enabled] or [disabled]')

  iap_settings = messages.BackendServiceIAP()
  if 'enabled' in iap_arg_parsed:
    iap_settings.enabled = True
  elif 'disabled' in iap_arg_parsed:
    iap_settings.enabled = False
  elif existing_iap_settings is None:
    iap_settings.enabled = False
  else:
    iap_settings.enabled = existing_iap_settings.enabled

  if ('oauth2-client-id' in iap_arg_parsed or
      'oauth2-client-secret' in iap_arg_parsed):
    iap_settings.oauth2ClientId = iap_arg_parsed.get('oauth2-client-id')
    iap_settings.oauth2ClientSecret = iap_arg_parsed.get('oauth2-client-secret')
    # If either oauth2-client-id or oauth2-client-secret is specified,
    # then the other should also be specified.
    if not iap_settings.oauth2ClientId or not iap_settings.oauth2ClientSecret:
      raise exceptions.InvalidArgumentException(
          '--iap', 'Both [oauth2-client-id] and [oauth2-client-secret] must be '
          'specified together')

  return iap_settings


def IapBestPracticesNotice():
  return ('IAP only protects requests that go through the Cloud Load Balancer. '
          'See the IAP documentation for important security best practices: '
          'https://cloud.google.com/iap/')


def IapHttpWarning():
  return ('IAP has been enabled for a backend service that does not use HTTPS. '
          'Data sent from the Load Balancer to your VM will not be encrypted.')


def _ValidateGroupMatchesArgs(args):
  """Validate if the group arg is used with the correct group specific flags."""
  invalid_arg = None
  if args.instance_group:
    if args.max_rate_per_endpoint is not None:
      invalid_arg = '--max-rate-per-endpoint'
    elif args.max_connections_per_endpoint is not None:
      invalid_arg = '--max-connections-per-endpoint'
    if invalid_arg is not None:
      raise exceptions.InvalidArgumentException(
          invalid_arg, 'cannot be set with --instance-group')
  elif args.network_endpoint_group:
    if args.max_rate_per_instance is not None:
      invalid_arg = '--max-rate-per-instance'
    elif args.max_connections_per_instance is not None:
      invalid_arg = '--max-connections-per-instance'
    if invalid_arg is not None:
      raise exceptions.InvalidArgumentException(
          invalid_arg, 'cannot be set with --network-endpoint-group')


def ValidateBalancingModeArgs(messages,
                              add_or_update_backend_args,
                              current_balancing_mode=None):
  """Check whether the setup of the backend LB related fields is valid.

  Args:
    messages: API messages class, determined by release track.
    add_or_update_backend_args: argparse Namespace. The arguments provided to
      add-backend or update-backend commands.
    current_balancing_mode: BalancingModeValueValuesEnum. The balancing mode of
      the existing backend, in case of update-backend command. Must be None
      otherwise.
  """
  balancing_mode_enum = messages.Backend.BalancingModeValueValuesEnum
  balancing_mode = current_balancing_mode
  if add_or_update_backend_args.balancing_mode:
    balancing_mode = balancing_mode_enum(
        add_or_update_backend_args.balancing_mode)

  _ValidateGroupMatchesArgs(add_or_update_backend_args)

  invalid_arg = None
  if balancing_mode == balancing_mode_enum.RATE:
    if add_or_update_backend_args.max_utilization is not None:
      invalid_arg = '--max-utilization'
    elif add_or_update_backend_args.max_connections is not None:
      invalid_arg = '--max-connections'
    elif add_or_update_backend_args.max_connections_per_instance is not None:
      invalid_arg = '--max-connections-per-instance'
    elif add_or_update_backend_args.max_connections_per_endpoint is not None:
      invalid_arg = '--max-connections-per-endpoint'

    if invalid_arg is not None:
      raise exceptions.InvalidArgumentException(
          invalid_arg, 'cannot be set with RATE balancing mode')
  elif balancing_mode == balancing_mode_enum.CONNECTION:
    if add_or_update_backend_args.max_utilization is not None:
      invalid_arg = '--max-utilization'
    elif add_or_update_backend_args.max_rate is not None:
      invalid_arg = '--max-rate'
    elif add_or_update_backend_args.max_rate_per_instance is not None:
      invalid_arg = '--max-rate-per-instance'
    elif add_or_update_backend_args.max_rate_per_endpoint is not None:
      invalid_arg = '--max-rate-per-endpoint'

    if invalid_arg is not None:
      raise exceptions.InvalidArgumentException(
          invalid_arg, 'cannot be set with CONNECTION balancing mode')
  elif balancing_mode == balancing_mode_enum.UTILIZATION:
    if add_or_update_backend_args.network_endpoint_group is not None:
      raise exceptions.InvalidArgumentException(
          '--network-endpoint-group',
          'cannot be set with UTILIZATION balancing mode')


def UpdateCacheKeyPolicy(args, cache_key_policy):
  """Sets the cache_key_policy according to the command line arguments.

  Args:
    args: Arguments specified through command line.
    cache_key_policy: new CacheKeyPolicy to be set (or preexisting one if using
      update).
  """
  if args.cache_key_include_protocol is not None:
    cache_key_policy.includeProtocol = args.cache_key_include_protocol
  if args.cache_key_include_host is not None:
    cache_key_policy.includeHost = args.cache_key_include_host
  if args.cache_key_include_query_string is not None:
    cache_key_policy.includeQueryString = args.cache_key_include_query_string
    if not args.cache_key_include_query_string:
      cache_key_policy.queryStringWhitelist = []
      cache_key_policy.queryStringBlacklist = []
  if args.cache_key_query_string_whitelist is not None:
    (cache_key_policy.queryStringWhitelist
    ) = args.cache_key_query_string_whitelist
    cache_key_policy.includeQueryString = True
    cache_key_policy.queryStringBlacklist = []
  if args.cache_key_query_string_blacklist is not None:
    (cache_key_policy.queryStringBlacklist
    ) = args.cache_key_query_string_blacklist
    cache_key_policy.includeQueryString = True
    cache_key_policy.queryStringWhitelist = []
  if args.cache_key_include_http_header is not None:
    cache_key_policy.includeHttpHeaders = args.cache_key_include_http_header
  if args.cache_key_include_named_cookie is not None:
    cache_key_policy.includeNamedCookies = args.cache_key_include_named_cookie


def ValidateCacheKeyPolicyArgs(cache_key_policy_args):
  # If includeQueryString is not set, it should default to True
  include_query_string = (
      cache_key_policy_args.cache_key_include_query_string is None or
      cache_key_policy_args.cache_key_include_query_string)
  if not include_query_string:
    if (cache_key_policy_args.cache_key_query_string_whitelist is not None or
        cache_key_policy_args.cache_key_query_string_blacklist is not None):
      raise CacheKeyQueryStringException()


def HasCacheKeyPolicyArgsForCreate(args):
  """Returns true if create request requires a CacheKeyPolicy message.

  Args:
    args: The arguments passed to the gcloud command.

  Returns:
    True if there are cache key policy related arguments which require adding
    a CacheKeyPolicy message in the create request.
  """
  # When doing create cache_key_include_host, cache_key_include_protocol,
  # and cache_key_include_query_string have defaults in the API set to True.
  # So only if the user specifies False for any of these or if the user has
  # specified cache_key_query_string_whitelist,
  # cache_key_query_string_blacklist we need to add a CacheKeyPolicy message
  # in the request.
  return (not args.cache_key_include_host or
          not args.cache_key_include_protocol or
          not args.cache_key_include_query_string or
          args.IsSpecified('cache_key_query_string_whitelist') or
          args.IsSpecified('cache_key_query_string_blacklist') or
          args.IsSpecified('cache_key_include_http_header') or
          args.IsSpecified('cache_key_include_named_cookie'))


def HasSubsettingArgs(args):
  """Returns true if request requires a Subsetting message.

  Args:
    args: The arguments passed to the gcloud command.

  Returns:
    True if request requires a Subsetting message.
  """
  return args.IsSpecified('subsetting_policy')


def HasSubsettingSubsetSizeArgs(args):
  """Returns true if request requires a Subsetting.subset_size field.

  Args:
    args: The arguments passed to the gcloud command.

  Returns:
    True if request requires a Subsetting.subset_size field.
  """
  return args.IsSpecified('subsetting_subset_size')


def HasCacheKeyPolicyArgsForUpdate(args):
  """Returns true if update request requires a CacheKeyPolicy message.

  Args:
    args: The arguments passed to the gcloud command.

  Returns:
    True if there are cache key policy related arguments which require adding
    a CacheKeyPolicy message in the update request.
  """
  # When doing update, if any of the cache key related fields have been
  # specified by the user in the command line, we need to add a
  # CacheKeyPolicy message in the request.
  return (args.IsSpecified('cache_key_include_protocol') or
          args.IsSpecified('cache_key_include_host') or
          args.IsSpecified('cache_key_include_query_string') or
          args.IsSpecified('cache_key_query_string_whitelist') or
          args.IsSpecified('cache_key_query_string_blacklist') or
          args.IsSpecified('cache_key_include_http_header') or
          args.IsSpecified('cache_key_include_named_cookie'))


def GetCacheKeyPolicy(client, args, backend_service):
  """Validates and returns the cache key policy.

  Args:
    client: The client used by gcloud.
    args: The arguments passed to the gcloud command.
    backend_service: The backend service object. If the backend service object
      contains a cache key policy already, it is used as the base to apply
      changes based on args.

  Returns:
    The cache key policy.
  """
  cache_key_policy = client.messages.CacheKeyPolicy()
  if (backend_service.cdnPolicy is not None and
      backend_service.cdnPolicy.cacheKeyPolicy is not None):
    cache_key_policy = backend_service.cdnPolicy.cacheKeyPolicy

  ValidateCacheKeyPolicyArgs(args)
  UpdateCacheKeyPolicy(args, cache_key_policy)
  return cache_key_policy


def ApplySubsettingArgs(client, args, backend_service, use_subset_size):
  """Applies the Subsetting argument(s) to the specified backend service.

  Args:
    client: The client used by gcloud.
    args: The arguments passed to the gcloud command.
    backend_service: The backend service object.
    use_subset_size: Should Subsetting.subset_size be used?
  """
  subsetting_args = {}
  add_subsetting = HasSubsettingArgs(args)
  if add_subsetting:
    subsetting_args[
        'policy'] = client.messages.Subsetting.PolicyValueValuesEnum(
            args.subsetting_policy)
    if use_subset_size and HasSubsettingSubsetSizeArgs(args):
      subsetting_args['subsetSize'] = args.subsetting_subset_size
  if subsetting_args:
    backend_service.subsetting = client.messages.Subsetting(**subsetting_args)


def GetNegativeCachingPolicy(client, args, backend_service):
  """Returns the negative caching policy.

  Args:
    client: The client used by gcloud.
    args: The arguments passed to the gcloud command.
    backend_service: The backend service object. If the backend service object
      contains a negative caching policy already, it is used as the base to
      apply changes based on args.

  Returns:
    The negative caching policy.
  """
  negative_caching_policy = None
  if args.negative_caching_policy:
    negative_caching_policy = []
    for code, ttl in args.negative_caching_policy.items():
      negative_caching_policy.append(
          client.messages.BackendServiceCdnPolicyNegativeCachingPolicy(
              code=code, ttl=ttl))
  else:
    if (backend_service.cdnPolicy is not None and
        backend_service.cdnPolicy.negativeCachingPolicy is not None):
      negative_caching_policy = backend_service.cdnPolicy.negativeCachingPolicy

  return negative_caching_policy


def GetBypassCacheOnRequestHeaders(client, args):
  """Returns bypass cache on request headers.

  Args:
    client: The client used by gcloud.
    args: The arguments passed to the gcloud command.

  Returns:
    The bypass cache on request headers.
  """
  bypass_cache_on_request_headers = None
  if args.bypass_cache_on_request_headers:
    bypass_cache_on_request_headers = []
    for header in args.bypass_cache_on_request_headers:
      bypass_cache_on_request_headers.append(
          client.messages.BackendServiceCdnPolicyBypassCacheOnRequestHeader(
              headerName=header))

  return bypass_cache_on_request_headers


def ApplyConnectionTrackingPolicyArgs(client, args, backend_service,
                                      support_strong_session_affinity):
  """Applies the connection tracking policy arguments to the specified backend service.

  If there are no arguments related to connection tracking policy, the backend
  service remains unmodified.

  Args:
    client: The client used by gcloud.
    args: The arguments passed to the gcloud command.
    backend_service: The backend service object.
    support_strong_session_affinity: If True, then support
      enable_strong_affinity.
  """
  if backend_service.connectionTrackingPolicy is not None:
    connection_tracking_policy = encoding.CopyProtoMessage(
        backend_service.connectionTrackingPolicy)
  else:
    connection_tracking_policy = (
        client.messages.BackendServiceConnectionTrackingPolicy())

  if args.connection_persistence_on_unhealthy_backends:
    connection_tracking_policy.connectionPersistenceOnUnhealthyBackends = (
        client.messages.BackendServiceConnectionTrackingPolicy
        .ConnectionPersistenceOnUnhealthyBackendsValueValuesEnum(
            args.connection_persistence_on_unhealthy_backends))

  if args.tracking_mode:
    connection_tracking_policy.trackingMode = (
        client.messages.BackendServiceConnectionTrackingPolicy
        .TrackingModeValueValuesEnum(args.tracking_mode))

  if args.idle_timeout_sec:
    connection_tracking_policy.idleTimeoutSec = args.idle_timeout_sec

  if support_strong_session_affinity:
    if args.enable_strong_affinity:
      connection_tracking_policy.enableStrongAffinity = (
          args.enable_strong_affinity)

  if connection_tracking_policy != (
      client.messages.BackendServiceConnectionTrackingPolicy()):
    backend_service.connectionTrackingPolicy = connection_tracking_policy


def ApplyCdnPolicyArgs(client,
                       args,
                       backend_service,
                       is_update=False,
                       apply_signed_url_cache_max_age=False,
                       cleared_fields=None):
  """Applies the CdnPolicy arguments to the specified backend service.

  If there are no arguments related to CdnPolicy, the backend service remains
  unmodified.

  Args:
    client: The client used by gcloud.
    args: The arguments passed to the gcloud command.
    backend_service: The backend service object.
    is_update: True if this is called on behalf of an update command instead of
      a create command, False otherwise.
    apply_signed_url_cache_max_age: If True, also adds the
      signedUrlCacheMaxAgeSec parameter to the CdnPolicy if present in the input
      arguments.
    cleared_fields: Reference to list with fields that should be cleared. Valid
      only for update command.
  """
  if backend_service.cdnPolicy is not None:
    cdn_policy = encoding.CopyProtoMessage(backend_service.cdnPolicy)
  else:
    cdn_policy = client.messages.BackendServiceCdnPolicy()

  if is_update:
    add_cache_key_policy = HasCacheKeyPolicyArgsForUpdate(args)
  else:
    add_cache_key_policy = HasCacheKeyPolicyArgsForCreate(args)

  if add_cache_key_policy:
    cdn_policy.cacheKeyPolicy = GetCacheKeyPolicy(client, args, backend_service)
  if apply_signed_url_cache_max_age and args.IsSpecified(
      'signed_url_cache_max_age'):
    cdn_policy.signedUrlCacheMaxAgeSec = args.signed_url_cache_max_age

  if args.request_coalescing is not None:
    cdn_policy.requestCoalescing = args.request_coalescing

  if args.cache_mode:
    cdn_policy.cacheMode = client.messages.BackendServiceCdnPolicy.\
      CacheModeValueValuesEnum(args.cache_mode)
  if args.client_ttl is not None:
    cdn_policy.clientTtl = args.client_ttl
  if args.default_ttl is not None:
    cdn_policy.defaultTtl = args.default_ttl
  if args.max_ttl is not None:
    cdn_policy.maxTtl = args.max_ttl

  if is_update:
    # Takes care of resetting fields that are invalid for given cache modes.
    should_clean_client_ttl = args.cache_mode == 'USE_ORIGIN_HEADERS' and \
                              args.client_ttl is None
    if args.no_client_ttl or should_clean_client_ttl:
      cleared_fields.append('cdnPolicy.clientTtl')
      cdn_policy.clientTtl = None

    should_clean_default_ttl = args.cache_mode == 'USE_ORIGIN_HEADERS' and \
                               args.default_ttl is None
    if args.no_default_ttl or should_clean_default_ttl:
      cleared_fields.append('cdnPolicy.defaultTtl')
      cdn_policy.defaultTtl = None

    should_clean_max_ttl = (args.cache_mode == 'USE_ORIGIN_HEADERS' or \
               args.cache_mode == 'FORCE_CACHE_ALL') and args.max_ttl is None
    if args.no_max_ttl or should_clean_max_ttl:
      cleared_fields.append('cdnPolicy.maxTtl')
      cdn_policy.maxTtl = None

  if args.negative_caching is not None:
    cdn_policy.negativeCaching = args.negative_caching
  negative_caching_policy = GetNegativeCachingPolicy(client, args,
                                                     backend_service)
  if negative_caching_policy is not None:
    cdn_policy.negativeCachingPolicy = negative_caching_policy
  if args.negative_caching_policy and not cdn_policy.negativeCaching:
    # TODO (b/209813007): Replace implicit config change with warning that
    # negative caching is disabled and a prompt to enable it with
    # --negative-caching
    log.warning(
        'Setting a negative cache policy also enabled negative caching. If ' +
        'this was not intended, disable negative caching with ' +
        '`--no-negative-caching`.')
    cdn_policy.negativeCaching = True

  if is_update:
    if args.no_negative_caching_policies or \
        (args.negative_caching is not None and not args.negative_caching):
      cleared_fields.append('cdnPolicy.negativeCachingPolicy')
      cdn_policy.negativeCachingPolicy = []

  if args.serve_while_stale is not None:
    cdn_policy.serveWhileStale = args.serve_while_stale

  bypass_cache_on_request_headers = GetBypassCacheOnRequestHeaders(client, args)
  if bypass_cache_on_request_headers is not None:
    cdn_policy.bypassCacheOnRequestHeaders = bypass_cache_on_request_headers

  if is_update:
    if args.no_serve_while_stale:
      cleared_fields.append('cdnPolicy.serveWhileStale')
      cdn_policy.serveWhileStale = None
    if args.no_bypass_cache_on_request_headers:
      cleared_fields.append('cdnPolicy.bypassCacheOnRequestHeaders')
      cdn_policy.bypassCacheOnRequestHeaders = []

  if cdn_policy != client.messages.BackendServiceCdnPolicy():
    backend_service.cdnPolicy = cdn_policy


def ApplyFailoverPolicyArgs(messages, args, backend_service, support_failover):
  """Applies the FailoverPolicy arguments to the specified backend service.

  If there are no arguments related to FailoverPolicy, the backend service
  remains unmodified.

  Args:
    messages: The available API proto messages.
    args: The arguments passed to the gcloud command.
    backend_service: The backend service proto message object.
    support_failover: Failover functionality is supported.
  """
  if ((support_failover and (args.IsSpecified('connection_drain_on_failover') or
                             args.IsSpecified('drop_traffic_if_unhealthy'))) and
      backend_service.loadBalancingScheme
      == messages.BackendService.LoadBalancingSchemeValueValuesEnum.EXTERNAL):
    raise exceptions.InvalidArgumentException(
        '--load-balancing-scheme',
        'can only specify --connection-drain-on-failover or '
        '--drop-traffic-if-unhealthy if the load balancing scheme is INTERNAL.')
  if ((support_failover and args.IsSpecified('connection_drain_on_failover'))
      and backend_service.protocol !=
      messages.BackendService.ProtocolValueValuesEnum.TCP):
    raise exceptions.InvalidArgumentException(
        '--protocol', 'can only specify --connection-drain-on-failover '
        'if the protocol is TCP.')

  if (support_failover and (args.IsSpecified('connection_drain_on_failover') or
                            args.IsSpecified('drop_traffic_if_unhealthy') or
                            args.IsSpecified('failover_ratio'))):
    failover_policy = (
        backend_service.failoverPolicy if backend_service.failoverPolicy else
        messages.BackendServiceFailoverPolicy())
    if args.connection_drain_on_failover is not None:
      failover_policy.disableConnectionDrainOnFailover = (
          not args.connection_drain_on_failover)
    if args.drop_traffic_if_unhealthy is not None:
      failover_policy.dropTrafficIfUnhealthy = args.drop_traffic_if_unhealthy
    if args.failover_ratio is not None:
      failover_policy.failoverRatio = args.failover_ratio
    backend_service.failoverPolicy = failover_policy


def ApplyLogConfigArgs(messages, args, backend_service, support_logging):
  """Applies the LogConfig arguments to the specified backend service.

  If there are no arguments related to LogConfig, the backend service
  remains unmodified.

  Args:
    messages: The available API proto messages.
    args: The arguments passed to the gcloud command.
    backend_service: The backend service proto message object.
    support_logging: Support logging functionality.
  """
  logging_specified = (
      support_logging and (args.IsSpecified('enable_logging') or
                           args.IsSpecified('logging_sample_rate')))
  if (logging_specified and backend_service.protocol !=
      messages.BackendService.ProtocolValueValuesEnum.HTTP and
      backend_service.protocol !=
      messages.BackendService.ProtocolValueValuesEnum.HTTPS and
      backend_service.protocol !=
      messages.BackendService.ProtocolValueValuesEnum.HTTP2):
    raise exceptions.InvalidArgumentException(
        '--protocol',
        'can only specify --enable-logging or --logging-sample-rate if the '
        'protocol is HTTP/HTTPS/HTTP2.')

  if logging_specified:
    if backend_service.logConfig:
      log_config = backend_service.logConfig
    else:
      log_config = messages.BackendServiceLogConfig()
    if args.enable_logging is not None:
      log_config.enable = args.enable_logging
    if args.logging_sample_rate is not None:
      log_config.sampleRate = args.logging_sample_rate
    backend_service.logConfig = log_config


def SendGetRequest(client, backend_service_ref):
  """Send Backend Services get request."""
  if backend_service_ref.Collection() == 'compute.regionBackendServices':
    return client.apitools_client.regionBackendServices.Get(
        client.messages.ComputeRegionBackendServicesGetRequest(
            **backend_service_ref.AsDict()))
  return client.apitools_client.backendServices.Get(
      client.messages.ComputeBackendServicesGetRequest(
          **backend_service_ref.AsDict()))


def WaitForOperation(resources, service, operation, backend_service_ref,
                     message):
  """Waits for the backend service operation to finish.

  Args:
    resources: The resource parser.
    service: apitools.base.py.base_api.BaseApiService, the service representing
      the target of the operation.
    operation: The operation to wait for.
    backend_service_ref: The backend service reference.
    message: The message to show.

  Returns:
    The operation result.
  """
  params = {'project': backend_service_ref.project}
  if backend_service_ref.Collection() == 'compute.regionBackendServices':
    collection = 'compute.regionOperations'
    params['region'] = backend_service_ref.region
  else:
    collection = 'compute.globalOperations'
  operation_ref = resources.Parse(
      operation.name, params=params, collection=collection)
  operation_poller = poller.Poller(service, backend_service_ref)
  return waiter.WaitFor(operation_poller, operation_ref, message)
