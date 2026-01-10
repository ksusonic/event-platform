package models

import "time"

type RawPost struct {
	Link        string
	Content     string
	PublishedAt time.Time
}

type Entity struct {
	Type  string
	Value string
}
