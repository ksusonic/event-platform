package rss

import (
	"strings"
	"testing"

	"github.com/stretchr/testify/assert"
)

const testRSSData = `<?xml version="1.0" encoding="UTF-8"?>
<rss xmlns:atom="http://www.w3.org/2005/Atom" xmlns:media="http://search.yahoo.com/mrss/" version="2.0">
  <channel>
    <title>ML-легушька - Telegram</title>
    <description>ML-легушька - Telegram</description>
    <link>https://t.me/s/somechannel</link>
    <atom:link rel="alternate" type="text/html" href="https://t.me/s/somechannel"/>
    <atom:link rel="self" type="application/atom+xml" href="https://rss-bridge.org/bridge01/?action=display&amp;username=somechannel&amp;bridge=TelegramBridge&amp;format=Mrss"/>
    <image>
      <url>https://t.me/favicon.ico</url>
      <title>ML-легушька - Telegram</title>
      <link>https://t.me/s/somechannel</link>
    </image>
    <item>
      <title>Почему я не могу разделить 10 яблок на 0 человек, но могу...</title>
      <link>https://t.me/s/somechannel/3060</link>
      <guid isPermaLink="true">https://t.me/s/somechannel/3060</guid>
      <pubDate>Sat, 01 Nov 2025 11:39:35 +0000</pubDate>
      <description>&lt;div class="tgme_widget_message_text js-message_text" dir="auto"&gt;Почему я не могу разделить 10 яблок на 0 человек, но могу разделить 0 яблок на 10 человек? &lt;br/&gt;В каком варианте все останутся сыты?&lt;/div&gt;</description>
    </item>
    <item>
      <title>Когда онлайн помогает оффлайну.</title>
      <link>https://t.me/s/somechannel/3057</link>
      <guid isPermaLink="true">https://t.me/s/somechannel/3057</guid>
      <pubDate>Thu, 30 Oct 2025 09:44:46 +0000</pubDate>
      <description>&lt;a href="https://t.me/s/somechannel/3057?single"&gt;&lt;img src="https://cdn4.cdn-telegram.org/file/image.jpg" /&gt;&lt;/a&gt;В последний год я активно помогаю компаниям внедрять ML-решения.&lt;/a&gt;</description>
    </item>
    <item>
      <title>Data Science основы</title>
      <link>https://t.me/s/somechannel/3050</link>
      <guid isPermaLink="true">https://t.me/s/somechannel/3050</guid>
      <pubDate>Wed, 29 Oct 2025 14:30:00 +0000</pubDate>
      <description>&lt;p&gt;Важные концепции в Data Science&lt;/p&gt;</description>
    </item>
  </channel>
</rss>`

func TestParseValidRSS(t *testing.T) {
	reader := strings.NewReader(testRSSData)

	channel, err := parse(reader)

	assert.NoError(t, err)
	assert.NotNil(t, channel)
	assert.Equal(t, "ML-легушька - Telegram", channel.Title)
	assert.Equal(t, "ML-легушька - Telegram", channel.Description)
	assert.Len(t, channel.Items, 3)
}

func TestParseItemDetails(t *testing.T) {
	reader := strings.NewReader(testRSSData)
	channel, err := parse(reader)
	assert.NoError(t, err)

	firstItem := channel.Items[0]
	assert.Equal(t, "Почему я не могу разделить 10 яблок на 0 человек, но могу...", firstItem.Title)
	assert.Equal(t, "https://t.me/s/somechannel/3060", firstItem.Link)
	assert.Equal(t, "Sat, 01 Nov 2025 11:39:35 +0000", firstItem.PubDate)
	assert.Contains(t, firstItem.Description, "Почему я не могу разделить")

	secondItem := channel.Items[1]
	assert.Equal(t, "Когда онлайн помогает оффлайну.", secondItem.Title)

	thirdItem := channel.Items[2]
	assert.Equal(t, "Data Science основы", thirdItem.Title)
}

func TestParseDateParsing(t *testing.T) {
	reader := strings.NewReader(testRSSData)
	channel, err := parse(reader)
	assert.NoError(t, err)

	firstItem := channel.Items[0]
	assert.False(t, firstItem.ParsedDate.IsZero(), "First item ParsedDate should be parsed")

	assert.Equal(t, 2025, firstItem.ParsedDate.Year())
	assert.Equal(t, 11, int(firstItem.ParsedDate.Month()))
	assert.Equal(t, 1, firstItem.ParsedDate.Day())
	assert.Equal(t, 11, firstItem.ParsedDate.Hour())
	assert.Equal(t, 39, firstItem.ParsedDate.Minute())
	assert.Equal(t, 35, firstItem.ParsedDate.Second())

	secondItem := channel.Items[1]
	assert.Equal(t, 2025, secondItem.ParsedDate.Year())
	assert.Equal(t, 10, int(secondItem.ParsedDate.Month()))
	assert.Equal(t, 30, secondItem.ParsedDate.Day())
	assert.Equal(t, 9, secondItem.ParsedDate.Hour())
	assert.Equal(t, 44, secondItem.ParsedDate.Minute())
	assert.Equal(t, 46, secondItem.ParsedDate.Second())
}

func TestParseInvalidXML(t *testing.T) {
	invalidXML := `<?xml version="1.0"?>
<rss>
  <channel>
    <title>Test</title>
  <!-- Missing closing channel tag -->
</rss>`

	reader := strings.NewReader(invalidXML)
	_, err := parse(reader)
	assert.Error(t, err)
}

func TestParseEmptyFeed(t *testing.T) {
	emptyFeed := `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Empty Feed</title>
    <link>https://example.com</link>
    <description>An empty feed</description>
  </channel>
</rss>`

	reader := strings.NewReader(emptyFeed)
	channel, err := parse(reader)
	assert.NoError(t, err)
	assert.Equal(t, "Empty Feed", channel.Title)
	assert.Len(t, channel.Items, 0)
}

func TestParseItemsOrdering(t *testing.T) {
	reader := strings.NewReader(testRSSData)
	channel, err := parse(reader)
	assert.NoError(t, err)

	expectedTitles := []string{
		"Почему я не могу разделить 10 яблок на 0 человек, но могу...",
		"Когда онлайн помогает оффлайну.",
		"Data Science основы",
	}

	assert.Len(t, channel.Items, len(expectedTitles))
	for i, expectedTitle := range expectedTitles {
		assert.Equal(t, expectedTitle, channel.Items[i].Title)
	}
}

func TestParseHTMLEntities(t *testing.T) {
	reader := strings.NewReader(testRSSData)
	channel, err := parse(reader)
	assert.NoError(t, err)

	firstItem := channel.Items[0]
	assert.Contains(t, firstItem.Description, "div")
}
