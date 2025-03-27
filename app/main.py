from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from typing import Dict
import openai
import os
from dotenv import load_dotenv

from cloud_scanners.aws_scanner import AWSScanner
from cloud_scanners.azure_scanner import AzureScanner
from database import init_db, store_infrastructure_data, get_latest_infrastructure_data

load_dotenv()

app = FastAPI(title="Cloud Infrastructure Scanner")
SessionLocal = init_db()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/scan/aws")
async def scan_aws(
    services: Optional[List[str]] = Query(None, description="List of services to scan (ec2, vpc, s3, rds, lambda, cloudwatch, logs)"),
    db: Session = Depends(get_db)
):
    """Scan AWS infrastructure and store the results."""
    try:
        scanner = AWSScanner()
        infrastructure_data = scanner.scan_resources(services=services)
        store_infrastructure_data(db, "aws", infrastructure_data)
        return {"message": "AWS infrastructure scan completed", "data": infrastructure_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scan/azure")
async def scan_azure(
    subscription_id: Optional[str] = Query(None, description="Azure subscription ID. If not provided, uses default subscription"),
    services: Optional[List[str]] = Query(None, description="List of services to scan (compute, network, storage, web, container, cosmos, sql)"),
    db: Session = Depends(get_db)
):
    """Scan Azure infrastructure and store the results."""
    try:
        scanner = AzureScanner()
        infrastructure_data = scanner.scan_resources(subscription_id, services=services)
        store_infrastructure_data(db, "azure", infrastructure_data)
        return {"message": "Azure infrastructure scan completed", "data": infrastructure_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query/aws")
async def query_aws_infrastructure(request: dict, db: Session = Depends(get_db)):
    question = request.get("question")
    """Query AWS infrastructure using GPT-4."""
    try:
        # Get latest AWS data
        aws_data = get_latest_infrastructure_data(db).get('aws')
        
        if not aws_data:
            raise HTTPException(status_code=404, detail="No AWS infrastructure data found")
            
        # Prepare the prompt for GPT-4
        system_prompt = """You are an AWS cloud infrastructure expert. 
        Analyze the provided AWS infrastructure data and answer the user's question. 
        Focus only on AWS resources and provide clear, actionable insights."""
        
        user_prompt = f"""
        AWS Infrastructure Data:
        {aws_data}
        
        User Question:
        {question}
        """
        
        # Call GPT-4
        response = openai.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return {
            "question": question,
            "answer": response.choices[0].message.content,
            "cloud": "aws"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query/azure")
async def query_azure_infrastructure(request: dict, db: Session = Depends(get_db)):
    """Query Azure infrastructure using GPT-4."""
    try:
        question = request.get("question")
        if not question:
            raise HTTPException(status_code=400, detail="Question is required")

        # Get latest Azure data
        infrastructure_data = get_latest_infrastructure_data(db)
        if not infrastructure_data:
            return {
                "question": question,
                "answer": "No infrastructure data found. Please scan your Azure resources first.",
                "cloud": "azure",
                "error": "no_data"
            }

        azure_data = infrastructure_data.get('azure')
        if not azure_data:
            return {
                "question": question,
                "answer": "No Azure infrastructure data found. Please scan your Azure resources first.",
                "cloud": "azure",
                "error": "no_azure_data"
            }

        # Prepare the prompt for GPT-4
        system_prompt = """You are an Azure cloud infrastructure expert. 
        Analyze the provided Azure infrastructure data and answer the user's question. 
        Focus only on Azure resources and provide clear, actionable insights."""

        user_prompt = f"""
        Azure Infrastructure Data:
        {azure_data}

        User Question:
        {question}
        """

        # Call GPT-4
        response = openai.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )

        return {
            "question": question,
            "answer": response.choices[0].message.content,
            "cloud": "azure"
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        logging.error(f"Error querying Azure infrastructure: {str(e)}")
        return {
            "question": question,
            "answer": f"Error analyzing Azure infrastructure: {str(e)}",
            "cloud": "azure",
            "error": "query_error"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
async def query_infrastructure(request: dict, db: Session = Depends(get_db)):
    question = request.get("question")
    """Query both AWS and Azure infrastructure using GPT-4."""
    try:
        infrastructure_data = get_latest_infrastructure_data(db)
        
        if not infrastructure_data:
            raise HTTPException(status_code=404, detail="No infrastructure data found")
            
        # Prepare the prompt for GPT-4
        system_prompt = """You are an expert in both AWS and Azure cloud infrastructure. 
        Analyze the provided infrastructure data and answer the user's question. 
        Consider resources from both clouds and provide comprehensive insights."""
        
        user_prompt = f"""
        Infrastructure Data:
        {infrastructure_data}
        
        User Question:
        {question}
        """
        
        # Call GPT-4
        response = openai.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return {
            "question": question,
            "answer": response.choices[0].message.content,
            "clouds": list(infrastructure_data.keys())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
