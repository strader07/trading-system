package main

// Candle representation over a timeperiod
type Candle struct {
	Open   float64
	High   float64
	Low    float64
	Close  float64
	Volume float64
	Vwap   float64
	Ts     int64
}
