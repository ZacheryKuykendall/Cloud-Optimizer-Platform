import React, { useState, useEffect } from 'react';
import { Box, Grid, Typography, Card, CardContent, CircularProgress, Alert } from '@mui/material';
import { Bar } from 'react-chartjs-2';
import { Chart, registerables } from 'chart.js';
import { getResources, getNormalizedCosts } from '../services/api';

// Register Chart.js components
Chart.register(...registerables);

const Dashboard = () => {
  const [resources, setResources] = useState({});
  const [costs, setCosts] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Get resource data
        const resourceResponse = await getResources();
        setResources(resourceResponse.data);

        // Get cost data for the last 30 days
        const today = new Date();
        const thirtyDaysAgo = new Date(today);
        thirtyDaysAgo.setDate(today.getDate() - 30);

        const startDate = thirtyDaysAgo.toISOString().split('T')[0];
        const endDate = today.toISOString().split('T')[0];

        const costResponse = await getNormalizedCosts(true, startDate, endDate, 'daily');
        setCosts(costResponse.data);
      } catch (err) {
        console.error('Error fetching dashboard data:', err);
        setError('Failed to load dashboard data. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Count resources by provider and type
  const getResourceCounts = () => {
    if (!resources || Object.keys(resources).length === 0) return {};

    const counts = { total: 0, byProvider: {}, byType: {} };

    Object.entries(resources).forEach(([provider, providerResources]) => {
      counts.byProvider[provider] = providerResources.length;
      counts.total += providerResources.length;

      providerResources.forEach((resource) => {
        const type = resource.type;
        if (!counts.byType[type]) counts.byType[type] = 0;
        counts.byType[type]++;
      });
    });

    return counts;
  };

  // Prepare chart data for costs
  const prepareCostChartData = () => {
    if (!costs.summary || !costs.details) {
      return {
        labels: [],
        datasets: [],
      };
    }

    // Group costs by date and provider
    const costsByDate = {};
    const providers = [];

    Object.entries(costs.details).forEach(([provider, providerCosts]) => {
      if (providerCosts.length > 0) {
        providers.push(provider);

        providerCosts.forEach((cost) => {
          const date = cost.start_date || cost.date;
          if (!costsByDate[date]) costsByDate[date] = {};
          if (!costsByDate[date][provider]) costsByDate[date][provider] = 0;
          costsByDate[date][provider] += parseFloat(cost.amount);
        });
      }
    });

    // Convert to chart format
    const labels = Object.keys(costsByDate).sort();
    const datasets = providers.map((provider) => {
      const color = provider === 'aws' ? '#FF9900' : provider === 'azure' ? '#0089D6' : '#4285F4';
      return {
        label: provider.toUpperCase(),
        data: labels.map((date) => costsByDate[date][provider] || 0),
        backgroundColor: color,
      };
    });

    return {
      labels,
      datasets,
    };
  };

  const resourceCounts = getResourceCounts();
  const costChartData = prepareCostChartData();

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="80vh">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box mt={3}>
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Cloud Dashboard
      </Typography>

      {/* Resource Summary */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Resources
              </Typography>
              <Typography variant="h3">{resourceCounts.total || 0}</Typography>
            </CardContent>
          </Card>
        </Grid>
        {Object.entries(resourceCounts.byProvider || {}).map(([provider, count]) => (
          <Grid item xs={12} md={4} key={provider}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  {provider.toUpperCase()} Resources
                </Typography>
                <Typography variant="h3">{count}</Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Cost Chart */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Cloud Costs (Last 30 Days)
          </Typography>
          {costChartData.labels.length > 0 ? (
            <Box height={300}>
              <Bar
                data={costChartData}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  scales: {
                    x: {
                      stacked: true,
                    },
                    y: {
                      stacked: true,
                      title: {
                        display: true,
                        text: 'Cost (USD)',
                      },
                    },
                  },
                }}
              />
            </Box>
          ) : (
            <Typography>No cost data available.</Typography>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};

export default Dashboard; 