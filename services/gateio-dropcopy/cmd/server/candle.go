package main

import (
	"fmt"
	"time"
)

func (c *Candle) String() string {
	return fmt.Sprintf("Period: %d Open: %f Close: %f High: %f Low: %f Last: %f Volume: %f, Quote Volume: %f Time: %d", c.Period, c.Open, c.Close, c.High, c.Low, c.Last, c.BaseVolume, c.QuoteVolume, c.Time.UnixNano())
}

// Candle type
type Candle struct {
	Period      int     `json:"period"`
	Open        float64 `json:"open"`
	Close       float64 `json:"close"`
	High        float64 `json:"high"`
	Low         float64 `json:"low"`
	Last        float64 `json:"last"`
	Change      float64 `json:"change"`
	QuoteVolume float64 `json:"quoteVolume"`
	BaseVolume  float64 `json:"baseVolume"`
	Time        time.Time
}

// type range int

// // range duration values
// const (
// 	minutely range = 0
// 	hourly   range = 1
// 	daily    range = 2
// )
