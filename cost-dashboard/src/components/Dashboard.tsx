import React, { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { 
  Card, 
  Grid, 
  Typography, 
  Box, 
  CircularProgress, 
  Alert,
  Tabs,
  Tab,
} from '@mui/material';
import CostAnalysis from './CostAnalysis';
import ProviderComparison from './ProviderComparison';
import ResourceComparison from './ResourceComparison';
import CostSavingOpportunities from './CostSavingOpportunities';
import PerformanceImprovements from './PerformanceImprovements';
import ResourceOptimization from './ResourceOptimization';
import ImplementationPlans from './ImplementationPlans';

interface CostData {
  date: string;
  amount: number;
  provider: string;
  service: string;
  region: string;
}

interface CostBreakdown {
  byProvider: { [key: string]: number };
  byService: { [key: string]: number };
  byRegion: { [key: string]: number };
}

interface DashboardProps {
  startDate: Date;
  endDate: Date;
  refreshInterval?: number;
}

const Dashboard: React.FC<DashboardProps> = ({
  startDate,
  endDate,
  refreshInterval = 300000, // 5 minutes default
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [costData, setCostData] = useState<CostData[]>([]);
  const [costBreakdown, setCostBreakdown] = useState<CostBreakdown>({
    byProvider: {},
    byService: {},
    byRegion: {},
  });
  const [activeTab, setActiveTab] = useState(0);

  const fetchCostData = async () => {
    try {
      const response = await fetch('/api/v1/costs', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          start_date: startDate.toISOString(),
          end_date: endDate.toISOString(),
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to fetch cost data');
      }

      const data = await response.json();
      setCostData(data.costs);
      setCostBreakdown({
        byProvider: data.breakdown.by_provider,
        byService: data.breakdown.by_service,
        byRegion: data.breakdown.by_region,
      });
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCostData();
    const interval = setInterval(fetchCostData, refreshInterval);
    return () => clearInterval(interval);
  }, [startDate, endDate, refreshInterval]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
      </Alert>
    );
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case 0: // Overview
        return (
          <Grid container spacing={3}>
            {/* Total Cost Card */}
            <Grid item xs={12} md={4}>
              <Card sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Total Cost
                </Typography>
                <Typography variant="h4">
                  {formatCurrency(costData.reduce((sum, item) => sum + item.amount, 0))}
                </Typography>
              </Card>
            </Grid>

            {/* Cost Trend Chart */}
            <Grid item xs={12}>
              <Card sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Cost Trend
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={costData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip formatter={(value) => formatCurrency(value as number)} />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="amount"
                      stroke="#8884d8"
                      name="Daily Cost"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </Card>
            </Grid>

            {/* Cost by Provider */}
            <Grid item xs={12} md={4}>
              <Card sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Cost by Provider
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={Object.entries(costBreakdown.byProvider).map(([name, value]) => ({
                        name,
                        value,
                      }))}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      fill="#8884d8"
                      label={({ name, percent }) =>
                        `${name} (${(percent * 100).toFixed(0)}%)`
                      }
                    />
                    <Tooltip formatter={(value) => formatCurrency(value as number)} />
                  </PieChart>
                </ResponsiveContainer>
              </Card>
            </Grid>

            {/* Cost by Service */}
            <Grid item xs={12} md={4}>
              <Card sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Cost by Service
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart
                    data={Object.entries(costBreakdown.byService)
                      .map(([name, value]) => ({
                        name,
                        value,
                      }))
                      .sort((a, b) => b.value - a.value)
                      .slice(0, 10)}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip formatter={(value) => formatCurrency(value as number)} />
                    <Bar dataKey="value" fill="#82ca9d" name="Cost" />
                  </BarChart>
                </ResponsiveContainer>
              </Card>
            </Grid>

            {/* Cost by Region */}
            <Grid item xs={12} md={4}>
              <Card sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Cost by Region
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={Object.entries(costBreakdown.byRegion).map(([name, value]) => ({
                        name,
                        value,
                      }))}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      fill="#ffc658"
                      label={({ name, percent }) =>
                        `${name} (${(percent * 100).toFixed(0)}%)`
                      }
                    />
                    <Tooltip formatter={(value) => formatCurrency(value as number)} />
                  </PieChart>
                </ResponsiveContainer>
              </Card>
            </Grid>
          </Grid>
        );
      case 1: // Analysis
        return (
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <CostAnalysis startDate={startDate} endDate={endDate} />
            </Grid>
            <Grid item xs={12}>
              <ProviderComparison startDate={startDate} endDate={endDate} />
            </Grid>
            <Grid item xs={12}>
              <ResourceComparison startDate={startDate} endDate={endDate} />
            </Grid>
          </Grid>
        );
      case 2: // Optimization
        return (
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <CostSavingOpportunities startDate={startDate} endDate={endDate} />
            </Grid>
            <Grid item xs={12}>
              <PerformanceImprovements startDate={startDate} endDate={endDate} />
            </Grid>
            <Grid item xs={12}>
              <ResourceOptimization startDate={startDate} endDate={endDate} />
            </Grid>
            <Grid item xs={12}>
              <ImplementationPlans startDate={startDate} endDate={endDate} />
            </Grid>
          </Grid>
        );
      default:
        return null;
    }
  };

  return (
    <Box>
      <Tabs
        value={activeTab}
        onChange={handleTabChange}
        indicatorColor="primary"
        textColor="primary"
        sx={{ mb: 3 }}
      >
        <Tab label="Overview" />
        <Tab label="Analysis" />
        <Tab label="Optimization" />
      </Tabs>
      {renderTabContent()}
    </Box>
  );
};

export default Dashboard;
