import React, { useState, useEffect } from 'react';
import {
  Card,
  Grid,
  Typography,
  Box,
  CircularProgress,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Tabs,
  Tab,
  Paper,
} from '@mui/material';
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
  Cell,
} from 'recharts';
import AnalyticsIcon from '@mui/icons-material/Analytics';

interface CostData {
  date: string;
  amount: number;
  category: string;
  service: string;
}

interface CostBreakdown {
  byService: { [key: string]: number };
  byRegion: { [key: string]: number };
  byTag: { [key: string]: { [key: string]: number } };
  byTime: { [key: string]: number };
}

interface CostTrend {
  date: string;
  actual: number;
  projected: number;
}

interface CostAnalysisProps {
  startDate: Date;
  endDate: Date;
  onExport?: (data: any) => void;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

const CostAnalysis: React.FC<CostAnalysisProps> = ({
  startDate,
  endDate,
  onExport,
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [costData, setCostData] = useState<CostData[]>([]);
  const [breakdown, setBreakdown] = useState<CostBreakdown>({
    byService: {},
    byRegion: {},
    byTag: {},
    byTime: {},
  });
  const [trends, setTrends] = useState<CostTrend[]>([]);
  const [selectedView, setSelectedView] = useState<string>('overview');
  const [selectedTag, setSelectedTag] = useState<string>('all');
  const [tabValue, setTabValue] = useState(0);

  const fetchAnalysisData = async () => {
    try {
      const response = await fetch('/api/v1/costs/analysis', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          start_date: startDate.toISOString(),
          end_date: endDate.toISOString(),
          view: selectedView,
          tag: selectedTag === 'all' ? undefined : selectedTag,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to fetch cost analysis data');
      }

      const data = await response.json();
      setCostData(data.costs);
      setBreakdown(data.breakdown);
      setTrends(data.trends);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalysisData();
  }, [startDate, endDate, selectedView, selectedTag]);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  };

  const handleExport = () => {
    if (onExport) {
      onExport({
        costs: costData,
        breakdown,
        trends,
        period: {
          start: startDate,
          end: endDate,
        },
        filters: {
          view: selectedView,
          tag: selectedTag,
        },
      });
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
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
            Cost Analysis
          </Typography>
          <Box display="flex" gap={2}>
            <FormControl sx={{ minWidth: 200 }}>
              <InputLabel>View</InputLabel>
              <Select
                value={selectedView}
                label="View"
                onChange={(e) => setSelectedView(e.target.value)}
              >
                <MenuItem value="overview">Overview</MenuItem>
                <MenuItem value="detailed">Detailed</MenuItem>
                <MenuItem value="trends">Trends</MenuItem>
              </Select>
            </FormControl>
            <FormControl sx={{ minWidth: 200 }}>
              <InputLabel>Tag</InputLabel>
              <Select
                value={selectedTag}
                label="Tag"
                onChange={(e) => setSelectedTag(e.target.value)}
              >
                <MenuItem value="all">All Tags</MenuItem>
                {Object.keys(breakdown.byTag).map((tag) => (
                  <MenuItem key={tag} value={tag}>
                    {tag}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <Button
              variant="contained"
              startIcon={<AnalyticsIcon />}
              onClick={handleExport}
            >
              Export Analysis
            </Button>
          </Box>
        </Box>
      </Grid>

      <Grid item xs={12}>
        <Paper sx={{ width: '100%', bgcolor: 'background.paper' }}>
          <Tabs
            value={tabValue}
            onChange={handleTabChange}
            indicatorColor="primary"
            textColor="primary"
            centered
          >
            <Tab label="Cost Distribution" />
            <Tab label="Time Analysis" />
            <Tab label="Cost Trends" />
          </Tabs>
        </Paper>
      </Grid>

      <Grid item xs={12}>
        {tabValue === 0 && (
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Cost by Service
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={Object.entries(breakdown.byService).map(([name, value]) => ({
                        name,
                        value,
                      }))}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      label={({ name, percent }) =>
                        `${name} (${(percent * 100).toFixed(0)}%)`
                      }
                    >
                      {Object.entries(breakdown.byService).map((entry, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={COLORS[index % COLORS.length]}
                        />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value) => formatCurrency(value as number)} />
                  </PieChart>
                </ResponsiveContainer>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Cost by Region
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart
                    data={Object.entries(breakdown.byRegion).map(([name, value]) => ({
                      name,
                      value,
                    }))}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip formatter={(value) => formatCurrency(value as number)} />
                    <Bar dataKey="value" fill="#8884d8" />
                  </BarChart>
                </ResponsiveContainer>
              </Card>
            </Grid>
          </Grid>
        )}

        {tabValue === 1 && (
          <Card sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Daily Cost Distribution
            </Typography>
            <ResponsiveContainer width="100%" height={400}>
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
                  name="Cost"
                />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        )}

        {tabValue === 2 && (
          <Card sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Cost Trends and Projections
            </Typography>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={trends}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip formatter={(value) => formatCurrency(value as number)} />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="actual"
                  stroke="#8884d8"
                  name="Actual Cost"
                />
                <Line
                  type="monotone"
                  dataKey="projected"
                  stroke="#82ca9d"
                  name="Projected Cost"
                  strokeDasharray="5 5"
                />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        )}
      </Grid>
    </Grid>
  );
};

export default CostAnalysis;
