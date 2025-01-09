package config

import (
	"fmt"
	"os"
	"path/filepath"

	"github.com/spf13/viper"
	"gopkg.in/yaml.v2"
)

// Config represents the CLI configuration
type Config struct {
	DefaultProvider string            `yaml:"default_provider"`
	DefaultRegion   string            `yaml:"default_region"`
	Credentials     ProviderCreds     `yaml:"credentials"`
	OutputFormat    string            `yaml:"output_format"`
	Preferences     UserPreferences   `yaml:"preferences"`
	APIEndpoints    map[string]string `yaml:"api_endpoints"`
}

// ProviderCreds holds cloud provider credentials
type ProviderCreds struct {
	AWS   AWSCreds   `yaml:"aws"`
	Azure AzureCreds `yaml:"azure"`
	GCP   GCPCreds   `yaml:"gcp"`
}

// AWSCreds holds AWS credentials
type AWSCreds struct {
	AccessKeyID     string `yaml:"access_key_id"`
	SecretAccessKey string `yaml:"secret_access_key"`
	Region          string `yaml:"region"`
	Profile         string `yaml:"profile"`
}

// AzureCreds holds Azure credentials
type AzureCreds struct {
	TenantID       string `yaml:"tenant_id"`
	SubscriptionID string `yaml:"subscription_id"`
	ClientID       string `yaml:"client_id"`
	ClientSecret   string `yaml:"client_secret"`
}

// GCPCreds holds GCP credentials
type GCPCreds struct {
	ProjectID      string `yaml:"project_id"`
	CredentialFile string `yaml:"credential_file"`
}

// UserPreferences holds user-specific settings
type UserPreferences struct {
	AutoConfirm    bool     `yaml:"auto_confirm"`
	CostThreshold  float64  `yaml:"cost_threshold"`
	NotifyEmail    string   `yaml:"notify_email"`
	ExcludeRegions []string `yaml:"exclude_regions"`
}

// DefaultConfig returns a default configuration
func DefaultConfig() *Config {
	return &Config{
		DefaultProvider: "aws",
		DefaultRegion:   "us-west-2",
		OutputFormat:    "text",
		Preferences: UserPreferences{
			AutoConfirm:   false,
			CostThreshold: 100.0,
		},
		APIEndpoints: map[string]string{
			"optimizer": "http://localhost:8080",
			"analyzer":  "http://localhost:8081",
		},
	}
}

// LoadConfig loads the configuration from file
func LoadConfig() (*Config, error) {
	configDir, err := getConfigDir()
	if err != nil {
		return nil, err
	}

	configFile := filepath.Join(configDir, "config.yaml")
	if _, err := os.Stat(configFile); os.IsNotExist(err) {
		// Create default config if it doesn't exist
		config := DefaultConfig()
		if err := config.Save(); err != nil {
			return nil, fmt.Errorf("failed to create default config: %v", err)
		}
		return config, nil
	}

	var config Config
	data, err := os.ReadFile(configFile)
	if err != nil {
		return nil, fmt.Errorf("failed to read config file: %v", err)
	}

	if err := yaml.Unmarshal(data, &config); err != nil {
		return nil, fmt.Errorf("failed to parse config file: %v", err)
	}

	return &config, nil
}

// Save writes the configuration to file
func (c *Config) Save() error {
	configDir, err := getConfigDir()
	if err != nil {
		return err
	}

	if err := os.MkdirAll(configDir, 0755); err != nil {
		return fmt.Errorf("failed to create config directory: %v", err)
	}

	data, err := yaml.Marshal(c)
	if err != nil {
		return fmt.Errorf("failed to marshal config: %v", err)
	}

	configFile := filepath.Join(configDir, "config.yaml")
	if err := os.WriteFile(configFile, data, 0600); err != nil {
		return fmt.Errorf("failed to write config file: %v", err)
	}

	return nil
}

// Update updates the configuration with environment variables and flags
func (c *Config) Update() error {
	// Update from environment variables
	if provider := os.Getenv("CLOUDOPT_PROVIDER"); provider != "" {
		c.DefaultProvider = provider
	}
	if region := os.Getenv("CLOUDOPT_REGION"); region != "" {
		c.DefaultRegion = region
	}

	// Update from viper (flags)
	if provider := viper.GetString("provider"); provider != "" {
		c.DefaultProvider = provider
	}
	if region := viper.GetString("region"); region != "" {
		c.DefaultRegion = region
	}
	if format := viper.GetString("output"); format != "" {
		c.OutputFormat = format
	}

	return nil
}

// Validate checks if the configuration is valid
func (c *Config) Validate() error {
	// Validate provider
	switch c.DefaultProvider {
	case "aws", "azure", "gcp":
		// Valid provider
	default:
		return fmt.Errorf("invalid provider: %s", c.DefaultProvider)
	}

	// Validate output format
	switch c.OutputFormat {
	case "text", "json", "yaml":
		// Valid format
	default:
		return fmt.Errorf("invalid output format: %s", c.OutputFormat)
	}

	// Validate credentials based on provider
	switch c.DefaultProvider {
	case "aws":
		if err := c.validateAWSCreds(); err != nil {
			return err
		}
	case "azure":
		if err := c.validateAzureCreds(); err != nil {
			return err
		}
	case "gcp":
		if err := c.validateGCPCreds(); err != nil {
			return err
		}
	}

	return nil
}

func (c *Config) validateAWSCreds() error {
	creds := c.Credentials.AWS
	if creds.Profile == "" && (creds.AccessKeyID == "" || creds.SecretAccessKey == "") {
		return fmt.Errorf("AWS credentials not configured")
	}
	return nil
}

func (c *Config) validateAzureCreds() error {
	creds := c.Credentials.Azure
	if creds.TenantID == "" || creds.SubscriptionID == "" || 
		creds.ClientID == "" || creds.ClientSecret == "" {
		return fmt.Errorf("Azure credentials not configured")
	}
	return nil
}

func (c *Config) validateGCPCreds() error {
	creds := c.Credentials.GCP
	if creds.ProjectID == "" || creds.CredentialFile == "" {
		return fmt.Errorf("GCP credentials not configured")
	}
	return nil
}

func getConfigDir() (string, error) {
	homeDir, err := os.UserHomeDir()
	if err != nil {
		return "", fmt.Errorf("failed to get home directory: %v", err)
	}
	return filepath.Join(homeDir, ".cloudopt"), nil
}
