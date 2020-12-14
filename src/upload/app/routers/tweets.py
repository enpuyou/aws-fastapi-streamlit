"Provide an API to authenticate user and retreive twitter data using Tweepy"

import tweepy
import json
from datetime import datetime
from fastapi import APIRouter
from textblob import TextBlob
from collections import defaultdict


router = APIRouter()

# Required keys in credentials
# CONSUMER_KEY
# CONSUMER_SECRET
# ACCESS_TOKEN
# ACCESS_TOKEN_SECRET
# ENVIRONMENT


def tweepy_auth(credentials: dict):
    """authorize through a dict of tokens and return tweepy api object"""
    # Use credentials to create a tweepy api
    auth = tweepy.OAuthHandler(
        credentials["CONSUMER_KEY"], credentials["CONSUMER_SECRET"]
    )
    auth.set_access_token(
        credentials["ACCESS_TOKEN"], credentials["ACCESS_TOKEN_SECRET"]
    )
    api = tweepy.API(auth)
    return api


def tweets_to_date_dict(tweets):
    """Return a dict of dates and list[tweet]"""
    dates_dict = defaultdict(list)
    for tweet in tweets:
        date = tweet.created_at.date().strftime("%Y-%m-%d")
        text = tweet.text
        dates_dict[date].append(text)
    return dates_dict


@router.post("/tweets", tags=["tweets"])
def get_tweets(credentials: dict, keyword: str, start: str, end: str, num: int):
    """Use tweepy to get a specified number of tweets within a date range"""
    # Date format must be: YYYYMMDDHHMM, for example: 202011190000
    # Use credentials to create a tweepy api
    api = tweepy_auth(credentials)

    tweets = tweepy.Cursor(
        api.search_full_archive,
        environment_name=credentials["ENVIRONMENT"],
        query=keyword,
        fromDate=start,
        toDate=end,
    ).items(num)
    data = tweets_to_date_dict(tweets)
    return data


@router.post("/weeklyTweets", tags=["tweets"])
def get_week_tweets(credentials: dict, keyword: str):
    """Use tweepy to get the most popular tweets
    from last week"""
    # Use credentials to create a tweepy api
    api = tweepy_auth(credentials)

    # Get the tweets and store them in the needed format
    # Use today's date as string
    today_date = datetime.today().strftime("%Y-%m-%d")
    tweets = tweepy.Cursor(
        api.search,
        lang="en",
        result_type="popular",
        q=keyword,
        until=today_date,
    ).items()
    data = tweets_to_date_dict(tweets)
    return data


def compute_sentiment_score(text: str):
    """return the polarity score of a sentence"""
    polarity = TextBlob(text).sentiment.polarity
    return polarity
