package main

import (
	"bytes"
	"crypto/hmac"
	"crypto/sha512"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"net/url"
	"strconv"
	"time"

	"github.com/gorilla/websocket"
)

// Messages IDs
const (
	AUTH             int = 1
	TRADESUB         int = 2
	BALANCESUB       int = 3
	BALANCEQUERY     int = 4
	ORDERSUB         int = 5
	TICKERDAILYQUERY int = 6
	TICKER4HOURQUERY int = 7
)

// GATEIOClient wraps around a connection to GATEIO
type GATEIOClient struct {
	ws              *websocket.Conn
	tradesChan      chan *Trade
	balanceChan     chan *Balance
	positionsChan   chan *Position
	fillChan        chan *Fill
	ordersChan      chan *[]Order
	orderUpdateChan chan *Order
	tickerRangeChan chan *Candle
	symbol          string
	instrument      string
	coin            string
	redisCache      *RedisCache
	done            chan struct{}
}

func (client *GATEIOClient) populateCandle(data map[string]interface{}) Candle {
	candle := &Candle{}
	candle.Period = int(data["period"].(float64))
	candle.Open, _ = strconv.ParseFloat(data["open"].(string), 64)
	candle.Close, _ = strconv.ParseFloat(data["close"].(string), 64)
	candle.High, _ = strconv.ParseFloat(data["high"].(string), 64)
	candle.Low, _ = strconv.ParseFloat(data["low"].(string), 64)
	candle.Last, _ = strconv.ParseFloat(data["last"].(string), 64)
	candle.Change, _ = strconv.ParseFloat(data["change"].(string), 64)
	candle.QuoteVolume, _ = strconv.ParseFloat(data["quoteVolume"].(string), 64)
	candle.BaseVolume, _ = strconv.ParseFloat(data["baseVolume"].(string), 64)
	loc, _ := time.LoadLocation("UTC")
	now := time.Now().In(loc)
	candle.Time = now
	return *candle
}

func (client *GATEIOClient) processMessage() {
	defer close(client.done)
	defer close(client.tradesChan)
	defer close(client.balanceChan)
	defer close(client.positionsChan)
	defer close(client.fillChan)
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

		if err, ok := resp["error"]; ok && err != nil {
			errjson, _ := json.Marshal(resp)
			e := "Error: " + string(errjson)
			panic(e)
		}

		if _, ok := resp["id"]; ok && resp["id"] != nil {
			if int(resp["id"].(float64)) == AUTH {
				log.Printf("Authentication successful")
				// subscribe after auth
				client.subscribe()
			} else if int(resp["id"].(float64)) == BALANCEQUERY {
				data := resp["result"].(map[string]interface{})

				for key, value := range data {
					slice := value.(map[string]interface{})

					balance := &Balance{}
					balance.Available, _ = strconv.ParseFloat(slice["available"].(string), 64)
					balance.Freeze, _ = strconv.ParseFloat(slice["freeze"].(string), 64)
					balance.Symbol = key

					client.balanceChan <- balance
				}
			} else if int(resp["id"].(float64)) == TICKER4HOURQUERY {
				data := resp["result"].(map[string]interface{})
				candle := client.populateCandle(data)
				// candle.Period = 1
				client.tickerRangeChan <- &candle
			} else if int(resp["id"].(float64)) == TICKERDAILYQUERY {
				data := resp["result"].(map[string]interface{})
				candle := client.populateCandle(data)
				// candle.Period = 2
				client.tickerRangeChan <- &candle
			}
		}

		if _, ok := resp["method"]; ok {
			if resp["method"].(string) == "trades.update" {
				dataList := resp["params"].([]interface{})
				data := dataList[1].([]interface{})
				symbol := dataList[0].(string)

				for i := range data {
					rData := data[len(data)-i-1] // reverse range
					slice := rData.(map[string]interface{})
					trade := &Trade{}
					trade.ID = int64(slice["id"].(float64))
					trade.Time = slice["time"].(float64)
					trade.Price, _ = strconv.ParseFloat(slice["price"].(string), 64)
					trade.Size, _ = strconv.ParseFloat(slice["amount"].(string), 64)
					trade.Side = slice["type"].(string)
					trade.Market = symbol

					client.tradesChan <- trade
				}
			} else if resp["method"].(string) == "balance.update" {
				dataList := resp["params"].([]interface{})
				for _, b := range dataList {
					data := b.(map[string]interface{})

					for key, value := range data {
						slice := value.(map[string]interface{})

						balance := &Balance{}
						balance.Available, _ = strconv.ParseFloat(slice["available"].(string), 64)
						balance.Freeze, _ = strconv.ParseFloat(slice["freeze"].(string), 64)
						balance.Symbol = key

						if client.coin == key {
							position := &Position{}
							position.AvgPx = 0
							position.Instrument = client.instrument
							if balance.Available > client.redisCache.StartingBalance {
								position.Size = balance.Available - client.redisCache.StartingBalance
								position.Side = "buy"
								if client.redisCache.FillsCount > 0 {
									position.AvgPx = client.redisCache.FillsTotalPx / float64(client.redisCache.FillsCount)
								}
							} else if balance.Available < client.redisCache.StartingBalance {
								position.Size = client.redisCache.StartingBalance - balance.Available
								position.Side = "sell"
								if client.redisCache.FillsCount > 0 {
									position.AvgPx = client.redisCache.FillsTotalPx / float64(client.redisCache.FillsCount)
								}
							} else {
								// TODO handle 0 position
								position.Size = 0
							}

							client.positionsChan <- position
						}

						client.balanceChan <- balance
					}
				}
			} else if resp["method"].(string) == "order.update" {
				dataList := resp["params"].([]interface{})
				event := int(dataList[0].(float64))
				data := dataList[1].(map[string]interface{})
				orderId := int64(data["id"].(float64))

				go client.getOpenOrders()
				go client.getOrder(orderId)

				if event != 1 {
					fill := &Fill{}
					fill.OrderId = orderId
					fill.Market = data["market"].(string)
					fill.Price, _ = strconv.ParseFloat(data["price"].(string), 64)
					fill.Size, _ = strconv.ParseFloat(data["filledAmount"].(string), 64)

					switch side := int(data["type"].(float64)); side {
					case 1:
						fill.Side = "sell"
					default:
						fill.Side = "buy"
					}
					fill.Fee, _ = strconv.ParseFloat(data["dealFee"].(string), 64)
					fill.Time = data["mtime"].(float64)

					client.fillChan <- fill
				}
			}
		}
	}
}

func (client *GATEIOClient) ping() {
	ticker := time.NewTicker(15 * time.Second)
	id := 100
	defer ticker.Stop()
	for {
		select {
		case <-ticker.C:
			type pingStruct struct {
				Id     int      `json:"id"`
				Method string   `json:"method"`
				Params []string `json:"params"`
			}

			command := &pingStruct{
				Id:     id,
				Method: "server.ping",
				Params: []string{},
			}
			id = id + 1
			err := client.ws.WriteJSON(command)
			if err != nil {
				return
			}
		}
	}
}

func (client *GATEIOClient) auth() {
	type authStruct struct {
		Id     int           `json:"id"`
		Method string        `json:"method"`
		Params []interface{} `json:"params"`
	}

	config := GetConfig()
	nonce := int64(time.Now().UnixNano() / 1000000)

	message := strconv.FormatInt(nonce, 10)

	h := hmac.New(sha512.New, []byte(config.secret))
	h.Write([]byte(message))
	signature := hex.EncodeToString(h.Sum(nil))

	command := &authStruct{
		Id:     AUTH,
		Method: "server.sign",
		Params: []interface{}{
			config.key,
			signature,
			nonce,
		},
	}
	err := client.ws.WriteJSON(command)
	if err != nil {
		return
	}

}

func (client *GATEIOClient) subscribe() {
	type commandStruct struct {
		Id     int           `json:"id"`
		Method string        `json:"method"`
		Params []interface{} `json:"params"`
	}

	// Trades subscribe

	// Command := &commandStruct{
	// 	Id:     TRADESUB,
	// 	Method: "trades.subscribe",
	// 	Params: []interface{}{
	// 		client.symbol,
	// 	},
	// }

	// ConnectionErr := client.ws.WriteJSON(Command)
	// if ConnectionErr != nil {
	// 	log.Println("write error:", ConnectionErr)
	// 	panic(ConnectionErr)
	// }

	// Balance query

	Command := &commandStruct{
		Id:     BALANCEQUERY,
		Method: "balance.query",
		Params: []interface{}{},
	}

	ConnectionErr := client.ws.WriteJSON(Command)
	if ConnectionErr != nil {
		log.Println("write error:", ConnectionErr)
		panic(ConnectionErr)
	}

	// Balance subscribe

	Command = &commandStruct{
		Id:     BALANCESUB,
		Method: "balance.subscribe",
		Params: []interface{}{},
	}

	ConnectionErr = client.ws.WriteJSON(Command)
	if ConnectionErr != nil {
		log.Println("write error:", ConnectionErr)
		panic(ConnectionErr)
	}

	// Orders subscribe for fills

	Command = &commandStruct{
		Id:     ORDERSUB,
		Method: "order.subscribe",
		Params: []interface{}{
			client.symbol,
		},
	}

	ConnectionErr = client.ws.WriteJSON(Command)
	if ConnectionErr != nil {
		log.Println("write error:", ConnectionErr)
		panic(ConnectionErr)
	}
}

func (client *GATEIOClient) connect(symbol string, instrument string, coin string, redisCache *RedisCache) {
	client.tradesChan = make(chan *Trade)
	client.balanceChan = make(chan *Balance)
	client.positionsChan = make(chan *Position)
	client.fillChan = make(chan *Fill)
	client.ordersChan = make(chan *[]Order)
	client.orderUpdateChan = make(chan *Order)
	client.tickerRangeChan = make(chan *Candle)
	client.done = make(chan struct{})

	addr := "ws.gate.io"
	u := url.URL{Scheme: "wss", Host: addr, Path: "/v4"}
	log.Printf("connecting to %s", u.String())

	ws, _, err := websocket.DefaultDialer.Dial(u.String(), nil)
	if err != nil {
		log.Fatal("dial:", err)
	}

	client.ws = ws
	client.symbol = symbol
	client.instrument = instrument
	client.coin = coin
	client.redisCache = redisCache

	// auth
	client.auth()

	go client.processMessage()
	go client.ping()
}

func (client *GATEIOClient) request(
	path string, method string,
	body string) (req *http.Request, err error) {

	config := GetConfig()

	requestUrl, err := url.Parse(path)
	if err != nil {
		return nil, err
	}

	h := sha512.New()
	if body != "" {
		h.Write([]byte(body))
	}

	bodyReader := bytes.NewReader([]byte(body))
	hashedPayload := hex.EncodeToString(h.Sum(nil))

	t := strconv.FormatInt(time.Now().Unix(), 10)
	rawQuery, err := url.QueryUnescape(requestUrl.RawQuery)
	if err != nil {
		return nil, err
	}
	msg := fmt.Sprintf("%s\n%s\n%s\n%s\n%s", method, requestUrl.Path, rawQuery, hashedPayload, t)
	mac := hmac.New(sha512.New, []byte(config.secret))
	mac.Write([]byte(msg))
	sign := hex.EncodeToString(mac.Sum(nil))

	req, err = http.NewRequest(method, requestUrl.String(), bodyReader)
	req.Header.Add("KEY", config.key)
	req.Header.Add("SIGN", sign)
	req.Header.Add("Timestamp", t)
	req.Header.Add("Accept", "application/json")
	req.Header.Add("Content-Type", "application/json")

	if err != nil {
		return nil, err
	}

	return req, nil
}

func (client *GATEIOClient) getOpenOrders() {
	host := "https://api.gateio.ws"
	prefix := "/api/v4"

	url := "/spot/orders"
	query := "currency_pair=" + client.symbol + "&status=open"

	req, err := client.request(host+prefix+url+"?"+query, "GET", "")

	if err != nil {
		log.Printf("Error creating request: %s", err)
		panic(err)
	}

	httpClient := http.Client{}

	resp, err := httpClient.Do(req)

	if err != nil {
		log.Printf("Error request: %s", err)
		panic(err)
	}

	body, err := ioutil.ReadAll(resp.Body)

	if err != nil {
		log.Printf("Error read response: %s", err)
		panic(err)
	}

	var v interface{}
	json.Unmarshal(body, &v)
	dataList := v.([]interface{})

	var allOrders []Order

	for _, o := range dataList {
		data := o.(map[string]interface{})

		order := &Order{}
		id, _ := strconv.ParseFloat(data["id"].(string), 64)
		order.OrderId = int64(id)
		order.Market = data["currency_pair"].(string)
		order.Price, _ = strconv.ParseFloat(data["price"].(string), 64)
		order.Size, _ = strconv.ParseFloat(data["amount"].(string), 64)
		order.Side = data["side"].(string)
		order.Status = data["status"].(string)
		order.Type = data["type"].(string)
		order.LeavesQty, _ = strconv.ParseFloat(data["left"].(string), 64)
		order.FilledTotal, _ = strconv.ParseFloat(data["filled_total"].(string), 64)
		order.FillPrice, _ = strconv.ParseFloat(data["fill_price"].(string), 64)

		allOrders = append(allOrders, *order)
	}

	client.ordersChan <- &allOrders
}

func (client *GATEIOClient) getOrder(orderId int64) {
	host := "https://api.gateio.ws"
	prefix := "/api/v4"

	url := "/spot/orders/" + strconv.FormatInt(orderId, 10)
	query := "currency_pair=" + client.symbol

	req, err := client.request(host+prefix+url+"?"+query, "GET", "")

	if err != nil {
		log.Printf("Error creating request: %s", err)
		panic(err)
	}

	httpClient := http.Client{}

	resp, err := httpClient.Do(req)
	if err != nil {
		log.Printf("Error request: %s", err)
		panic(err)
	}

	body, err := ioutil.ReadAll(resp.Body)

	if err != nil {
		log.Printf("Error read response: %s", err)
		panic(err)
	}

	var v interface{}
	json.Unmarshal(body, &v)
	data := v.(map[string]interface{})

	order := &Order{}
	id, _ := strconv.ParseFloat(data["id"].(string), 64)
	order.OrderId = int64(id)
	order.Market = data["currency_pair"].(string)
	order.Price, _ = strconv.ParseFloat(data["price"].(string), 64)
	order.Size, _ = strconv.ParseFloat(data["amount"].(string), 64)
	order.Side = data["side"].(string)
	order.Status = data["status"].(string)
	order.Type = data["type"].(string)
	order.LeavesQty, _ = strconv.ParseFloat(data["left"].(string), 64)
	order.FilledTotal, _ = strconv.ParseFloat(data["filled_total"].(string), 64)
	order.FillPrice, _ = strconv.ParseFloat(data["fill_price"].(string), 64)

	client.orderUpdateChan <- order
}

func (client *GATEIOClient) getDailyRange() {
	type tickerStruct struct {
		ID     int           `json:"id"`
		Method string        `json:"method"`
		Params []interface{} `json:"params"`
	}

	Command := &tickerStruct{
		ID:     TICKERDAILYQUERY,
		Method: "ticker.query",
		Params: []interface{}{
			client.symbol,
			86400,
		},
	}

	ConnectionErr := client.ws.WriteJSON(Command)
	if ConnectionErr != nil {
		log.Println("write error:", ConnectionErr)
		panic(ConnectionErr)
	}
}

func (client *GATEIOClient) getFourHourRange() {
	type tickerStruct struct {
		ID     int           `json:"id"`
		Method string        `json:"method"`
		Params []interface{} `json:"params"`
	}

	Command := &tickerStruct{
		ID:     TICKER4HOURQUERY,
		Method: "ticker.query",
		Params: []interface{}{
			client.symbol,
			14400,
		},
	}

	ConnectionErr := client.ws.WriteJSON(Command)
	if ConnectionErr != nil {
		log.Println("write error:", ConnectionErr)
		panic(ConnectionErr)
	}
}
