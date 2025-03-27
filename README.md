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

A powerful cloud infrastructure scanner and analyzer that provides real-time insights into your AWS and Azure resources using natural language queries.

## Features

### Multi-Cloud Support
- **AWS Scanner**: EC2, VPC, S3, RDS, Lambda, CloudWatch
- **Azure Scanner**: VMs, Networks, Storage, App Services, Databases
- Parallel processing for faster scanning
- 15-minute caching to reduce API calls

### Smart Analysis
- Natural language queries powered by GPT-4
- Cross-cloud resource comparison
- Infrastructure insights and recommendations
- Real-time scanning and analysis

### Modern Interface
- Streamlit-based interactive dashboard
- Separate views for AWS and Azure
- Visual resource representation
- Easy-to-use query interface

## Installation

1. **Clone the Repository**
```bash
git clone git@github.com:suseendar1414/CloudFinWise.git
cd CloudFinWise
```

2. **Set Up Virtual Environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure Cloud Credentials**

AWS:
```bash
# Option 1: AWS CLI
aws configure

# Option 2: Environment Variables
export AWS_ACCESS_KEY_ID="your_access_key"
export AWS_SECRET_ACCESS_KEY="your_secret_key"
export AWS_DEFAULT_REGION="your_region"
```

Azure:
```bash
# Option 1: Azure CLI
az login

# Option 2: Environment Variables
export AZURE_SUBSCRIPTION_ID="your_subscription_id"
export AZURE_TENANT_ID="your_tenant_id"
export AZURE_CLIENT_ID="your_client_id"
export AZURE_CLIENT_SECRET="your_client_secret"
```

## Usage

1. **Start the Backend Server**
```bash
cd app
uvicorn main:app --reload --port 8006
```

2. **Start the Frontend**
```bash
cd app/frontend
streamlit run streamlit_app.py
```

3. **Access the Application**
- Frontend Dashboard: http://localhost:8501
- Backend API: http://localhost:8006

## Example Queries

### AWS Examples
```
- "How many EC2 instances are running?"
- "List all S3 buckets with public access"
- "Show me resources in us-east-1"
```

### Azure Examples
```
- "List all VMs in East US"
- "Which storage accounts are not encrypted?"
- "Show me all App Services"
```

### Cross-Cloud Examples
```
- "Compare compute resources between AWS and Azure"
- "Show total storage across both clouds"
- "Which cloud has more running services?"
```

## Project Structure
```
CloudFinWise/
├── app/
│   ├── cloud_scanners/
│   │   ├── aws_scanner.py    # AWS resource scanning
│   │   └── azure_scanner.py  # Azure resource scanning
│   ├── frontend/
│   │   └── streamlit_app.py  # Streamlit dashboard
│   ├── main.py              # FastAPI backend
│   └── database.py          # SQLite database handling
├── requirements.txt         # Python dependencies
└── README.md               # Project documentation
```

## API Endpoints

### Scanning Endpoints
- `POST /scan/aws`: Scan AWS resources
- `POST /scan/azure`: Scan Azure resources

### Query Endpoints
- `POST /query/aws`: Query AWS infrastructure
- `POST /query/azure`: Query Azure infrastructure
- `POST /query`: Query both clouds

## Contributing
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License
This project is licensed under the MIT License - see the LICENSE file for details.
