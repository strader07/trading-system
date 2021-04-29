package main

import "fmt"

func (b *Balance) String() string {
	return fmt.Sprintf("Available: %v, Freeze: %v, Symbol: %s", b.Available, b.Freeze, b.Symbol)
}

type Balance struct {
	Available float64 `json:"available"`
	Freeze    float64 `json:"freeze"`
	Symbol    string  `json:"coin"`
}
