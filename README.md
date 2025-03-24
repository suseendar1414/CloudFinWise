# Cloud Infrastructure Scanner

This application scans AWS and Azure cloud infrastructure, stores the data, and allows users to query the infrastructure using natural language through GPT-4.

## Features

- Scans AWS resources including:
  - EC2 instances
  - VPCs
  - S3 buckets
  - RDS instances
  - Lambda functions

- Scans Azure resources including:
  - Virtual Machines
  - Virtual Networks
  - Storage Accounts
  - Resource Groups

- Stores infrastructure data in a SQLite database
- Provides natural language querying using GPT-4

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables in `.env`:
```
OPENAI_API_KEY=your_openai_api_key
```

3. Configure cloud credentials:
- For AWS: Configure AWS credentials using AWS CLI or environment variables
- For Azure: Use Azure CLI to log in or set up service principal credentials

## Usage

1. Start the server:
```bash
python -m uvicorn app.main:app --reload
```

2. API Endpoints:
- POST `/scan/aws`: Scan AWS infrastructure
- POST `/scan/azure`: Scan Azure infrastructure (requires subscription_id)
- POST `/query`: Query infrastructure using natural language

## Example Usage

1. Scan AWS infrastructure:
```bash
curl -X POST http://localhost:8000/scan/aws
```

2. Scan Azure infrastructure:
```bash
curl -X POST http://localhost:8000/scan/azure?subscription_id=your_subscription_id
```

3. Query infrastructure:
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "How many EC2 instances are running in us-east-1?"}'
```
# CloudFinWise
