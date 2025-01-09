package cmd

import (
	"fmt"
	"strings"

	"github.com/manifoldco/promptui"
	"github.com/spf13/cobra"
)

// interactiveCmd represents the interactive command
var interactiveCmd = &cobra.Command{
	Use:   "interactive",
	Short: "Start interactive mode",
	Long: `Start an interactive session that guides you through cloud resource optimization.
This mode provides a user-friendly interface for:

- Analyzing cloud resources
- Comparing costs across providers
- Generating optimization recommendations
- Managing cloud budgets
- Checking compliance`,
	RunE: func(cmd *cobra.Command, args []string) error {
		return runInteractiveMode()
	},
}

func init() {
	rootCmd.AddCommand(interactiveCmd)
}

func runInteractiveMode() error {
	for {
		// Main menu
		action, err := promptMainMenu()
		if err != nil {
			if err == promptui.ErrInterrupt {
				fmt.Println("\nExiting interactive mode...")
				return nil
			}
			return fmt.Errorf("main menu error: %v", err)
		}

		// Handle the selected action
		if err := handleMainMenuAction(action); err != nil {
			if err == promptui.ErrInterrupt {
				continue
			}
			fmt.Printf("Error: %v\n", err)
		}

		// Ask if user wants to continue
		if !promptContinue() {
			fmt.Println("Exiting interactive mode...")
			return nil
		}
	}
}

func promptMainMenu() (string, error) {
	prompt := promptui.Select{
		Label: "Select an action",
		Items: []string{
			"Analyze Resources",
			"Compare Costs",
			"View Recommendations",
			"Manage Budgets",
			"Check Compliance",
			"Configure Settings",
			"Exit",
		},
		Templates: &promptui.SelectTemplates{
			Label:    "{{ . }}?",
			Active:   "\U0001F449 {{ . | cyan }}",
			Inactive: "  {{ . | white }}",
			Selected: "\U0001F44D {{ . | green }}",
		},
	}

	_, result, err := prompt.Run()
	return result, err
}

func handleMainMenuAction(action string) error {
	switch action {
	case "Analyze Resources":
		return handleAnalyzeResources()
	case "Compare Costs":
		return handleCompareCosts()
	case "View Recommendations":
		return handleViewRecommendations()
	case "Manage Budgets":
		return handleManageBudgets()
	case "Check Compliance":
		return handleCheckCompliance()
	case "Configure Settings":
		return handleConfigureSettings()
	case "Exit":
		return promptui.ErrInterrupt
	default:
		return fmt.Errorf("unknown action: %s", action)
	}
}

func handleAnalyzeResources() error {
	// Select provider
	provider, err := promptProvider()
	if err != nil {
		return err
	}

	// Select region
	region, err := promptRegion(provider)
	if err != nil {
		return err
	}

	// Select resource type
	resourceType, err := promptResourceType()
	if err != nil {
		return err
	}

	// Configure analysis options
	options, err := promptAnalysisOptions()
	if err != nil {
		return err
	}

	fmt.Printf("\nAnalyzing %s resources in %s/%s with options: %v\n", resourceType, provider, region, options)
	// TODO: Implement actual analysis
	return nil
}

func handleCompareCosts() error {
	fmt.Println("Cost comparison feature coming soon...")
	return nil
}

func handleViewRecommendations() error {
	fmt.Println("Recommendations feature coming soon...")
	return nil
}

func handleManageBudgets() error {
	fmt.Println("Budget management feature coming soon...")
	return nil
}

func handleCheckCompliance() error {
	fmt.Println("Compliance checking feature coming soon...")
	return nil
}

func handleConfigureSettings() error {
	fmt.Println("Settings configuration feature coming soon...")
	return nil
}

func promptProvider() (string, error) {
	prompt := promptui.Select{
		Label: "Select cloud provider",
		Items: []string{"AWS", "Azure", "GCP"},
	}

	_, result, err := prompt.Run()
	return strings.ToLower(result), err
}

func promptRegion(provider string) (string, error) {
	var regions []string
	switch provider {
	case "aws":
		regions = []string{"us-east-1", "us-west-2", "eu-west-1"}
	case "azure":
		regions = []string{"eastus", "westus2", "westeurope"}
	case "gcp":
		regions = []string{"us-central1", "us-east1", "europe-west1"}
	}

	prompt := promptui.Select{
		Label: "Select region",
		Items: regions,
	}

	_, result, err := prompt.Run()
	return result, err
}

func promptResourceType() (string, error) {
	prompt := promptui.Select{
		Label: "Select resource type",
		Items: []string{
			"Compute (VMs)",
			"Storage",
			"Database",
			"Network",
			"All Resources",
		},
	}

	_, result, err := prompt.Run()
	return result, err
}

func promptAnalysisOptions() (map[string]bool, error) {
	options := map[string]bool{
		"Cost Analysis":     false,
		"Performance":       false,
		"Security":         false,
		"Compliance":       false,
		"Recommendations":  false,
	}

	for option := range options {
		prompt := promptui.Prompt{
			Label:     fmt.Sprintf("Include %s", option),
			IsConfirm: true,
		}

		result, err := prompt.Run()
		if err != nil {
			if err == promptui.ErrInterrupt {
				return nil, err
			}
			continue
		}

		options[option] = strings.ToLower(result) == "y"
	}

	return options, nil
}

func promptContinue() bool {
	prompt := promptui.Prompt{
		Label:     "Would you like to perform another action",
		IsConfirm: true,
	}

	result, err := prompt.Run()
	if err != nil {
		return false
	}

	return strings.ToLower(result) == "y"
}
