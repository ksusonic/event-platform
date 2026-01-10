"""Tests for RSS parser."""

from rss_parser import RSSParser, RSSChannel, RSSItem


def test_parse_rss_content():
    """Test parsing basic RSS content."""
    rss_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
        <channel>
            <title>Test Feed</title>
            <link>https://example.com</link>
            <description>Test Description</description>
            <item>
                <title>Test Item</title>
                <link>https://example.com/item1</link>
                <description>Test item description</description>
                <pubDate>Mon, 10 Jan 2026 12:00:00 GMT</pubDate>
            </item>
        </channel>
    </rss>"""

    parser = RSSParser()
    feed = parser.parse_content(rss_xml)

    assert feed.title == "Test Feed"
    assert feed.link == "https://example.com"
    assert len(feed.items) == 1


def test_parse_atom_content():
    """Test parsing Atom feed content."""
    atom_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
        <title>Test Atom Feed</title>
        <link href="https://example.com"/>
        <subtitle>Test Subtitle</subtitle>
        <entry>
            <title>Test Entry</title>
            <link href="https://example.com/entry1"/>
            <id>entry1</id>
            <published>2026-01-10T12:00:00Z</published>
            <content>Test content</content>
        </entry>
    </feed>"""

    parser = RSSParser()
    feed = parser.parse_content(atom_xml)

    assert feed.title == "Test Atom Feed"
    assert len(feed.items) == 1


def test_parse_media_urls():
    """Test parsing media URLs from RSS feed with media:content and HTML images."""
    rss_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/">
        <channel>
            <title>Test Feed with Media</title>
            <link>https://example.com</link>
            <description>Test Description</description>
            <item>
                <title>Test Item with Media</title>
                <link>https://example.com/item1</link>
                <description><![CDATA[
                    <img src="https://cdn4.telesco.pe/file/test-image1.jpg"/>
                    <video poster="https://cdn4.telesco.pe/file/test-video-poster.jpg">
                        <source src="https://cdn4.telesco.pe/file/test-video.mp4"/>
                    </video>
                    <img src="https://cdn4.telesco.pe/file/test-image2.jpg"/>
                ]]></description>
                <pubDate>Mon, 10 Jan 2026 12:00:00 GMT</pubDate>
                <media:content url="https://cdn4.telesco.pe/file/media-content.jpg" type="image/jpeg"/>
            </item>
        </channel>
    </rss>"""

    parser = RSSParser()
    feed = parser.parse_content(rss_xml)

    assert len(feed.items) == 1
    item = feed.items[0]

    # Check that media URLs are extracted
    assert len(item.media_urls) > 0

    # Check that media:content URL is included
    assert "https://cdn4.telesco.pe/file/media-content.jpg" in item.media_urls

    # Check that img src URLs are included
    assert "https://cdn4.telesco.pe/file/test-image1.jpg" in item.media_urls
    assert "https://cdn4.telesco.pe/file/test-image2.jpg" in item.media_urls

    # Check that video poster URL is included
    assert "https://cdn4.telesco.pe/file/test-video-poster.jpg" in item.media_urls

    # Total should be 4 unique URLs
    assert len(item.media_urls) == 4


def test_rss_item_to_dict():
    """Test converting RSSItem to dictionary."""
    item = RSSItem(link="https://example.com", description="Test description")

    item_dict = item.to_dict()
    assert item_dict["link"] == "https://example.com"


def test_rss_channel_to_json():
    """Test converting RSSChannel to JSON."""
    channel = RSSChannel(title="Test Feed", link="https://example.com", description="Test")

    json_str = channel.to_json()
    assert "Test Feed" in json_str
    assert "item_count" in json_str


def test_parse_centralbank_russia_fixture():
    """Test parsing the Central Bank of Russia RSS feed fixture."""
    import os

    # Load the fixture file
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "centralbank_russia.xml")
    with open(fixture_path, "r", encoding="utf-8") as f:
        rss_content = f.read()

    # Parse the RSS feed
    parser = RSSParser()
    feed = parser.parse_content(rss_content)

    # Verify channel metadata
    assert feed.title == "Банк России (@centralbank_russia) - Telegram"
    assert feed.link == "https://t.me/s/centralbank_russia"
    assert feed.description == "Банк России (@centralbank_russia) - Telegram"

    # Verify items were parsed
    assert len(feed.items) > 0
    assert len(feed.items) == 20  # Total number of items in the fixture

    # Verify first item
    first_item = feed.items[0]
    assert first_item.link == "https://t.me/centralbank_russia/3235"
    assert first_item.pub_date == "Fri, 09 Jan 2026 10:15:06 +0000"

    # Verify that descriptions contain HTML content
    assert first_item.description is not None
    assert len(first_item.description) > 0
    assert "Банк России будет учитывать два новых показателя" in first_item.description

    # Verify another item with different content
    second_item = feed.items[1]
    assert second_item.link == "https://t.me/centralbank_russia/3234"

    # Test that all items have required fields
    for item in feed.items:
        assert item.link is not None


def test_centralbank_media_extraction():
    """Test that media URLs are correctly extracted from the Central Bank RSS feed fixture."""
    import os

    # Load the fixture file
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "centralbank_russia.xml")
    with open(fixture_path, "r", encoding="utf-8") as f:
        rss_content = f.read()

    # Parse the RSS feed
    parser = RSSParser()
    feed = parser.parse_content(rss_content)

    # Test first item - has image in description
    first_item = feed.items[0]
    assert first_item.media_urls is not None
    assert len(first_item.media_urls) > 0
    # Check that the image URL from the HTML is extracted
    assert any(
        "cdn4.telesco.pe/file/EIf7N3nLRg0uxcIl_qbdqYxQ3s7uIuoHn04F8BsqYi7GrXywA" in url
        for url in first_item.media_urls
    )

    # Test second item - also has image in description
    second_item = feed.items[1]
    assert len(second_item.media_urls) > 0
    assert any(
        "cdn4.telesco.pe/file/tmA8JTxApF_SUGCME82uIdOKk8UNlv2YUPe0iyl2ZFfuXOJ" in url
        for url in second_item.media_urls
    )

    # Test third item - has video poster and media:content tag
    third_item = feed.items[2]
    assert len(third_item.media_urls) > 0
    # Should have video poster URL
    assert any(
        "cdn4.telesco.pe/file/MOMtF_YYEpnIGYrJSHWTdRtKuotxc" in url for url in third_item.media_urls
    )
    # Media:content URL should also be present (it's the same as poster in this case)

    # Test fourth item - has video poster and media:content tag
    fourth_item = feed.items[3]
    assert len(fourth_item.media_urls) > 0
    # Should have both video poster and media:content
    assert any(
        "cdn4.telesco.pe/file/QREqxpPjX_snuYmn5RTCM" in url for url in fourth_item.media_urls
    )

    # Test that media URLs are being extracted across all items with media
    items_with_media = [item for item in feed.items if len(item.media_urls) > 0]
    # Most items in this feed should have media
    assert len(items_with_media) > 5

    # Verify all media URLs are valid (start with https://)
    for item in feed.items:
        for media_url in item.media_urls:
            assert media_url.startswith("https://"), f"Invalid media URL: {media_url}"
            # Most should be from cdn4.telesco.pe
            assert "telesco.pe" in media_url or "telegram.org" in media_url
