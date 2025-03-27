import boto3
from typing import Dict, List, Optional, Set
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

class AWSScanner:
    def __init__(self):
        self.session = boto3.Session()
        self.regions = self._get_available_regions()
        self.cache = {}
        self.cache_ttl = timedelta(minutes=15)  # 15 minutes cache TTL
        
    def _get_available_regions(self) -> List[str]:
        """Get list of all available AWS regions."""
        ec2 = boto3.client('ec2')
        return [region['RegionName'] for region in ec2.describe_regions()['Regions']]
    
    def scan_region(self, region: str, services: Set[str]) -> Dict:
        """Scan specific services in a single region."""
        result = {}
        
        # Initialize AWS clients
        clients = {}
        try:
            clients = {
                'ec2': boto3.client('ec2', region_name=region),
                'rds': boto3.client('rds', region_name=region),
                'cloudwatch': boto3.client('cloudwatch', region_name=region),
                'logs': boto3.client('logs', region_name=region),
                'lambda': boto3.client('lambda', region_name=region),
                'iam': boto3.client('iam', region_name=region),
                'dynamodb': boto3.client('dynamodb', region_name=region),
                'elasticache': boto3.client('elasticache', region_name=region),
                'elb': boto3.client('elbv2', region_name=region),
                'eks': boto3.client('eks', region_name=region)
            }
        except Exception as e:
            logging.error(f"Error initializing AWS clients in region {region}: {str(e)}")
            return result
        try:
            # EC2 Resources
            if 'ec2' in services:
                instances = clients['ec2'].describe_instances()
                result['ec2_instances'] = [
                    {
                        'instance_id': instance['InstanceId'],
                        'instance_type': instance['InstanceType'],
                        'state': instance['State']['Name'],
                        'region': region,
                        'tags': instance.get('Tags', [])
                    }
                    for reservation in instances['Reservations']
                    for instance in reservation['Instances']
                ]
                
                # VPCs and Subnets
                vpcs = clients['ec2'].describe_vpcs()
                result['vpcs'] = [
                    {
                        'vpc_id': vpc['VpcId'],
                        'cidr_block': vpc['CidrBlock'],
                        'region': region,
                        'tags': vpc.get('Tags', [])
                    }
                    for vpc in vpcs['Vpcs']
                ]
                
                # Security Groups
                security_groups = clients['ec2'].describe_security_groups()
                result['security_groups'] = [
                    {
                        'group_id': sg['GroupId'],
                        'group_name': sg['GroupName'],
                        'description': sg['Description'],
                        'vpc_id': sg.get('VpcId'),
                        'region': region
                    }
                    for sg in security_groups['SecurityGroups']
                ]

            # Load Balancers
            if 'elb' in services:
                try:
                    lbs = clients['elb'].describe_load_balancers()
                    result['load_balancers'] = [
                        {
                            'arn': lb['LoadBalancerArn'],
                            'name': lb['LoadBalancerName'],
                            'type': lb['Type'],
                            'state': lb['State']['Code'],
                            'dns_name': lb['DNSName'],
                            'region': region
                        }
                        for lb in lbs['LoadBalancers']
                    ]
                except Exception as e:
                    logging.warning(f"Error scanning ELB in region {region}: {str(e)}")
                    result['load_balancers'] = []

            # EKS Clusters
            if 'eks' in services:
                try:
                    clusters = clients['eks'].list_clusters()
                    result['eks_clusters'] = [
                        {
                            'name': cluster_name,
                            'region': region
                        }
                        for cluster_name in clusters['clusters']
                    ]
                except Exception as e:
                    logging.warning(f"Error scanning EKS in region {region}: {str(e)}")
                    result['eks_clusters'] = []

            # DynamoDB Tables
            if 'dynamodb' in services:
                try:
                    tables = clients['dynamodb'].list_tables()
                    result['dynamodb_tables'] = [
                        {
                            'name': table_name,
                            'region': region
                        }
                        for table_name in tables['TableNames']
                    ]
                except Exception as e:
                    logging.warning(f"Error scanning DynamoDB in region {region}: {str(e)}")
                    result['dynamodb_tables'] = []

            # ElastiCache Clusters
            if 'elasticache' in services:
                try:
                    clusters = clients['elasticache'].describe_cache_clusters()
                    result['elasticache_clusters'] = [
                        {
                            'cluster_id': cluster['CacheClusterId'],
                            'engine': cluster['Engine'],
                            'status': cluster['CacheClusterStatus'],
                            'region': region
                        }
                        for cluster in clusters['CacheClusters']
                    ]
                except Exception as e:
                    logging.warning(f"Error scanning ElastiCache in region {region}: {str(e)}")
                    result['elasticache_clusters'] = []

            if 'logs' in services:
                logs = boto3.client('logs', region_name=region)
                log_groups = logs.describe_log_groups()
                result['cloudwatch_logs'] = [
                    {
                        'name': group['logGroupName'],
                        'retention_days': group.get('retentionInDays'),
                        'stored_bytes': group.get('storedBytes'),
                        'region': region
                    }
                    for group in log_groups['logGroups']
                ]

            if 'rds' in services:
                rds = boto3.client('rds', region_name=region)
                db_instances = rds.describe_db_instances()
                result['rds_instances'] = [
                    {
                        'db_identifier': db['DBInstanceIdentifier'],
                        'engine': db['Engine'],
                        'status': db['DBInstanceStatus'],
                        'region': region
                    }
                    for db in db_instances['DBInstances']
                ]

            if 'lambda' in services:
                lambda_client = boto3.client('lambda', region_name=region)
                functions = lambda_client.list_functions()
                result['lambda_functions'] = [
                    {
                        'function_name': func['FunctionName'],
                        'runtime': func['Runtime'],
                        'region': region
                    }
                    for func in functions['Functions']
                ]

        except Exception as e:
            logging.error(f"Error scanning region {region}: {str(e)}")
            
        return result

    def scan_resources(self, services: Optional[List[str]] = None) -> Dict:
        """Scan all AWS resources across regions."""
        # Use cache if available and not expired
        cache_key = f"all_regions-{','.join(sorted(services or []))}"
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < self.cache_ttl:
                return cached_data

        infrastructure_data = {
            'ec2_instances': [],
            'vpcs': [],
            's3_buckets': [],
            'rds_instances': [],
            'lambda_functions': [],
            'cloudwatch_metrics': [],
            'cloudwatch_alarms': [],
            'cloudwatch_logs': []
        }
        
        # Convert services to set for faster lookup
        services_set = set(services or [
            'ec2',        # EC2 instances, VPCs, Security Groups
            'rds',        # RDS databases
            'lambda',     # Lambda functions
            'dynamodb',   # DynamoDB tables
            'elasticache',# ElastiCache clusters
            'elb',       # Load balancers
            'eks'        # Kubernetes clusters
        ])
        
        try:
            if 's3' in services_set:
                # Scan S3 (Global service)
                s3_client = boto3.client('s3')
                buckets = s3_client.list_buckets()['Buckets']
                infrastructure_data['s3_buckets'] = [
                    {
                        'name': bucket['Name'],
                        'creation_date': bucket['CreationDate'].isoformat()
                    }
                    for bucket in buckets
                ]
            
            # Scan regional resources in parallel
            with ThreadPoolExecutor(max_workers=min(len(self.regions), 10)) as executor:
                future_to_region = {executor.submit(self.scan_region, region, services_set): region for region in self.regions}
                # Process completed futures
                for future in as_completed(future_to_region):
                    region = future_to_region[future]
                    try:
                        result = future.result()
                        for service_type, resources in result.items():
                            if service_type in infrastructure_data:
                                infrastructure_data[service_type].extend(resources)
                    except Exception as e:
                        logging.error(f"Error processing results from region {region}: {str(e)}")

        except Exception as e:
            logging.error(f"Error during AWS resource scanning: {str(e)}")
            
        # Cache the results
        self.cache[cache_key] = (infrastructure_data, datetime.now())
        return infrastructure_data
