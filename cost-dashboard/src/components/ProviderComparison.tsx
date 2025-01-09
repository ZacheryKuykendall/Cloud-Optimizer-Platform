import React, { useState, useEffect } from 'react';
import {
  Card,
  Grid,
  Typography,
  Box,
  CircularProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Button,
} from '@mui/material';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import CompareArrowsIcon from '@mui/icons-material/CompareArrows';

interface ProviderCosts {
  aws: number;
  azure: number;
  gcp: number;
}

interface ServiceComparison {
  service: string;
  costs: ProviderCosts;
  recommendation: string;
}

interface ProviderComparisonProps {
  startDate: Date;
  endDate: Date;
  onExport?: (data: any) => void;
}

const ProviderComparison: React.FC<ProviderComparisonProps> = ({
  startDate,
  endDate,
  onExport,
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [comparisons, setComparisons] = useState<ServiceComparison[]>([]);
  const [selectedService, setSelectedService] = useState<string>('all');
  const [totalCosts, setTotalCosts] = useState<ProviderCosts>({
    aws: 0,
    azure: 0,
    gcp: 0,
  });

  const fetchComparisonData = async () => {
    try {
      const response = await fetch('/api/v1/comparisons/providers', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          start_date: startDate.toISOString(),
          end_date: endDate.toISOString(),
          service: selectedService === 'all' ? undefined : selectedService,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to fetch comparison data');
      }

      const data = await response.json();
      setComparisons(data.comparisons);
      setTotalCosts(data.totals);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchComparisonData();
  }, [startDate, endDate, selectedService]);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  };

  const getChartData = () => {
    return [
      {
        name: 'AWS',
        cost: totalCosts.aws,
      },
      {
        name: 'Azure',
        cost: totalCosts.azure,
      },
      {
        name: 'GCP',
        cost: totalCosts.gcp,
      },
    ];
  };

  const handleExport = () => {
    if (onExport) {
      onExport({
        comparisons,
        totals: totalCosts,
        period: {
          start: startDate,
          end: endDate,
        },
      });
    }
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

  return (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h5" component="h2">
            Provider Cost Comparison
          </Typography>
          <Box display="flex" gap={2}>
            <FormControl sx={{ minWidth: 200 }}>
              <InputLabel>Service</InputLabel>
              <Select
                value={selectedService}
                label="Service"
                onChange={(e) => setSelectedService(e.target.value)}
              >
                <MenuItem value="all">All Services</MenuItem>
                {comparisons.map((comparison) => (
                  <MenuItem key={comparison.service} value={comparison.service}>
                    {comparison.service}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <Button
              variant="contained"
              startIcon={<CompareArrowsIcon />}
              onClick={handleExport}
            >
              Export Comparison
            </Button>
          </Box>
        </Box>
      </Grid>

      <Grid item xs={12}>
        <Card sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Total Cost by Provider
          </Typography>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={getChartData()}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip formatter={(value) => formatCurrency(value as number)} />
              <Legend />
              <Bar dataKey="cost" fill="#8884d8" name="Cost" />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </Grid>

      <Grid item xs={12}>
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Service</TableCell>
                <TableCell align="right">AWS</TableCell>
                <TableCell align="right">Azure</TableCell>
                <TableCell align="right">GCP</TableCell>
                <TableCell>Recommendation</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {comparisons.map((comparison) => (
                <TableRow key={comparison.service}>
                  <TableCell component="th" scope="row">
                    {comparison.service}
                  </TableCell>
                  <TableCell align="right">{formatCurrency(comparison.costs.aws)}</TableCell>
                  <TableCell align="right">{formatCurrency(comparison.costs.azure)}</TableCell>
                  <TableCell align="right">{formatCurrency(comparison.costs.gcp)}</TableCell>
                  <TableCell>{comparison.recommendation}</TableCell>
                </TableRow>
              ))}
              <TableRow sx={{ '& td': { fontWeight: 'bold' } }}>
                <TableCell>Total</TableCell>
                <TableCell align="right">{formatCurrency(totalCosts.aws)}</TableCell>
                <TableCell align="right">{formatCurrency(totalCosts.azure)}</TableCell>
                <TableCell align="right">{formatCurrency(totalCosts.gcp)}</TableCell>
                <TableCell />
              </TableRow>
            </TableBody>
          </Table>
        </TableContainer>
      </Grid>
    </Grid>
  );
};

export default ProviderComparison;
