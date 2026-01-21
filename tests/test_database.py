"""Tests for database functionality."""

import pytest
import pytest_asyncio
from datetime import datetime
from src.feed.db import db, RSSPost, RSSPostRepository


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Set up database connection and clean for each test."""
    # Create a new connection pool for each test to avoid event loop issues
    if db.pool is not None:
        await db.disconnect()

    await db.connect()

    # Clean database before test
    await db.execute("TRUNCATE TABLE rss_posts RESTART IDENTITY CASCADE")

    yield

    # Disconnect after each test
    await db.disconnect()


@pytest.mark.asyncio
async def test_create_post():
    """Test creating a new post."""
    post = RSSPost(
        link="https://example.com/test-1",
        content="Test post content",
        pub_date="2026-01-10T10:00:00Z",
    )

    link = await RSSPostRepository.create(post)
    assert link is not None
    assert link == post.link


@pytest.mark.asyncio
async def test_create_post_with_media():
    """Test creating a post with media URLs."""
    post = RSSPost(
        link="https://example.com/test-2",
        content="Test post with media",
        media="https://example.com/image.jpg,https://example.com/video.mp4",
    )

    link = await RSSPostRepository.create(post)
    retrieved = await RSSPostRepository.get_by_link(link)

    assert retrieved is not None
    assert retrieved.media == post.media


@pytest.mark.asyncio
async def test_get_by_link():
    """Test retrieving a post by link."""
    post = RSSPost(
        link="https://example.com/test-3",
        content="Test content",
    )

    link = await RSSPostRepository.create(post)
    retrieved = await RSSPostRepository.get_by_link(link)

    assert retrieved is not None
    assert retrieved.link == link
    assert retrieved.link == post.link
    assert retrieved.content == post.content


@pytest.mark.asyncio
async def test_get_nonexistent_post():
    """Test retrieving a nonexistent post."""
    retrieved = await RSSPostRepository.get_by_link("https://nonexistent.com")
    assert retrieved is None


@pytest.mark.asyncio
async def test_exists_by_link():
    """Test checking if post exists by link."""
    post = RSSPost(
        link="https://example.com/test-5",
        content="Test content",
    )

    exists_before = await RSSPostRepository.exists_by_link(post.link)
    assert exists_before is False

    await RSSPostRepository.create(post)

    exists_after = await RSSPostRepository.exists_by_link(post.link)
    assert exists_after is True


@pytest.mark.asyncio
async def test_get_unprocessed():
    """Test retrieving unprocessed posts."""
    # Create some posts
    for i in range(5):
        post = RSSPost(
            link=f"https://example.com/test-{i}",
            content=f"Test {i}",
        )
        await RSSPostRepository.create(post)

    # Mark some as processed
    posts = await RSSPostRepository.get_all()
    await RSSPostRepository.mark_as_processed(posts[0].link, is_event=True)
    await RSSPostRepository.mark_as_processed(posts[1].link, is_event=False)

    # Get unprocessed
    unprocessed = await RSSPostRepository.get_unprocessed()
    assert len(unprocessed) == 3


@pytest.mark.asyncio
async def test_mark_as_processed():
    """Test marking a post as processed."""
    post = RSSPost(
        link="https://example.com/test-6",
        content="Event announcement",
    )

    link = await RSSPostRepository.create(post)

    # Mark as processed
    classification_data = {"confidence": 0.95, "classifier": "test"}
    await RSSPostRepository.mark_as_processed(
        link,
        is_event=True,
        classification_data=classification_data,
    )

    # Verify
    retrieved = await RSSPostRepository.get_by_link(link)
    assert retrieved.is_processed is True
    assert retrieved.is_event is True
    assert retrieved.classification_data == classification_data
    assert retrieved.classified_at is not None


@pytest.mark.asyncio
async def test_mark_as_unprocessed():
    """Test marking a post as unprocessed."""
    post = RSSPost(
        link="https://example.com/test-7",
        content="Test content",
    )

    link = await RSSPostRepository.create(post)
    await RSSPostRepository.mark_as_processed(link, is_event=True)

    # Mark as unprocessed
    await RSSPostRepository.mark_as_unprocessed(link)

    # Verify
    retrieved = await RSSPostRepository.get_by_link(link)
    assert retrieved.is_processed is False


@pytest.mark.asyncio
async def test_update_classification():
    """Test updating classification data."""
    post = RSSPost(
        link="https://example.com/test-8",
        content="Test content",
    )

    link = await RSSPostRepository.create(post)

    # Update classification
    new_classification = {"confidence": 0.88, "tags": ["event", "conference"]}
    await RSSPostRepository.update_classification(
        link,
        is_event=True,
        classification_data=new_classification,
    )

    # Verify
    retrieved = await RSSPostRepository.get_by_link(link)
    assert retrieved.is_event is True
    assert retrieved.classification_data == new_classification


@pytest.mark.asyncio
async def test_get_all_with_filters():
    """Test retrieving posts with filters."""
    # Create various posts
    posts_data = [
        ("https://example.com/event-1", True, True),
        ("https://example.com/event-2", True, True),
        ("https://example.com/news-1", True, False),
        ("https://example.com/unprocessed-1", False, None),
    ]

    for link, processed, is_event in posts_data:
        post = RSSPost(link=link, content="Test")
        created_link = await RSSPostRepository.create(post)
        if processed:
            await RSSPostRepository.mark_as_processed(created_link, is_event=is_event)

    # Test filters
    all_posts = await RSSPostRepository.get_all()
    assert len(all_posts) == 4

    processed = await RSSPostRepository.get_all(is_processed=True)
    assert len(processed) == 3

    events = await RSSPostRepository.get_all(is_event=True)
    assert len(events) == 2

    unprocessed = await RSSPostRepository.get_all(is_processed=False)
    assert len(unprocessed) == 1


@pytest.mark.asyncio
async def test_get_all_pagination():
    """Test pagination in get_all."""
    # Create 10 posts
    for i in range(10):
        post = RSSPost(
            link=f"https://example.com/test-{i}",
            content=f"Test {i}",
        )
        await RSSPostRepository.create(post)

    # Test pagination
    page1 = await RSSPostRepository.get_all(limit=3, offset=0)
    assert len(page1) == 3

    page2 = await RSSPostRepository.get_all(limit=3, offset=3)
    assert len(page2) == 3

    # Ensure different posts
    page1_links = {p.link for p in page1}
    page2_links = {p.link for p in page2}
    assert page1_links.isdisjoint(page2_links)


@pytest.mark.asyncio
async def test_delete_post():
    """Test deleting a post."""
    post = RSSPost(
        link="https://example.com/test-delete",
        content="Test content",
    )

    link = await RSSPostRepository.create(post)

    # Verify exists
    retrieved = await RSSPostRepository.get_by_link(link)
    assert retrieved is not None

    # Delete
    await RSSPostRepository.delete(link)

    # Verify deleted
    retrieved_after = await RSSPostRepository.get_by_link(link)
    assert retrieved_after is None


@pytest.mark.asyncio
async def test_get_stats():
    """Test getting database statistics."""
    # Create various posts
    for i in range(10):
        post = RSSPost(
            link=f"https://example.com/test-{i}",
            content=f"Test {i}",
        )
        link = await RSSPostRepository.create(post)

        # Mark some as processed
        if i < 7:
            is_event = i < 4
            await RSSPostRepository.mark_as_processed(link, is_event=is_event)

    # Get stats
    stats = await RSSPostRepository.get_stats()

    assert stats["total"] == 10
    assert stats["processed"] == 7
    assert stats["unprocessed"] == 3
    assert stats["events"] == 4


@pytest.mark.asyncio
async def test_post_dataclass_conversions():
    """Test RSSPost dataclass conversions."""
    post = RSSPost(
        link="https://example.com/test",
        content="Test content",
        media="https://example.com/image.jpg",
    )

    # Test to_dict
    post_dict = post.to_dict()
    assert "link" in post_dict
    assert "content" in post_dict

    # Test from_row
    row_data = {
        "link": "https://example.com/test",
        "content": "Test",
        "pub_date": "2026-01-10",
        "media": "test.jpg",
        "is_processed": True,
        "is_event": False,
        "classification_data": {"confidence": 0.9},
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "classified_at": None,
    }

    post_from_row = RSSPost.from_row(row_data)
    assert post_from_row.link == row_data["link"]
    assert post_from_row.is_processed is True
    assert post_from_row.is_event is False
