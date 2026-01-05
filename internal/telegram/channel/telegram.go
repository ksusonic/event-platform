package channel

import (
	"fmt"

	"github.com/ksusonic/event-platform/internal/models"
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

func (tc *TelegramChannel) GetRawPosts() ([]models.RawPost, error) {
	channel, err := rss.ParseURL(fmt.Sprintf(rssBridgeURLTemplate, tc.Name))
	if err != nil {
		return nil, fmt.Errorf("parse RSS by URL: %w", err)
	}

	posts := make([]models.RawPost, 0, len(channel.Items))
	for _, item := range channel.Items {
		posts = append(posts, models.RawPost{
			Link:        item.Link,
			Content:     cleanContent(item.Description),
			PublishedAt: item.ParsedDate,
		})
	}

	return posts, nil
}
