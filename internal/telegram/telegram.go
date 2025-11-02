package telegram

import (
	"fmt"

	"github.com/ksusonic/event-platform/pkg/rss"
)

const (
	rssBridgeURLTemplate = "https://rss-bridge.org/bridge01/?action=display&username=%s&bridge=TelegramBridge&format=Mrss"
)

type TelegramChannel struct {
	Name string
}

func NewTelegramChannel(name string) *TelegramChannel {
	return &TelegramChannel{
		Name: name,
	}
}

func (tc *TelegramChannel) GetName() string {
	return tc.Name
}

func (tc *TelegramChannel) GetPosts() ([]Post, error) {
	channel, err := rss.ParseURL(fmt.Sprintf(rssBridgeURLTemplate, tc.Name))
	if err != nil {
		return nil, fmt.Errorf("parse RSS by URL: %w", err)
	}

	posts := make([]Post, 0, len(channel.Items))
	for _, item := range channel.Items {
		posts = append(posts, Post{
			Link:        item.Link,
			Content:     CleanContent(item.Description),
			Images:      ExtractImages(item.Description),
			PublishedAt: item.ParsedDate,
			ChannelName: tc.Name,
		})
	}

	return posts, nil
}
