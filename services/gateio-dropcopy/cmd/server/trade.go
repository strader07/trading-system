package main

import "fmt"

func (t *Trade) String() string {
	return fmt.Sprintf("ID: %v, Time: %v, Price: %v, Size: %v, Side: %s, Market: %s", t.ID, t.Time, t.Price, t.Size, t.Side, t.Market)
}

// Trade represents a market trade
type Trade struct {
	ID     int64
	Time   float64
	Price  float64
	Size   float64
	Side   string
	Market string
}
