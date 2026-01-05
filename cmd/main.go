package main

import (
	"fmt"

	"github.com/ksusonic/event-platform/internal/telegram/channel"
)

func main() {
	ch := channel.NewTelegramChannel("mediarzn")

	posts, err := ch.GetRawPosts()
	if err != nil {
		panic(fmt.Errorf("get telegram posts: %w", err))
	}

	fmt.Printf("Retrieved %d posts\n", len(posts))
	for i, post := range posts {
		fmt.Printf("\nPost %d:\n", i+1)
		fmt.Printf("  Link: %s\n", post.Link)
		fmt.Printf("  Published: %s\n", post.PublishedAt)
		fmt.Printf("  Content: %s\n", post.Content[:min(50, len(post.Content))])
	}
}
