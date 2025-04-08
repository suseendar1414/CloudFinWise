from typing import Dict, List, Optional
from datetime import datetime, timedelta
import boto3
from azure.monitor.query import MetricsQueryClient
from azure.identity import DefaultAzureCredential
from .query_parser import MetricQuery

class MetricFetcher:
    def __init__(self):
        # AWS clients
        self.cloudwatch = boto3.client('cloudwatch')
        
        # Azure clients
        self.azure_credential = DefaultAzureCredential()
        self.azure_metrics_client = MetricsQueryClient(self.azure_credential)

    async def fetch_aws_metrics(self, query: MetricQuery) -> Dict:
        """Fetch metrics from AWS CloudWatch."""
        metric_mappings = {
            'cpu': {
                'vm': 'AWS/EC2:CPUUtilization',
                'database': 'AWS/RDS:CPUUtilization',
                'function': 'AWS/Lambda:Duration'
            },
            'memory': {
                'vm': 'System/Linux:MemoryUtilization',
                'function': 'AWS/Lambda:MemoryUtilization'
            },
            'disk': {
                'vm': 'AWS/EBS:VolumeReadBytes',
                'database': 'AWS/RDS:FreeStorageSpace'
            },
            'network': {
                'vm': 'AWS/EC2:NetworkIn',
                'database': 'AWS/RDS:NetworkReceiveThroughput'
            }
        }

        namespace, metric_name = metric_mappings[query.metric][query.resource_type].split(':')

        response = self.cloudwatch.get_metric_data(
            MetricDataQueries=[
                {
                    'Id': 'm1',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': namespace,
                            'MetricName': metric_name
                        },
                        'Period': query.period,
                        'Stat': query.aggregation.capitalize()
                    },
                    'ReturnData': True
                }
            ],
            StartTime=query.start_time,
            EndTime=query.end_time
        )

        return {
            'timestamps': response['MetricDataResults'][0]['Timestamps'],
            'values': response['MetricDataResults'][0]['Values'],
            'label': f"{metric_name} ({query.aggregation})"
        }

    async def fetch_azure_metrics(self, query: MetricQuery) -> Dict:
        """Fetch metrics from Azure Monitor."""
        metric_mappings = {
            'cpu': {
                'vm': 'Percentage CPU',
                'database': 'cpu_percent',
                'function': 'FunctionExecutionUnits'
            },
            'memory': {
                'vm': 'Available Memory Bytes',
                'function': 'MemoryWorkingSet'
            },
            'disk': {
                'vm': 'Disk Read Bytes',
                'database': 'storage_percent'
            },
            'network': {
                'vm': 'Network In Total',
                'database': 'network_bytes_ingress'
            }
        }

        metric_name = metric_mappings[query.metric][query.resource_type]
        
        response = self.azure_metrics_client.query_resource(
            resource_uri=f"/subscriptions/{subscription_id}/...",  # Complete URI based on resource
            metric_names=[metric_name],
            timespan=f"{query.start_time}/{query.end_time}",
            granularity=f"PT{query.period}S",
            aggregation=query.aggregation
        )

        metrics_data = response.metrics[0]
        time_series = metrics_data.timeseries[0]
        
        return {
            'timestamps': [point.timestamp for point in time_series.data],
            'values': [getattr(point, query.aggregation) for point in time_series.data],
            'label': f"{metric_name} ({query.aggregation})"
        }

    async def fetch_metrics(self, query: MetricQuery, cloud_provider: str) -> Dict:
        """Fetch metrics from specified cloud provider."""
        if cloud_provider.lower() == 'aws':
            return await self.fetch_aws_metrics(query)
        elif cloud_provider.lower() == 'azure':
            return await self.fetch_azure_metrics(query)
        else:
            raise ValueError(f"Unsupported cloud provider: {cloud_provider}")

# Example usage:
# fetcher = MetricFetcher()
# query = MetricQuery.from_natural_language("Show CPU usage for VMs in last hour")
# data = await fetcher.fetch_metrics(query, "aws")
