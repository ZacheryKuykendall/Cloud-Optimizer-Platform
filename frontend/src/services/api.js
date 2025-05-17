import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || '/api';
const COST_URL = process.env.REACT_APP_COST_URL || '/api/cost';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

const costApi = axios.create({
  baseURL: COST_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API Gateway endpoints
export const getHealthStatus = () => api.get('/health');
export const getResources = (provider, resourceType) => {
  let url = '/resources';
  const params = {};
  if (provider) params.provider = provider;
  if (resourceType) params.resource_type = resourceType;
  return api.get(url, { params });
};

export const getCosts = (provider, startDate, endDate, granularity = 'daily') => {
  let url = '/costs';
  const params = {};
  if (provider) params.provider = provider;
  if (startDate) params.start_date = startDate;
  if (endDate) params.end_date = endDate;
  if (granularity) params.granularity = granularity;
  return api.get(url, { params });
};

// Cost Normalization endpoints
export const getNormalizedCosts = (allProviders = true, startDate, endDate, granularity = 'daily') => {
  let url = '/normalize';
  const params = {
    all_providers: allProviders,
    target_currency: 'USD',
  };
  if (startDate) params.start_date = startDate;
  if (endDate) params.end_date = endDate;
  if (granularity) params.granularity = granularity;
  return costApi.get(url, { params });
};

export const getCostComparison = (resourceType, size, region) => {
  let url = '/cost-comparison';
  const params = {
    resource_type: resourceType,
  };
  if (size) params.size = size;
  if (region) params.region = region;
  return costApi.get(url, { params });
};

export default { getHealthStatus, getResources, getCosts, getNormalizedCosts, getCostComparison }; 