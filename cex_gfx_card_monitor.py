"""
Scrape GFX card data from CEX IE and alert for newly available cards

API reference: https://github.com/Dionakra/webuy-api

"""

import requests
import json
import smtplib
import logging

logging.basicConfig(filename="cex_monitor_log.log",
                    encoding="utf-8",
                    level=logging.INFO,
                    format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %H:%M:%S')
logging.info("Script started")

GMAIL_ADDRESS = "MyGmailAddress@gmail.com"
GMAIL_USERNAME = "MyGmailUsername"
GMAIL_PASSWORD = "MyGmailPassword"
RECIPIENT_EMAIL = "emailtosendalerts@email.local"

def cex_search(search_string):
    """
    Search CEX for search string, returning results in json (in stock, sorted by price, high to low)
    """
    url = "https://wss2.cex.ie.webuy.io/v3/boxes"
    query = fr"q={search_string}&firstRecord=1&count=50&sortBy=sellprice&sortOrder=desc&inStockOnline=1&inStock=1"

    try:
        r = requests.get(url, params=query)
        r.raise_for_status()
        logging.info(f"Request returned {r.status_code}")
        return r.json()['response']['data']['boxes']

    except requests.exceptions.HTTPError as errh:
        logging.error(errh)
    except requests.exceptions.ConnectionError as errc:
        logging.error(errc)
    except requests.exceptions.Timeout as errt:
        logging.error(errt)
    except requests.exceptions.RequestException as err:
        logging.error(err)

def save_json(data, filename):
    with open(f'{filename}', 'w') as outfile:
        json.dump(data, outfile)
    logging.info(f"Saved data to {filename}")

def load_json(filename):
    with open(filename) as infile:
        return json.load(infile)

def get_new_cards(results):

    """
    Returns a dictionary of new cards since last check. Dictionary contains only fields relevant to
    the email body (name, price, previous price etc), not the full dictionary in the API request
    """

    # Check if file exists. If it doesn't, probably first run of program, so create an empty dictionary of results
    try:
        last_check = load_json('last_check.json')
    except:
        last_check = {}

    new_cards = []
    for result in results:
        is_new_card = True
        for card in last_check:
            if result['boxId'] == card['boxId']:
                is_new_card = False
                break
        if is_new_card:
            new_cards.append({'boxId': result['boxId'],
                              'boxName': result['boxName'],
                              'sellPrice': result['sellPrice'],
                              'previousPrice': result['previousPrice'],
                              'firstPrice': result['firstPrice'],
                              'lastPriceUpdatedDate': result['lastPriceUpdatedDate']
                              })
    return new_cards

def send_alert_email(new_cards):

    email_body = ""
    email_body += "\nThere are new GFX cards available on CEX: \n"

    for card in new_cards:
        card_string = f"\n" \
                      f"Name: \t{card['boxName']}\n" \
                      f"Price: \t{card['sellPrice']}\n" \
                      f"Prev: \t{card['previousPrice']}\n" \
                      f"Orig: \t{card['firstPrice']}\n" \
                      f"Update: \t{card['lastPriceUpdatedDate']}\n"
        email_body += card_string

    email_body += "\nLink: https://ie.webuy.com/search?inStock=1&categoryIds=892&sortBy=sellprice&sortOrder=desc&view=list&inStockOnline=1"

    with smtplib.SMTP("smtp.gmail.com") as connection:
        connection.starttls()
        connection.login(user=GMAIL_USERNAME, password=GMAIL_PASSWORD)
        connection.sendmail(from_addr=GMAIL_ADDRESS,
                            to_addrs=RECIPIENT_EMAIL,
                            msg=f"Subject:CEX Alert\n\n{email_body}"
                            )

    logging.info(f"Email alert sent")

results = cex_search("PCI-Express Graphics")

new_cards = get_new_cards(results)

if len(new_cards) > 0:
    send_alert_email(new_cards)
    save_json(results, "last_check.json")

else:
    logging.info("No new cards found")
    pass



