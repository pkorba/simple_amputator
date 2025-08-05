import aiohttp
import asyncio
import unittest
from simple_amputator.simple_amputator import SimpleAmputatorBot
from maubot.matrix import MaubotMatrixClient
from mautrix.api import HTTPAPI
from mautrix.types import MessageType, TextMessageEventContent
from mautrix.util.logging import TraceLogger
from unittest.mock import AsyncMock


class TestSimpleAmputatorBot(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.session = aiohttp.ClientSession()
        api = HTTPAPI(base_url="http://matrix.example.com", client_session=self.session)
        client = MaubotMatrixClient(api=api)
        self.bot = SimpleAmputatorBot(
            client=client,
            loop=asyncio.get_event_loop(),
            http=self.session,
            instance_id="matrix.example.com",
            log=TraceLogger("testlogger"),
            config=None,
            database=None,
            webapp=None,
            webapp_url=None,
            loader=None
        )

    async def asyncTearDown(self):
        await self.session.close()

    async def create_resp(self, status_code=200, text=None, content_type=None):
        resp = AsyncMock(status_code=status_code, content_type=content_type)
        resp.text.return_value = text
        return resp

    async def test_fetch_page_content_when_aiohttp_error_then_return_empty_string(self):
        # Arrange
        url = "https://example.com/"
        self.bot.http.get = AsyncMock(side_effect=aiohttp.ClientError)

        # Act
        result = await self.bot.fetch_page_content(url)

        # Assert
        self.assertEqual(result, "")

    async def test_fetch_page_content_when_exception_then_return_empty_string(self):
        # Arrange
        url = "https://example.com/"
        self.bot.http.get = AsyncMock(side_effect=Exception)

        # Act
        result = await self.bot.fetch_page_content(url)

        # Assert
        self.assertEqual(result, "")

    async def test_fetch_page_content_when_matching_content_type_return_text(self):
        # Arrange
        url = "https://example.com/"
        text = "test"
        data = (
            (text, "text/html"),
            (text, "application/xhtml+xml"),
            (text, "application/xml"),
            ("", "video/mp4"),
            ("", "image/png")
        )
        for expected_result, content_type in data:
            with self.subTest(expected_result=expected_result, content_type=content_type):
                self.bot.http.get = AsyncMock(return_value=await self.create_resp(200, text=text, content_type=content_type))

                # Act
                result = await self.bot.fetch_page_content(url)

                # Assert
                self.assertEqual(result, expected_result)

    async def test_extract_canonical_url(self):
        # Arrange
        documents = (
            ("", "", ""),
            ("https://www.example.com/url/to/amp/document.html",
                """
                <!DOCTYPE html>
                <html ⚡ lang="en">
                <body></body>
                </html>
                """,
                ""),
            ("https://www.example.com/url/to/amp/document.html",
                """
                <!DOCTYPE html>
                <html ⚡ lang="en">
                <head>
                    <link rel="canonical" href="https://www.example.com/url/to/canonical/document.html" />
                </head>
                <body></body>
                </html>
                """,
                "https://www.example.com/url/to/canonical/document.html"),
            ("https://www.example.com/url/to/amp/document.html",
                """
                <!DOCTYPE html>
                <html amp lang="en">
                <head>
                    <link rel="canonical" href="https://www.example.com/url/to/canonical/document.html" />
                </head>
                <body></body>
                </html>
                """,
                "https://www.example.com/url/to/canonical/document.html"),
            ("https://www.example.com/url/to/amp/document.html",
                """
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <link rel="canonical" href="https://www.example.com/url/to/canonical/document.html" />
                    <link rel="amphtml" href="https://www.example.com/url/to/amp/document.html" />
                </head>
                <body></body>
                </html>
                """,
                "https://www.example.com/url/to/canonical/document.html"),
            ("https://www.example.com/url/to/amp/document.html",
                """
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <link rel="amphtml" href="https://www.example.com/url/to/amp/document.html" />
                </head>
                <body></body>
                </html>
                """,
                ""),
            ("https://www.example.com/",
                """
                <!DOCTYPE html>
                <html amp lang="en">
                <head>
                    <link rel="amphtml" href="https://www.example.com/url/to/amp/document.html" />
                </head>
                <body></body>
                </html>
                """,
                ""),
            ("https://www.example.com/",
                """
                <!DOCTYPE html>
                <html amp lang="en">
                <head>
                    <link rel="canonical" href="https://www.example.com/url/to/canonical/document.html" />
                    <link rel="amphtml" href="https://www.example.com/url/to/amp/document.html" />
                </head>
                <body></body>
                </html>
                """,
                "https://www.example.com/url/to/canonical/document.html"),
            ("https://www.example.com/",
                """
                <!DOCTYPE html>
                <html amp lang="en">
                <head>
                    <link rel="canonical" href="https://www.example.com/url/to/amp/document.html" />
                    <link rel="amphtml" href="https://www.example.com/url/to/amp/document.html" />
                </head>
                <body></body>
                </html>
                """,
                "")
        )

        for url, text, expected_result in documents:
            with self.subTest(url=url, text=text, expected_result=expected_result):
                # Act
                result = self.bot.extract_canonical_url(url, text)

                # Assert
                self.assertEqual(result, expected_result)

    async def test_urls_match(self):
        # Arrange
        data = (
            ("https://example.com/", "https://example.com/", True),
            ("https://example.com/", "https://example.com", True),
            ("https://example.com/", "http://example.com/", True),
            ("https://example.com/", "http://example.com", True),
            ("https://example.com/path.html?query=test", "http://example.com/path.html?query=test", True),
            ("https://example.com/path.html?query=test", "http://example.com/path.html?query=test1", False),
            ("https://example.com/", "https://example.com/path/", False),
            ("https://example.com/path/", "https://example.com/path1/", False),
            ("https://example.com/", "https://example.org/", False),
            ("https://example.com/", "https://www.example.com/", False),
            ("https://example.com/", "https://test.com/", False),
        )
        for url1, url2, expected_result in data:
            with self.subTest(url1=url1, url2=url2, expected_result=expected_result):
                # Act
                result = self.bot.urls_match(url1, url2)

                # Assert
                self.assertEqual(result, expected_result)

    async def test_get_canonical_urls_when_text_and_links_exist_return_links(self):
        # Arrange
        urls = [("test", "test")]
        self.bot.fetch_page_content = AsyncMock(return_value="text")
        asyncio.get_event_loop().run_in_executor = AsyncMock(return_value="canonical_link")

        # Act
        result = await self.bot.get_canonical_urls(urls)

        # Assert
        self.assertEqual(result, ["canonical_link"])

    async def test_get_canonical_urls_when_no_text_return_empty_list(self):
        # Arrange
        urls = [("test", "test")]
        self.bot.fetch_page_content = AsyncMock(return_value="")

        # Act
        result = await self.bot.get_canonical_urls(urls)

        # Assert
        self.assertEqual(result, [])

    async def test_get_canonical_urls_when_text_and_no_links_return_empty_list(self):
        # Arrange
        urls = [("test", "test")]
        self.bot.fetch_page_content = AsyncMock(return_value="text")
        asyncio.get_event_loop().run_in_executor = AsyncMock(return_value="")

        # Act
        result = await self.bot.get_canonical_urls(urls)

        # Assert
        self.assertEqual(result, [])

    async def test_prepare_message_return_TextMessageEventContent(self):
        # Arrange
        canonical_urls = ["https://example.com/", "https://test.com/"]

        # Act
        result = await self.bot.prepare_message(canonical_urls)

        # Assert
        self.assertIsInstance(result, TextMessageEventContent)
        self.assertEqual(result.msgtype, MessageType.NOTICE)
        self.assertIn(canonical_urls[0], result.body)
        self.assertIn(canonical_urls[1], result.body)
        self.assertIn(canonical_urls[0], result.formatted_body)
        self.assertIn(canonical_urls[1], result.formatted_body)


if __name__ == '__main__':
    unittest.main()
