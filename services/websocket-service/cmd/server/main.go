package main

import (
	"fmt"
	"log"
	"net/http"

	"github.com/caarlos0/env"
	_logger "github.com/muwazana/backoffice/pkg/logger"
	"github.com/muwazana/backoffice/services/websocket-service/pkg/api"
)

type config struct {
	LogLevel    string `env:"LOG_LEVEL" envDefault:"info"`
	ServiceName string `env:"SERVICE_HOSTNAME,required"`
	Port        string `env:"SERVICE_PORT" envDefault:"4000"`
}

var (
	cfg    config
	logger *_logger.Log
)

func init() {
	err := env.Parse(&cfg)
	if err != nil {
		log.Fatalf("error parsing config: %+v", err)
	}

	exitFunc := func(_ int) {}
	logger = _logger.NewLogger(cfg.LogLevel, cfg.ServiceName, &exitFunc)
}

func main() {

	http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		_, _ = fmt.Fprintf(w, "OK")
	})

	// create router instance
	router := api.NewRouter()

	api.ListenToRedis(router)

	// handle all requests to /ws, upgrade to WebSocket via our router handler.
	http.Handle("/ws", router)

	// start server.
	err := http.ListenAndServe(fmt.Sprintf(":%s", cfg.Port), nil)
	if err != nil {
		logger.Log().Fatalf("error while listening %+v", err)
	}
}
