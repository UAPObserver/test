'''
Provided by:
https://UAP.Observer project.

Please note: This is written by someone with very little exerience in coding. It can and should be improved upon by a lot!
'''

from bs4 import BeautifulSoup
import requests
import sys
from requests import get
from fake_useragent import UserAgent
from redvid import Downloader
import telebot
import time
import random
import string
import os
import logging
import traceback
import youtube_dl as yt_dl
from waybackpy import WaybackMachineSaveAPI
from pathlib import Path
from selenium import webdriver
from PIL import Image
import numpy as np
import cv2
import internetarchive
from internetarchive import configure
from internetarchive import get_session
from internetarchive import upload
import tweepy
import re
from predict import predict_one_image
from app import video_prediction


############################################################################################
'''
Config files you will have to change the values here to your API key, auths, account, ect.
'''

# Archive.org account info
configure('user@email.com', 'password')
config = {'s3': {'access': 'foo', 'secret': 'bar'}}

# Your local pathways
root_path = '/home/d/observer/'
main_path = "/home/d/observer/reddit/"
chromium_path = '/home/d/observer/reddit/chromedriver'

# Telegram bot auth key
tb = telebot.TeleBot("526343468:AAEDcroJqYLUTRhrgvJoACbHA-mmzsd")

#Telegram Channel ID
chat_id = '-14456554566659'

# Twitter bot API access
consumer_key = "ngggfdgfgdAn5viXr4x6PwO"
consumer_secret = "9rJa54akNRpvU7KgdgW7sEkVZgggdfgddfddZ8ZzHA6"
access_token = "14455473dg545645-gdg0ITjPec7MA4QuGZfRiIv"
access_token_secret = "DYKKxBZAcduc3qwggBgCwXcgbMZEj3WdFQ"

# Media links you want to find.
search_directory = ["v.redd.it", "i.redd.it", "youtube.com", "youtu.be", "i.imgur.com"]

# All categories available in a Subreddit
categories = ["Discussion", "Photo", "Video", "News", "Article", "Witness/Sighting", "Clipping", "Resource", "Compilation", "Documentary", "Document/Research", "Podcast", "UFO Blog", "Meta", "X-post", "Classic Case", "Sighting Report"]
# The ones you want to stil archive or predict even if they dont contain a search directory link.
select = ["Video", "Witness/Sighting", "Sighting Report"]

############################################################################################

# Starts Archive.org session
s = get_session(config)
s.access_key

# Starts up the Twitter bot
client = tweepy.Client(consumer_key=consumer_key, consumer_secret=consumer_secret, access_token=access_token, access_token_secret=access_token_secret, wait_on_rate_limit = True)

# Starts Reddit media downloader
reddit = Downloader(max_q=True)
ua = UserAgent()

# Post filler tiles for starting up.
main_title = 'x'
current_title = 'y'

############################################################################################

# Tweets any custom generated string message passed down
def send_tweet(tweet, client):
    try:
        stat = ""
        response = client.create_tweet(text=tweet)
    except Exception as e:
        print(str(e))
        print("Error: cannot send tweet.")

    #print(f"https://twitter.com/UAP_Observer/status/{response.data['id']}")

# Uploads media to Archive.org, bless their soul.
def upload_archive(path, multiple, mediatypee, rand, full_link, main_title):
    main_title = str(re.sub("[\(\[].*?[\)\]]", "", main_title))
    md = {'title': str(main_title) , 'creator': 'UAP_Observer'}

    if multiple == False:
        print("c")
        media_link_r = upload(str(rand), [path],  metadata=md, queue_derive=True)
        print("File succesfully uploaded to archived.")
        media_link = "https://archive.org/embed/" + str(rand) + "/"
        return str(media_link)

# Retrieves full page sourcecode from a link.
def lovely_soup(u):
    r = get(u, headers={'User-Agent': ua.chrome})
    return BeautifulSoup(r.text, 'lxml')

# Generates a random sting of chars given length.
def get_random_string(length):
    # choose from all lowercase letter
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return str(result_str)

# Retrieves subpath to where a video post is now located locally.
def get_subpath(basepath):
    for entry in os.scandir(basepath):
        if entry.is_dir():
            sub_path = entry.name
            return str(sub_path)

# Retrieves exact name of the video it just downloaded
def get_video_name(main_path):
    for mp4_path in Path(main_path).glob("*.mp4"):
        return  str(mp4_path)

# Splits a Reddit post title from the category it is in, returns them seperately..
def process_title(title):
    category = "Uncategorized"
    for i in range(len(categories)):
        if (categories[i] in title) == 1:
            new_title = title.replace(categories[i], '')
            category = categories[i]
            final_title = new_title + " - Category: " + categories[i]
            return str(final_title), str(category)
    return title, category

# Generates custom Twitter message ready to be tweeted.
def gen_tb_msg(full_link, authenthicity, main_title, embed, embed_archive, prediction):
    main_title = re.sub("[\(\[].*?[\)\]]", "", main_title) # Filters search directory from the post title
    user_agent = "Mozilla/5.0 (Windows NT 5.1; rv:40.0) Gecko/20100101 Firefox/40.0"
    if (authenthicity == 0):
        save_api = WaybackMachineSaveAPI(full_link, user_agent)

        try:
            archive_link = str(save_api.save())
        except( BaseException ):
            archive_link = "None."

        if ((embed == "yes") == True):
            full_link = full_link.replace("https://","www.")
        else:
            full_link = full_link
    if len(embed_archive) > 1 == True:
        full_msg = str("💠 Title:  " +str(main_title) + "\n\n🔍 " + str(prediction) +  "\n\n🔗 Source: " + str(full_link)  +"\n\n🎬 Archived Media: " + str(embed_archive) + "\n\n📚 Archived Source: " + str(archive_link))
    else:
        full_msg = str("💠 Title:  " + str(main_title) + "\n\n🔍 " + str(prediction) + "\n\n🔗 Source: " +str(full_link)  + "\n\n📚 Archived Source: " + str(archive_link))
    return full_msg

def create_tweet_msg(media_link, main_title, full_link, category, prediction):
    main_title = re.sub("[\(\[].*?[\)\]]", "", main_title)
    tweet_msg1 = str("Title: " + str(main_title) + "\n\n🔍 " + str(prediction) + "\n\n🔗 Source: " + str(full_link) + "\n\n🎬 Media: " +str(media_link) + "\n\n(#UFOTwitter #UAP #UFOSightings #Disclosure #UFOs)")
    title_i = main_title.find("Category") - 11
    titlez = str(main_title[0:title_i])
    title = str(titlez +  ".. " +   "⚪ Category: " + str(category))
    tweet_msg2 = str("💠 Title: " + str(title) + "\n\n🔍 " + str(prediction) + "\n\n🔗 Source: " + str(full_link)  + "\n\n🎬 Media: " + str(media_link)  + "\n\n(#UFOTwitter #UAP #UFOs #UFOSightings)")
    tweet_msg3  = str("🔍 " + str(prediction) +  "\n\n⚪ Category: " + str(category) + "\n\n🔗 Source: " + str(full_link)  + "\n\n🎬 Media: " + str(media_link)  + "\n\n(#UFOTwitter #UAP #UFO)")
    tweet_msg4 = str("🔍 " + str(prediction) +  "\n\n⚪ Category: " + str(category) + "\n\n🔗 Source: " + str(full_link)  + "\n\n(#UFOTwitter #UFO #UAP #UFOSightings)")

    if (((len(tweet_msg1)) > 280) == False):
        msg = tweet_msg1

    elif ((len(tweet_msg2) > 280) == False):
        msg = tweet_msg2
    elif ((len(tweet_msg3) > 280) == False):
        msg = tweet_msg3
        print(len(tweet_msg3))
    else:
        msg = str(tweet_msg4)
    return str(msg)

############################################################################################

'''
Indefinite loop that will refresh reddit works at 35 seconds t
o extract the latest post title.
Then it will compare to latest post title. If it fits a new submission of data crtieria, then
store locally and use a Telegram bot to post to specific channel.
'''

def main(main_title, current_title):
    while(True):
        print("Searching")
        while(True):
            time.sleep(35) # Refresh rate you want in seconds
            subreddit_link = 'https://old.reddit.com/r/UFOs/new/'
            soup = lovely_soup(subreddit_link)
            soup_str = str(soup)
            partial_post_link = "https://reddit.com/r/"

            comments_index1 = soup_str.find("data-permalink") + 19
            comments_index2 = soup_str.find("data-rank") - 24
            full_link = partial_post_link + str(soup_str[comments_index1:comments_index2])

            main_title = soup.find('p', class_="title").text
            main_title, category = process_title(main_title)
            print("first category: ", category)
            posts = soup.find_all('p')
            last_post = str(posts[29])
            print("last_post: ", last_post)
            print("Current Post Title: ", main_title)
            print("Current Post Link: ", full_link)
            print("Looking for new images or videos. ~~~>")

            # Checks if it's a not the same post title before procceeding, and updates variables.
            if(((main_title != current_title) and (main_title != 'x'))):
                current_title = main_title
                current_post = last_post

                # In case a new video has been submitted to the UFOs subreddit.
                if ((str(search_directory[0]) in current_post) and (category != "X-post")):
                    # Isolates new video post URL from page source to be used later.
                    index_x = current_post.find("href=") + 6
                    index_y = current_post.find("rel") - 3
                    partial_link = str(current_post[index_x:index_y])
                    partial_link = full_link
                    post_link =  full_link

                    #Retrieving exact download URL for the newwly found video.
                    soup = lovely_soup(post_link)
                    raw_post_data = soup.find_all('p')
                    post_data = last_post
                    index_2 = post_data.find("data-href-url=") + 15
                    index_1 = post_data.find("data-outbound") - 2
                    exact_url = full_link
                    prediction = "~"

                    # Saves the source code and specific string variables related to the new video submission post.
                    rand_string = get_random_string(5)
                    text_filename = "video_metadata_" + str(rand_string) + ".txt"
                    local_path = str(main_path)+ str(rand_string) + "/"
                    text_pathname = str(local_path) + str(text_filename)
                    if (os.path.isdir(local_path) == 0) == True:
                        os.mkdir(local_path)

                    with open(text_pathname, "w", encoding="utf-8") as text_file:
                        text_file.write("Source code:  " + str(current_post))
                        text_file.write("\n\n")
                        text_file.write("Source URL: " + str(exact_url))
                        text_file.close()

                    # Saving the video onto local storage first.
                    reddit.path = local_path
                    reddit.url = exact_url
                    reddit.download()
                    video_filename = str(get_video_name(local_path))

                    filename = video_filename.split('/')[-1]

                    prediction = video_prediction(video_filename)

                    # For now the script assumes the video always comes with audio.
                    audio_signal = "on"
                    upload_link = str(upload_archive(video_filename, False, "video", rand_string, full_link, main_title))

                    msg = gen_tb_msg(full_link, 0, main_title, "yes", upload_link, prediction)

                    video = open(video_filename, 'rb')
                    tb.send_message(chat_id, "------—————------")
                    tb.send_message(chat_id, msg, disable_web_page_preview  = True)
                    tb.send_video(chat_id, video)
                    doc = open(text_pathname, 'rb')
                    tb.send_document(chat_id, doc)

                    twitter_vid_msg = create_tweet_msg(upload_link,  main_title,  full_link, category, prediction)
                    send_tweet(str(twitter_vid_msg), client)

                    main(main_title, current_title)

                # In case the the video is on YouTube, and post is par
                elif (((str(search_directory[2]) in current_post) or (str(search_directory[3]) in current_post)) and ((category == "Witness/Sighting") or(category == "Classic Case") or (category == "Video") or (category == "Photo") or (category == "Discussion") or (category == "Compilation") or (category == "Clipping") or (category == "Documentary") or (category == "X-post"))):
                    index_1 = current_post.find("data-href-url=") + 15
                    index_2 = current_post.find("data-outbound") - 2
                    embed_archive = ""

                    rand_string = get_random_string(5)
                    text_filename = "video_metadata_" + str(rand_string) + ".txt"
                    local_path = str(main_path)+ str(rand_string) + "/"
                    text_pathname = str(local_path) + str(text_filename)
                    if (os.path.isdir(local_path) == 0) == True:
                        os.mkdir(local_path)

                    with open(text_pathname, "w", encoding="utf-8") as text_file:
                        text_file.write("Source code:  " + str(current_post))
                        text_file.write("\n\n")
                        text_file.write("Source URL: " + str(full_link))
                        text_file.close()

                    yt_link = str(current_post[index_1:index_2])
                    prediction = " ~"
                    msg2 = gen_tb_msg(full_link, 0, main_title, "yes", embed_archive, prediction)
                    msg = str(msg2) + "\n" + "\n▶️ YouTube Link: " + "\n" + str(yt_link)
                    tb.send_message(chat_id, "------—————------")
                    tb.send_message(chat_id, msg, disable_web_page_preview  = False)
                    doc = open(text_pathname, 'rb')
                    tb.send_document(chat_id, doc)

                    msg3 = msg + "\n\n(#UFOTwitter #UAP #UFOs #UAP #UFOSightings #UFO)"
                    if (len(msg3) > 280) == False:
                        send_tweet(str(msg3), client)
                    else:
                        uploaded_link = str(yt_link)
                        twitter_msg = str(create_tweet_msg(uploaded_link, main_title, full_link, category, prediction))
                        send_tweet(twitter_msg, client)

                    main(main_title, current_title)

                # In case the new subissionn is an image, proccess it and post to Telegram channel and save image locally too.
                elif ((str(search_directory[1]) in current_post) or (str(search_directory[4]) in current_post)):
                    index_1 = current_post.find("href") + 6
                    index_2 = current_post.find("tabindex") - 3
                    partial_link = current_post[index_1:index_2]
                    post_link = "https://old.reddit.com/" + str(partial_link)
                    soup = lovely_soup(str(post_link))
                    raw_post_data = soup.find_all('p')

                    # Retrieves the exact URL for this image submission
                    try:
                        post_data = str(raw_post_data[29])
                    except (BaseException, Exception):
                        post_data = current_post

                    index_1 = post_data.find("data-href-url=") + 15
                    index_2 = post_data.find("data-outbound") - 2
                    post_url = str(post_data[index_1:index_2])

                    exact_url = post_url

                    # Saving raw post data from thhe subreddit submission of immage
                    rand_string = get_random_string(5)
                    text_filename = "photo_metadata_" + str(rand_string) + ".txt"
                    text_pathname = str(main_path) +  str(rand_string) + "/"
                    text_path = str(text_pathname) + str(text_filename)

                    if (os.path.isdir(text_pathname) == 0) == True:
                        os.mkdir(text_pathname)

                    # Saves post source code into a .txt file
                    with open(text_path, "w", encoding="utf-8") as text_file:
                        text_file.write("Post source: " + str(post_data))
                        text_file.write("\n\n")
                        text_file.write("Source URL: " + str(full_link))
                        text_file.close()

                    filename = str(exact_url.split('/')[-1])
                    image_pathway = str(text_pathname) + "/" + str(filename)


                    # Save image to local storage first and then send to Telegram channel.
                    response = get(exact_url)
                    if response.status_code == 200:
                        with open(image_pathway, 'wb') as f:
                            f.write(response.content)

                    prediction_proba, prediction = predict_one_image(str(image_pathway))

                    uploaded_link = upload_archive(str(image_pathway), False, "image", rand_string, str(full_link) , main_title)

                    photo = open(image_pathway, 'rb')
                    msg = gen_tb_msg(full_link, 0, main_title, "no", uploaded_link, prediction)
                    tb.send_message(chat_id, "------—————------")
                    tb.send_photo(chat_id, photo, caption = str(msg))
                    doc = open(text_path, 'rb')
                    tb.send_document(chat_id, doc)

                    full_link = full_link.replace("https://","www.")
                    twitter_msg = str(create_tweet_msg(uploaded_link, main_title, full_link, category, prediction))

                    print("Twitter msg: ", twitter_msg)
                    send_tweet(twitter_msg, client)
                    main(main_title, current_title)


                # In case it's a miscellaneous self-post consisting out of text only, and could be a classified as a sighting submission.
                elif str(category) in select:
                    rand_string = get_random_string(5)
                    post_path = str(main_path) + str(rand_string) + "/"

                    # Full image pathway linking.
                    png_path = str(main_path) + str(rand_string) + "/" + "ss.png"
                    ss_path_full = str(main_path) + str(rand_string) + "/" + "ss_full.jpg"
                    ss_path = str(main_path) + str(rand_string) + "/" + "ss.jpg"
                    if (os.path.isdir(post_path) == 0) == True:
                        os.mkdir(post_path)

                    text_filename = "screenshot_metadata_" + str(rand_string) + ".txt"
                    local_path = str(main_path)+ str(rand_string) + "/"
                    text_pathname = str(local_path) + str(text_filename)


                    with open(text_pathname, "w", encoding="utf-8") as text_file:
                        text_file.write("Post source:  " + str(current_post))
                        text_file.write("\n\n")
                        text_file.write("Source URL: " + str(full_link))
                        text_file.close()

                    # Makes chromium driver refresh page URL invisibly, without exhausting the GPU on a fixed window size and saved local screenshot of it.
                    options = webdriver.ChromeOptions()
                    options.add_argument('--headless') # Invisible browser
                    options.add_argument('--window-size=750x1500')
                    options.add_argument("--disable-gpu") # No need to exhaust GPU.

                    driver = webdriver.Chrome(chromium_path, options=options) # Chromium path linking
                    driver.get(str(full_link))

                    screenshot = driver.save_screenshot(png_path)

                    # Turning .png screenshot file to .jpg
                    ss = Image.open(png_path)
                    rgb_im = ss.convert('RGB')
                    rgb_im.save(ss_path_full)

                    img = cv2.imread(ss_path_full)

                    # Cropping the screenshot to reduce dynamic noise and highlight relevant listing.
                    cropped_image = img[350:1200, 0:450]
                    cropped_image1 = cv2.imwrite(ss_path, cropped_image)

                    # Sending photo of the submission post to Telegram channel.
                    uploaded_link = str(upload_archive(ss_path, False, "image", str(rand_string), str(full_link), main_title))
                    prediction = "~"
                    msg = gen_tb_msg(full_link, 0, main_title, "no", uploaded_link, prediction)
                    tb.send_message(chat_id, "------—————------")
                    tb.send_message(chat_id, msg, disable_web_page_preview = True)
                    photo = open(ss_path, 'rb')
                    tb.send_photo(chat_id, photo)
                    doc = open(text_pathname, 'rb')
                    tb.send_document(chat_id, doc)
                    full_link = full_link.replace("https://","www.")
                    twitter_msg = create_tweet_msg(uploaded_link, main_title, full_link, category, prediction)
                    send_tweet(twitter_msg, client)
                    driver.quit()
                    main(main_title, current_title)

                else:
                    print("No images or videos found")
            else:
                print("No new submission.")
                time.sleep(15)
                main(main_title, current_title)

            main(main_title, current_title)


#Run main() for as long as possible incase of a crash; wait then restart the whole program.
try:
    while(True):
        try:
            main(main_title, current_title)
        except Exception as e:
            logging.error(traceback.format_exc())
            print("Error 009: Waiting before restarting the program.")
            time.sleep(60*15)
            print("Restarting...")
            main(main_title, current_title)
except (BaseException, ConnectionError, Exception):
    print("Error x010: Complete crash of first loop.")
    time.sleep(600)
    main(main_title, current_title)
