# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals

# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter
import random



class NewsScraperSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class NewsScraperDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    USER_AGENT_LIST = []

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        s.load_user_agents("/root/Finantial-News/news_scraper/news_scraper/user_agents.txt")
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def load_user_agents(self, filepath):
        """Load User-Agent strings from a file and store them in a list."""
        try:
            with open(filepath, 'r') as file:
                for line in file:
                    # Split at '|' and get the User-Agent part
                    parts = line.strip().split('|')
                    if len(parts) > 1:
                        self.USER_AGENT_LIST.append(parts[1])
        except FileNotFoundError:
            print(f"User-Agent file not found: {filepath}")
        except Exception as e:
            print(f"Error loading User-Agents: {e}")

    def process_request(self, request, spider):
        # Set a random User-Agent from the list for each request
        if self.USER_AGENT_LIST:
            user_agent = random.choice(self.USER_AGENT_LIST)
            request.headers['User-Agent'] = user_agent
            spider.logger.info(f"User-Agent set to: {user_agent}")

        # Set other headers
        request.headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        request.headers['Accept-Language'] = 'en-US,en;q=0.5'
        request.headers['Connection'] = 'keep-alive'
        request.headers['Upgrade-Insecure-Requests'] = '1'
        request.headers['Referer'] = 'https://example.com'  # Change this to the appropriate referer if needed

        # Log the complete headers for debugging
        spider.logger.info(f"Request headers set: {request.headers}")

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.
        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)
