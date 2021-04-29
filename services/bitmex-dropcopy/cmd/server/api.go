package main

import (
	"encoding/json"
	"log"
	"net/url"
	"time"

	"github.com/gorilla/websocket"
)

func min(a, b float64) float64 {
	if a < b {
		return a
	}
	return b
}

func max(a, b float64) float64 {
	if a > b {
		return a
	}
	return b
}

// BitMEXClient wraps around a connection to BitMEX
type BitMEXClient struct {
	ws            *websocket.Conn
	candlesQueue  Queue
	tradeBin5min  chan *Candle
	tradeBin15min chan *Candle
	done          chan struct{}
}

func (client *BitMEXClient) processMessage() {
	defer close(client.done)
	defer close(client.tradeBin5min)
	defer close(client.tradeBin15min)
	defer client.ws.Close()

	for {
		_, message, err := client.ws.ReadMessage()
		if err != nil {
			log.Printf("error read: %s", err)
			panic(err)
		}

		var v interface{}
		json.Unmarshal(message, &v)
		resp := v.(map[string]interface{})

		if success, ok := resp["success"]; ok {
			if success == false {
				error := "Failed to connect to: " + resp["subscribe"].(string)
				panic(error)
			}
		}

		if _, ok := resp["table"]; ok {
			dataList := resp["data"].([]interface{})
			data := dataList[0].(map[string]interface{})

			candle := &Candle{}
			candle.Open = data["open"].(float64)
			candle.High = data["high"].(float64)
			candle.Low = data["low"].(float64)
			candle.Close = data["close"].(float64)
			candle.Volume = data["volume"].(float64)
			candle.Vwap = data["vwap"].(float64)
			candle.Ts = time.Now().Unix()
			client.tradeBin5min <- candle

			client.candlesQueue.Push(*candle)

			if client.candlesQueue.len == maxQueueSize {
				front := client.candlesQueue.content[0]
				back := client.candlesQueue.content[maxQueueSize-1]

				candle15 := &Candle{}
				candle15.Open = front.Open
				candle15.Close = back.Close
				candle15.High = front.High
				candle15.Low = front.Low
				candle15.Ts = back.Ts

				for _, candle := range client.candlesQueue.content {
					candle15.High = max(candle15.High, candle.High)
					candle15.Low = min(candle15.Low, candle.Low)
					candle15.Volume += candle.Volume
				}

				client.tradeBin15min <- candle15
				client.candlesQueue.Clear()
			}
		}
	}
}

func (client *BitMEXClient) ping() {
	ticker := time.NewTicker(60 * time.Second)
	defer ticker.Stop()
	for {
		select {
		case <-ticker.C:
			if err := client.ws.WriteMessage(websocket.PingMessage, nil); err != nil {
				return
			}
		}
	}
}

func (client *BitMEXClient) connect(topic string) {
	client.tradeBin5min = make(chan *Candle)
	client.tradeBin15min = make(chan *Candle)
	client.done = make(chan struct{})

	addr := "www.bitmex.com:443"
	u := url.URL{Scheme: "wss", Host: addr, Path: "/realtime"}
	log.Printf("connecting to %s", u.String())

	ws, _, err := websocket.DefaultDialer.Dial(u.String(), nil)
	if err != nil {
		log.Fatal("dial:", err)
	}

	client.ws = ws

	if _, _, err := ws.ReadMessage(); err != nil {
		panic(err)
	}

	go client.processMessage()
	go client.ping()

	type commandStruct struct {
		Op   string   `json:"op"`
		Args []string `json:"args"`
	}
	command := &commandStruct{
		Op:   "subscribe",
		Args: []string{topic},
	}
	connectionErr := ws.WriteJSON(command)
	if connectionErr != nil {
		log.Println("write error:", connectionErr)
		panic(connectionErr)
	}
}
