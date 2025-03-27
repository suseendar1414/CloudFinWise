from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.monitor import MonitorManagementClient
from azure.mgmt.containerservice import ContainerServiceClient
from azure.mgmt.web import WebSiteManagementClient
from azure.mgmt.cosmosdb import CosmosDBManagementClient
from azure.mgmt.sql import SqlManagementClient
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
import logging

class AzureScanner:
    def __init__(self):
        self.credential = DefaultAzureCredential()
        self.cache = {}
        self.cache_ttl = timedelta(minutes=15)  # 15 minutes cache TTL
        
    def _get_default_subscription(self) -> str:
        """Get the default subscription ID from Azure."""
        try:
            # Create a resource client without subscription
            resource_client = ResourceManagementClient(self.credential, "")
            # Get the first subscription
            subscriptions = list(resource_client.subscriptions.list())
            if not subscriptions:
                raise Exception("No Azure subscriptions found")
            return subscriptions[0].subscription_id
        except Exception as e:
            logging.error(f"Error getting default subscription: {str(e)}")
            raise
        
    def _init_clients(self, subscription_id: str, services: Set[str]) -> Dict:
        """Initialize Azure clients only for requested services."""
        clients = {
            'resource': ResourceManagementClient(self.credential, subscription_id)
        }
        
        # Only initialize clients for requested services
        service_to_client = {
            'compute': ComputeManagementClient,
            'network': NetworkManagementClient,
            'storage': StorageManagementClient,
            'monitor': MonitorManagementClient,
            'container': ContainerServiceClient,
            'web': WebSiteManagementClient,
            'cosmos': CosmosDBManagementClient,
            'sql': SqlManagementClient
        }
        
        for service in services:
            if service in service_to_client:
                clients[service] = service_to_client[service](self.credential, subscription_id)
                
        return clients
        
    def _get_active_resource_groups(self, resource_client) -> List[str]:
        """Get list of resource groups that have active resources."""
        active_groups = set()
        
        # Get all resources in the subscription
        resources = resource_client.resources.list()
        for resource in resources:
            if resource.type in [
                'Microsoft.Compute/virtualMachines',
                'Microsoft.Web/sites',
                'Microsoft.Storage/storageAccounts',
                'Microsoft.ContainerService/managedClusters',
                'Microsoft.DocumentDB/databaseAccounts',
                'Microsoft.Sql/servers'
            ]:
                active_groups.add(resource.id.split('/')[4])  # Extract resource group name from resource ID
                
        return list(active_groups)
        
    def scan_resource_group(self, resource_group: str, clients: Dict, services: Set[str]) -> Dict:
        """Scan resources in a specific resource group."""
        result = {}
        
        try:
            # Virtual Machines
            if 'compute' in services:
                vms = clients['compute'].virtual_machines.list(resource_group)
                result['virtual_machines'] = [
                    {
                        'name': vm.name,
                        'location': vm.location,
                        'vm_size': vm.hardware_profile.vm_size,
                        'os_type': vm.storage_profile.os_disk.os_type,
                        'resource_group': resource_group,
                        'tags': vm.tags
                    } for vm in vms
                ]
            
            # Virtual Networks
            if 'network' in services:
                vnets = clients['network'].virtual_networks.list(resource_group)
                result['virtual_networks'] = [
                    {
                        'name': vnet.name,
                        'location': vnet.location,
                        'address_space': [addr_space for addr_space in vnet.address_space.address_prefixes],
                        'resource_group': resource_group,
                        'tags': vnet.tags
                    } for vnet in vnets
                ]
                
                # Network Security Groups
                nsgs = clients['network'].network_security_groups.list(resource_group)
                result['network_security_groups'] = [
                    {
                        'name': nsg.name,
                        'location': nsg.location,
                        'resource_group': resource_group,
                        'tags': nsg.tags
                    } for nsg in nsgs
                ]
            
            # Storage Accounts
            if 'storage' in services:
                storage_accounts = clients['storage'].storage_accounts.list_by_resource_group(resource_group)
                result['storage_accounts'] = [
                    {
                        'name': storage.name,
                        'location': storage.location,
                        'sku': storage.sku.name,
                        'kind': storage.kind,
                        'resource_group': resource_group,
                        'tags': storage.tags
                    } for storage in storage_accounts
                ]
            
            # App Services
            if 'web' in services:
                try:
                    web_apps = clients['web'].web_apps.list_by_resource_group(resource_group)
                    result['web_apps'] = [
                        {
                            'name': app.name,
                            'location': app.location,
                            'state': app.state,
                            'resource_group': resource_group,
                            'tags': app.tags
                        } for app in web_apps
                    ]
                except Exception as e:
                    logging.warning(f"Error scanning web apps in {resource_group}: {str(e)}")
                    result['web_apps'] = []
            
            # AKS Clusters
            if 'container' in services:
                try:
                    clusters = clients['container'].managed_clusters.list_by_resource_group(resource_group)
                    result['aks_clusters'] = [
                        {
                            'name': cluster.name,
                            'location': cluster.location,
                            'kubernetes_version': cluster.kubernetes_version,
                            'resource_group': resource_group,
                            'tags': cluster.tags
                        } for cluster in clusters
                    ]
                except Exception as e:
                    logging.warning(f"Error scanning AKS clusters in {resource_group}: {str(e)}")
                    result['aks_clusters'] = []
            
            # Cosmos DB
            if 'cosmos' in services:
                try:
                    accounts = clients['cosmos'].database_accounts.list_by_resource_group(resource_group)
                    result['cosmos_db'] = [
                        {
                            'name': account.name,
                            'location': account.location,
                            'kind': account.kind,
                            'resource_group': resource_group,
                            'tags': account.tags
                        } for account in accounts
                    ]
                except Exception as e:
                    logging.warning(f"Error scanning Cosmos DB in {resource_group}: {str(e)}")
                    result['cosmos_db'] = []
            
            # SQL Databases
            if 'sql' in services:
                try:
                    servers = clients['sql'].servers.list_by_resource_group(resource_group)
                    result['sql_servers'] = []
                    for server in servers:
                        databases = clients['sql'].databases.list_by_server(resource_group, server.name)
                        result['sql_servers'].append({
                            'name': server.name,
                            'location': server.location,
                            'version': server.version,
                            'resource_group': resource_group,
                            'databases': [
                                {
                                    'name': db.name,
                                    'status': db.status,
                                    'max_size_bytes': db.max_size_bytes
                                } for db in databases
                            ],
                            'tags': server.tags
                        })
                except Exception as e:
                    logging.warning(f"Error scanning SQL servers in {resource_group}: {str(e)}")
                    result['sql_servers'] = []
                    
        except Exception as e:
            logging.error(f"Error scanning resource group {resource_group}: {str(e)}")
            
        return result
        
    def scan_resources(self, subscription_id: Optional[str] = None, services: Optional[List[str]] = None) -> Dict:
        """Scan all Azure resources in the subscription.
        Args:
            subscription_id: Optional Azure subscription ID. If not provided, uses default subscription.
            services: Optional list of services to scan. If not provided, scans all supported services.
        Returns:
            Dict containing scanned resources.
        """
        """Scan all Azure resources in the subscription."""
        # Get default subscription if none provided
        if subscription_id is None:
            subscription_id = self._get_default_subscription()
            logging.info(f"Using default subscription: {subscription_id}")

        # Use cache if available and not expired
        cache_key = f"{subscription_id}-{','.join(sorted(services or []))}"
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < self.cache_ttl:
                return cached_data
                
        # Convert services to set and add dependencies
        services_set = set(services or [
            'compute',    # Virtual Machines
            'storage',    # Storage Accounts
            'web',        # App Services
            'container',  # AKS Clusters
            'cosmos',     # Cosmos DB
            'sql'         # SQL Databases
        ])
        
        # Add network service if compute is requested (for NSGs)
        if 'compute' in services_set:
            services_set.add('network')
                
        infrastructure_data = {
            'virtual_machines': [],
            'virtual_networks': [],
            'network_security_groups': [],
            'storage_accounts': [],
            'web_apps': [],
            'aks_clusters': [],
            'cosmos_db': [],
            'sql_servers': [],
            'resource_groups': []
        }
        
        try:
            # Initialize only needed clients
            clients = self._init_clients(subscription_id, services_set)
            
            # Get only active resource groups
            resource_groups = self._get_active_resource_groups(clients['resource'])
            
            # Store active resource group info
            for rg_name in resource_groups:
                rg = clients['resource'].resource_groups.get(rg_name)
                infrastructure_data['resource_groups'].append({
                    'name': rg.name,
                    'location': rg.location,
                    'tags': rg.tags
                })
            
            # Scan resource groups in parallel
            with ThreadPoolExecutor(max_workers=min(len(resource_groups), 10)) as executor:
                future_to_rg = {executor.submit(self.scan_resource_group, rg, clients, services_set): rg 
                               for rg in resource_groups}
                
                # Process completed futures
                for future in as_completed(future_to_rg):
                    rg = future_to_rg[future]
                    try:
                        result = future.result()
                        for service_type, resources in result.items():
                            if service_type in infrastructure_data:
                                infrastructure_data[service_type].extend(resources)
                    except Exception as e:
                        logging.error(f"Error processing results from resource group {rg}: {str(e)}")


                    
        except Exception as e:
            logging.error(f"Error during Azure resource scanning: {str(e)}")
            
        # Cache the results
        self.cache[cache_key] = (infrastructure_data, datetime.now())
        return infrastructure_data
