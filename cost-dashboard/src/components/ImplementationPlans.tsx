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
  Stepper,
  Step,
  StepLabel,
  StepContent,
  LinearProgress,
} from '@mui/material';
import {
  PlaylistAddCheck,
  ExpandMore,
  Schedule,
  Assignment,
  CheckCircle,
  Warning,
  ErrorOutline,
  ArrowForward,
} from '@mui/icons-material';

interface ImplementationStep {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  estimatedDuration: number; // in minutes
  dependencies: string[];
  assignee?: string;
  startedAt?: string;
  completedAt?: string;
  notes?: string[];
}

interface ImplementationPlan {
  id: string;
  title: string;
  description: string;
  category: 'cost' | 'performance' | 'resource';
  priority: 'high' | 'medium' | 'low';
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  estimatedSavings: number;
  estimatedEffort: number; // in person-hours
  risks: {
    description: string;
    severity: 'high' | 'medium' | 'low';
    mitigation: string;
  }[];
  steps: ImplementationStep[];
  startDate?: string;
  dueDate?: string;
  assignedTeam?: string;
  progress: number;
}

interface ImplementationPlansProps {
  startDate: Date;
  endDate: Date;
  onUpdateStep?: (planId: string, stepId: string, status: string) => Promise<void>;
}

const ImplementationPlans: React.FC<ImplementationPlansProps> = ({
  startDate,
  endDate,
  onUpdateStep,
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [plans, setPlans] = useState<ImplementationPlan[]>([]);
  const [selectedPlan, setSelectedPlan] = useState<ImplementationPlan | null>(null);
  const [updateDialogOpen, setUpdateDialogOpen] = useState(false);
  const [selectedStep, setSelectedStep] = useState<ImplementationStep | null>(null);

  const fetchPlans = async () => {
    try {
      const response = await fetch('/api/v1/optimization/implementation-plans', {
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
        throw new Error('Failed to fetch implementation plans');
      }

      const data = await response.json();
      setPlans(data.plans);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPlans();
  }, [startDate, endDate]);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  };

  const formatDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    return `${hours}h ${remainingMinutes}m`;
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
      case 'completed':
        return <CheckCircle color="success" />;
      case 'in_progress':
        return <Warning color="warning" />;
      case 'failed':
        return <ErrorOutline color="error" />;
      default:
        return <Schedule color="disabled" />;
    }
  };

  const handleUpdateStep = async (status: string) => {
    if (selectedPlan && selectedStep && onUpdateStep) {
      try {
        await onUpdateStep(selectedPlan.id, selectedStep.id, status);
        await fetchPlans(); // Refresh the list
        setUpdateDialogOpen(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to update step');
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

  const totalSavings = plans.reduce((sum, plan) => sum + plan.estimatedSavings, 0);

  return (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <Card sx={{ p: 2, mb: 3 }}>
          <Box display="flex" alignItems="center" gap={2}>
            <PlaylistAddCheck sx={{ fontSize: 40, color: 'primary.main' }} />
            <Box>
              <Typography variant="h6">Implementation Plans</Typography>
              <Typography variant="h4" color="success.main">
                {formatCurrency(totalSavings)} potential savings
              </Typography>
            </Box>
          </Box>
        </Card>
      </Grid>

      <Grid item xs={12}>
        <List>
          {plans.map((plan) => (
            <Accordion key={plan.id} sx={{ mb: 2 }}>
              <AccordionSummary expandIcon={<ExpandMore />}>
                <Grid container alignItems="center" spacing={2}>
                  <Grid item>
                    <ListItemIcon>{getStatusIcon(plan.status)}</ListItemIcon>
                  </Grid>
                  <Grid item xs>
                    <ListItemText
                      primary={plan.title}
                      secondary={`Estimated Effort: ${plan.estimatedEffort} hours`}
                    />
                  </Grid>
                  <Grid item>
                    <Box display="flex" gap={1}>
                      <Chip
                        label={formatCurrency(plan.estimatedSavings)}
                        color="success"
                        size="small"
                      />
                      <Chip
                        label={`Priority: ${plan.priority}`}
                        color={getPriorityColor(plan.priority)}
                        size="small"
                      />
                      <LinearProgress
                        variant="determinate"
                        value={plan.progress}
                        sx={{ width: 100, alignSelf: 'center' }}
                      />
                    </Box>
                  </Grid>
                </Grid>
              </AccordionSummary>
              <AccordionDetails>
                <Box>
                  <Typography variant="body1" paragraph>
                    {plan.description}
                  </Typography>

                  {plan.risks.length > 0 && (
                    <>
                      <Typography variant="subtitle1" gutterBottom>
                        Risks and Mitigations:
                      </Typography>
                      <List>
                        {plan.risks.map((risk, index) => (
                          <ListItem key={index}>
                            <ListItemText
                              primary={
                                <Box display="flex" alignItems="center" gap={1}>
                                  <Typography variant="body1">{risk.description}</Typography>
                                  <Chip
                                    label={risk.severity}
                                    color={getPriorityColor(risk.severity)}
                                    size="small"
                                  />
                                </Box>
                              }
                              secondary={`Mitigation: ${risk.mitigation}`}
                            />
                          </ListItem>
                        ))}
                      </List>
                    </>
                  )}

                  <Typography variant="subtitle1" gutterBottom sx={{ mt: 2 }}>
                    Implementation Steps:
                  </Typography>
                  <Stepper orientation="vertical">
                    {plan.steps.map((step) => (
                      <Step key={step.id} active={step.status !== 'pending'}>
                        <StepLabel
                          optional={
                            <Typography variant="caption">
                              {formatDuration(step.estimatedDuration)}
                            </Typography>
                          }
                          icon={getStatusIcon(step.status)}
                        >
                          {step.title}
                        </StepLabel>
                        <StepContent>
                          <Typography>{step.description}</Typography>
                          {step.status === 'pending' && (
                            <Box sx={{ mt: 2 }}>
                              <Button
                                variant="contained"
                                onClick={() => {
                                  setSelectedPlan(plan);
                                  setSelectedStep(step);
                                  setUpdateDialogOpen(true);
                                }}
                                endIcon={<ArrowForward />}
                              >
                                Start Step
                              </Button>
                            </Box>
                          )}
                        </StepContent>
                      </Step>
                    ))}
                  </Stepper>
                </Box>
              </AccordionDetails>
            </Accordion>
          ))}
        </List>
      </Grid>

      <Dialog
        open={updateDialogOpen}
        onClose={() => setUpdateDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Update Implementation Step</DialogTitle>
        <DialogContent>
          {selectedStep && (
            <Box>
              <Typography variant="h6" gutterBottom>
                {selectedStep.title}
              </Typography>
              <Typography variant="body1" paragraph>
                {selectedStep.description}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Estimated duration: {formatDuration(selectedStep.estimatedDuration)}
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUpdateDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            color="primary"
            onClick={() => handleUpdateStep('in_progress')}
          >
            Start Implementation
          </Button>
        </DialogActions>
      </Dialog>
    </Grid>
  );
};

export default ImplementationPlans;
