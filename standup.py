# -*- coding: utf-8 -*-
import json
import time
import smtplib
import ssl
import pickle
from email.mime.text import MIMEText
from datetime import date

import slack

import config

today = date.today()
today_str = today.strftime("%B %d, %Y")

def conformToAscii(text):
    text = text.replace('•', '-')
    return ''.join([i if ord(i) < 128 else ' ' for i in text])

def send_standup_email(msg_lst):
    ascii_msg_lst = list(map(conformToAscii, msg_lst)) #necessary to use the SMTP_SSL mail server
    msg = MIMEText("PGP Daily Standup: \n\n{}".format("\n\n".join(ascii_msg_lst)))
    msg['Subject'] = "PGP Daily Standup - {}".format(today_str)
    sender = config.gmail_username
    recipient_lst = [config.gmail_username, 'bdemers@princeton.edu', 'baxter.demers@gmail.com'] if config.debug else config.to_emails
    recipients =  ", ".join(recipient_lst)
    print("recipients: ", recipients)
    msg['From'] = sender
    msg['To'] = recipients
    port = 465
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
        server.login(config.gmail_username, config.gmail_password)
        server.sendmail(sender, recipient_lst, msg.as_string())

def send_weekly_email():
    msg = MIMEText("""
    Hi Team, 
    
    Here's your weekly email: 
    
    1. What are your main goals for this week, and what OKR's do they fit under (or not).
    2. Are there any problem solvings you would like to have this week to push you forward? Any blockers?
    3. Are there any big (or small) accomplishments you want to celebrate with the group? Any recent developments or decisions made?
    4. What is something you thought didn't go well last week, and what can we do to be more prepared/do better next time?
    """)
    msg['Subject'] = "Weekly email for {}".format(today_str)
    sender = config.gmail_username
    recipient_lst = [config.gmail_username, 'bdemers@princeton.edu', 'baxter.demers@gmail.com'] if config.debug else config.to_emails
    recipients =  ", ".join(recipient_lst)
    msg['From'] = sender
    msg['To'] = recipients
    port = 465
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
        server.login(config.gmail_username, config.gmail_password)
        server.sendmail(sender, recipient_lst, msg.as_string())

def slack_message(message, channel=config.slack_channel):
    response = sc.chat_postMessage(channel=channel,text=message, username='Standup Bot', icon_emoji=':robot_face:')
    thread_ts = response['ts']
    return thread_ts
    
if __name__ == "__main__":
    #reset the message file (to be used for persistent asynchronous communication with the listener.py proccess)
    with open('msg_lst', 'wb') as f:
        real_nameToStandup = {}
        pickle.dump(real_nameToStandup, f)

    sc = slack.WebClient(config.slack_token)

    # thread time stamp serves as a way to identify messages which are replies to the standup request
    # replies will have a 'thread_ts' field equal to the ts of this request (ts = timestamp)
    thread_ts = slack_message("""{} Standup Meeting Thread \n Good morning <!channel>! Reply to this thread with
    • what you worked on yesterday
    • what you’re planning to working on today
    • a list of any blockers you have.""".format(today_str))

    # puts the thread_ts in persistent storage so that the listener.py can asynchronously access it
    with open('thread_ts_pickle', 'wb') as f:
        pickle.dump(thread_ts, f)

    time.sleep(54 if config.debug else 5400) # wait 1.5 hours
    slack_message("Reminder - only 30 minutes left to submit your standup report.")
    time.sleep(18 if config.debug else 1800) # wait .5 hours
    slack_message("Responses are closed for today - emailing Baxter the responses")

    # reads the list of standup reports collected by listener.py
    with open('msg_lst', 'rb') as f:
        real_nameToStandup = pickle.load(f)
        print("msg_lst : ", real_nameToStandup)

    msg_lst = ["{}: {}".format(k, v) for k,v in real_nameToStandup.items()]
    send_standup_email(msg_lst)

