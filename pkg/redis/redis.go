package redis

import (
	"github.com/caarlos0/env"
	"github.com/go-redis/redis"
)

type (
	redisConfig struct {
		Host string `env:"REDIS_NODE_ADDR" envDefault:"localhost"`
		Port string `env:"REDIS_NODE_TCP_PORT" envDefault:"6379"`
	}
)

var (
	config redisConfig
)

func init() {
	err := env.Parse(&config)
	if err != nil {
		panic(err)
	}
}

//New returns a redis Client
func New() *redis.Client {
	return redis.NewClient(&redis.Options{
		Addr: config.Host + ":" + config.Port,
	})
}
