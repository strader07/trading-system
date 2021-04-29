package main

import "fmt"

func (p *Position) String() string {
	return fmt.Sprintf("Size: %v, Side: %s, AvgPx: %v, Instrument: %s", p.Size, p.Side, p.AvgPx, p.Instrument)
}

type Position struct {
	Size       float64 `json:"net_size"`
	Side       string  `json:"side"`
	AvgPx      float64 `json:"avg_price"`
	Instrument string  `json:"instrument"`
}
