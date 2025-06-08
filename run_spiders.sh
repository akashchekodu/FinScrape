#!/bin/bash
# Navigate to the Scrapy project directory
cd /root/Finantial-News/news_scraper

# Run three Scrapy spiders sequentially
/usr/bin/python3 -m scrapy crawl mcnewsspider
/usr/bin/python3 -m scrapy crawl pulsenewsspider
/usr/bin/python3 -m scrapy crawl bsnewsspider

