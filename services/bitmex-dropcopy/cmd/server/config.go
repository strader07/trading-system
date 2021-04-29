package main

import (
	"os"
)

// Config defines the app settings
type Config struct {
	key       string
	secret    string
	redisHost string
	redisPort string
	redisPW   string
	// instruments []string
}

// GetConfig retrieves the app config object
func GetConfig() *Config {
	return &Config{
		key:       os.Getenv("BITMEXKEY"),
		secret:    os.Getenv("BITMEXSECRET"),
		redisHost: os.Getenv("REDIS_NODE_ADDR"),
		redisPort: os.Getenv("REDIS_NODE_TCP_PORT"),
		redisPW:   os.Getenv("REDISPW"),
		// instruments: strings.Split(os.Getenv("INSTRUMENTS"), ","), // verify
	}
	// fill in what to subscribe to
}
