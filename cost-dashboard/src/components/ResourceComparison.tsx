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
  Chip,
} from '@mui/material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import CompareArrowsIcon from '@mui/icons-material/CompareArrows';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';

interface ResourceMetrics {
  cost: number;
  usage: number;
  efficiency: number;
  utilization: number;
}

interface ResourceData {
  id: string;
  name: string;
  type: string;
  provider: string;
  region: string;
  metrics: ResourceMetrics;
  historicalData: {
    date: string;
    cost: number;
    usage: number;
  }[];
}

interface ResourceComparisonProps {
  startDate: Date;
  endDate: Date;
  onExport?: (data: any) => void;
}

const ResourceComparison: React.FC<ResourceComparisonProps> = ({
  startDate,
  endDate,
  onExport,
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [resources, setResources] = useState<ResourceData[]>([]);
  const [selectedType, setSelectedType] = useState<string>('all');
  const [selectedMetric, setSelectedMetric] = useState<keyof ResourceMetrics>('cost');

  const fetchResourceData = async () => {
    try {
      const response = await fetch('/api/v1/resources/comparison', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          start_date: startDate.toISOString(),
          end_date: endDate.toISOString(),
          type: selectedType === 'all' ? undefined : selectedType,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to fetch resource data');
      }

      const data = await response.json();
      setResources(data.resources);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchResourceData();
  }, [startDate, endDate, selectedType]);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  };

  const formatPercentage = (value: number) => {
    return `${(value * 100).toFixed(1)}%`;
  };

  const formatMetricValue = (metric: keyof ResourceMetrics, value: number) => {
    switch (metric) {
      case 'cost':
        return formatCurrency(value);
      case 'efficiency':
      case 'utilization':
        return formatPercentage(value);
      default:
        return value.toFixed(2);
    }
  };

  const getMetricLabel = (metric: keyof ResourceMetrics) => {
    switch (metric) {
      case 'cost':
        return 'Cost';
      case 'usage':
        return 'Usage';
      case 'efficiency':
        return 'Efficiency';
      case 'utilization':
        return 'Utilization';
      default:
        return metric;
    }
  };

  const getEfficiencyColor = (value: number) => {
    if (value >= 0.8) return 'success';
    if (value >= 0.6) return 'warning';
    return 'error';
  };

  const handleExport = () => {
    if (onExport) {
      onExport({
        resources,
        period: {
          start: startDate,
          end: endDate,
        },
        filters: {
          type: selectedType,
          metric: selectedMetric,
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
            Resource Comparison
          </Typography>
          <Box display="flex" gap={2}>
            <FormControl sx={{ minWidth: 200 }}>
              <InputLabel>Resource Type</InputLabel>
              <Select
                value={selectedType}
                label="Resource Type"
                onChange={(e) => setSelectedType(e.target.value)}
              >
                <MenuItem value="all">All Types</MenuItem>
                <MenuItem value="compute">Compute</MenuItem>
                <MenuItem value="storage">Storage</MenuItem>
                <MenuItem value="network">Network</MenuItem>
                <MenuItem value="database">Database</MenuItem>
              </Select>
            </FormControl>
            <FormControl sx={{ minWidth: 200 }}>
              <InputLabel>Metric</InputLabel>
              <Select
                value={selectedMetric}
                label="Metric"
                onChange={(e) => setSelectedMetric(e.target.value as keyof ResourceMetrics)}
              >
                <MenuItem value="cost">Cost</MenuItem>
                <MenuItem value="usage">Usage</MenuItem>
                <MenuItem value="efficiency">Efficiency</MenuItem>
                <MenuItem value="utilization">Utilization</MenuItem>
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
            {getMetricLabel(selectedMetric)} Trend
          </Typography>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="date"
                type="category"
                allowDuplicatedCategory={false}
              />
              <YAxis />
              <Tooltip
                formatter={(value) =>
                  formatMetricValue(selectedMetric, value as number)
                }
              />
              <Legend />
              {resources.map((resource) => (
                <Line
                  key={resource.id}
                  data={resource.historicalData}
                  name={resource.name}
                  dataKey={selectedMetric}
                  stroke={`#${Math.floor(Math.random()*16777215).toString(16)}`}
                  dot={false}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </Card>
      </Grid>

      <Grid item xs={12}>
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Resource</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Provider</TableCell>
                <TableCell>Region</TableCell>
                <TableCell align="right">Cost</TableCell>
                <TableCell align="right">Usage</TableCell>
                <TableCell align="right">Efficiency</TableCell>
                <TableCell align="right">Utilization</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {resources.map((resource) => (
                <TableRow key={resource.id}>
                  <TableCell>{resource.name}</TableCell>
                  <TableCell>{resource.type}</TableCell>
                  <TableCell>{resource.provider}</TableCell>
                  <TableCell>{resource.region}</TableCell>
                  <TableCell align="right">
                    {formatCurrency(resource.metrics.cost)}
                  </TableCell>
                  <TableCell align="right">
                    {resource.metrics.usage.toFixed(2)}
                  </TableCell>
                  <TableCell align="right">
                    <Chip
                      icon={
                        resource.metrics.efficiency >= 0.7 ? (
                          <TrendingUpIcon />
                        ) : (
                          <TrendingDownIcon />
                        )
                      }
                      label={formatPercentage(resource.metrics.efficiency)}
                      color={getEfficiencyColor(resource.metrics.efficiency)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell align="right">
                    {formatPercentage(resource.metrics.utilization)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Grid>
    </Grid>
  );
};

export default ResourceComparison;
