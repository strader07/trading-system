package api

import (
	"log"

	"github.com/gorilla/websocket"
)

// Message is a object used to pass data on sockets.
type Message struct {
	Name string      `json:"name"`
	Data interface{} `json:"data"`
}

// FindHandler is a type that defines handler finding functions.
type FindHandler func(Event) (Handler, bool)

// Client is a type that reads and writes on sockets.
type Client struct {
	Send        Message
	socket      *websocket.Conn
	findHandler FindHandler
}

// NewClient accepts a socket and returns an initialized Client.
func NewClient(socket *websocket.Conn, findHandler FindHandler) *Client {
	return &Client{
		socket:      socket,
		findHandler: findHandler,
	}
}

// Write receives messages from the channel and writes to the socket.
func (c *Client) Write() {
	msg := c.Send
	err := c.socket.WriteJSON(msg)
	c.socket.RemoteAddr()
	if err != nil {
		log.Printf("socket write error: %v\n", err)
	}
}

// Read intercepts messages on the socket and assigns them to a handler function.
func (c *Client) Read() {
	var msg Message
	for {
		// read incoming message from socket
		if err := c.socket.ReadJSON(&msg); err != nil {
			log.Printf("socket read error: %v\n", err)
			break
		}
		// assign message to a function handler
		if handler, found := c.findHandler(Event(msg.Name)); found {
			log.Printf("found %s", msg.Name)

			handler(c, msg.Data)
		}
	}
	log.Println("exiting read loop")

	// close interrupted socket connection
	err := c.socket.Close()
	if err != nil {
		log.Fatalf("error closing socket: %+v", err)
	}
}
