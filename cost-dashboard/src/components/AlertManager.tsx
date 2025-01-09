import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  List,
  ListItem,
  ListItemSecondaryAction,
  ListItemText,
  TextField,
  Typography,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';

interface Alert {
  id: string;
  name: string;
  type: 'budget' | 'trend' | 'anomaly';
  threshold: number;
  frequency: 'daily' | 'weekly' | 'monthly';
  target: string;
  enabled: boolean;
}

interface AlertManagerProps {
  onAlertChange?: (alerts: Alert[]) => void;
}

const AlertManager: React.FC<AlertManagerProps> = ({ onAlertChange }) => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [openDialog, setOpenDialog] = useState(false);
  const [newAlert, setNewAlert] = useState<Partial<Alert>>({
    type: 'budget',
    frequency: 'daily',
    enabled: true,
  });

  useEffect(() => {
    // Fetch existing alerts
    fetchAlerts();
  }, []);

  const fetchAlerts = async () => {
    try {
      const response = await fetch('/api/v1/alerts', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      if (!response.ok) throw new Error('Failed to fetch alerts');
      const data = await response.json();
      setAlerts(data);
      onAlertChange?.(data);
    } catch (error) {
      console.error('Error fetching alerts:', error);
    }
  };

  const handleCreateAlert = async () => {
    try {
      const response = await fetch('/api/v1/alerts', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newAlert),
      });
      if (!response.ok) throw new Error('Failed to create alert');
      await fetchAlerts();
      setOpenDialog(false);
      setNewAlert({
        type: 'budget',
        frequency: 'daily',
        enabled: true,
      });
    } catch (error) {
      console.error('Error creating alert:', error);
    }
  };

  const handleDeleteAlert = async (id: string) => {
    try {
      const response = await fetch(`/api/v1/alerts/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      if (!response.ok) throw new Error('Failed to delete alert');
      await fetchAlerts();
    } catch (error) {
      console.error('Error deleting alert:', error);
    }
  };

  return (
    <Card sx={{ p: 2 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h6">Cost Alerts</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setOpenDialog(true)}
        >
          Create Alert
        </Button>
      </Box>

      <List>
        {alerts.map((alert) => (
          <ListItem key={alert.id}>
            <ListItemText
              primary={alert.name}
              secondary={`${alert.type} alert - ${alert.threshold} USD - ${alert.frequency}`}
            />
            <ListItemSecondaryAction>
              <IconButton
                edge="end"
                aria-label="delete"
                onClick={() => handleDeleteAlert(alert.id)}
              >
                <DeleteIcon />
              </IconButton>
            </ListItemSecondaryAction>
          </ListItem>
        ))}
      </List>

      <Dialog open={openDialog} onClose={() => setOpenDialog(false)}>
        <DialogTitle>Create New Alert</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <TextField
              fullWidth
              label="Alert Name"
              value={newAlert.name || ''}
              onChange={(e) => setNewAlert({ ...newAlert, name: e.target.value })}
              sx={{ mb: 2 }}
            />

            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Alert Type</InputLabel>
              <Select
                value={newAlert.type || 'budget'}
                label="Alert Type"
                onChange={(e) => setNewAlert({ ...newAlert, type: e.target.value as Alert['type'] })}
              >
                <MenuItem value="budget">Budget</MenuItem>
                <MenuItem value="trend">Trend</MenuItem>
                <MenuItem value="anomaly">Anomaly</MenuItem>
              </Select>
            </FormControl>

            <TextField
              fullWidth
              type="number"
              label="Threshold (USD)"
              value={newAlert.threshold || ''}
              onChange={(e) => setNewAlert({ ...newAlert, threshold: parseFloat(e.target.value) })}
              sx={{ mb: 2 }}
            />

            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Frequency</InputLabel>
              <Select
                value={newAlert.frequency || 'daily'}
                label="Frequency"
                onChange={(e) => setNewAlert({ ...newAlert, frequency: e.target.value as Alert['frequency'] })}
              >
                <MenuItem value="daily">Daily</MenuItem>
                <MenuItem value="weekly">Weekly</MenuItem>
                <MenuItem value="monthly">Monthly</MenuItem>
              </Select>
            </FormControl>

            <TextField
              fullWidth
              label="Target (Resource/Tag)"
              value={newAlert.target || ''}
              onChange={(e) => setNewAlert({ ...newAlert, target: e.target.value })}
              helperText="Resource ID, tag, or '*' for all resources"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button
            onClick={handleCreateAlert}
            variant="contained"
            disabled={!newAlert.name || !newAlert.threshold}
          >
            Create
          </Button>
        </DialogActions>
      </Dialog>
    </Card>
  );
};

export default AlertManager;
