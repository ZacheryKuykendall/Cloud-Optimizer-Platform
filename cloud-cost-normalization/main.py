from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware

import os

import sys

import importlib.util

from typing import Dict, List, Optional, Any

import json

from datetime import datetime



app = FastAPI(

    title="Cloud Cost Normalization Service",

    description="Service to normalize cost data across different cloud providers",

    version="0.1.0"

)



# Add CORS middleware

app.add_middleware(

    CORSMiddleware,

    allow_origins=["*"],  # Allow all origins in development

    allow_credentials=True,

    allow_methods=["*"],  # Allow all methods

    allow_headers=["*"],  # Allow all headers

)



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



def get_integrations():

    """Dependency to get cloud integrations"""

    return integrations



@app.get("/health")

async def health_check():

    """Health check endpoint"""

    return {"status": "healthy", "timestamp": datetime.now().isoformat()}



@app.get("/")

async def read_root():

    """Root endpoint"""

    return {

        "service": "Cloud Cost Normalization",

        "version": "0.1.0",

        "active_integrations": list(integrations.keys()) if integrations else []

    }



@app.get("/normalize", response_model=Dict[str, Any])

async def normalize_costs(

    all_providers: bool = Query(False, description="Include all providers or only active ones"),

    target_currency: str = Query("USD", description="Target currency for normalization"),

    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),

    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),

    granularity: str = Query("daily", description="Cost granularity (daily, monthly)"),

    integrations: Dict[str, Any] = Depends(get_integrations)

):

    """Normalize cost data across cloud providers"""

    if not integrations:

        raise HTTPException(status_code=503, detail="No cloud integrations available")

    

    # Get cost data from all active providers

    all_costs = {}

    normalized_costs = {

        "summary": {

            "total": 0.0,

            "currency": target_currency,

            "providers": {},

            "period": {

                "start": start_date,

                "end": end_date

            }

        },

        "details": {}

    }

    

    # Collect costs from each provider

    for provider_name, integration in integrations.items():

        costs = integration.get_cost_data(start_date, end_date, granularity)

        all_costs[provider_name] = costs

        

        provider_total = sum(cost.get("amount", 0) for cost in costs)

        normalized_costs["summary"]["total"] += provider_total

        normalized_costs["summary"]["providers"][provider_name] = provider_total

        normalized_costs["details"][provider_name] = costs

    

    return normalized_costs



@app.get("/cost-comparison", response_model=Dict[str, Any])

async def cost_comparison(

    resource_type: str = Query(..., description="Resource type to compare (e.g., vm, storage)"),

    size: Optional[str] = Query(None, description="Resource size or tier"),

    region: Optional[str] = Query(None, description="Region to compare"),

    integrations: Dict[str, Any] = Depends(get_integrations)

):

    """Compare costs for similar resources across providers"""

    if not integrations:

        raise HTTPException(status_code=503, detail="No cloud integrations available")

    

    # Map of provider-specific resource types

    resource_type_map = {

        "vm": {"aws": "ec2", "azure": "vm", "gcp": "compute"},

        "storage": {"aws": "s3", "azure": "storage", "gcp": "storage"}

    }

    

    if resource_type not in resource_type_map:

        raise HTTPException(status_code=400, detail=f"Unsupported resource type: {resource_type}")

    

    comparison = {

        "resource_type": resource_type,

        "size": size,

        "region": region,

        "providers": {}

    }

    

    # Get resources from each provider and calculate cost approximations

    for provider_name, integration in integrations.items():

        provider_resource_type = resource_type_map.get(resource_type, {}).get(provider_name)

        if not provider_resource_type:

            continue

            

        resources = integration.get_resources(provider_resource_type)

        

        # Filter by size and region if specified

        if size or region:

            filtered_resources = []

            for resource in resources:

                size_match = not size or (resource.get("size") == size or resource.get("machine_type") == size)

                region_match = not region or (resource.get("region") == region or resource.get("location") == region)

                if size_match and region_match:

                    filtered_resources.append(resource)

        else:

            filtered_resources = resources

            

        comparison["providers"][provider_name] = {

            "count": len(filtered_resources),

            "resources": filtered_resources[:5]  # Include only 5 examples

        }

    

    return comparison

