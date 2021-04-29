package main

import (
	"os"
)

// Config defines the app settings
type Config struct {
	key          string
	secret       string
	redisHost    string
	redisPort    string
	expRedisHost string
	expRedisPort string
	expRedisPW   string
	// instruments: strings.Split(os.Getenv("INSTRUMENTS"), ","), // verify
}

// GetConfig retrieves the app config object
func GetConfig() *Config {
	key := os.Getenv("GATEKEY")
	secret := os.Getenv("GATESECRET")
	if len(key) == 0 {
		panic("Invalid GATEKEY")
	}
	if len(secret) == 0 {
		panic("Invalid GATESECRET")
	}

	return &Config{
		key:          os.Getenv("GATEKEY"),
		secret:       os.Getenv("GATESECRET"),
		redisHost:    os.Getenv("REDIS_NODE_ADDR"),
		redisPort:    os.Getenv("REDIS_NODE_TCP_PORT"),
		expRedisHost: os.Getenv("EXP_REDIS_NODE_ADDR"),
		expRedisPort: os.Getenv("EXP_REDIS_NODE_TCP_PORT"),
		expRedisPW:   os.Getenv("EXP_REDIS_PASSWORD"),
		// instruments: strings.Split(os.Getenv("INSTRUMENTS"), ","), // verify
	}
	// fill in what to subscribe to
}
