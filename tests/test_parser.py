"""Tests for RSS parser."""

import pytest
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
    assert feed.items[0].title == "Test Item"


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
    assert feed.items[0].title == "Test Entry"


def test_rss_item_to_dict():
    """Test converting RSSItem to dictionary."""
    item = RSSItem(title="Test", link="https://example.com", description="Test description")

    item_dict = item.to_dict()
    assert item_dict["title"] == "Test"
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
    assert first_item.title == "👀 Банк России будет учитывать два новых показателя..."
    assert first_item.link == "https://t.me/centralbank_russia/3235"
    assert first_item.pub_date == "Fri, 09 Jan 2026 10:15:06 +0000"
    assert first_item.guid == "https://t.me/centralbank_russia/3235"

    # Verify that descriptions contain HTML content
    assert first_item.description is not None
    assert len(first_item.description) > 0
    assert "Банк России будет учитывать два новых показателя" in first_item.description

    # Verify another item with different content
    second_item = feed.items[1]
    assert second_item.title == "🎧 Аудиоподкасты об экономике для студентов и не..."
    assert second_item.link == "https://t.me/centralbank_russia/3234"

    # Test that all items have required fields
    for item in feed.items:
        assert item.title is not None
        assert item.link is not None
        assert item.guid is not None
