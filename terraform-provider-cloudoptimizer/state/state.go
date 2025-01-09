package state

import (
	"context"
	"encoding/json"
	"fmt"
	"sync"
	"time"

	"github.com/hashicorp/terraform-plugin-sdk/v2/helper/schema"
)

// StateManager handles state persistence and management for resources
type StateManager struct {
	mu    sync.RWMutex
	cache map[string]*ResourceState
}

// ResourceState represents the state of a managed resource
type ResourceState struct {
	ID           string                 `json:"id"`
	ResourceType string                 `json:"resource_type"`
	Attributes   map[string]interface{} `json:"attributes"`
	Dependencies []string               `json:"dependencies,omitempty"`
	LastUpdated  time.Time             `json:"last_updated"`
	Version      int64                 `json:"version"`
}

// NewStateManager creates a new state manager instance
func NewStateManager() *StateManager {
	return &StateManager{
		cache: make(map[string]*ResourceState),
	}
}

// SaveResourceState saves the state of a resource
func (sm *StateManager) SaveResourceState(ctx context.Context, d *schema.ResourceData) error {
	sm.mu.Lock()
	defer sm.mu.Unlock()

	resourceType := d.Get("__resource_type").(string)
	if resourceType == "" {
		return fmt.Errorf("resource type not set in resource data")
	}

	// Create resource state
	state := &ResourceState{
		ID:           d.Id(),
		ResourceType: resourceType,
		Attributes:   make(map[string]interface{}),
		LastUpdated:  time.Now().UTC(),
		Version:      time.Now().UnixNano(),
	}

	// Extract all attributes from schema
	for k, v := range d.State().Attributes {
		// Skip internal attributes
		if k == "id" || k == "__resource_type" {
			continue
		}
		state.Attributes[k] = v
	}

	// Extract dependencies if any
	if deps, ok := d.GetOk("depends_on"); ok {
		if depSet, ok := deps.(*schema.Set); ok {
			dependencies := make([]string, depSet.Len())
			for i, dep := range depSet.List() {
				dependencies[i] = dep.(string)
			}
			state.Dependencies = dependencies
		}
	}

	// Store in cache
	sm.cache[state.ID] = state

	return nil
}

// LoadResourceState loads the state of a resource
func (sm *StateManager) LoadResourceState(ctx context.Context, d *schema.ResourceData) error {
	sm.mu.RLock()
	defer sm.mu.RUnlock()

	state, exists := sm.cache[d.Id()]
	if !exists {
		return fmt.Errorf("state not found for resource %s", d.Id())
	}

	// Set all attributes from state
	for k, v := range state.Attributes {
		if err := d.Set(k, v); err != nil {
			return fmt.Errorf("error setting attribute %s: %v", k, err)
		}
	}

	// Set resource type
	if err := d.Set("__resource_type", state.ResourceType); err != nil {
		return fmt.Errorf("error setting resource type: %v", err)
	}

	return nil
}

// DeleteResourceState deletes the state of a resource
func (sm *StateManager) DeleteResourceState(ctx context.Context, d *schema.ResourceData) error {
	sm.mu.Lock()
	defer sm.mu.Unlock()

	delete(sm.cache, d.Id())
	return nil
}

// ImportResourceState imports an existing resource's state
func (sm *StateManager) ImportResourceState(ctx context.Context, d *schema.ResourceData, meta interface{}) ([]*schema.ResourceData, error) {
	// This would typically make an API call to get the resource's current state
	// For now, we'll just create a basic state entry
	state := &ResourceState{
		ID:           d.Id(),
		ResourceType: d.Get("__resource_type").(string),
		Attributes:   make(map[string]interface{}),
		LastUpdated:  time.Now().UTC(),
		Version:      time.Now().UnixNano(),
	}

	sm.mu.Lock()
	sm.cache[state.ID] = state
	sm.mu.Unlock()

	return []*schema.ResourceData{d}, nil
}

// RefreshResourceState refreshes the state of a resource from the remote API
func (sm *StateManager) RefreshResourceState(ctx context.Context, d *schema.ResourceData, meta interface{}) error {
	// This would typically make an API call to get the resource's current state
	// For now, we'll just return the cached state
	return sm.LoadResourceState(ctx, d)
}

// ValidateResourceState validates the state of a resource
func (sm *StateManager) ValidateResourceState(ctx context.Context, d *schema.ResourceData) error {
	sm.mu.RLock()
	defer sm.mu.RUnlock()

	state, exists := sm.cache[d.Id()]
	if !exists {
		return fmt.Errorf("state not found for resource %s", d.Id())
	}

	// Validate required attributes
	requiredAttrs := []string{"name", "regions"}
	for _, attr := range requiredAttrs {
		if _, exists := state.Attributes[attr]; !exists {
			return fmt.Errorf("required attribute %s not found in state", attr)
		}
	}

	return nil
}

// MigrateResourceState migrates the state of a resource to a new version
func (sm *StateManager) MigrateResourceState(ctx context.Context, d *schema.ResourceData, meta interface{}, fromVersion int, toVersion int) error {
	sm.mu.Lock()
	defer sm.mu.Unlock()

	state, exists := sm.cache[d.Id()]
	if !exists {
		return fmt.Errorf("state not found for resource %s", d.Id())
	}

	// Perform version-specific migrations
	switch fromVersion {
	case 0:
		if toVersion > 0 {
			// Example migration: rename an attribute
			if oldValue, exists := state.Attributes["old_attr"]; exists {
				state.Attributes["new_attr"] = oldValue
				delete(state.Attributes, "old_attr")
			}
		}
	}

	return nil
}

// ExportResourceState exports the state of a resource
func (sm *StateManager) ExportResourceState(ctx context.Context, d *schema.ResourceData) ([]byte, error) {
	sm.mu.RLock()
	defer sm.mu.RUnlock()

	state, exists := sm.cache[d.Id()]
	if !exists {
		return nil, fmt.Errorf("state not found for resource %s", d.Id())
	}

	return json.Marshal(state)
}

// ImportResourceStateFromBytes imports resource state from a byte array
func (sm *StateManager) ImportResourceStateFromBytes(ctx context.Context, d *schema.ResourceData, data []byte) error {
	var state ResourceState
	if err := json.Unmarshal(data, &state); err != nil {
		return fmt.Errorf("error unmarshaling state: %v", err)
	}

	sm.mu.Lock()
	sm.cache[state.ID] = &state
	sm.mu.Unlock()

	return sm.LoadResourceState(ctx, d)
}
