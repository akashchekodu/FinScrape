# FinScrape

FinScrape is a tool developed to scrape financial data and store it efficiently in a database using Flask. This project focuses on the backend, handling data collection and storage. It is deployed on an AWS server, making it accessible for real-time or periodic data updates.

## Features

- **Data Scraping**: Collects financial data from specified sources.
- **Database Integration**: Saves data into a database using Flask, allowing easy access and retrieval.
- **AWS Deployment**: Hosted on an AWS server for reliable and scalable access.

## Data Sources

FinScrape collects data from the following sources:

- [Business Standard](https://www.business-standard.com/)
- [MoneyControl](https://www.moneycontrol.com/)
- [Pulse](https://pulse.zerodha.com/)


## Getting Started

### Prerequisites

- **Python** (v3.7+)
- **Flask** (v2.0+)
- **SQLAlchemy** or any preferred ORM (optional for database management)

### Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/akashchekodu/FinScrape.git
   cd FinScrape
   ```

2. **Install Requirements**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Database**

   - Update database configuration in `config.py` (or your database configuration file).

4. **Run the Application**
   ```bash
   flask run
   ```
   The application will start locally at `http://127.0.0.1:5000`.

### Deployment

This project is deployed on an AWS server. To deploy it yourself, follow these steps:

1. **Prepare AWS Server**: Set up an EC2 instance or other compute resources.
2. **Configure Environment**: Set up Flask and the necessary Python environment on the AWS server.
3. **Run Application**: Deploy the app by running `flask run` or setting it up with a web server like Nginx for production use.

## Notes

This repository does not include a frontend. The focus is on data scraping and backend functionality.

---

For additional resources, see [NewsFolio](https://newsfolio.vercel.app/), project made by using this collected data.

## License

This project is licensed under the MIT License.

