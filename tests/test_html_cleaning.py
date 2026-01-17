"""Tests for HTML content cleaning functionality."""

from feed.utils.html import clean_content


class TestCleanContent:
    """Test the clean_content function with various HTML scenarios."""

    def test_remove_unsupported_media(self):
        """Test removal of unsupported media message divs."""
        html = (
            '<p>Hello</p><div class="message_media_not_supported">Not supported</div><p>World</p>'
        )
        result = clean_content(html)
        assert "Not supported" not in result
        assert "Hello" in result
        assert "World" in result

    def test_remove_action_links(self):
        """Test removal of action links like VIEW IN TELEGRAM."""
        html = '<p>Check this</p><a class="message_media_view_in_telegram" href="#">VIEW IN TELEGRAM</a>'
        result = clean_content(html)
        assert "VIEW IN TELEGRAM" not in result
        assert "Check this" in result

    def test_convert_line_breaks(self):
        """Test conversion of HTML line breaks to newlines."""
        html = "Line1<br>Line2<br/>Line3"
        result = clean_content(html)
        assert result == "Line1\nLine2\nLine3"

    def test_remove_img_tags(self):
        """Test removal of image tags."""
        html = '<p>Text before</p><img src="photo.jpg" alt="Photo"/><p>Text after</p>'
        result = clean_content(html)
        assert "<img" not in result
        assert "Text before" in result
        assert "Text after" in result

    def test_remove_link_tags_keep_text(self):
        """Test removal of link tags while keeping text content."""
        html = '<p>Visit <a href="https://example.com">this link</a> for more</p>'
        result = clean_content(html)
        assert "<a" not in result
        assert "href" not in result
        assert "this link" in result
        assert "Visit" in result
        assert "for more" in result

    def test_extract_emoji_from_tg_emoji_tags(self):
        """Test extraction of emoji from telegram emoji tags."""
        html = 'Hello <tg-emoji emoji-id="123"><b>👋</b></tg-emoji> world'
        result = clean_content(html)
        assert "👋" in result
        assert "tg-emoji" not in result
        assert "Hello" in result
        assert "world" in result

    def test_unescape_html_entities(self):
        """Test unescaping of HTML entities."""
        html = "Hello &amp; goodbye &quot;test&quot;"
        result = clean_content(html)
        assert result == 'Hello & goodbye "test"'

        # Test that escaped HTML tags are properly removed after unescaping
        html_with_tags = "Text &lt;div&gt;content&lt;/div&gt; more"
        result2 = clean_content(html_with_tags)
        assert result2 == "Text content more"

    def test_normalize_whitespace(self):
        """Test normalization of multiple spaces and tabs."""
        html = "<p>Too   many    spaces\t\tand\t\ttabs</p>"
        result = clean_content(html)
        assert result == "Too many spaces and tabs"

    def test_preserve_newlines_in_whitespace_normalization(self):
        """Test that newlines are preserved during space normalization."""
        html = "<p>Line1</p><br/><p>Line2</p>"
        result = clean_content(html)
        # Should have newline from <br/> preserved
        assert "\n" in result

    def test_trim_leading_trailing_whitespace(self):
        """Test trimming of leading and trailing whitespace."""
        html = "  <p>  Content  </p>  "
        result = clean_content(html)
        assert result == "Content"
        assert not result.startswith(" ")
        assert not result.endswith(" ")

    def test_empty_string(self):
        """Test handling of empty string."""
        assert clean_content("") == ""

    def test_complex_telegram_message(self):
        """Test a complex telegram-style message with multiple elements."""
        html = """
        <div class="message_media_not_supported">Unsupported</div>
        <p>Check out this <a href="https://t.me/channel">channel</a>!</p>
        <img src="image.jpg" alt="Image"/>
        <p>It&#39;s amazing <tg-emoji emoji-id="456"><b>🔥</b></tg-emoji></p>
        <a class="message_media_view_in_telegram" href="#">VIEW IN TELEGRAM</a>
        """
        result = clean_content(html)

        # Should contain
        assert "Check out this" in result
        assert "channel" in result
        assert "amazing" in result
        assert "🔥" in result
        assert "It's" in result  # Unescaped entity

        # Should not contain
        assert "Unsupported" not in result
        assert "VIEW IN TELEGRAM" not in result
        assert "<img" not in result
        assert "tg-emoji" not in result
        assert "message_media_not_supported" not in result

    def test_multiple_line_breaks(self):
        """Test handling of multiple line breaks."""
        html = "Line1<br><br>Line2<br/><br/>Line3"
        result = clean_content(html)
        assert "Line1" in result
        assert "Line2" in result
        assert "Line3" in result
        # Should have preserved newlines
        lines = [line for line in result.split("\n") if line]
        assert len(lines) == 3

    def test_double_encoded_html(self):
        """Test handling of double-encoded HTML (escaped HTML entities)."""
        # This is how RSS feeds often encode HTML content
        html = '&lt;div class="message_media_not_supported"&gt;&lt;span class="message_media_not_supported_label"&gt;This media is not supported&lt;/span&gt;&lt;span class="message_media_view_in_telegram"&gt;VIEW IN TELEGRAM&lt;/span&gt;&lt;/div&gt;&lt;p&gt;Actual content here&lt;/p&gt;'
        result = clean_content(html)

        # Should NOT contain
        assert "VIEW IN TELEGRAM" not in result
        assert "This media is not supported" not in result
        assert "message_media_not_supported" not in result

        # Should contain
        assert "Actual content here" in result

    def test_real_rss_example(self):
        """Test with real RSS feed example containing double-encoded unsupported media."""
        html = """   &lt;div class="message_media_not_supported"&gt;     &lt;div class="message_media_not_supported_label"&gt;This media is not supported in your browser&lt;/div&gt;     &lt;span class="message_media_view_in_telegram"&gt;VIEW IN TELEGRAM&lt;/span&gt;   &lt;/div&gt; &lt;video controls="" poster="https://cdn4.telesco.pe/file/example.jpg" style="max-width:100%;"&gt;"""
        result = clean_content(html)

        # Should NOT contain any of these strings
        assert "VIEW IN TELEGRAM" not in result
        assert "This media is not supported in your browser" not in result
        assert "message_media_not_supported" not in result
        assert "<div" not in result.lower()
        assert "<span" not in result.lower()
        assert "<video" not in result.lower()

        # Result should be essentially empty or just whitespace after cleaning
        assert result.strip() == ""
