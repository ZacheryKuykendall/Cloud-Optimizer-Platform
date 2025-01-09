package client

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

const (
	defaultTimeout = 30 * time.Second
)

// Client represents a Cloud Optimizer API client
type Client struct {
	apiEndpoint string
	apiKey      string
	httpClient  *http.Client
}

// NewClient creates a new Cloud Optimizer API client
func NewClient(apiEndpoint, apiKey string) *Client {
	return &Client{
		apiEndpoint: apiEndpoint,
		apiKey:      apiKey,
		httpClient: &http.Client{
			Timeout: defaultTimeout,
		},
	}
}

// ComputeRequirements represents the requirements for compute resource placement
type ComputeRequirements struct {
	Name                string    `json:"name"`
	VCPUs               int       `json:"vcpus"`
	MemoryGB           float64   `json:"memory_gb"`
	Regions            []string  `json:"regions"`
	MinAvailability    float64   `json:"min_availability"`
	MaxMonthlyBudget   *float64  `json:"max_monthly_budget,omitempty"`
	PreferredProviders []string  `json:"preferred_providers,omitempty"`
	ExcludedProviders  []string  `json:"excluded_providers,omitempty"`
	RequiredFeatures   []string  `json:"required_features,omitempty"`
	ComplianceFrameworks []string `json:"compliance_frameworks,omitempty"`
}

// StorageRequirements represents the requirements for storage resource placement
type StorageRequirements struct {
	Name             string    `json:"name"`
	CapacityGB       int       `json:"capacity_gb"`
	IOPS            *int      `json:"iops,omitempty"`
	ThroughputMBPS  *int      `json:"throughput_mbps,omitempty"`
	Regions         []string  `json:"regions"`
	MinAvailability float64   `json:"min_availability"`
	MaxMonthlyBudget *float64 `json:"max_monthly_budget,omitempty"`
}

// NetworkRequirements represents the requirements for network resource placement
type NetworkRequirements struct {
	Name             string    `json:"name"`
	BandwidthGbps    float64   `json:"bandwidth_gbps"`
	CrossRegion      bool      `json:"cross_region"`
	Regions         []string  `json:"regions"`
	MinAvailability float64   `json:"min_availability"`
	MaxMonthlyBudget *float64 `json:"max_monthly_budget,omitempty"`
}

// DatabaseRequirements represents the requirements for database resource placement
type DatabaseRequirements struct {
	Name             string    `json:"name"`
	Engine           string    `json:"engine"`
	Version          string    `json:"version"`
	Regions         []string  `json:"regions"`
	MinAvailability float64   `json:"min_availability"`
	MaxMonthlyBudget *float64 `json:"max_monthly_budget,omitempty"`
}

// PlacementResult represents the result of a resource placement decision
type PlacementResult struct {
	ID                   string    `json:"id"`
	SelectedProvider     string    `json:"selected_provider"`
	SelectedRegion       string    `json:"selected_region"`
	InstanceType         string    `json:"instance_type,omitempty"`
	EstimatedMonthlyCost float64   `json:"estimated_monthly_cost"`
	PerformanceScore     float64   `json:"performance_score"`
	ComplianceScore      float64   `json:"compliance_score"`
	TotalScore          float64   `json:"total_score"`
	Recommendations     []Alternative `json:"recommendations"`
	CreatedAt           time.Time `json:"created_at"`
	UpdatedAt           time.Time `json:"updated_at"`
}

// Alternative represents an alternative placement recommendation
type Alternative struct {
	Provider           string  `json:"provider"`
	Region            string  `json:"region"`
	InstanceType      string  `json:"instance_type,omitempty"`
	MonthlyCost       float64 `json:"monthly_cost"`
	PerformanceScore  float64 `json:"performance_score"`
	ComplianceScore   float64 `json:"compliance_score"`
	TotalScore        float64 `json:"total_score"`
}

// CreateComputePlacement creates a new compute resource placement
func (c *Client) CreateComputePlacement(req *ComputeRequirements) (*PlacementResult, error) {
	return c.createPlacement("compute", req)
}

// GetComputePlacement gets an existing compute resource placement
func (c *Client) GetComputePlacement(id string) (*PlacementResult, error) {
	return c.getPlacement("compute", id)
}

// UpdateComputePlacement updates an existing compute resource placement
func (c *Client) UpdateComputePlacement(id string, req *ComputeRequirements) (*PlacementResult, error) {
	return c.updatePlacement("compute", id, req)
}

// DeleteComputePlacement deletes an existing compute resource placement
func (c *Client) DeleteComputePlacement(id string) error {
	return c.deletePlacement("compute", id)
}

// CreateStoragePlacement creates a new storage resource placement
func (c *Client) CreateStoragePlacement(req *StorageRequirements) (*PlacementResult, error) {
	return c.createPlacement("storage", req)
}

// GetStoragePlacement gets an existing storage resource placement
func (c *Client) GetStoragePlacement(id string) (*PlacementResult, error) {
	return c.getPlacement("storage", id)
}

// UpdateStoragePlacement updates an existing storage resource placement
func (c *Client) UpdateStoragePlacement(id string, req *StorageRequirements) (*PlacementResult, error) {
	return c.updatePlacement("storage", id, req)
}

// DeleteStoragePlacement deletes an existing storage resource placement
func (c *Client) DeleteStoragePlacement(id string) error {
	return c.deletePlacement("storage", id)
}

// CreateNetworkPlacement creates a new network resource placement
func (c *Client) CreateNetworkPlacement(req *NetworkRequirements) (*PlacementResult, error) {
	return c.createPlacement("network", req)
}

// GetNetworkPlacement gets an existing network resource placement
func (c *Client) GetNetworkPlacement(id string) (*PlacementResult, error) {
	return c.getPlacement("network", id)
}

// UpdateNetworkPlacement updates an existing network resource placement
func (c *Client) UpdateNetworkPlacement(id string, req *NetworkRequirements) (*PlacementResult, error) {
	return c.updatePlacement("network", id, req)
}

// DeleteNetworkPlacement deletes an existing network resource placement
func (c *Client) DeleteNetworkPlacement(id string) error {
	return c.deletePlacement("network", id)
}

// CreateDatabasePlacement creates a new database resource placement
func (c *Client) CreateDatabasePlacement(req *DatabaseRequirements) (*PlacementResult, error) {
	return c.createPlacement("database", req)
}

// GetDatabasePlacement gets an existing database resource placement
func (c *Client) GetDatabasePlacement(id string) (*PlacementResult, error) {
	return c.getPlacement("database", id)
}

// UpdateDatabasePlacement updates an existing database resource placement
func (c *Client) UpdateDatabasePlacement(id string, req *DatabaseRequirements) (*PlacementResult, error) {
	return c.updatePlacement("database", id, req)
}

// DeleteDatabasePlacement deletes an existing database resource placement
func (c *Client) DeleteDatabasePlacement(id string) error {
	return c.deletePlacement("database", id)
}

func (c *Client) createPlacement(resourceType string, req interface{}) (*PlacementResult, error) {
	body, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %v", err)
	}

	resp, err := c.doRequest(http.MethodPost, fmt.Sprintf("/placements/%s", resourceType), body)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var result PlacementResult
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %v", err)
	}

	return &result, nil
}

func (c *Client) getPlacement(resourceType, id string) (*PlacementResult, error) {
	resp, err := c.doRequest(http.MethodGet, fmt.Sprintf("/placements/%s/%s", resourceType, id), nil)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var result PlacementResult
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %v", err)
	}

	return &result, nil
}

func (c *Client) updatePlacement(resourceType, id string, req interface{}) (*PlacementResult, error) {
	body, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %v", err)
	}

	resp, err := c.doRequest(http.MethodPut, fmt.Sprintf("/placements/%s/%s", resourceType, id), body)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var result PlacementResult
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %v", err)
	}

	return &result, nil
}

func (c *Client) deletePlacement(resourceType, id string) error {
	resp, err := c.doRequest(http.MethodDelete, fmt.Sprintf("/placements/%s/%s", resourceType, id), nil)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	return nil
}

func (c *Client) doRequest(method, path string, body []byte) (*http.Response, error) {
	url := fmt.Sprintf("%s%s", c.apiEndpoint, path)

	var reqBody io.Reader
	if body != nil {
		reqBody = bytes.NewBuffer(body)
	}

	req, err := http.NewRequest(method, url, reqBody)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %v", err)
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", c.apiKey))

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to send request: %v", err)
	}

	if resp.StatusCode >= 400 {
		defer resp.Body.Close()
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("request failed with status %d: %s", resp.StatusCode, string(body))
	}

	return resp, nil
}
