package telegram

import (
	"html"
	"regexp"
	"strings"
)

var (
	// Extract image src URLs from img tags
	imgSrcRegex = regexp.MustCompile(`<img[^>]+src="([^"]+)"`)

	// Remove unsupported media message div
	unsupportedMediaRegex = regexp.MustCompile(`<div class="message_media_not_supported"[^>]*>.*?</div>`)

	// Remove action links like "VIEW IN TELEGRAM"
	actionLinkRegex = regexp.MustCompile(`<a[^>]*class="message_media_view_in_telegram"[^>]*>.*?</a>`)

	// Remove HTML tags
	htmlTagRegex = regexp.MustCompile(`<[^>]+>`)

	// Normalize multiple spaces (but not newlines)
	spaceRegex = regexp.MustCompile(`[ \t]+`)
)

// ExtractImages extracts image URLs from HTML content
func ExtractImages(htmlContent string) []string {
	matches := imgSrcRegex.FindAllStringSubmatch(htmlContent, -1)
	images := make([]string, 0, len(matches))

	for _, match := range matches {
		if len(match) > 1 {
			images = append(images, match[1])
		}
	}

	return images
}

// CleanContent cleans up HTML content by:
// - Removing unsupported media message divs
// - Removing action links (like "VIEW IN TELEGRAM")
// - Removing HTML tags
// - Unescaping HTML entities
// - Normalizing whitespace
func CleanContent(htmlContent string) string {
	// Remove unsupported media messages
	content := unsupportedMediaRegex.ReplaceAllString(htmlContent, "")

	// Remove action links like "VIEW IN TELEGRAM"
	content = actionLinkRegex.ReplaceAllString(content, "")

	// Remove line breaks within links and other tags
	content = strings.ReplaceAll(content, "<br/>", "\n")
	content = strings.ReplaceAll(content, "<br>", "\n")

	// Remove img tags (they've been extracted)
	content = regexp.MustCompile(`<img[^>]*/?>`).ReplaceAllString(content, "")

	// Remove link tags but keep the text content
	content = regexp.MustCompile(`<a[^>]*href="([^"]*)"[^>]*>`).ReplaceAllString(content, "")
	content = strings.ReplaceAll(content, "</a>", "")

	// Remove emoji tags and keep the emoji
	content = regexp.MustCompile(`<tg-emoji[^>]*>.*?<b>([^<]*)</b>.*?</tg-emoji>`).ReplaceAllString(content, "$1")

	// Remove all remaining HTML tags
	content = htmlTagRegex.ReplaceAllString(content, "")

	// Unescape HTML entities
	content = html.UnescapeString(content)

	// Normalize spaces and tabs (but preserve newlines)
	content = spaceRegex.ReplaceAllString(content, " ")

	// Trim leading/trailing whitespace
	content = strings.TrimSpace(content)

	return content
}
