package main

const maxQueueSize int = 3

// Queue holding MaxQueueSize candles
type Queue struct {
	content   [maxQueueSize]Candle
	readHead  int
	writeHead int
	len       int
}

// Push a new candle
func (q *Queue) Push(e Candle) bool {
	if q.len >= maxQueueSize {
		return false
	}
	q.content[q.writeHead] = e
	q.writeHead = (q.writeHead + 1) % maxQueueSize
	q.len++
	return true
}

// Pop a candle in FIFO fashion
func (q *Queue) Pop() (Candle, bool) {
	if q.len <= 0 {
		return Candle{}, false
	}
	result := q.content[q.readHead]
	q.content[q.readHead] = Candle{}
	q.readHead = (q.readHead + 1) % maxQueueSize
	q.len--
	return result, true
}

// Clear the queue's content
func (q *Queue) Clear() {
	for i := range q.content {
		q.content[i] = Candle{}
	}
	q.readHead = 0
	q.writeHead = 0
	q.len = 0
}

// Front returns the element at the front of the queue
func (q *Queue) Front() Candle {
	if q.len <= 0 {
		return Candle{}
	}
	return q.content[q.writeHead]
}

// Back returns the element at the back of the queue
func (q *Queue) Back() Candle {
	if q.len <= 0 {
		return Candle{}
	}
	return q.content[q.readHead]
}
