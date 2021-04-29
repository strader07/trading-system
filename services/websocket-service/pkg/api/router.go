package api

import (
	"fmt"
	"github.com/go-redis/redis"
	"log"
	"net/http"

	"github.com/gorilla/websocket"
)

// Handler is a type representing functions which resolve requests.
type Handler func(*Client, interface{})

// Event is a type representing request names.
type Event string

// Router is a message routing object mapping events to function handlers.
type Router struct {
	clients map[string]*Client
	rules   map[Event]Handler // rules maps events to functions.
}

// NewRouter returns an initialized Router.
func NewRouter() *Router {
	return &Router{
		clients: make(map[string]*Client, 0),
		rules:   make(map[Event]Handler),
	}
}

// ServeHTTP creates the socket connection and begins the read routine.
func (rt *Router) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	// configure upgrader
	fmt.Println(r.RemoteAddr)
	upgrader := websocket.Upgrader{
		ReadBufferSize:  1024,
		WriteBufferSize: 1024,
		// accept all?
		CheckOrigin: func(r *http.Request) bool { return true },
	}

	// upgrade connection to socket
	socket, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Printf("socket server configuration error: %v\n", err)
		w.WriteHeader(http.StatusInternalServerError)
		return
	}

	client := NewClient(socket, rt.FindHandler)
	rt.clients[r.RemoteAddr] = client
	// running method for reading from sockets, in main routine
	client.Read()
}

// FindHandler implements a handler finding function for router.
func (rt *Router) FindHandler(event Event) (Handler, bool) {
	handler, found := rt.rules[event]
	return handler, found
}

// Handle is a function to add handlers to the router.
func (rt *Router) Handle(event Event, handler Handler) {
	// store in to router rules
	rt.rules[event] = handler
}

func (rt *Router) sendToAll(msg *redis.Message) {
	for addr, client := range rt.clients {
		fmt.Printf("Address: %s\n", addr)
		client.Send = Message{Name: msg.Channel, Data: msg.Payload}
		client.Write()
	}
}
