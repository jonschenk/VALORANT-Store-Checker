import os
import json
import time
import schedule
import threading
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta
from pynput import keyboard
from valorantstore import ValorantStore
from email.mime.image import MIMEImage
import requests
import pygetwindow as gw
from io import BytesIO

with open('config.json', 'r') as config_file:
    config = json.load(config_file)

USRNAME = config['USRNAME']
PASSWORD = config['PASSWORD']
SKIN_IDS = config['SKIN_IDS']
FROM_EMAIL = config['FROM_EMAIL']
TO_EMAIL = config['TO_EMAIL']
EMAIL_PASSWORD = config['EMAIL_PASSWORD']

valorant_store = ValorantStore(username=USRNAME, password=PASSWORD, region="na", sess_path=None, proxy=None)
current_store = ''
daily_offers = ''

def refresh():
    """
    Refreshes the VALORANT Store
    """
    global current_store, daily_offers
    current_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    current_store = valorant_store.store(True)
    daily_offers = current_store['daily_offers']['data']

    print(f"\nStore refreshed on {current_date}")
    item_check()

def on_press(key):
    """
    Listens for hotkey presses
    """
    try:
        active_window = gw.getActiveWindowTitle()

        if "Windows PowerShell" in active_window:
            if key == keyboard.KeyCode.from_char('r'):
                refresh()
            if key == keyboard.Key.esc:
                end()
    except AttributeError:
        pass

def item_check():
    """
    Checks if the specified item exists in the daily offers
    """
    success = False
    item_list = []
    for item in daily_offers:
        if item['id'] in SKIN_IDS:
            success = True
            item_list.append(valorant_store.skin_info(item['id'])['displayName'])

    current_store = []
    images = []
    for item in daily_offers:
        current_store.append(valorant_store.skin_info(item['id'])['displayName'])
        images.append(valorant_store.skin_info(item['id'])['displayIcon'])
    print(current_store)

    current_store_str = ', '.join(current_store)
    
    if success:
        items_str = ', '.join(item_list)
        email_alert("VALORANT Store Checker", f"{items_str} is in your VALORANT store!\n\nCurrent store:\n{current_store_str}\n\n\nhttps://github.com/jonschenk", TO_EMAIL, images)
        print(f"\n{items_str} is in your VALORANT store!")
    else:
        print("\nNo sought after items were found in your VALORANT store today. Better luck tomorrow!")
        email_alert("VALORANT Store Checker", f"No sought after items were found in your VALORANT store today. Better luck tomorrow!\n\nCurrent store:\n{current_store_str}\n\n\nhttps://github.com/jonschenk", TO_EMAIL, images)

def email_alert(subject, body, to, image_paths=[]):
    msg = EmailMessage()
    msg.set_content(body)
    msg['from'] = FROM_EMAIL
    msg['subject'] = subject
    msg['to'] = to

    for image_path in image_paths:
        if image_path.startswith('http://') or image_path.startswith('https://'):
            response = requests.get(image_path)
            img_data = BytesIO(response.content).read()
            img_name = os.path.basename(image_path)
        else:
            with open(image_path, 'rb') as img:
                img_data = img.read()
                img_name = os.path.basename(image_path)

        msg.add_attachment(img_data, maintype='image', subtype='jpeg', filename=img_name)

    user = FROM_EMAIL
    password = EMAIL_PASSWORD

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(user, password)
    server.send_message(msg)

    server.quit()

def get_remaining_time():
    now = datetime.now()
    next_update = now.replace(hour=17, minute=0, second=5, microsecond=0)
    if now > next_update:
        next_update += timedelta(days=1)
    remaining_time = next_update - now
    remaining_time = str(remaining_time).split('.')[0]
    return remaining_time

def countdown_to_update():
    while True:
        remaining_time = get_remaining_time()
        print(f"Time until next store update: {remaining_time}", end='\r')
        time.sleep(1)

def end():
    """
    Ends the program
    """
    print("Exiting...")
    os._exit(0)

if __name__ == '__main__':
    print("\n\nVALORANT Store Checker by Jon Schenk: https://github.com/jonschenk\n\n")
    print(f"Logged in as {USRNAME}\n\n")

    #list target items
    items = []
    print("Target items:")
    for skin_id in SKIN_IDS:
        items.append(valorant_store.skin_info(skin_id)['displayName'])

    print(items)

    email_alert("VALORANT Store Checker", f"VALORANT Store Checker has started. The next store update will be in {get_remaining_time()}\n\n\nhttps://github.com/jonschenk", TO_EMAIL)

    refresh()
    schedule.every().day.at("17:00:05").do(refresh)

    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    countdown_thread = threading.Thread(target=countdown_to_update)
    countdown_thread.daemon = True
    countdown_thread.start()

    while True:
        schedule.run_pending()
        time.sleep(1)