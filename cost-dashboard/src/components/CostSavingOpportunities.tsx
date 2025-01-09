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
} from '@mui/material';
import {
  SavingsOutlined,
  ExpandMore,
  TrendingUp,
  Warning,
  CheckCircle,
} from '@mui/icons-material';

interface SavingOpportunity {
  id: string;
  title: string;
  description: string;
  estimatedSavings: number;
  difficulty: 'easy' | 'medium' | 'complex';
  impact: 'high' | 'medium' | 'low';
  category: string;
  status: 'pending' | 'in_progress' | 'implemented';
  implementationSteps: string[];
  affectedResources: {
    id: string;
    name: string;
    type: string;
    currentCost: number;
    projectedCost: number;
  }[];
}

interface CostSavingOpportunitiesProps {
  startDate: Date;
  endDate: Date;
  onImplement?: (opportunity: SavingOpportunity) => Promise<void>;
}

const CostSavingOpportunities: React.FC<CostSavingOpportunitiesProps> = ({
  startDate,
  endDate,
  onImplement,
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [opportunities, setOpportunities] = useState<SavingOpportunity[]>([]);
  const [selectedOpportunity, setSelectedOpportunity] = useState<SavingOpportunity | null>(
    null
  );
  const [implementationDialogOpen, setImplementationDialogOpen] = useState(false);

  const fetchOpportunities = async () => {
    try {
      const response = await fetch('/api/v1/optimization/opportunities', {
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
        throw new Error('Failed to fetch optimization opportunities');
      }

      const data = await response.json();
      setOpportunities(data.opportunities);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOpportunities();
  }, [startDate, endDate]);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'easy':
        return 'success';
      case 'medium':
        return 'warning';
      case 'complex':
        return 'error';
      default:
        return 'default';
    }
  };

  const getImpactColor = (impact: string) => {
    switch (impact) {
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
        return <TrendingUp color="warning" />;
      default:
        return <Warning color="error" />;
    }
  };

  const handleImplement = async (opportunity: SavingOpportunity) => {
    if (onImplement) {
      try {
        await onImplement(opportunity);
        await fetchOpportunities(); // Refresh the list
        setImplementationDialogOpen(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to implement opportunity');
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

  const totalPotentialSavings = opportunities.reduce(
    (sum, opp) => sum + opp.estimatedSavings,
    0
  );

  return (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <Card sx={{ p: 2, mb: 3 }}>
          <Box display="flex" alignItems="center" gap={2}>
            <SavingsOutlined sx={{ fontSize: 40, color: 'success.main' }} />
            <Box>
              <Typography variant="h6">Total Potential Savings</Typography>
              <Typography variant="h4" color="success.main">
                {formatCurrency(totalPotentialSavings)}
              </Typography>
            </Box>
          </Box>
        </Card>
      </Grid>

      <Grid item xs={12}>
        <List>
          {opportunities.map((opportunity) => (
            <Accordion key={opportunity.id} sx={{ mb: 2 }}>
              <AccordionSummary expandIcon={<ExpandMore />}>
                <Grid container alignItems="center" spacing={2}>
                  <Grid item>
                    <ListItemIcon>{getStatusIcon(opportunity.status)}</ListItemIcon>
                  </Grid>
                  <Grid item xs>
                    <ListItemText
                      primary={opportunity.title}
                      secondary={`Estimated Savings: ${formatCurrency(
                        opportunity.estimatedSavings
                      )}`}
                    />
                  </Grid>
                  <Grid item>
                    <Box display="flex" gap={1}>
                      <Chip
                        label={`Difficulty: ${opportunity.difficulty}`}
                        color={getDifficultyColor(opportunity.difficulty)}
                        size="small"
                      />
                      <Chip
                        label={`Impact: ${opportunity.impact}`}
                        color={getImpactColor(opportunity.impact)}
                        size="small"
                      />
                    </Box>
                  </Grid>
                </Grid>
              </AccordionSummary>
              <AccordionDetails>
                <Box>
                  <Typography variant="body1" paragraph>
                    {opportunity.description}
                  </Typography>

                  <Typography variant="subtitle1" gutterBottom>
                    Implementation Steps:
                  </Typography>
                  <List>
                    {opportunity.implementationSteps.map((step, index) => (
                      <ListItem key={index}>
                        <ListItemText primary={`${index + 1}. ${step}`} />
                      </ListItem>
                    ))}
                  </List>

                  <Typography variant="subtitle1" gutterBottom>
                    Affected Resources:
                  </Typography>
                  <List>
                    {opportunity.affectedResources.map((resource) => (
                      <ListItem key={resource.id}>
                        <ListItemText
                          primary={resource.name}
                          secondary={`Current Cost: ${formatCurrency(
                            resource.currentCost
                          )} → Projected Cost: ${formatCurrency(resource.projectedCost)}`}
                        />
                      </ListItem>
                    ))}
                  </List>

                  {opportunity.status === 'pending' && (
                    <Box display="flex" justifyContent="flex-end" mt={2}>
                      <Button
                        variant="contained"
                        color="primary"
                        onClick={() => {
                          setSelectedOpportunity(opportunity);
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
        <DialogTitle>Implement Cost Saving Opportunity</DialogTitle>
        <DialogContent>
          {selectedOpportunity && (
            <Box>
              <Typography variant="h6" gutterBottom>
                {selectedOpportunity.title}
              </Typography>
              <Typography variant="body1" paragraph>
                Are you sure you want to implement this cost saving opportunity? This will:
              </Typography>
              <List>
                <ListItem>
                  <ListItemText
                    primary={`Save an estimated ${formatCurrency(
                      selectedOpportunity.estimatedSavings
                    )} per month`}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText primary="Modify the affected resources automatically" />
                </ListItem>
                <ListItem>
                  <ListItemText primary="Track the implementation progress" />
                </ListItem>
              </List>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setImplementationDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            color="primary"
            onClick={() => selectedOpportunity && handleImplement(selectedOpportunity)}
          >
            Confirm Implementation
          </Button>
        </DialogActions>
      </Dialog>
    </Grid>
  );
};

export default CostSavingOpportunities;
