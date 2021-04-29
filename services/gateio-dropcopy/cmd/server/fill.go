package main

import "fmt"

func (f *Fill) String() string {
	return fmt.Sprintf("OrderId: %v, Market: %s, Price: %v, Size: %v, Side: %s, Fee: %v, Time: %v", f.OrderId, f.Market, f.Price, f.Size, f.Side, f.Fee, f.Time)
}

type Fill struct {
	OrderId int64   `json:"order_id"`
	Market  string  `json:"market"`
	Price   float64 `json:"price"`
	Size    float64 `json:"size"`
	Side    string  `json:"side"`
	Fee     float64 `json:"fee"`
	Time    float64 `json:"time"`
}
