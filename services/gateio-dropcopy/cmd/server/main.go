package main

import (
	"encoding/json"
	"fmt"
	"log"
	"math"
	"os"
	"os/signal"
	"time"
	"strconv"
    "strings"

	"github.com/jasonlvhit/gocron"

	"github.com/go-redis/redis"
	"github.com/gorilla/websocket"
)

var redisClient *redis.Client
var expRedisClient *redis.Client
var redisCache *RedisCache

func publishTrade(trade *Trade) {
	messageID := fmt.Sprintf("%v-%v", int64(trade.Time*1000), trade.ID)
	channel := "stream:gateio:trades:JNTUSDT"
	expRedisClient.XAdd(&redis.XAddArgs{
		Stream: channel,
		MaxLen: 40,
		ID:     messageID,
		Values: map[string]interface{}{"price": trade.Price, "size": trade.Size, "side": trade.Side},
	})
}

func publishFill(fill *Fill) {
	type Payload struct {
		Data *Fill  `json:"data"`
		Date string `json:"date"`
	}

	date := time.Now().Format("2/1/2006 15:4:5 -07:00")

	payload := &Payload{
		Data: fill,
		Date: date,
	}
	payloadJSON, err := json.Marshal(payload)
	if err != nil {
		log.Printf("Error marshalling fills Payload to JSON")
		panic(err)
	}

	channel := "stream:gateio:fills"
	err = redisClient.Publish(channel, string(payloadJSON)).Err()
	if err != nil {
		log.Printf("Error publishing fills to redis")
		panic(err)
	}

	redisCache.LastFillPx = fill.Price
	redisCache.FillsTotalPx = redisCache.FillsTotalPx + fill.Price
	redisCache.FillsCount = redisCache.FillsCount + 1

	cache := map[string]interface{}{
		"last_fill_px":   redisCache.LastFillPx,
		"fills_total_px": redisCache.FillsTotalPx,
		"fills_count":    redisCache.FillsCount,
	}
	err = expRedisClient.HMSet("gateio:poscache:JNTUSDT", cache).Err()
	if err != nil {
		log.Printf("Error publishing cache to redis")
		panic(err)
	}
}

func publishOrderUpdate(order *Order) {
	type Payload struct {
		Data *Order `json:"data"`
		Date string `json:"date"`
	}

	date := time.Now().Format("2/1/2006 15:4:5 -07:00")

	payload := &Payload{
		Data: order,
		Date: date,
	}
	payloadJSON, err := json.Marshal(payload)
	if err != nil {
		log.Printf("Error marshalling updates Payload to JSON")
		panic(err)
	}

	channel := "stream:gateio:orders"
	err = redisClient.Publish(channel, string(payloadJSON)).Err()
	if err != nil {
		log.Printf("Error publishing updates to redis")
		panic(err)
	}
}

func publishOrders(orders *[]Order) {
	type Payload struct {
		Data *[]Order `json:"data"`
		Date string   `json:"date"`
	}

	date := time.Now().Format("2/1/2006 15:4:5 -07:00")

	payload := &Payload{
		Data: &[]Order{},
		Date: date,
	}
	if len(*orders) > 0 {
		payload = &Payload{
			Data: orders,
			Date: date,
		}
	}

	payloadJSON, err := json.Marshal(payload)
	if err != nil {
		log.Printf("Error marshalling orders Payload to JSON")
		panic(err)
	}

	channel := "public:gateio:orders"
	err = redisClient.Publish(channel, string(payloadJSON)).Err()
	if err != nil {
		log.Printf("Error publishing orders to redis")
		panic(err)
	}
}

func publishBalance(balance *Balance) {
	payload, err := json.Marshal(balance)
	if err != nil {
		log.Printf("Error marshalling balance to JSON")
		panic(err)
	}

	channel := "public:gateio:wallets"
	err = redisClient.Publish(channel, string(payload)).Err()
	if err != nil {
		log.Printf("Error publishing balance to redis")
		panic(err)
	}
}

func publishRange(candle *Candle, key string) {
	ticker := map[string]interface{}{
		"open":        candle.Open,
		"close":       candle.Close,
		"high":        candle.High,
		"low":         candle.Low,
		"volume":      math.Round(candle.BaseVolume*100) / 100,  // 2dp
		"quoteVolume": math.Round(candle.QuoteVolume*100) / 100, // 2dp
		"time":        candle.Time.Unix(),
	}
	err := expRedisClient.HMSet(key, ticker).Err()
	if err != nil {
		log.Printf("Error publishing candle to redis")
		panic(err)
	}
}

func publishPosition(position *Position) {
	key := fmt.Sprintf("gateio:positions:%s", position.Instrument)
	cache_key := fmt.Sprintf("gateio:poscache:%s", position.Instrument)

	side, err := expRedisClient.HGet(key, "side").Result()
	if err == nil {
		// reverted position
		if side != position.Side {
			cache := map[string]interface{}{
				"fills_total_px": redisCache.LastFillPx,
				"fills_count":    1,
			}
			cache_err := expRedisClient.HMSet(cache_key, cache).Err()
			if cache_err != nil {
				log.Printf("Error publishing cache to redis")
				panic(err)
			}

			position.AvgPx = redisCache.LastFillPx
		}
	}

	pos := map[string]interface{}{
		"net_size":  position.Size,
		"side":      position.Side,
		"avg_price": position.AvgPx,
	}

	err = expRedisClient.HMSet(key, pos).Err()
	if err != nil {
		log.Printf("Error publishing position to redis")
		panic(err)
	}
}

func connectRedis() *redis.Client {
	config := GetConfig()

	return redis.NewClient(&redis.Options{
		Addr: config.redisHost + ":" + config.redisPort,
	})
}

func connectExpRedis() *redis.Client {
	config := GetConfig()

	return redis.NewClient(&redis.Options{
		Addr:     config.expRedisHost + ":" + config.expRedisPort,
		Password: config.expRedisPW,
	})
}

func publishMarketConfig() {
	log.Println("Publishing daily market config.")
	key := "gateio:JNTUSDT"
	marketConfig := map[string]interface{}{
		"market":          "JNT_USDT",
		"instrument":      "JNTUSDT",
		"tick_size":       "0.0001",
		"min_size":        "0.0001",
		"price_precision": "0.0001",
		"size_precision":  "0.0001",
		"maker_fee":       "0.002",
		"taker_fee":       "0.002",
		"mm_size":         "0",
		"enabled":         "1",
		"clOrdID":         "0",
	}
	clOrdID, err := expRedisClient.HGet(key, "clOrdID").Result()
	if err == nil {
		marketConfig["clOrdID"] = clOrdID
	}

	err = expRedisClient.HMSet(key, marketConfig).Err()
	if err != nil {
		log.Printf("Error publishing to redis")
		panic(err)
	}
}

func getRedisCache() {
	key := "gateio:starting_balance:JNT"
	cache_key := "gateio:poscache:JNTUSDT"
	
	starting_balance, err := expRedisClient.HGet(key, "balance").Result()
	if err != nil {
		log.Printf("Error getting initial balance from redis")
		panic(err)
	}
	redisCache.StartingBalance, _ = strconv.ParseFloat(starting_balance, 64)

	last_fill_px, err := expRedisClient.HGet(cache_key, "last_fill_px").Result()
	if err != nil {
		redisCache.LastFillPx = 0
	} else {
		redisCache.LastFillPx, _ = strconv.ParseFloat(last_fill_px, 64)
	}

	fills_total_px, err := expRedisClient.HGet(cache_key, "fills_total_px").Result()
	if err != nil {
		redisCache.FillsTotalPx = 0
	} else {
		redisCache.FillsTotalPx, _ = strconv.ParseFloat(fills_total_px, 64)
	}

	fills_count, err := expRedisClient.HGet(cache_key, "fills_count").Result()
	if err != nil {
		redisCache.FillsCount = 0
	} else {
		redisCache.FillsCount, _ = strconv.ParseInt(fills_count, 10, 64)
	}
}

func main() {
	interrupt := make(chan os.Signal, 1)
	signal.Notify(interrupt, os.Interrupt)

	redisClient = connectRedis()
	expRedisClient = connectExpRedis()

	redisCache = &RedisCache{}
	getRedisCache()

	symbol := "JNT_USDT"
	instrument := "JNTUSDT"
	coins := strings.Split(symbol, "_")

	// TODO:
	// - Subscribe to list of instruments

	gateio := new(GATEIOClient)
	gateio.connect(symbol, instrument, coins[0], redisCache)

	publishMarketConfig()
	gateio.getDailyRange()
	midnightScheduler := gocron.NewScheduler()
	midnightScheduler.Every(1).Day().At("00:00").Do(func() {
		log.Println("Running midnight scheduler.")
		publishMarketConfig()
		gateio.getDailyRange()
	})

	gateio.getFourHourRange()
	t := time.Date(2020, time.January, 0, 0, 0, 0, 0, time.UTC)
	gocron.Every(4).Hour().From(&t).Do(func() {
		log.Println("Running 4 hour scheduler.")
		gateio.getFourHourRange()
	})

	for {
		select {
		case trade := <-gateio.tradesChan:
			publishTrade(trade)
		case balance := <-gateio.balanceChan:
			publishBalance(balance)
		case position := <-gateio.positionsChan:
			publishPosition(position)
		case fill := <-gateio.fillChan:
			publishFill(fill)
		case order := <-gateio.orderUpdateChan:
			publishOrderUpdate(order)
		case allOrder := <-gateio.ordersChan:
			publishOrders(allOrder)
		case candle := <-gateio.tickerRangeChan:
			fmt.Println(candle)
			if candle.Period == 14400 {
				publishRange(candle, "gateio:ticker:4h:JNTUSDT")
			} else if candle.Period == 86400 {
				publishRange(candle, "gateio:ticker:24h:JNTUSDT")
			}
		case <-gateio.done:
			log.Println("done")
			return
		case <-midnightScheduler.Start():
			return
		case <-interrupt:
			log.Println("interrupt")
			// Cleanly close the connection by sending a close message and then
			// waiting (with timeout) for the server to close the connection.
			err := gateio.ws.WriteMessage(websocket.CloseMessage, websocket.FormatCloseMessage(websocket.CloseNormalClosure, ""))
			if err != nil {
				log.Println("write close:", err)
				return
			}

			return
		}
	}

}
