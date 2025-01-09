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
  LinearProgress,
} from '@mui/material';
import {
  Speed,
  ExpandMore,
  Memory,
  Storage,
  NetworkCheck,
  CheckCircle,
  Warning,
  ErrorOutline,
} from '@mui/icons-material';

interface ResourceMetrics {
  cpu: {
    utilization: number;
    throttling: number;
  };
  memory: {
    utilization: number;
    swapUsage: number;
  };
  disk: {
    iops: number;
    latency: number;
    throughput: number;
  };
  network: {
    throughput: number;
    latency: number;
    packetLoss: number;
  };
}

interface PerformanceImprovement {
  id: string;
  title: string;
  description: string;
  category: 'compute' | 'memory' | 'storage' | 'network';
  priority: 'high' | 'medium' | 'low';
  status: 'pending' | 'in_progress' | 'implemented';
  impact: {
    performance: number;
    reliability: number;
    cost: number;
  };
  affectedResources: {
    id: string;
    name: string;
    type: string;
    currentMetrics: ResourceMetrics;
    projectedMetrics: ResourceMetrics;
  }[];
  implementationSteps: string[];
  risks: string[];
  prerequisites: string[];
}

interface PerformanceImprovementsProps {
  startDate: Date;
  endDate: Date;
  onImplement?: (improvement: PerformanceImprovement) => Promise<void>;
}

const PerformanceImprovements: React.FC<PerformanceImprovementsProps> = ({
  startDate,
  endDate,
  onImplement,
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [improvements, setImprovements] = useState<PerformanceImprovement[]>([]);
  const [selectedImprovement, setSelectedImprovement] = useState<PerformanceImprovement | null>(
    null
  );
  const [implementationDialogOpen, setImplementationDialogOpen] = useState(false);

  const fetchImprovements = async () => {
    try {
      const response = await fetch('/api/v1/optimization/performance', {
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
        throw new Error('Failed to fetch performance improvements');
      }

      const data = await response.json();
      setImprovements(data.improvements);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchImprovements();
  }, [startDate, endDate]);

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'compute':
        return <Memory />;
      case 'storage':
        return <Storage />;
      case 'network':
        return <NetworkCheck />;
      default:
        return <Speed />;
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

  const formatPercentage = (value: number) => {
    return `${(value * 100).toFixed(1)}%`;
  };

  const handleImplement = async (improvement: PerformanceImprovement) => {
    if (onImplement) {
      try {
        await onImplement(improvement);
        await fetchImprovements(); // Refresh the list
        setImplementationDialogOpen(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to implement improvement');
      }
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
        <Card sx={{ p: 2, mb: 3 }}>
          <Box display="flex" alignItems="center" gap={2}>
            <Speed sx={{ fontSize: 40, color: 'primary.main' }} />
            <Box>
              <Typography variant="h6">Performance Improvements</Typography>
              <Typography variant="subtitle1" color="text.secondary">
                {improvements.length} opportunities identified
              </Typography>
            </Box>
          </Box>
        </Card>
      </Grid>

      <Grid item xs={12}>
        <List>
          {improvements.map((improvement) => (
            <Accordion key={improvement.id} sx={{ mb: 2 }}>
              <AccordionSummary expandIcon={<ExpandMore />}>
                <Grid container alignItems="center" spacing={2}>
                  <Grid item>
                    <ListItemIcon>{getCategoryIcon(improvement.category)}</ListItemIcon>
                  </Grid>
                  <Grid item xs>
                    <ListItemText
                      primary={improvement.title}
                      secondary={`Category: ${improvement.category}`}
                    />
                  </Grid>
                  <Grid item>
                    <Box display="flex" gap={1}>
                      <Chip
                        label={`Priority: ${improvement.priority}`}
                        color={getPriorityColor(improvement.priority)}
                        size="small"
                      />
                      {getStatusIcon(improvement.status)}
                    </Box>
                  </Grid>
                </Grid>
              </AccordionSummary>
              <AccordionDetails>
                <Box>
                  <Typography variant="body1" paragraph>
                    {improvement.description}
                  </Typography>

                  <Typography variant="subtitle1" gutterBottom>
                    Impact:
                  </Typography>
                  <Grid container spacing={2} sx={{ mb: 2 }}>
                    <Grid item xs={4}>
                      <Typography variant="body2">Performance</Typography>
                      <LinearProgress
                        variant="determinate"
                        value={improvement.impact.performance * 100}
                        color="primary"
                        sx={{ mt: 1 }}
                      />
                      <Typography variant="caption">
                        {formatPercentage(improvement.impact.performance)} improvement
                      </Typography>
                    </Grid>
                    <Grid item xs={4}>
                      <Typography variant="body2">Reliability</Typography>
                      <LinearProgress
                        variant="determinate"
                        value={improvement.impact.reliability * 100}
                        color="success"
                        sx={{ mt: 1 }}
                      />
                      <Typography variant="caption">
                        {formatPercentage(improvement.impact.reliability)} improvement
                      </Typography>
                    </Grid>
                    <Grid item xs={4}>
                      <Typography variant="body2">Cost Efficiency</Typography>
                      <LinearProgress
                        variant="determinate"
                        value={improvement.impact.cost * 100}
                        color="warning"
                        sx={{ mt: 1 }}
                      />
                      <Typography variant="caption">
                        {formatPercentage(improvement.impact.cost)} improvement
                      </Typography>
                    </Grid>
                  </Grid>

                  <Typography variant="subtitle1" gutterBottom>
                    Implementation Steps:
                  </Typography>
                  <List>
                    {improvement.implementationSteps.map((step, index) => (
                      <ListItem key={index}>
                        <ListItemText primary={`${index + 1}. ${step}`} />
                      </ListItem>
                    ))}
                  </List>

                  <Typography variant="subtitle1" gutterBottom>
                    Affected Resources:
                  </Typography>
                  <List>
                    {improvement.affectedResources.map((resource) => (
                      <ListItem key={resource.id}>
                        <ListItemText
                          primary={resource.name}
                          secondary={
                            <Box>
                              <Typography variant="body2">
                                Current CPU Utilization:{' '}
                                {formatPercentage(resource.currentMetrics.cpu.utilization)}
                              </Typography>
                              <Typography variant="body2">
                                Projected CPU Utilization:{' '}
                                {formatPercentage(resource.projectedMetrics.cpu.utilization)}
                              </Typography>
                            </Box>
                          }
                        />
                      </ListItem>
                    ))}
                  </List>

                  {improvement.risks.length > 0 && (
                    <>
                      <Typography variant="subtitle1" gutterBottom>
                        Risks:
                      </Typography>
                      <List>
                        {improvement.risks.map((risk, index) => (
                          <ListItem key={index}>
                            <ListItemText primary={risk} />
                          </ListItem>
                        ))}
                      </List>
                    </>
                  )}

                  {improvement.status === 'pending' && (
                    <Box display="flex" justifyContent="flex-end" mt={2}>
                      <Button
                        variant="contained"
                        color="primary"
                        onClick={() => {
                          setSelectedImprovement(improvement);
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
        <DialogTitle>Implement Performance Improvement</DialogTitle>
        <DialogContent>
          {selectedImprovement && (
            <Box>
              <Typography variant="h6" gutterBottom>
                {selectedImprovement.title}
              </Typography>
              <Typography variant="body1" paragraph>
                Are you sure you want to implement this performance improvement? This will:
              </Typography>
              <List>
                <ListItem>
                  <ListItemText
                    primary={`Improve performance by ${formatPercentage(
                      selectedImprovement.impact.performance
                    )}`}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary={`Affect ${selectedImprovement.affectedResources.length} resources`}
                  />
                </ListItem>
                {selectedImprovement.prerequisites.length > 0 && (
                  <ListItem>
                    <ListItemText
                      primary="Prerequisites:"
                      secondary={selectedImprovement.prerequisites.join(', ')}
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
            onClick={() => selectedImprovement && handleImplement(selectedImprovement)}
          >
            Confirm Implementation
          </Button>
        </DialogActions>
      </Dialog>
    </Grid>
  );
};

export default PerformanceImprovements;
