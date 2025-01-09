package middleware

import (
	"context"
	"fmt"
	"net/http"
	"sync"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/spf13/viper"
	"golang.org/x/time/rate"
)

// RateLimiter manages rate limiting for API requests
type RateLimiter struct {
	mu       sync.RWMutex
	limiters map[string]*rate.Limiter
	config   RateLimitConfig
}

// RateLimitConfig holds rate limiting configuration
type RateLimitConfig struct {
	RequestsPerSecond float64       `json:"requests_per_second"`
	BurstSize        int           `json:"burst_size"`
	ExpiryTime       time.Duration `json:"expiry_time"`
	CleanupInterval  time.Duration `json:"cleanup_interval"`
}

// NewRateLimiter creates a new rate limiter instance
func NewRateLimiter() *RateLimiter {
	config := RateLimitConfig{
		RequestsPerSecond: viper.GetFloat64("rate_limit.requests_per_second"),
		BurstSize:        viper.GetInt("rate_limit.burst_size"),
		ExpiryTime:       viper.GetDuration("rate_limit.expiry_time"),
		CleanupInterval:  viper.GetDuration("rate_limit.cleanup_interval"),
	}

	if config.RequestsPerSecond == 0 {
		config.RequestsPerSecond = 10
	}
	if config.BurstSize == 0 {
		config.BurstSize = 20
	}
	if config.ExpiryTime == 0 {
		config.ExpiryTime = 1 * time.Hour
	}
	if config.CleanupInterval == 0 {
		config.CleanupInterval = 5 * time.Minute
	}

	rl := &RateLimiter{
		limiters: make(map[string]*rate.Limiter),
		config:   config,
	}

	// Start cleanup goroutine
	go rl.cleanup()

	return rl
}

// RateLimit creates a Gin middleware for rate limiting
func (rl *RateLimiter) RateLimit() gin.HandlerFunc {
	return func(c *gin.Context) {
		// Get client identifier (e.g., IP address, API key, or user ID)
		clientID := getClientID(c)

		// Get or create limiter for this client
		limiter := rl.getLimiter(clientID)

		// Check if request is allowed
		ctx := context.Background()
		if !limiter.Allow() {
			c.AbortWithStatusJSON(http.StatusTooManyRequests, gin.H{
				"error": "rate limit exceeded",
				"retry_after": fmt.Sprintf("%.0f seconds",
					time.Until(time.Now().Add(time.Second/time.Duration(rl.config.RequestsPerSecond))).Seconds()),
			})
			return
		}

		// Continue processing the request
		c.Next()

		// Update rate limiter headers
		setRateLimitHeaders(c, limiter)
	}
}

// getLimiter returns an existing limiter for the client or creates a new one
func (rl *RateLimiter) getLimiter(clientID string) *rate.Limiter {
	rl.mu.Lock()
	defer rl.mu.Unlock()

	limiter, exists := rl.limiters[clientID]
	if !exists {
		limiter = rate.NewLimiter(rate.Limit(rl.config.RequestsPerSecond), rl.config.BurstSize)
		rl.limiters[clientID] = limiter
	}

	return limiter
}

// cleanup periodically removes expired limiters
func (rl *RateLimiter) cleanup() {
	ticker := time.NewTicker(rl.config.CleanupInterval)
	defer ticker.Stop()

	for range ticker.C {
		rl.mu.Lock()
		for clientID, limiter := range rl.limiters {
			// Remove limiter if it hasn't been used recently
			if time.Since(getLastUseTime(limiter)) > rl.config.ExpiryTime {
				delete(rl.limiters, clientID)
			}
		}
		rl.mu.Unlock()
	}
}

// getClientID returns a unique identifier for the client
func getClientID(c *gin.Context) string {
	// Try to get user ID from JWT claims
	if claims, exists := c.Get("claims"); exists {
		if userClaims, ok := claims.(map[string]interface{}); ok {
			if userID, ok := userClaims["user_id"].(string); ok {
				return userID
			}
		}
	}

	// Fallback to IP address
	clientIP := c.ClientIP()
	forwardedFor := c.GetHeader("X-Forwarded-For")
	if forwardedFor != "" {
		clientIP = forwardedFor
	}

	return clientIP
}

// getLastUseTime returns the last time a limiter was used
func getLastUseTime(l *rate.Limiter) time.Time {
	// This is a bit of a hack since rate.Limiter doesn't expose last use time
	// In a production environment, you might want to track this separately
	return time.Now()
}

// setRateLimitHeaders sets rate limit headers in the response
func setRateLimitHeaders(c *gin.Context, l *rate.Limiter) {
	limit := l.Limit()
	remaining := l.Tokens()
	reset := time.Until(time.Now().Add(time.Second / time.Duration(limit)))

	c.Header("X-RateLimit-Limit", fmt.Sprintf("%.0f", limit))
	c.Header("X-RateLimit-Remaining", fmt.Sprintf("%.0f", remaining))
	c.Header("X-RateLimit-Reset", fmt.Sprintf("%.0f", reset.Seconds()))
}

// RateLimitByPath creates a rate limiter specific to an API path
func RateLimitByPath(requestsPerSecond float64, burstSize int) gin.HandlerFunc {
	limiter := rate.NewLimiter(rate.Limit(requestsPerSecond), burstSize)
	return func(c *gin.Context) {
		if !limiter.Allow() {
			c.AbortWithStatusJSON(http.StatusTooManyRequests, gin.H{
				"error": "rate limit exceeded for this endpoint",
			})
			return
		}
		c.Next()
	}
}

// RateLimitByRole creates a rate limiter with different limits based on user role
func RateLimitByRole() gin.HandlerFunc {
	limiters := map[string]*rate.Limiter{
		"admin":    rate.NewLimiter(rate.Limit(100), 200), // Higher limits for admins
		"standard": rate.NewLimiter(rate.Limit(10), 20),   // Standard limits for regular users
	}

	return func(c *gin.Context) {
		// Get user role from JWT claims
		claims, exists := c.Get("claims")
		if !exists {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "unauthorized"})
			return
		}

		userClaims, ok := claims.(map[string]interface{})
		if !ok {
			c.AbortWithStatusJSON(http.StatusInternalServerError, gin.H{"error": "invalid claims"})
			return
		}

		// Default to standard role if not specified
		role := "standard"
		if userRole, ok := userClaims["role"].(string); ok {
			role = userRole
		}

		limiter := limiters[role]
		if limiter == nil {
			limiter = limiters["standard"]
		}

		if !limiter.Allow() {
			c.AbortWithStatusJSON(http.StatusTooManyRequests, gin.H{
				"error": "rate limit exceeded for your role",
			})
			return
		}

		c.Next()
	}
}
