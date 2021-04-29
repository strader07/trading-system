package main

import (
	"encoding/json"
	"log"
	"os"
	"os/signal"

	"github.com/go-redis/redis"
	"github.com/gorilla/websocket"
)

var redisClient *redis.Client

func publishCandle(candle *Candle, timeframe string) {
	out, err := json.Marshal(candle)
	if err != nil {
		log.Printf("Error marshalling Candle to JSON")
		panic(err)
	}
	channel := "BITMEX:BTCUSDP:candles:" + timeframe
	err = redisClient.Publish(channel, string(out)).Err()
	if err != nil {
		log.Printf("Error publishing to redis")
		panic(err)
	}
}

func connectRedis() *redis.Client {
	config := GetConfig()

	return redis.NewClient(&redis.Options{
		Addr: config.redisHost + ":" + config.redisPort,
	})
}

func main() {
	interrupt := make(chan os.Signal, 1)
	signal.Notify(interrupt, os.Interrupt)

	redisClient = connectRedis()

	// TODO:
	// - Subscribe to list of instruments
	// - Get fills

	bitmex := new(BitMEXClient)
	bitmex.connect("tradeBin5m:XBTUSD")

	for {
		select {
		case candle := <-bitmex.tradeBin5min:
			publishCandle(candle, "5m")
		case candle := <-bitmex.tradeBin15min:
			publishCandle(candle, "15m")
		case <-bitmex.done:
			log.Println("done")
			return
		case <-interrupt:
			log.Println("interrupt")
			// Cleanly close the connection by sending a close message and then
			// waiting (with timeout) for the server to close the connection.
			err := bitmex.ws.WriteMessage(websocket.CloseMessage, websocket.FormatCloseMessage(websocket.CloseNormalClosure, ""))
			if err != nil {
				log.Println("write close:", err)
				return
			}

			return
		}
	}

}
