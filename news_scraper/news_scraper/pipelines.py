import os
import psycopg2
from dotenv import load_dotenv
from itemadapter import ItemAdapter
from datetime import datetime, timedelta, timedelta

# Load environment variables from .env file
load_dotenv()

# Get the connection string and password from the environment variables
DB_CONNECTION_STRING = os.getenv("DB_CONNECTION_STRING")

class NewsScraperPipeline:
    def open_spider(self, spider):
        # Create a database connection using the connection string
        self.connection = psycopg2.connect(DB_CONNECTION_STRING)
        self.cursor = self.connection.cursor()
        # Cleanup old news when the spider opens
        self.delete_old_news(spider)

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        # Prepare the data to be inserted
        data = (
            adapter.get('title'),
            adapter.get('link'),
            adapter.get('date'),  # Ensure this matches the format expected in the database
            adapter.get('description'),
            adapter.get('source')
        )

        # Insert the data into the PostgreSQL database
        try:
            self.cursor.execute("""
                INSERT INTO news (title, link, date, description, source)
                VALUES (%s, %s, %s, %s, %s)
            """, data)
            self.connection.commit()
        except Exception as e:
            spider.logger.error(f"Error inserting into PostgreSQL: {e}")

        return item

    def delete_old_news(self, spider):
        one_day_ago_ist = datetime.utcnow() - timedelta(days=1)

        try:
            # Perform the deletion
            self.cursor.execute("""
                DELETE FROM news WHERE date < %s OR created_at < %s
            """, (one_day_ago_ist,one_day_ago_ist))
            self.connection.commit()
            spider.logger.info("Old news deleted successfully")
        except Exception as e:
            spider.logger.error(f"An exception occurred while deleting old news: {str(e)}")

    def close_spider(self, spider):
        # Close the database connection when the spider closes
        self.cursor.close()
        self.connection.close()
