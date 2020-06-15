# A simple script that logs when your Nord VPN IP address changes, along with how
# long the previous IP was held for. ~ defaultroot

import requests
from time import sleep, time
import logging
import pickle

def logging_setup(log_level='INFO', file_name='nord_ip_log.log'):

    # Set up logging levels, formatting and file name

    logging.basicConfig(level=log_level,
                        format='%(asctime)s\t%(message)s', datefmt='%d/%m/%y %H:%M',
                        filename=file_name)


def get_ip():

    # Make request to nordvpn.com for current VPN details, and extract IP from the returned JSON

    try:
        r = requests.get('https://nordvpn.com/api/vpn/check/full')
        ip_result = r.json()['ip']
        print(f"IP: {ip_result}")   # Console feedback
        return ip_result
    except:
        logging.error("Could not retrieve IP address from nordvpn.com")


def save_pickle(ip, filename):
    try:
        with open(f"{filename}", "wb") as f:
            pickle.dump(ip, f)
        logging.debug(f"Saved IP {ip} to {filename}")

    except:
        logging.error(f"Error saving {ip} to {filename}")

def load_pickle(filename):

    try:
        with open(f"{filename}", "rb") as f:
            imported_pickle = pickle.load(f)
        logging.debug(f"Loaded {filename} with IP {imported_pickle}")
        return imported_pickle

    except:
        logging.warning(f"No file named {filename} found, so returning an empty IP. Normal if first run of program.")
        return "0.0.0.0"


### Variables ###

RECHECK_TIME_IN_MINUTES = 1        # How often IP address is checked

#################

def main():

    logging_setup()

    current_ip = load_pickle("last_ip")

    start_time = time()  # For measuring how long an IP was retained for

    while True:

        ip = get_ip()

        if ip is not None:

            if ip != current_ip:

                # Calculate how long the previous IP was held in minutes, and log the change. Print for console feedback
                elapsed_time = round((time() - start_time) / 60, 2)
                print(f"Changed IP from {current_ip} to {ip} after {elapsed_time} minutes")
                logging.info(f"Changed IP from {current_ip} to {ip} after {elapsed_time} minutes")

                # Update the current IP, save the IP to pickle file, and reset the timer for the new IP.
                current_ip = ip
                save_pickle(ip, "last_ip")
                start_time = time()

            else:
                pass    # No new IP, so pass
        else:
            pass        # Nord VPN API probably not available, so just pass

        sleep(RECHECK_TIME_IN_MINUTES * 60)


if __name__ == '__main__':
    main()
