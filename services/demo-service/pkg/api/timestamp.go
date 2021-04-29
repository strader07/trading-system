package api

import (
	"time"

	"github.com/muwazana/backoffice/pkg/redis"

	_logger "github.com/muwazana/backoffice/pkg/logger"
	"github.com/robfig/cron/v3"
)

//StartTimestampCronJob .
func StartTimestampCronJob(logger *_logger.Log) (*cron.Cron, error) {
	utcTime, _ := time.LoadLocation("Etc/UTC")

	c := cron.New(cron.WithSeconds(), cron.WithLocation(utcTime))
	redisClient := redis.New()

	_, err := c.AddFunc("@every 1s", func() {
		t := time.Now()
		currentTime := t.String()

		_, err := redisClient.Publish("public:timestamp", currentTime).Result()
		if err != nil {
			logger.Log().Fatalf("%+v", err)
		}

		logger.Log().WithField("current", currentTime).Info("UTC current time")
	})

	return c, err
}
