import React, { useState, useEffect } from 'react';
import {
  Card,
  Grid,
  Typography,
  Box,
  CircularProgress,
  Alert,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Tabs,
  Tab,
  Paper,
} from '@mui/material';
import {
  TrendingUp,
  ExpandMore,
  Settings,
  Storage,
  Memory,
  CloudQueue,
  CheckCircle,
  Warning,
  ErrorOutline,
} from '@mui/icons-material';

interface ResourceConfig {
  current: {
    size: string;
    type: string;
    settings: Record<string, any>;
  };
  recommended: {
    size: string;
    type: string;
    settings: Record<string, any>;
  };
}

interface OptimizationMetrics {
  costSavings: number;
  performanceImprovement: number;
  utilizationImprovement: number;
  reliabilityScore: number;
}

interface ResourceOptimizationItem {
  id: string;
  resourceId: string;
  resourceName: string;
  resourceType: string;
  provider: string;
  region: string;
  category: 'sizing' | 'configuration' | 'replacement';
  priority: 'high' | 'medium' | 'low';
  status: 'pending' | 'in_progress' | 'implemented';
  description: string;
  rationale: string;
  configuration: ResourceConfig;
  metrics: OptimizationMetrics;
  implementationSteps: string[];
  risks: string[];
  dependencies: string[];
}

interface ResourceOptimizationProps {
  startDate: Date;
  endDate: Date;
  onImplement?: (optimization: ResourceOptimizationItem) => Promise<void>;
}

const ResourceOptimization: React.FC<ResourceOptimizationProps> = ({
  startDate,
  endDate,
  onImplement,
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [optimizations, setOptimizations] = useState<ResourceOptimizationItem[]>([]);
  const [selectedOptimization, setSelectedOptimization] = useState<ResourceOptimizationItem | null>(
    null
  );
  const [implementationDialogOpen, setImplementationDialogOpen] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [tabValue, setTabValue] = useState<'all' | 'sizing' | 'configuration' | 'replacement'>('all');

  const fetchOptimizations = async () => {
    try {
      const response = await fetch('/api/v1/optimization/resources', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          start_date: startDate.toISOString(),
          end_date: endDate.toISOString(),
          category: selectedCategory === 'all' ? undefined : selectedCategory,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to fetch resource optimizations');
      }

      const data = await response.json();
      setOptimizations(data.optimizations);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOptimizations();
  }, [startDate, endDate, selectedCategory]);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  };

  const formatPercentage = (value: number) => {
    return `${(value * 100).toFixed(1)}%`;
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'sizing':
        return <Memory />;
      case 'configuration':
        return <Settings />;
      case 'replacement':
        return <CloudQueue />;
      default:
        return <Storage />;
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'error';
      case 'medium':
        return 'warning';
      case 'low':
        return 'success';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'implemented':
        return <CheckCircle color="success" />;
      case 'in_progress':
        return <Warning color="warning" />;
      default:
        return <ErrorOutline color="error" />;
    }
  };

  const handleImplement = async (optimization: ResourceOptimizationItem) => {
    if (onImplement) {
      try {
        await onImplement(optimization);
        await fetchOptimizations(); // Refresh the list
        setImplementationDialogOpen(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to implement optimization');
      }
    }
  };

  const handleTabChange = (
    event: React.SyntheticEvent,
    newValue: 'all' | 'sizing' | 'configuration' | 'replacement'
  ) => {
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

  const totalSavings = optimizations.reduce(
    (sum, opt) => sum + opt.metrics.costSavings,
    0
  );

  return (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <Card sx={{ p: 2, mb: 3 }}>
          <Box display="flex" alignItems="center" gap={2}>
            <TrendingUp sx={{ fontSize: 40, color: 'success.main' }} />
            <Box>
              <Typography variant="h6">Resource Optimizations</Typography>
              <Typography variant="h4" color="success.main">
                {formatCurrency(totalSavings)} potential savings
              </Typography>
            </Box>
          </Box>
        </Card>
      </Grid>

      <Grid item xs={12}>
        <Paper sx={{ width: '100%', mb: 2 }}>
          <Tabs
            value={tabValue}
            onChange={handleTabChange}
            indicatorColor="primary"
            textColor="primary"
            centered
          >
            <Tab label="All" value="all" />
            <Tab label="Sizing" value="sizing" />
            <Tab label="Configuration" value="configuration" />
            <Tab label="Replacement" value="replacement" />
          </Tabs>
        </Paper>
      </Grid>

      <Grid item xs={12}>
        <List>
          {optimizations
            .filter(
              (opt) => tabValue === 'all' || opt.category === tabValue
            )
            .map((optimization) => (
              <Accordion key={optimization.id} sx={{ mb: 2 }}>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Grid container alignItems="center" spacing={2}>
                    <Grid item>
                      <ListItemIcon>{getCategoryIcon(optimization.category)}</ListItemIcon>
                    </Grid>
                    <Grid item xs>
                      <ListItemText
                        primary={optimization.resourceName}
                        secondary={`${optimization.resourceType} - ${optimization.provider}`}
                      />
                    </Grid>
                    <Grid item>
                      <Box display="flex" gap={1}>
                        <Chip
                          label={formatCurrency(optimization.metrics.costSavings)}
                          color="success"
                          size="small"
                        />
                        <Chip
                          label={`Priority: ${optimization.priority}`}
                          color={getPriorityColor(optimization.priority)}
                          size="small"
                        />
                        {getStatusIcon(optimization.status)}
                      </Box>
                    </Grid>
                  </Grid>
                </AccordionSummary>
                <AccordionDetails>
                  <Box>
                    <Typography variant="body1" paragraph>
                      {optimization.description}
                    </Typography>

                    <Typography variant="subtitle1" gutterBottom>
                      Rationale:
                    </Typography>
                    <Typography variant="body2" paragraph>
                      {optimization.rationale}
                    </Typography>

                    <Grid container spacing={2} sx={{ mb: 2 }}>
                      <Grid item xs={6}>
                        <Typography variant="subtitle1" gutterBottom>
                          Current Configuration:
                        </Typography>
                        <List dense>
                          <ListItem>
                            <ListItemText
                              primary="Size"
                              secondary={optimization.configuration.current.size}
                            />
                          </ListItem>
                          <ListItem>
                            <ListItemText
                              primary="Type"
                              secondary={optimization.configuration.current.type}
                            />
                          </ListItem>
                        </List>
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="subtitle1" gutterBottom>
                          Recommended Configuration:
                        </Typography>
                        <List dense>
                          <ListItem>
                            <ListItemText
                              primary="Size"
                              secondary={optimization.configuration.recommended.size}
                            />
                          </ListItem>
                          <ListItem>
                            <ListItemText
                              primary="Type"
                              secondary={optimization.configuration.recommended.type}
                            />
                          </ListItem>
                        </List>
                      </Grid>
                    </Grid>

                    <Typography variant="subtitle1" gutterBottom>
                      Expected Improvements:
                    </Typography>
                    <Grid container spacing={2} sx={{ mb: 2 }}>
                      <Grid item xs={3}>
                        <Typography variant="body2">Cost Savings</Typography>
                        <Typography variant="h6" color="success.main">
                          {formatCurrency(optimization.metrics.costSavings)}
                        </Typography>
                      </Grid>
                      <Grid item xs={3}>
                        <Typography variant="body2">Performance</Typography>
                        <Typography variant="h6" color="primary.main">
                          {formatPercentage(optimization.metrics.performanceImprovement)}
                        </Typography>
                      </Grid>
                      <Grid item xs={3}>
                        <Typography variant="body2">Utilization</Typography>
                        <Typography variant="h6" color="info.main">
                          {formatPercentage(optimization.metrics.utilizationImprovement)}
                        </Typography>
                      </Grid>
                      <Grid item xs={3}>
                        <Typography variant="body2">Reliability Score</Typography>
                        <Typography variant="h6">
                          {optimization.metrics.reliabilityScore.toFixed(1)}/10
                        </Typography>
                      </Grid>
                    </Grid>

                    {optimization.status === 'pending' && (
                      <Box display="flex" justifyContent="flex-end" mt={2}>
                        <Button
                          variant="contained"
                          color="primary"
                          onClick={() => {
                            setSelectedOptimization(optimization);
                            setImplementationDialogOpen(true);
                          }}
                        >
                          Implement
                        </Button>
                      </Box>
                    )}
                  </Box>
                </AccordionDetails>
              </Accordion>
            ))}
        </List>
      </Grid>

      <Dialog
        open={implementationDialogOpen}
        onClose={() => setImplementationDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Implement Resource Optimization</DialogTitle>
        <DialogContent>
          {selectedOptimization && (
            <Box>
              <Typography variant="h6" gutterBottom>
                {selectedOptimization.resourceName}
              </Typography>
              <Typography variant="body1" paragraph>
                Are you sure you want to implement this optimization? This will:
              </Typography>
              <List>
                <ListItem>
                  <ListItemText
                    primary={`Save ${formatCurrency(selectedOptimization.metrics.costSavings)} per month`}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary={`Improve performance by ${formatPercentage(
                      selectedOptimization.metrics.performanceImprovement
                    )}`}
                  />
                </ListItem>
                {selectedOptimization.risks.length > 0 && (
                  <ListItem>
                    <ListItemText
                      primary="Potential Risks:"
                      secondary={selectedOptimization.risks.join(', ')}
                    />
                  </ListItem>
                )}
              </List>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setImplementationDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            color="primary"
            onClick={() => selectedOptimization && handleImplement(selectedOptimization)}
          >
            Confirm Implementation
          </Button>
        </DialogActions>
      </Dialog>
    </Grid>
  );
};

export default ResourceOptimization;
