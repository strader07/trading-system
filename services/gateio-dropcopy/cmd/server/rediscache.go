package main

import "fmt"

func (rc *RedisCache) String() string {
	return fmt.Sprintf("StartingBalance: %v, LastFillPx: %v, FillsTotalPx: %v, FillsCount: %v", rc.StartingBalance, rc.LastFillPx, rc.FillsTotalPx, rc.FillsCount)
}

type RedisCache struct {
	StartingBalance     float64
	LastFillPx			float64
	FillsTotalPx   		float64
	FillsCount     		int64
}