import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  Grid,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Divider,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
} from '@mui/material';
import { getNormalizedCosts, getCostComparison } from '../services/api';
import { Pie } from 'react-chartjs-2';
import { Chart, registerables } from 'chart.js';

// Register Chart.js components
Chart.register(...registerables);

const Costs = () => {
  const [costs, setCosts] = useState({});
  const [comparison, setComparison] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  // Form states
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [granularity, setGranularity] = useState('daily');
  const [resourceType, setResourceType] = useState('vm');
  const [resourceSize, setResourceSize] = useState('');
  const [region, setRegion] = useState('');

  useEffect(() => {
    const fetchCosts = async () => {
      try {
        setLoading(true);
        setError(null);

        // Set default dates if not provided
        const today = new Date();
        const defaultEndDate = today.toISOString().split('T')[0];
        
        const thirtyDaysAgo = new Date(today);
        thirtyDaysAgo.setDate(today.getDate() - 30);
        const defaultStartDate = thirtyDaysAgo.toISOString().split('T')[0];

        // Get normalized costs
        const costResponse = await getNormalizedCosts(
          true,
          startDate || defaultStartDate,
          endDate || defaultEndDate,
          granularity
        );
        setCosts(costResponse.data);

        // Get cost comparison for the selected resource type
        const comparisonResponse = await getCostComparison(resourceType, resourceSize, region);
        setComparison(comparisonResponse.data);
      } catch (err) {
        console.error('Error fetching cost data:', err);
        setError('Failed to load cost data. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchCosts();
  }, [startDate, endDate, granularity, resourceType, resourceSize, region]);

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const preparePieChartData = () => {
    if (!costs.summary || !costs.summary.providers) {
      return {
        labels: [],
        datasets: [{ data: [] }],
      };
    }

    const providers = Object.keys(costs.summary.providers);
    const data = providers.map((provider) => costs.summary.providers[provider]);
    const backgroundColor = providers.map((provider) => 
      provider === 'aws' ? '#FF9900' : provider === 'azure' ? '#0089D6' : '#4285F4'
    );

    return {
      labels: providers.map((p) => p.toUpperCase()),
      datasets: [
        {
          data,
          backgroundColor,
          borderWidth: 1,
        },
      ],
    };
  };

  const pieChartData = preparePieChartData();

  // Prepare the cost details for the table
  const getAllCostDetails = () => {
    if (!costs.details) return [];
    
    let allDetails = [];
    
    Object.entries(costs.details).forEach(([provider, providerCosts]) => {
      providerCosts.forEach((cost) => {
        allDetails.push({
          provider,
          ...cost,
        });
      });
    });
    
    return allDetails;
  };

  const allCostDetails = getAllCostDetails();

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
        Cloud Costs
      </Typography>

      {/* Filters and Parameters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <TextField
                label="Start Date"
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                InputLabelProps={{
                  shrink: true,
                }}
                fullWidth
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                label="End Date"
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                InputLabelProps={{
                  shrink: true,
                }}
                fullWidth
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <FormControl fullWidth>
                <InputLabel id="granularity-label">Granularity</InputLabel>
                <Select
                  labelId="granularity-label"
                  id="granularity-select"
                  value={granularity}
                  label="Granularity"
                  onChange={(e) => setGranularity(e.target.value)}
                >
                  <MenuItem value="daily">Daily</MenuItem>
                  <MenuItem value="monthly">Monthly</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Cost Summary */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Total Cost
              </Typography>
              <Typography variant="h3">
                ${costs.summary?.total ? costs.summary.total.toFixed(2) : '0.00'}
              </Typography>
              <Typography color="textSecondary">
                {costs.summary?.period?.start} to {costs.summary?.period?.end}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Cost Distribution
              </Typography>
              {pieChartData.labels.length > 0 ? (
                <Box height={200}>
                  <Pie
                    data={pieChartData}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: {
                          position: 'right',
                        },
                      },
                    }}
                  />
                </Box>
              ) : (
                <Typography>No cost distribution data available.</Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Cost Details Table */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Cost Details
          </Typography>
          <Paper sx={{ width: '100%', overflow: 'hidden' }}>
            <TableContainer sx={{ maxHeight: 440 }}>
              <Table stickyHeader aria-label="cost details table">
                <TableHead>
                  <TableRow>
                    <TableCell>Provider</TableCell>
                    <TableCell>Service</TableCell>
                    <TableCell>Date</TableCell>
                    <TableCell align="right">Amount</TableCell>
                    <TableCell>Currency</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {allCostDetails
                    .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                    .map((cost, index) => (
                      <TableRow hover key={`cost-${index}`}>
                        <TableCell>{cost.provider.toUpperCase()}</TableCell>
                        <TableCell>{cost.service}</TableCell>
                        <TableCell>
                          {cost.start_date || cost.date || 'N/A'}
                        </TableCell>
                        <TableCell align="right">
                          {typeof cost.amount === 'number'
                            ? cost.amount.toFixed(2)
                            : cost.amount}
                        </TableCell>
                        <TableCell>{cost.currency}</TableCell>
                      </TableRow>
                    ))}
                  {allCostDetails.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={5} align="center">
                        No cost details available
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
            <TablePagination
              rowsPerPageOptions={[10, 25, 50]}
              component="div"
              count={allCostDetails.length}
              rowsPerPage={rowsPerPage}
              page={page}
              onPageChange={handleChangePage}
              onRowsPerPageChange={handleChangeRowsPerPage}
            />
          </Paper>
        </CardContent>
      </Card>

      {/* Resource Cost Comparison */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Resource Cost Comparison
          </Typography>

          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={12} md={4}>
              <FormControl fullWidth>
                <InputLabel id="resource-type-label">Resource Type</InputLabel>
                <Select
                  labelId="resource-type-label"
                  id="resource-type-select"
                  value={resourceType}
                  label="Resource Type"
                  onChange={(e) => setResourceType(e.target.value)}
                >
                  <MenuItem value="vm">Virtual Machines</MenuItem>
                  <MenuItem value="storage">Storage</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                label="Size/Tier"
                value={resourceSize}
                onChange={(e) => setResourceSize(e.target.value)}
                fullWidth
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                label="Region"
                value={region}
                onChange={(e) => setRegion(e.target.value)}
                fullWidth
              />
            </Grid>
          </Grid>

          {comparison.providers ? (
            <Grid container spacing={2}>
              {Object.entries(comparison.providers).map(([provider, data]) => (
                <Grid item xs={12} md={4} key={provider}>
                  <Paper sx={{ p: 2 }}>
                    <Typography variant="subtitle1" fontWeight="bold">
                      {provider.toUpperCase()}
                    </Typography>
                    <Typography>Resources found: {data.count}</Typography>
                    <Divider sx={{ my: 1 }} />
                    {data.count > 0 && (
                      <Box>
                        <Typography variant="subtitle2">Examples:</Typography>
                        <ul style={{ paddingLeft: '20px' }}>
                          {data.resources.slice(0, 3).map((resource, idx) => (
                            <li key={idx}>
                              {resource.name || resource.id} ({resource.size || resource.machine_type || resource.sku})
                            </li>
                          ))}
                        </ul>
                      </Box>
                    )}
                  </Paper>
                </Grid>
              ))}
            </Grid>
          ) : (
            <Typography>No comparison data available.</Typography>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};

export default Costs; 