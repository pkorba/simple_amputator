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
            deamped_url = await self._extract_canonical_url_from_amp(url[1])
            if deamped_url:
                deamped_urls.append(deamped_url)

        if not deamped_urls:
            return

        html = f"""It looks like your message contains a Google AMP link. Here, I've cleaned it up for you:<br>•
        {"<br>• ".join(deamped_urls)}"""
        body = f"It looks like your message contains a Google AMP link.. Here, I've cleaned it up for you:\n {"\n• ".join(deamped_urls)}"
        content = TextMessageEventContent(
            msgtype=MessageType.NOTICE,
            format=Format.HTML,
            body=body,
            formatted_body=f"{html}")
        await evt.respond(content)

    async def _extract_canonical_url_from_amp(self, url: str) -> str:
        headers = {
            "Sec-GPC": "1",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "pl,en-US;q=0.7,en;q=0.3",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64; rv:138.0) Gecko/20100101 Firefox/138.0"
        }
        try:
            response = await self.http.get(url, headers=headers, raise_for_status=True)
            if response.content_type in ["text/html", "application/xhtml+xml", "application/xml"]:
                text = await response.text()
            else:
                return ""
        except ClientError as e:
            self.log.error(f"Connection Error: {e}")
            return ""

        soup = BeautifulSoup(text, "html.parser")
        amp_link = None
        canonical_link = None
        if soup.head is not None:
            amp_link = soup.head.find("link", rel="amphtml")
            amp_link = None if amp_link is None else amp_link["href"]
            canonical_link = soup.head.find("link", rel="canonical")
            canonical_link = None if canonical_link is None else canonical_link["href"]

        if soup.find("html").has_attr("amp") or soup.find("html").has_attr("⚡") or await self._urls_match(amp_link, url):
            if canonical_link and canonical_link != amp_link:
                return canonical_link
        return ""

    @staticmethod
    async def _urls_match(url_string: str, url_string2: str) -> bool:
        if url_string is None or url_string2 is None:
            return False
        if url_string.endswith("/"):
            url_string = url_string[:-1]
        if url_string2.endswith("/"):
            url_string2 = url_string2[:-1]
        url1 = urlparse(url_string)
        url2 = urlparse(url_string2)
        return url1.netloc == url2.netloc and url1.path == url2.path and url1.query == url2.query and url1.params == url2.params
