package main

import (
	"fmt"

	"github.com/ksusonic/event-platform/internal/telegram"
)

func main() {
	channel := telegram.NewTelegramChannel("mediarzn")

	posts, err := channel.GetPosts()
	if err != nil {
		panic(fmt.Errorf("get telegram posts: %w", err))
	}

	fmt.Printf("%+v\n", posts)
}
