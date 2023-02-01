# Make sure you pip install snscrape pandas numpy re
import snscrape.modules.twitter as sntwitter
import pandas as pd
# import numpy as np
# import os
# import re

# Enter usersnames of the users whose tweets you need in the list
users = ['Starkiller_1991']
# Enter the number of tweets per user you'd like. Note: In case user has less than limit, all the tweets get downloaded.
limit = 10000000
for user in users:
    until = "2023-01-30"   # Enter the date until you want the tweet for
    since = "2000-01-01"   # Enter the date from the tweets start getting queried
    query = f"(from:{user}) until:{until} since:{since}"
    tweets = []

    for tweet in sntwitter.TwitterSearchScraper(query).get_items():
        # print(vars(tweet)) #gets all the attributes retrieved.
        if len(tweets) == limit:
            break
        else:
            contents = [tweet.user.displayname, tweet.user.username, tweet.url, tweet.date, tweet.content, tweet.retweetCount, tweet.likeCount]   # Instruction: Add more attributes here
            tweets.append(contents)

    df = pd.DataFrame(tweets, columns=["Username", "User handle", "Tweet", "Date of posting", "Text", "Retweet count", "Like count"])   # Instruction: add a new name for column added
    df.to_csv(user + 'tweets.csv')
