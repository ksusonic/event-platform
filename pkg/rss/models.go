package rss

import (
	"time"
)

type Channel struct {
	Title       string `xml:"title"`
	Link        string `xml:"link"`
	Description string `xml:"description"`
	Items       []Item `xml:"item"`
}

type Item struct {
	Title       string    `xml:"title"`
	Link        string    `xml:"link"`
	Description string    `xml:"description"`
	PubDate     string    `xml:"pubDate"`
	ParsedDate  time.Time `xml:"-"`
}

type RSS struct {
	Channel Channel `xml:"channel"`
}
