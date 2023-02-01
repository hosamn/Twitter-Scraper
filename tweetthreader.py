import os
import re
import time
from collections import namedtuple
import codecs
import tweepy
import json
from datetime import datetime
from requests.exceptions import Timeout, ConnectionError
from requests.packages.urllib3.exceptions import ReadTimeoutError, ProtocolError

#Twitter API credentials
consumer_key = ""
consumer_secret = ""
access_key = ""
access_secret = ""


#authorize twitter, initialize tweepy
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_key, access_secret)
api = tweepy.API(auth, wait_on_rate_limit=True)



Tweet = namedtuple('Tweet', ['user', 'tweet_id', 'text', 'created_at', 'media', 'reply_to_id', 'reply_to_screen_name'])
alltweets = []

errorCodesList = [
'130',
'131',
'500',
'502',
'503',
'504'
]

screenNamesList = [
'TIinExile'
]

start = datetime.now()

#create folder
fldName = os.getcwd() + "\\data\\"
if not os.path.exists(os.path.dirname(fldName)):
    os.makedirs(os.path.dirname(fldName))

def wait(minutes):
    seconds = minutes * 60
    time.sleep(seconds)

def checkError(response, screen_name):
    if response is None:
        print("\n*Parsing Error*\nRetrying ...\n")
        wait(3)
        getAllTweets(screen_name)
    else:
        msg = response.text
        regex = re.match("^.*?\"code\":([\d]+),\"message\":\"(.*?)\.\".+", msg)
        if regex:
            code = regex.group(1)
            message = regex.group(2)
            if code in errorCodesList:
                print("\nRetrying ...\n")
                wait(3)
                getAllTweets(screen_name)               
            else:
                print("\n*Error*\nUser: " + screen_name + " Message: " + message + ". Code: " + code + ".\n")
                pass
        else:
            if "Not authorized" in msg:
                print("\n*Error*\nUser: " + screen_name + " Message: This account's tweets are protected.\n")
                pass
            else:
                print(msg)
                pass


def get_filename(screen_name) :
    return os.getcwd() + "\\data\\{}.txt".format(screen_name)
def get_final_json(screen_name) :
    return os.getcwd() + "\\data\\threads\\{}.txt".format(screen_name)
def get_all_tweets(screen_name):
    try:
        #Twitter only allows access to a users most recent 3240 tweets with this method
        del alltweets[:]

        #make initial request for the most recent tweets (200 is the maximum allowed count)
        new_tweets = api.user_timeline(screen_name = screen_name,count=200, tweet_mode="extended")
        
        #save the most recent tweets
        alltweets.extend(new_tweets)
        
        #save the id of the oldest tweet minus one
        oldest = alltweets[-1].id - 1
        
        #keep retrieving tweets until there are no more tweets left
        while len(new_tweets) > 0:

            print("User: " + screen_name)
            print("Getting tweets before %s" % (oldest))
            
            #all subsequent requests use the max_id param to prevent duplicates
            new_tweets = api.user_timeline(screen_name = screen_name,count=200,max_id=oldest, tweet_mode="extended")
            
            #save the most recent tweets
            alltweets.extend(new_tweets)
            
            #update the id of the oldest tweet minus one
            oldest = alltweets[-1].id - 1
            
            print("...%s tweets downloaded so far" % (len(alltweets)) + "\n")

        filename = get_filename(screen_name)
        print("writing to " + filename)
        with codecs.open(filename, "a", "utf-8", "ignore") as outFile:
            for tweet in alltweets:

                    #remove unwanted line breaks from the tweet and replace them with spaces
                tweetid =tweet.id_str
                
                if hasattr(tweet, "retweeted_status"):  # Check if Retweet
                    try:
                        text = tweet.retweeted_status.extended_tweet["full_text"]
                    except AttributeError:
                        try:
                            text = tweet.retweeted_status.full_text
                        except AttributeError:
                            # text = tweet.retweeted_status.text
                            text = api.get_status(tweetid, tweet_mode="extended").retweeted_status.full_text
                else:
                    try:
                        text = tweet.extended_tweet["full_text"]
                    except AttributeError:
                        try:
                            text = tweet.full_text
                        except AttributeError:
                            text = api.get_status(tweetid, tweet_mode="extended").full_text


                text = text.replace("\n", "").replace("\r", "").strip()
                created_at = tweet.created_at
                try :
                    media_url = tweet.entities['media'][0]['media_url']
                except (NameError, KeyError):
                    media_url = '#'
                
                try :
                    reply_to_id = tweet.in_reply_to_status_id_str
                except AttributeError:
                    reply_to_id = '#'
                else :
                    if reply_to_id is None : reply_to_id = '#'
                
                try :
                    reply_to_screen_name = tweet.in_reply_to_screen_name
                except AttributeError:
                    reply_to_screen_name = '#'
                else :
                    if reply_to_screen_name is None : reply_to_screen_name = '#'
                

                
                #write to txt file
                outFile.write("user:{}|||tweet_id:{}|||text:{}|||created_at:{}|||media:{}|||reply_to_id:{}|||reply_to_screen_name:{}\n".format(screen_name, tweetid, text, created_at, media_url, reply_to_id, reply_to_screen_name)) #debugging

        print("Data writing completed")

    except (Timeout, ConnectionError, ReadTimeoutError, ProtocolError) as exc:
        print("\n*Timeout Error*\nRetrying ...\n")
        wait(3)
        get_all_tweets(screen_name)

    except tweepy.TweepError as e:
        checkError(e.response, screen_name)

    except IndexError:
        print("\nUser \"" + screen_name + "\" didn't have enough tweets to retrieve ...\n")
        pass

def extract_fields(line) :
    user, tweet_id, text, created_at, media, reply_to_id, reply_to_screen_name = [ x for x in line.strip().split("|||")]
    user = user.split("user:")[1]
    tweet_id = tweet_id.split("tweet_id:")[1]
    text = text.split("text:")[1]
    created_at = created_at.split("created_at:")[1]
    media = media.split("media:")[1]
    reply_to_id = reply_to_id.split("reply_to_id:")[1]
    reply_to_screen_name = reply_to_screen_name.split("reply_to_screen_name:")[1]

    return Tweet(user, tweet_id, text, created_at, media, reply_to_id, reply_to_screen_name)


def write_to_file(screen_name, threads) :
    filename = get_final_json(screen_name)
    print("writing JSON to " + filename)
    with codecs.open(filename, "w", "utf-8", "ignore") as outFile:
        json.dump(threads, outFile)

def get_tweet_threads(screen_name) :
    with codecs.open(get_filename(screen_name), "r", "utf-8", "ignore") as f :
        file_contents = f.readlines()
    
    file_dict = {}
    file_indx = {}
    indx = 0
    for line in file_contents :
        tweet = extract_fields(line)
        file_dict[tweet.tweet_id] = line
        file_indx[line] = indx
        indx += 1
    
    
    threads = {}
    for i,line in enumerate(file_contents) :
        rev_thread_list = []
        if line is None : continue
        tweet = extract_fields(line)        
        if tweet.reply_to_id is '#' :
            continue
        if tweet.reply_to_screen_name is '#' or tweet.reply_to_screen_name != screen_name :
            continue
        rev_thread_list.append(tweet)
        file_contents[i] = None
        flag = True
        new_tweet = tweet
        while flag :
            try :
                new_line = file_dict[new_tweet.reply_to_id]
            except KeyError:
                #maybe deleted tweet ?
                print("tweet not found id : {}", new_tweet.reply_to_id)
                flag = False
                continue

            new_tweet = extract_fields(new_line)
            rev_thread_list.append(new_tweet)
            file_contents[file_indx[new_line]] = None
            if new_tweet.reply_to_id is '#' :
                flag = False
                continue
            if new_tweet.reply_to_screen_name is '#' or new_tweet.reply_to_screen_name != screen_name :
                flag = False
                continue

        if len(rev_thread_list) < 2 :
            print("only one tweet in thread ? how tweetid:{}".format(rev_thread_list[0].tweet_id))
            continue
        thread_list = rev_thread_list[::-1]
        first_tweet_id = thread_list[0].tweet_id
        thread_list = [x._asdict() for x in thread_list]
        threads[first_tweet_id] = thread_list
    print( "total threads {}".format(len(threads)))
    write_to_file(screen_name, threads)



if __name__ == '__main__':   
    #pass in the username of the account you want to download
    for i, user in enumerate(screenNamesList):
        get_all_tweets(screenNamesList[i])
        get_tweet_threads(user)

end = datetime.now()
print("Elapsed time: {0}".format(end-start))
# input("Press [Enter] to exit ...")
