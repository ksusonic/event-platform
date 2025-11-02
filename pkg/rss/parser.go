package rss

import (
	"encoding/xml"
	"fmt"
	"io"
	"net/http"
	"time"
)

func ParseURL(url string) (*Channel, error) {
	resp, err := http.Get(url)
	if err != nil {
		return nil, fmt.Errorf("failed to fetch URL: %w", err)
	}
	defer resp.Body.Close() // nolint:errcheck

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("HTTP error: %d", resp.StatusCode)
	}

	return parse(resp.Body)
}

func parse(r io.Reader) (*Channel, error) {
	var rss RSS

	decoder := xml.NewDecoder(r)
	if err := decoder.Decode(&rss); err != nil {
		return nil, fmt.Errorf("failed to decode XML: %w", err)
	}

	for i := range rss.Channel.Items {
		if rss.Channel.Items[i].PubDate != "" {
			t, err := time.Parse(time.RFC1123Z, rss.Channel.Items[i].PubDate)
			if err == nil {
				rss.Channel.Items[i].ParsedDate = t
			}
		}
	}

	return &rss.Channel, nil
}
