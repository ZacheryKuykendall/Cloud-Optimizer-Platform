package main

import (
	"context"
	"fmt"
	"strconv"

	"github.com/hashicorp/terraform-plugin-sdk/v2/diag"
	"github.com/hashicorp/terraform-plugin-sdk/v2/helper/schema"
	"github.com/hashicorp/terraform-plugin-sdk/v2/helper/validation"

	"terraform-provider-cloudoptimizer/client"
)

func resourceComputePlacementCreate(ctx context.Context, d *schema.ResourceData, m interface{}) diag.Diagnostics {
	c := m.(*client.Client)

	// Build compute requirements from schema
	req := &client.ComputeRequirements{
		Name:     d.Get("name").(string),
		VCPUs:    d.Get("vcpus").(int),
		MemoryGB: d.Get("memory_gb").(float64),
		Regions:  expandStringSet(d.Get("regions").(*schema.Set)),
	}

	if v, ok := d.GetOk("min_availability"); ok {
		req.MinAvailability = v.(float64)
	}

	if v, ok := d.GetOk("max_monthly_budget"); ok {
		budget := v.(float64)
		req.MaxMonthlyBudget = &budget
	}

	if v, ok := d.GetOk("preferred_providers"); ok {
		req.PreferredProviders = expandStringSet(v.(*schema.Set))
	}

	if v, ok := d.GetOk("excluded_providers"); ok {
		req.ExcludedProviders = expandStringSet(v.(*schema.Set))
	}

	if v, ok := d.GetOk("required_features"); ok {
		req.RequiredFeatures = expandStringSet(v.(*schema.Set))
	}

	if v, ok := d.GetOk("compliance_frameworks"); ok {
		req.ComplianceFrameworks = expandStringSet(v.(*schema.Set))
	}

	// Create placement
	result, err := c.CreateComputePlacement(req)
	if err != nil {
		return diag.FromErr(fmt.Errorf("error creating compute placement: %v", err))
	}

	// Set ID and computed values
	d.SetId(result.ID)
	if err := setComputePlacementValues(d, result); err != nil {
		return diag.FromErr(err)
	}

	return nil
}

func resourceComputePlacementRead(ctx context.Context, d *schema.ResourceData, m interface{}) diag.Diagnostics {
	c := m.(*client.Client)

	// Get placement
	result, err := c.GetComputePlacement(d.Id())
	if err != nil {
		return diag.FromErr(fmt.Errorf("error reading compute placement: %v", err))
	}

	// Set computed values
	if err := setComputePlacementValues(d, result); err != nil {
		return diag.FromErr(err)
	}

	return nil
}

func resourceComputePlacementUpdate(ctx context.Context, d *schema.ResourceData, m interface{}) diag.Diagnostics {
	c := m.(*client.Client)

	// Build compute requirements from schema
	req := &client.ComputeRequirements{
		Name:     d.Get("name").(string),
		VCPUs:    d.Get("vcpus").(int),
		MemoryGB: d.Get("memory_gb").(float64),
		Regions:  expandStringSet(d.Get("regions").(*schema.Set)),
	}

	if v, ok := d.GetOk("min_availability"); ok {
		req.MinAvailability = v.(float64)
	}

	if v, ok := d.GetOk("max_monthly_budget"); ok {
		budget := v.(float64)
		req.MaxMonthlyBudget = &budget
	}

	if v, ok := d.GetOk("preferred_providers"); ok {
		req.PreferredProviders = expandStringSet(v.(*schema.Set))
	}

	if v, ok := d.GetOk("excluded_providers"); ok {
		req.ExcludedProviders = expandStringSet(v.(*schema.Set))
	}

	if v, ok := d.GetOk("required_features"); ok {
		req.RequiredFeatures = expandStringSet(v.(*schema.Set))
	}

	if v, ok := d.GetOk("compliance_frameworks"); ok {
		req.ComplianceFrameworks = expandStringSet(v.(*schema.Set))
	}

	// Update placement
	result, err := c.UpdateComputePlacement(d.Id(), req)
	if err != nil {
		return diag.FromErr(fmt.Errorf("error updating compute placement: %v", err))
	}

	// Set computed values
	if err := setComputePlacementValues(d, result); err != nil {
		return diag.FromErr(err)
	}

	return nil
}

func resourceComputePlacementDelete(ctx context.Context, d *schema.ResourceData, m interface{}) diag.Diagnostics {
	c := m.(*client.Client)

	// Delete placement
	if err := c.DeleteComputePlacement(d.Id()); err != nil {
		return diag.FromErr(fmt.Errorf("error deleting compute placement: %v", err))
	}

	return nil
}

func setComputePlacementValues(d *schema.ResourceData, result *client.PlacementResult) error {
	if err := d.Set("selected_provider", result.SelectedProvider); err != nil {
		return fmt.Errorf("error setting selected_provider: %v", err)
	}

	if err := d.Set("selected_region", result.SelectedRegion); err != nil {
		return fmt.Errorf("error setting selected_region: %v", err)
	}

	if err := d.Set("instance_type", result.InstanceType); err != nil {
		return fmt.Errorf("error setting instance_type: %v", err)
	}

	if err := d.Set("estimated_monthly_cost", result.EstimatedMonthlyCost); err != nil {
		return fmt.Errorf("error setting estimated_monthly_cost: %v", err)
	}

	if err := d.Set("performance_score", result.PerformanceScore); err != nil {
		return fmt.Errorf("error setting performance_score: %v", err)
	}

	if err := d.Set("compliance_score", result.ComplianceScore); err != nil {
		return fmt.Errorf("error setting compliance_score: %v", err)
	}

	if err := d.Set("total_score", result.TotalScore); err != nil {
		return fmt.Errorf("error setting total_score: %v", err)
	}

	recommendations := make([]interface{}, len(result.Recommendations))
	for i, rec := range result.Recommendations {
		recommendations[i] = map[string]interface{}{
			"provider":           rec.Provider,
			"region":            rec.Region,
			"instance_type":      rec.InstanceType,
			"monthly_cost":       rec.MonthlyCost,
			"performance_score":  rec.PerformanceScore,
			"compliance_score":   rec.ComplianceScore,
			"total_score":       rec.TotalScore,
		}
	}

	if err := d.Set("recommendations", recommendations); err != nil {
		return fmt.Errorf("error setting recommendations: %v", err)
	}

	return nil
}

func expandStringSet(set *schema.Set) []string {
	if set == nil {
		return nil
	}

	slice := make([]string, set.Len())
	for i, v := range set.List() {
		slice[i] = v.(string)
	}
	return slice
}

func validatePositiveFloat() schema.SchemaValidateFunc {
	return validation.FloatAtLeast(0.0)
}

func validatePositiveInt() schema.SchemaValidateFunc {
	return validation.IntAtLeast(1)
}

func validateAvailability() schema.SchemaValidateFunc {
	return validation.FloatBetween(0.0, 100.0)
}
