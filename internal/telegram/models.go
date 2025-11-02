package telegram

import "time"

type Post struct {
	Link        string
	Content     string
	Images      []string
	PublishedAt time.Time
	ChannelName string
}
