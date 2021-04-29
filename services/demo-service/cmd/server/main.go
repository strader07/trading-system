package main

import (
	"log"
	"os"
	"os/signal"

	"github.com/caarlos0/env"
	_logger "github.com/muwazana/backoffice/pkg/logger"
	"github.com/muwazana/backoffice/services/demo-service/pkg/api"
)

type config struct {
	LogLevel    string `env:"LOG_LEVEL" envDefault:"info"`
	ServiceName string `env:"SERVICE_HOSTNAME,required"`
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
	c, err := api.StartTimestampCronJob(logger)
	if err != nil {
		logger.Log().Fatal(err)
	}
	// Start the cron-job
	go c.Start()

	sig := make(chan os.Signal)
	signal.Notify(sig, os.Interrupt, os.Kill)
	<-sig
}
