import asyncio
from aiohttp import ClientError
from maubot import Plugin, MessageEvent
from maubot.handlers import command
from mautrix.types import TextMessageEventContent, MessageType, Format
from bs4 import BeautifulSoup
from urllib.parse import urlparse


class SimpleAmputatorBot(Plugin):
    @command.passive(r"(https?://\S+)", multiple=True)
    async def amputate(self, evt: MessageEvent, matches: list[tuple[str, str]]) -> None:
        if evt.sender == self.client.mxid:
            return
        await evt.mark_read()
        deamped_urls = []
        for url in matches:
            text = await self.fetch_page_content(url[1])
            if not text:
                return
            deamped_url = await asyncio.get_event_loop().run_in_executor(None, self.extract_canonical_url, url[1], text)
            if deamped_url:
                deamped_urls.append(deamped_url)
        if not deamped_urls:
            return

        html = (
            f"<blockquote>"
            f"It looks like your message contains a Google AMP link. Here's a clean link:<br>• "
            f"{'<br>• '.join(deamped_urls)}"
            f"</blockquote>"
        )
        body = (
            f"> It looks like your message contains a Google AMP link. Here's a clean link:  \n> • "
            f"{'  \n> • '.join(deamped_urls)}"
        )
        content = TextMessageEventContent(
            msgtype=MessageType.NOTICE,
            format=Format.HTML,
            body=body,
            formatted_body=html)
        await evt.respond(content)

    async def fetch_page_content(self, url: str) -> str:
        headers = {
            "Sec-GPC": "1",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "pl,en-US;q=0.7,en;q=0.3",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:139.0) Gecko/20100101 Firefox/139.0",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        try:
            response = await self.http.get(url, headers=headers, raise_for_status=True)
            if response.content_type in ["text/html", "application/xhtml+xml", "application/xml"]:
                return await response.text()
            else:
                return ""
        except ClientError as e:
            self.log.error(f"Connection Error: {e}")
            return ""
        except Exception as e:
            self.log.error(f"Unexpected Error: {e}")
            return ""

    def extract_canonical_url(self, url: str, text: str) -> str:
        soup = BeautifulSoup(text, "html.parser")
        amp_link = None
        canonical_link = None
        if soup and soup.head:
            amp_link = soup.head.find("link", rel="amphtml")
            amp_link = None if amp_link is None else amp_link["href"]
            canonical_link = soup.head.find("link", rel="canonical")
            canonical_link = None if canonical_link is None else canonical_link["href"]

        if soup.find("html").has_attr("amp") or soup.find("html").has_attr("⚡") or self.urls_match(amp_link, url):
            if canonical_link and canonical_link != amp_link:
                return canonical_link
        return ""

    @staticmethod
    def urls_match(url_string: str, url_string2: str) -> bool:
        if url_string is None or url_string2 is None:
            return False
        if url_string.endswith("/"):
            url_string = url_string[:-1]
        if url_string2.endswith("/"):
            url_string2 = url_string2[:-1]
        url1 = urlparse(url_string)
        url2 = urlparse(url_string2)
        return url1.netloc == url2.netloc and url1.path == url2.path and url1.query == url2.query and url1.params == url2.params
