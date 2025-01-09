package main

import (
	"github.com/hashicorp/terraform-plugin-sdk/v2/helper/schema"
	"github.com/hashicorp/terraform-plugin-sdk/v2/plugin"
)

func main() {
	plugin.Serve(&plugin.ServeOpts{
		ProviderFunc: Provider,
	})
}

// Provider returns a terraform.ResourceProvider.
func Provider() *schema.Provider {
	return &schema.Provider{
		Schema: map[string]*schema.Schema{
			"api_endpoint": {
				Type:        schema.TypeString,
				Required:    true,
				Sensitive:   false,
				DefaultFunc: schema.EnvDefaultFunc("CLOUDOPTIMIZER_API_ENDPOINT", nil),
				Description: "The API endpoint for the Cloud Optimizer service",
			},
			"api_key": {
				Type:        schema.TypeString,
				Required:    true,
				Sensitive:   true,
				DefaultFunc: schema.EnvDefaultFunc("CLOUDOPTIMIZER_API_KEY", nil),
				Description: "API key for authentication",
			},
		},
		ResourcesMap: map[string]*schema.Resource{
			"cloudoptimizer_compute_placement":  resourceComputePlacement(),
			"cloudoptimizer_storage_placement":  resourceStoragePlacement(),
			"cloudoptimizer_network_placement":  resourceNetworkPlacement(),
			"cloudoptimizer_database_placement": resourceDatabasePlacement(),
		},
		DataSourcesMap: map[string]*schema.Resource{
			"cloudoptimizer_compute_recommendation":  dataSourceComputeRecommendation(),
			"cloudoptimizer_storage_recommendation":  dataSourceStorageRecommendation(),
			"cloudoptimizer_network_recommendation":  dataSourceNetworkRecommendation(),
			"cloudoptimizer_database_recommendation": dataSourceDatabaseRecommendation(),
			"cloudoptimizer_cost_analysis":          dataSourceCostAnalysis(),
			"cloudoptimizer_performance_analysis":    dataSourcePerformanceAnalysis(),
			"cloudoptimizer_compliance_analysis":     dataSourceComplianceAnalysis(),
		},
	}
}

func resourceComputePlacement() *schema.Resource {
	return &schema.Resource{
		Create: resourceComputePlacementCreate,
		Read:   resourceComputePlacementRead,
		Update: resourceComputePlacementUpdate,
		Delete: resourceComputePlacementDelete,

		Schema: map[string]*schema.Schema{
			"name": {
				Type:        schema.TypeString,
				Required:    true,
				Description: "Name of the compute resource",
			},
			"vcpus": {
				Type:        schema.TypeInt,
				Required:    true,
				Description: "Number of virtual CPUs required",
			},
			"memory_gb": {
				Type:        schema.TypeFloat,
				Required:    true,
				Description: "Amount of memory required in GB",
			},
			"regions": {
				Type:     schema.TypeSet,
				Required: true,
				Elem: &schema.Schema{
					Type: schema.TypeString,
				},
				Description: "List of acceptable regions",
			},
			"min_availability": {
				Type:        schema.TypeFloat,
				Optional:    true,
				Default:     99.9,
				Description: "Minimum availability percentage required",
			},
			"max_monthly_budget": {
				Type:        schema.TypeFloat,
				Optional:    true,
				Description: "Maximum monthly budget in USD",
			},
			"preferred_providers": {
				Type:     schema.TypeSet,
				Optional: true,
				Elem: &schema.Schema{
					Type: schema.TypeString,
				},
				Description: "List of preferred cloud providers",
			},
			"excluded_providers": {
				Type:     schema.TypeSet,
				Optional: true,
				Elem: &schema.Schema{
					Type: schema.TypeString,
				},
				Description: "List of excluded cloud providers",
			},
			"required_features": {
				Type:     schema.TypeSet,
				Optional: true,
				Elem: &schema.Schema{
					Type: schema.TypeString,
				},
				Description: "List of required features",
			},
			"compliance_frameworks": {
				Type:     schema.TypeSet,
				Optional: true,
				Elem: &schema.Schema{
					Type: schema.TypeString,
				},
				Description: "List of required compliance frameworks",
			},
			// Computed values returned by the provider
			"selected_provider": {
				Type:        schema.TypeString,
				Computed:    true,
				Description: "Selected cloud provider",
			},
			"selected_region": {
				Type:        schema.TypeString,
				Computed:    true,
				Description: "Selected region",
			},
			"instance_type": {
				Type:        schema.TypeString,
				Computed:    true,
				Description: "Selected instance type",
			},
			"estimated_monthly_cost": {
				Type:        schema.TypeFloat,
				Computed:    true,
				Description: "Estimated monthly cost in USD",
			},
			"performance_score": {
				Type:        schema.TypeFloat,
				Computed:    true,
				Description: "Performance score (0-1)",
			},
			"compliance_score": {
				Type:        schema.TypeFloat,
				Computed:    true,
				Description: "Compliance score (0-1)",
			},
			"total_score": {
				Type:        schema.TypeFloat,
				Computed:    true,
				Description: "Total optimization score (0-1)",
			},
			"recommendations": {
				Type:     schema.TypeList,
				Computed: true,
				Elem: &schema.Resource{
					Schema: map[string]*schema.Schema{
						"provider": {
							Type:     schema.TypeString,
							Computed: true,
						},
						"region": {
							Type:     schema.TypeString,
							Computed: true,
						},
						"instance_type": {
							Type:     schema.TypeString,
							Computed: true,
						},
						"monthly_cost": {
							Type:     schema.TypeFloat,
							Computed: true,
						},
						"performance_score": {
							Type:     schema.TypeFloat,
							Computed: true,
						},
						"compliance_score": {
							Type:     schema.TypeFloat,
							Computed: true,
						},
						"total_score": {
							Type:     schema.TypeFloat,
							Computed: true,
						},
					},
				},
				Description: "Alternative recommendations",
			},
		},
	}
}

func resourceStoragePlacement() *schema.Resource {
	return &schema.Resource{
		Create: resourceStoragePlacementCreate,
		Read:   resourceStoragePlacementRead,
		Update: resourceStoragePlacementUpdate,
		Delete: resourceStoragePlacementDelete,

		Schema: map[string]*schema.Schema{
			"name": {
				Type:        schema.TypeString,
				Required:    true,
				Description: "Name of the storage resource",
			},
			"capacity_gb": {
				Type:        schema.TypeInt,
				Required:    true,
				Description: "Required storage capacity in GB",
			},
			"iops": {
				Type:        schema.TypeInt,
				Optional:    true,
				Description: "Required IOPS",
			},
			"throughput_mbps": {
				Type:        schema.TypeInt,
				Optional:    true,
				Description: "Required throughput in MB/s",
			},
			// Add common fields (regions, availability, budget, etc.)
			// Add computed fields (selected provider, costs, scores, etc.)
		},
	}
}

func resourceNetworkPlacement() *schema.Resource {
	return &schema.Resource{
		Create: resourceNetworkPlacementCreate,
		Read:   resourceNetworkPlacementRead,
		Update: resourceNetworkPlacementUpdate,
		Delete: resourceNetworkPlacementDelete,

		Schema: map[string]*schema.Schema{
			"name": {
				Type:        schema.TypeString,
				Required:    true,
				Description: "Name of the network resource",
			},
			"bandwidth_gbps": {
				Type:        schema.TypeFloat,
				Required:    true,
				Description: "Required bandwidth in Gbps",
			},
			"cross_region": {
				Type:        schema.TypeBool,
				Optional:    true,
				Default:     false,
				Description: "Whether cross-region connectivity is required",
			},
			// Add common fields (regions, availability, budget, etc.)
			// Add computed fields (selected provider, costs, scores, etc.)
		},
	}
}

func resourceDatabasePlacement() *schema.Resource {
	return &schema.Resource{
		Create: resourceDatabasePlacementCreate,
		Read:   resourceDatabasePlacementRead,
		Update: resourceDatabasePlacementUpdate,
		Delete: resourceDatabasePlacementDelete,

		Schema: map[string]*schema.Schema{
			"name": {
				Type:        schema.TypeString,
				Required:    true,
				Description: "Name of the database resource",
			},
			"engine": {
				Type:        schema.TypeString,
				Required:    true,
				Description: "Database engine (e.g., mysql, postgresql)",
			},
			"version": {
				Type:        schema.TypeString,
				Required:    true,
				Description: "Database engine version",
			},
			// Add common fields (regions, availability, budget, etc.)
			// Add computed fields (selected provider, costs, scores, etc.)
		},
	}
}

// TODO: Implement CRUD functions for each resource
// TODO: Implement data source functions
