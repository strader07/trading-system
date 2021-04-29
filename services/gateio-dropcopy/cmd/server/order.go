package main

import "fmt"

func (o *Order) String() string {
	return fmt.Sprintf("OrderId: %v, Market: %s, Price: %v, Size: %v, Side: %s, Status: %s, Type: %s, LeavesQty: %v, FilledTotal: %v, FillPrice: %v", o.OrderId, o.Market, o.Price, o.Size, o.Side, o.Status, o.Type, o.LeavesQty, o.FilledTotal, o.FillPrice)
}

type Order struct {
	OrderId     int64   `json:"id"`
	Market      string  `json:"symbol"`
	Price       float64 `json:"price"`
	Size        float64 `json:"size"`
	Side        string  `json:"side"`
	Status      string  `json:"status"`
	Type        string  `json:"type"`
	LeavesQty   float64 `json:"remaining_size"`
	FilledTotal float64 `json:"filled_size"`
	FillPrice   float64 `json:"avg_fill_price"`
}
