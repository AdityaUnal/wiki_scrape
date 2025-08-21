# Wiki-Scraper

- I have created an automation for extraction of information from the first 10 rows of the table "List of FIFA World Cup finals" on the [Wikipedia page](https://en.wikipedia.org/wiki/List_of_FIFA_World_Cup_finals).

## Assumptions

- The DOM elements for the table and each row would be known. If not we can use beautiful soup and the caption of the table.
- I have sent all 10 at once to the google sheet as the payload size is less here and google APIs allow upto 2 MB of data in one payload. This would make more sense in case the rows increase as google allows 300 writes per minute, so batching would scale better.

## Getting Started
- Setup the google cloud developer account and project for allowing to edit google sheet([Steps](https://ai2.appinventor.mit.edu/reference/other/googlesheets-api-setup.html))
- Download the json and save it.
- Setup the .env file :
```
GOOGLE-SHEET-JSON=path/to/google/api.json
SPREADSHEET-ID=xxxxx
```
- Use the following steps to append :
```
git clone https://github.com/AdityaUnal/wiki_scrape
pip install -r requirements.txt
python run automate.py
```
## Steps for automation
- ![alt text](https://github.com/AdityaUnal/wiki_scrape/blob/main/flow-chart.png)
