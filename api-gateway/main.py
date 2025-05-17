from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

import os

import httpx

import sys

from typing import List, Optional, Dict, Any

import importlib.util



app = FastAPI(title="Cloud Optimizer API Gateway", 

              description="API Gateway for Cloud Optimizer Platform",

              version="0.1.0")



# Add CORS middleware

app.add_middleware(

    CORSMiddleware,

    allow_origins=["*"],  # Allow all origins in development

    allow_credentials=True,

    allow_methods=["*"],  # Allow all methods

    allow_headers=["*"],  # Allow all headers

)



# Service endpoints from environment variables

COST_ANALYZER_SERVICE = os.getenv("COST_ANALYZER_SERVICE", "http://cost-analyzer:8000")

RESOURCE_OPTIMIZER_SERVICE = os.getenv("RESOURCE_OPTIMIZER_SERVICE", "http://resource-optimizer:8000")

CLOUD_COST_NORMALIZATION_SERVICE = os.getenv("CLOUD_COST_NORMALIZATION_SERVICE", "http://cloud-cost-normalization:8001")



# Import cloud_integrations.py

try:

    # Import cloud_integrations directly from the app directory

    spec = importlib.util.spec_from_file_location(

        "cloud_integrations",

        os.path.join(os.path.dirname(__file__), "cloud_integrations.py")

    )

    cloud_integrations = importlib.util.module_from_spec(spec)

    spec.loader.exec_module(cloud_integrations)

    

    # Initialize cloud integrations

    integrations = cloud_integrations.load_cloud_integrations()

    

except Exception as e:

    print(f"Error loading cloud integrations: {e}")

    integrations = {}



@app.get("/health")

async def health_check():

    return {"status": "healthy"}



@app.get("/")

async def root():

    return {

        "message": "Cloud Optimizer API Gateway",

        "services": {

            "cost_analyzer": COST_ANALYZER_SERVICE,

            "resource_optimizer": RESOURCE_OPTIMIZER_SERVICE,

            "cloud_cost_normalization": CLOUD_COST_NORMALIZATION_SERVICE

        },

        "active_integrations": list(integrations.keys()) if integrations else []

    }



@app.get("/resources", response_model=Dict[str, List[Dict[str, Any]]])

async def get_resources(

    provider: Optional[str] = Query(None, description="Cloud provider (aws, azure, gcp)"),

    resource_type: Optional[str] = Query(None, description="Resource type")

):

    """Get cloud resources across providers"""

    results = {}

    

    # If provider is specified, only query that provider

    if provider:

        if provider not in integrations:

            raise HTTPException(status_code=404, detail=f"Provider '{provider}' not found or not authenticated")

        

        results[provider] = integrations[provider].get_resources(resource_type)

    else:

        # Query all available providers

        for provider_name, integration in integrations.items():

            results[provider_name] = integration.get_resources(resource_type)

    

    return results



@app.get("/costs", response_model=Dict[str, List[Dict[str, Any]]])

async def get_costs(

    provider: Optional[str] = Query(None, description="Cloud provider (aws, azure, gcp)"),

    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),

    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),

    granularity: str = Query("daily", description="Cost granularity (daily, monthly)")

):

    """Get cost data across providers"""

    results = {}

    

    # If provider is specified, only query that provider

    if provider:

        if provider not in integrations:

            raise HTTPException(status_code=404, detail=f"Provider '{provider}' not found or not authenticated")

        

        results[provider] = integrations[provider].get_cost_data(start_date, end_date, granularity)

    else:

        # Query all available providers

        for provider_name, integration in integrations.items():

            results[provider_name] = integration.get_cost_data(start_date, end_date, granularity)

    

    return results

