# Simple Amputator Bot

A maubot for Matrix messaging that automatically checks if messages sent in the chat contain Google AMP links. If so the bot responds with retrieved canonical links. It requires no configuration.

![bot_simple_amputator](https://github.com/user-attachments/assets/fa26167d-213d-47a9-8a6a-aea8af2d26c6)

## Usage
The bot automatically analyzes all messages sent in the chat for potential AMP links. There's no need for manual activation by issuing message with a command. If it detects such a link, the bot sends a message with the original version of it.

### Notes
**Q:** What is an AMP link and why would I want to avoid it?  
**A:** AMP (Accelerated Mobile Pages) is an open source HTML framework originally created by Google as a competitor to Facebook Instant Articles and Apple News. AMP is optimized for mobile web browsing and intended to help webpages load faster. However, there are many concerns about AMP pages, among them:  
- questionable performance boost, 
- way cached AMP pages keep users in Google's ecosystem, 
- obscurity of publisher's domains on cached AMP pages, 
- loss of sovereignty of websites, 
- lack of functionality and diversity on some AMP pages
- privacy concerns

You can read more about it [on Wikipedia](https://en.wikipedia.org/wiki/Accelerated_Mobile_Pages#Reception).

**Q:** Someone sent a message with a URL that looks like an AMP link. Why does the bot not react?  
**A:** Not all links that seem to lead to AMP webpages actually do. As some publishers are dropping AMP technology, the old AMP links may lead to original versions of the webpage. There's no need to send the same link twice. Other than that, this bot doesn't aim to reach 100% success rate. It won't work with sites that do not implement AMP according to the spec. I wanted to keep it simple.

**Q:** How do I know if the bot has analyzed the message?  
**A:** The bot sends a read receipt to the message it has started analyzing. If after a few seconds there's no response from the bot, it means that the link in the message was not an AMP link or the bot failed to detect it / there was an error accessing the page.
