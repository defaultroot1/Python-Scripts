# A script that generates a report on users who have connected to Pulse Secure VPN in last 24 hours.
# Requires a command to run in PowerShell first to dump a list of domain users (line 93)
# Some variable/function names refactored so as not to identify workplace...hopefully still works after! ~ deafultroot

from selenium import webdriver
from time import sleep
from selenium.webdriver.common.keys import Keys
import csv
import smtplib
import glob, os
from datetime import datetime

PULSE_SECURE_HOSTNAME = "your_pulse_secure_hostname_or_ip"
PULSE_SECURE_USERNAME = "admin"
PULSE_SECURE_PASSWORD = "admin"

EMAIL_REPORT_SENDER_ADDRESS = "PulseSecureReport@yourdomain.com"
EMAIL_REPORT_RECIPIENTS = ['recipient1@yourdomain.com', 'recipient2@yourdomain.com']
EMAIL_REPORT_SMTP = "smtp@yourdomain.com"



def getUserLogFromPulseSecure():

    # Function logs into Pulse Secure and downloads User Activity log for the past 24 hours

    # ChomeDriver for Chrome 80 downloaded from https://chromedriver.storage.googleapis.com/index.html?path=80.0.3987.106/
    # and placed in C:\Windows\System32. Confirm in PATH by running chromedriver in CMD
    driver = webdriver.Chrome()

    # URL for Secure Remote login page
    url = f"https://{PULSE_SECURE_HOSTNAME}/dana-na/auth/url_admin/welcome.cgi"
    driver.get(url)

    # Click Advanced/Proceed on SSL Certificate warning screen
    driver.find_element_by_id("details-button").click()
    driver.find_element_by_id("proceed-link").click()

    # Find username field and enter username
    username = driver.find_element_by_id("username")
    username.clear()
    username.send_keys(PULSE_SECURE_USERNAME)
    print("Entered username")

    # Find password field and enter password
    password = driver.find_element_by_id("password")
    password.clear()
    password.send_keys(PULSE_SECURE_PASSWORD)
    print("Entered password")

    # Find Sumbit button and click
    driver.find_element_by_name("btnSubmit").click()
    print("Clicked Submit")

    # If admin account is already logged in, there may be a warning. If so, click "Read only access", otherwise proceed
    try:
        driver.find_element_by_name("btnReadOnly").click()
    except:
        pass

    # Fix to open a new tab, allowing a direct URL to be entered without starting a new session
    driver.find_element_by_tag_name('body').send_keys(Keys.CONTROL + 't')

    # Direct link to downloaded the CSV log file of active sessions
    driver.get(f"https://{PULSE_SECURE_HOSTNAME}/dana-admin/reporting/report_user_summary.cgi?download=1&amp;format=csv&amp;date_range=24hours&amp;username=&amp;realm=&amp;sort_column=username&amp;sort_order=2")
    # Small pause to allow CSV file to complete download
    sleep(3)

def getUser34FromPulseSecureLog(pathToCSV):

    # Empty array to hold user samAccountName ID strings
    users_by_samaccountname = []

    # Count to skip first line of CSV file (headings)
    count = 0

    with open(pathToCSV) as csv_file:
        csv_reader = csv.reader(csv_file)
        for line in csv_reader:
            # Skip first blank line
            if count == 0:
                count += 1
            else:
                users_by_samaccountname.append(str(line[0][8:]))
                count += 1

    # Return an array of samAccountName IDs
    return users_by_samaccountname

def getUsersOnPulseSecureLast24Hr(users_by_samaccountname):

    # Create a blank dictionary to hold [samAccountName:Display] name string pairs
    allUserDict = {}

    # Read all current samAccountName/Display names from a pre-made list generated from Powershell
    # get-aduser -filter * | select samaccountname, name | out-file c:\allusers.txt
    # Replace spaces with commas in text editor, import the text file into Excel CSV using commas as delimiter
    with open(r'c:\Scripts\allusers.csv') as csv_file:
        csv_reader = csv.reader(csv_file)
        for line in csv_reader:
            name = line[1].replace("’", "")
            allUserDict[line[0].lower()] = name

    # Blank list to hold string of user samAccountName IDs from Secure Pulse log
    usersLast24Hr = []

    for user in users_by_samaccountname:
        if user in allUserDict:
            usersLast24Hr.append(allUserDict[user])

    # Return a list of user samAccountName ID strings
    return usersLast24Hr

def getPathToLatestReport():

    # The CSV downloaded from Pulse Secure automatically downloads to Downloads folder. This function selects the
    # latest CSV file. Small chance if will pick up a non-Pulse Secure related CSV file!

    current_user = os.getlogin()

    list_of_files = glob.glob(f'c:\\users\\{current_user}\\downloads\\*.csv')
    latest_file = max(list_of_files, key=os.path.getctime)
    print(f"Using file: {latest_file}")

    # Returns full path to the CSV file
    return latest_file

def sendMailReport(users_last_24hr, sender, recipients, server):

    # Send email report to emails in 'recipients' list

    dateString = "{:%B %d, %Y}".format(datetime.now())

    server = smtplib.SMTP(server, 25)

    subject = f'Pulse Secure User Report for {dateString}'
    msg = f'Subject: {subject}\n\nThe following users were connected to Pulse Secure in the past 24 hours: \n\n'

    for user in users_last_24hr:
        msg += user + "\n"

    server.sendmail(sender, recipients, msg)

def main():

    getUserLogFromPulseSecure()

    users_by_34id = getUser34FromPulseSecureLog(getPathToLatestReport())

    users_last_24hr = getUsersOnPulseSecureLast24Hr(users_by_34id)

    sendMailReport(users_last_24hr, EMAIL_REPORT_SENDER_ADDRESS, EMAIL_REPORT_RECIPIENTS, EMAIL_REPORT_SMTP)

if __name__ == "__main__":
    main()

