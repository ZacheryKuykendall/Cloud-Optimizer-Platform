package plugin

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"plugin"
	"sync"
)

// Plugin represents a loadable plugin
type Plugin struct {
	Name        string          `json:"name"`
	Version     string          `json:"version"`
	Author      string          `json:"author"`
	Description string          `json:"description"`
	EntryPoint  string          `json:"entry_point"`
	Config      map[string]any  `json:"config"`
	Instance    PluginInstance  `json:"-"`
}

// PluginInstance represents the interface that all plugins must implement
type PluginInstance interface {
	// Initialize is called when the plugin is first loaded
	Initialize(config map[string]any) error

	// Execute runs the plugin with the given arguments
	Execute(args []string) (any, error)

	// GetCommands returns a list of commands provided by this plugin
	GetCommands() []Command

	// Cleanup is called when the plugin is being unloaded
	Cleanup() error
}

// Command represents a command provided by a plugin
type Command struct {
	Name        string   `json:"name"`
	Description string   `json:"description"`
	Usage       string   `json:"usage"`
	Flags       []Flag   `json:"flags"`
}

// Flag represents a command-line flag for a plugin command
type Flag struct {
	Name        string `json:"name"`
	Shorthand   string `json:"shorthand"`
	Usage       string `json:"usage"`
	Type        string `json:"type"`
	Required    bool   `json:"required"`
	Default     any    `json:"default"`
}

// Manager handles plugin lifecycle and execution
type Manager struct {
	mu      sync.RWMutex
	plugins map[string]*Plugin
}

// NewManager creates a new plugin manager
func NewManager() *Manager {
	return &Manager{
		plugins: make(map[string]*Plugin),
	}
}

// LoadPlugin loads a plugin from the given path
func (m *Manager) LoadPlugin(manifestPath string) error {
	// Read and parse the plugin manifest
	manifest, err := os.ReadFile(manifestPath)
	if err != nil {
		return fmt.Errorf("failed to read plugin manifest: %v", err)
	}

	var plugin Plugin
	if err := json.Unmarshal(manifest, &plugin); err != nil {
		return fmt.Errorf("failed to parse plugin manifest: %v", err)
	}

	// Validate plugin manifest
	if err := validatePlugin(&plugin); err != nil {
		return fmt.Errorf("invalid plugin manifest: %v", err)
	}

	// Load the plugin binary
	pluginPath := filepath.Join(filepath.Dir(manifestPath), plugin.EntryPoint)
	p, err := plugin.Open(pluginPath)
	if err != nil {
		return fmt.Errorf("failed to load plugin binary: %v", err)
	}

	// Look up the plugin's entry point symbol
	sym, err := p.Lookup("NewPlugin")
	if err != nil {
		return fmt.Errorf("plugin entry point not found: %v", err)
	}

	// Create a new instance of the plugin
	newPlugin, ok := sym.(func() PluginInstance)
	if !ok {
		return fmt.Errorf("invalid plugin entry point type")
	}

	plugin.Instance = newPlugin()

	// Initialize the plugin
	if err := plugin.Instance.Initialize(plugin.Config); err != nil {
		return fmt.Errorf("failed to initialize plugin: %v", err)
	}

	// Store the plugin
	m.mu.Lock()
	m.plugins[plugin.Name] = &plugin
	m.mu.Unlock()

	return nil
}

// UnloadPlugin unloads a plugin by name
func (m *Manager) UnloadPlugin(name string) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	plugin, exists := m.plugins[name]
	if !exists {
		return fmt.Errorf("plugin not found: %s", name)
	}

	if err := plugin.Instance.Cleanup(); err != nil {
		return fmt.Errorf("failed to cleanup plugin: %v", err)
	}

	delete(m.plugins, name)
	return nil
}

// ExecutePlugin executes a plugin by name with the given arguments
func (m *Manager) ExecutePlugin(name string, args []string) (any, error) {
	m.mu.RLock()
	plugin, exists := m.plugins[name]
	m.mu.RUnlock()

	if !exists {
		return nil, fmt.Errorf("plugin not found: %s", name)
	}

	return plugin.Instance.Execute(args)
}

// GetPluginCommands returns a list of commands provided by a plugin
func (m *Manager) GetPluginCommands(name string) ([]Command, error) {
	m.mu.RLock()
	plugin, exists := m.plugins[name]
	m.mu.RUnlock()

	if !exists {
		return nil, fmt.Errorf("plugin not found: %s", name)
	}

	return plugin.Instance.GetCommands(), nil
}

// ListPlugins returns a list of all loaded plugins
func (m *Manager) ListPlugins() []*Plugin {
	m.mu.RLock()
	defer m.mu.RUnlock()

	plugins := make([]*Plugin, 0, len(m.plugins))
	for _, p := range m.plugins {
		plugins = append(plugins, p)
	}
	return plugins
}

func validatePlugin(p *Plugin) error {
	if p.Name == "" {
		return fmt.Errorf("plugin name is required")
	}
	if p.Version == "" {
		return fmt.Errorf("plugin version is required")
	}
	if p.EntryPoint == "" {
		return fmt.Errorf("plugin entry point is required")
	}
	return nil
}

// Example plugin manifest (plugin.json):
/*
{
    "name": "cost-analyzer",
    "version": "1.0.0",
    "author": "Your Name",
    "description": "Analyzes cloud resource costs",
    "entry_point": "cost_analyzer.so",
    "config": {
        "api_endpoint": "http://localhost:8080",
        "refresh_interval": 300
    }
}
*/

// Example plugin implementation:
/*
package main

type CostAnalyzerPlugin struct {
    config map[string]any
}

func NewPlugin() plugin.PluginInstance {
    return &CostAnalyzerPlugin{}
}

func (p *CostAnalyzerPlugin) Initialize(config map[string]any) error {
    p.config = config
    return nil
}

func (p *CostAnalyzerPlugin) Execute(args []string) (any, error) {
    // Plugin logic here
    return nil, nil
}

func (p *CostAnalyzerPlugin) GetCommands() []plugin.Command {
    return []plugin.Command{
        {
            Name: "analyze",
            Description: "Analyze resource costs",
            Usage: "analyze [resource-id]",
            Flags: []plugin.Flag{
                {
                    Name: "period",
                    Shorthand: "p",
                    Usage: "Analysis period (days)",
                    Type: "int",
                    Default: 30,
                },
            },
        },
    }
}

func (p *CostAnalyzerPlugin) Cleanup() error {
    return nil
}
*/
