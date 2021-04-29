package api

import (
	"fmt"
	"github.com/go-redis/redis"
	_redis "github.com/muwazana/backoffice/pkg/redis"
)

func ListenToRedis(router *Router) {
	redisClient := _redis.New()
	pubsub := redisClient.PSubscribe("public*")

	go func() {
		for {
			read(pubsub, router)
		}
	}()
}

func read(pubsub *redis.PubSub, router *Router) {
	msg, err := pubsub.ReceiveMessage()
	if err != nil {
		return
	}

	fmt.Printf("Channel: %s\n", msg.Channel)
	fmt.Printf("Payload: %s\n", msg.Payload)

	router.sendToAll(msg)
}
