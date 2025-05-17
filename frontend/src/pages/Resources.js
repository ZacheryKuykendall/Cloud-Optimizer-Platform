import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Chip,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
} from '@mui/material';
import { getResources } from '../services/api';

const Resources = () => {
  const [resources, setResources] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [provider, setProvider] = useState('');
  const [resourceType, setResourceType] = useState('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  // Get available resource types from the loaded resources
  const getResourceTypes = () => {
    const types = new Set();
    Object.values(resources).forEach((providerResources) => {
      providerResources.forEach((resource) => {
        if (resource.type) types.add(resource.type);
      });
    });
    return Array.from(types);
  };

  // Filter resources based on selected provider and resource type
  const getFilteredResources = () => {
    let filtered = [];

    if (!resources || Object.keys(resources).length === 0) return [];

    // Filter by provider
    if (provider) {
      if (resources[provider]) {
        filtered = resources[provider];
      }
    } else {
      // If no provider selected, include all resources
      filtered = Object.values(resources).flat();
    }

    // Filter by resource type
    if (resourceType && filtered.length > 0) {
      filtered = filtered.filter((resource) => resource.type === resourceType);
    }

    return filtered;
  };

  useEffect(() => {
    const fetchResources = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await getResources(provider, resourceType);
        setResources(response.data);
      } catch (err) {
        console.error('Error fetching resources:', err);
        setError('Failed to load resources. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchResources();
  }, [provider, resourceType]);

  const handleProviderChange = (event) => {
    setProvider(event.target.value);
    setPage(0);
  };

  const handleResourceTypeChange = (event) => {
    setResourceType(event.target.value);
    setPage(0);
  };

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const filteredResources = getFilteredResources();
  const resourceTypes = getResourceTypes();

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
        Cloud Resources
      </Typography>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel id="provider-label">Cloud Provider</InputLabel>
                <Select
                  labelId="provider-label"
                  id="provider-select"
                  value={provider}
                  label="Cloud Provider"
                  onChange={handleProviderChange}
                >
                  <MenuItem value="">All Providers</MenuItem>
                  {Object.keys(resources).map((providerName) => (
                    <MenuItem key={providerName} value={providerName}>
                      {providerName.toUpperCase()}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel id="resource-type-label">Resource Type</InputLabel>
                <Select
                  labelId="resource-type-label"
                  id="resource-type-select"
                  value={resourceType}
                  label="Resource Type"
                  onChange={handleResourceTypeChange}
                >
                  <MenuItem value="">All Types</MenuItem>
                  {resourceTypes.map((type) => (
                    <MenuItem key={type} value={type}>
                      {type}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Resources Table */}
      <Paper sx={{ width: '100%', overflow: 'hidden' }}>
        <TableContainer sx={{ maxHeight: 440 }}>
          <Table stickyHeader aria-label="cloud resources table">
            <TableHead>
              <TableRow>
                <TableCell>Provider</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Name/ID</TableCell>
                <TableCell>Status/State</TableCell>
                <TableCell>Region/Location</TableCell>
                <TableCell>Details</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredResources
                .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                .map((resource, index) => (
                  <TableRow hover key={`${resource.provider}-${resource.id}-${index}`}>
                    <TableCell>
                      <Chip
                        label={resource.provider?.toUpperCase()}
                        color={
                          resource.provider === 'aws'
                            ? 'warning'
                            : resource.provider === 'azure'
                            ? 'primary'
                            : 'success'
                        }
                        size="small"
                      />
                    </TableCell>
                    <TableCell>{resource.type}</TableCell>
                    <TableCell>{resource.name || resource.id}</TableCell>
                    <TableCell>
                      {resource.state || resource.status || 'N/A'}
                    </TableCell>
                    <TableCell>
                      {resource.region || resource.location || 'N/A'}
                    </TableCell>
                    <TableCell>
                      {resource.size || resource.machine_type || resource.sku || 'N/A'}
                    </TableCell>
                  </TableRow>
                ))}
              {filteredResources.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} align="center">
                    No resources found matching the criteria
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
        <TablePagination
          rowsPerPageOptions={[10, 25, 50]}
          component="div"
          count={filteredResources.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />
      </Paper>
    </Box>
  );
};

export default Resources; 