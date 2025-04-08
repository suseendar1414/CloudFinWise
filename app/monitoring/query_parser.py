from typing import Dict, List, Optional
from datetime import datetime, timedelta
import re

class MetricQuery:
    def __init__(self, metric: str, resource_type: str, resource_id: Optional[str] = None,
                 start_time: Optional[datetime] = None, end_time: Optional[datetime] = None,
                 aggregation: str = 'average', period: int = 300):
        self.metric = metric
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.start_time = start_time or (datetime.utcnow() - timedelta(hours=3))
        self.end_time = end_time or datetime.utcnow()
        self.aggregation = aggregation
        self.period = period  # in seconds

    @classmethod
    def from_natural_language(cls, query: str) -> 'MetricQuery':
        """Parse natural language query into structured metric query."""
        query = query.lower()
        
        # Extract metric type
        metric_patterns = {
            'cpu': r'cpu|processor',
            'memory': r'memory|ram',
            'disk': r'disk|storage|volume',
            'network': r'network|bandwidth|traffic'
        }
        
        metric = next((k for k, pattern in metric_patterns.items() 
                      if re.search(pattern, query)), 'cpu')

        # Extract resource type
        resource_patterns = {
            'vm': r'vm|instance|server',
            'database': r'database|db|rds',
            'storage': r'storage|bucket|blob',
            'function': r'function|lambda'
        }
        
        resource_type = next((k for k, pattern in resource_patterns.items() 
                            if re.search(pattern, query)), 'vm')

        # Extract time range
        time_patterns = {
            'hour': (r'(last|\d+)\s*hour', 1),
            'day': (r'(last|\d+)\s*day', 24),
            'week': (r'(last|\d+)\s*week', 168),
            'month': (r'(last|\d+)\s*month', 720)
        }
        
        hours = 3  # default to last 3 hours
        for pattern, multiplier in time_patterns.values():
            if match := re.search(pattern, query):
                try:
                    num = int(match.group(1)) if match.group(1) != 'last' else 1
                    hours = num * multiplier
                except ValueError:
                    pass

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        # Extract aggregation
        agg_patterns = {
            'average': r'average|avg|mean',
            'maximum': r'max|maximum|highest',
            'minimum': r'min|minimum|lowest',
            'sum': r'sum|total'
        }
        
        aggregation = next((k for k, pattern in agg_patterns.items() 
                          if re.search(pattern, query)), 'average')

        return cls(
            metric=metric,
            resource_type=resource_type,
            start_time=start_time,
            end_time=end_time,
            aggregation=aggregation
        )

    def to_dict(self) -> Dict:
        """Convert query to dictionary format."""
        return {
            'metric': self.metric,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'aggregation': self.aggregation,
            'period': self.period
        }

# Example usage:
# query = "Show me CPU usage for all VMs in the last 2 hours"
# metric_query = MetricQuery.from_natural_language(query)
