package logger

import (
	"context"
	"fmt"
	"os"

	"github.com/google/uuid"
	"google.golang.org/grpc/grpclog"
	"google.golang.org/grpc/metadata"

	"github.com/sirupsen/logrus"
)

type Log struct {
	logger      *logrus.Logger
	logLevel    string
	serviceName string
}

const (
	SessionIDContextKey = "SESSION-ID" // sessionID is an id of a current user session
	RequestIDContextKey = "REQUEST-ID" // requestID is an id of a user request
	EndpointContextKey  = "ENDPOINT"   // endpoint is the endpoint in use
)

// NewLogger creates a logger with default settings for console logging. Default logLevel is Error.
// However, you can overwrite that by setting your designated log level to the LOG_LEVEL environment variable.
// This function will fail if LOG_LEVEL set to an undefined log level.
func NewLogger(logLevel, serviceName string, exitFunc *func(int)) *Log {
	logger := logrus.StandardLogger()
	if exitFunc != nil {
		logger.ExitFunc = *exitFunc
	}
	logLevel = getLogLevel(logLevel)
	logger.SetLevel(getLogrusLevel(logLevel))
	grpclog.SetLogger(logger) //nolint:staticcheck
	return &Log{
		logger:      logger,
		logLevel:    logLevel,
		serviceName: getServiceName(serviceName),
	}
}

// Log exports the configured logger ready to use.
func (l *Log) Log() *logrus.Logger {
	return l.logger
}

// WithContext exports the configured logger with fields extracted from context.Context
func (l *Log) WithContext(ctx context.Context) *logrus.Entry {
	var sessionID, requestID string
	md, ok := metadata.FromIncomingContext(ctx)
	if !ok {
		l.logger.Error("could not load metadata from context")
		return l.logger.WithFields(logrus.Fields{})
	}
	sessionIDs := md.Get(SessionIDContextKey)
	requestIDs := md.Get(RequestIDContextKey)

	if len(requestIDs) == 0 {
		requestID = uuid.New().String()
	} else {
		requestID = requestIDs[0]
	}

	if len(sessionIDs) == 0 {
		l.logger.Error("missing session id")
		return l.logger.WithField(RequestIDContextKey, requestID)
	}
	sessionID = sessionIDs[0]

	return l.logger.WithField(SessionIDContextKey, sessionID).WithField(RequestIDContextKey, requestID)
}

// getServiceName allows overwriting default service name 'hostname'
func getServiceName(serviceName string) string {
	if serviceName != "" {
		return serviceName
	}
	hostname, err := os.Hostname()
	if err != nil {
		return "unknown"
	}
	return hostname
}

// getLogLevel allows overwriting default log level 'Error'
func getLogLevel(logLevel string) string {
	if logLevel != "" {
		return logLevel
	}
	return os.Getenv("LOG_LEVEL")
}

func getLogrusLevel(logLevel string) logrus.Level {
	switch logLevel {
	case "": // not set
		return logrus.ErrorLevel
	case "panic":
		return logrus.PanicLevel
	case "fatal":
		return logrus.FatalLevel
	case "error":
		return logrus.ErrorLevel
	case "warn":
		return logrus.WarnLevel
	case "info":
		return logrus.InfoLevel
	case "debug":
		return logrus.DebugLevel
	case "trace":
		return logrus.TraceLevel
	}

	panic(fmt.Sprintf("LOG_LEVEL %s is not known", logLevel))
}
