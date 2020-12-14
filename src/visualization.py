import altair as alt
import pandas as pd
import streamlit as st
import aws
import driver
import requests
import json
import os
from textblob import TextBlob
import datetime
import time

credentials_path = "credentials.json"

auth_dict = {
    "CONSUMER_KEY": "nplQuaMHPcMxDhDZRBTpdQw9G",
    "CONSUMER_SECRET": "n8LSd7vokOjkNm8qF0cgbT0evtu8Z06WqH3HOvwlfLxwOCGTcO",
    "ACCESS_TOKEN": "1331097642517073921-BqeOQf7NdDeNVnfgK3ISQxURoVDcyj",
    "ACCESS_TOKEN_SECRET": "dsjPO62JmE15fXcJdtv9uOwn2AV5hzTueKOtKYotchD0n",
    "ENVIRONMENT": "TweetMiner"
}


def get_individual_stock_data(ticker, start="", end="", interval="1d", period="ytd"):
    """get individual stock data"""
    ip_address = get_current_ip()
    if ip_address == None:
        st.warning("IP not valid! Please Create an AWS instance or add valid IP")
        return

    response = requests.get(
        f"http://{ip_address}/stocks/stock?ticker={ticker}&start={start}&end={end}&interval={interval}&period={period}"
    )
    data_dict = response.json()
    # print(data_dict)
    return data_dict


# Streamlit command: pipenv run streamlit run <path_to_file>.py

def preprocess_stock_data(stock_dict):
    stock_df = pd.DataFrame(stock_dict)
    # rename index to date
    stock_df.index.rename("Date", inplace=True)
    stock_df.reset_index(inplace=True)
    stock_df = stock_df.rename(columns={"index": "Date"})
    # convert string time to datetime object
    stock_df["Date"] = pd.to_datetime(
        stock_df["Date"], format="%Y-%m-%dT%H:%M:%S")
    return stock_df


def barplot(df, y, x, title=""):
    """barplot with input of a data frame"""
    bar_plot = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            alt.Y(y),
            alt.X(x),
            opacity=alt.value(0.7),
            color=alt.value("blue"),
        )
        .properties(title=title, width=700, height=300)
    ).interactive()
    return bar_plot


def lineplot(df, y, x):
    """lineplot with input of a data frame"""
    lineplot = (
        alt.Chart(df)
        .mark_line()
        .encode(
            alt.Y(y),
            alt.X(x),
            opacity=alt.value(0.7),
            color=alt.value("blue"),
        )
        .properties(width=700, height=300)
    ).interactive()
    return lineplot


def combined_area_plot(df, y, x):
    brush = alt.selection(type="interval", encodings=["x"])
    base = (
        alt.Chart(df)
        .mark_area()
        .encode(
            x=x,
            y=y,
            opacity=alt.value(0.7),
            color=alt.value("blue"),
        )
        .properties(width=700, height=300)
    ).interactive()
    upper = base.encode(alt.X(x, scale=alt.Scale(domain=brush)))
    lower = base.properties(height=100).add_selection(brush)
    combined = alt.vconcat(upper, lower)
    return combined


def combined_bar_line_plot(df, y, x):
    brush = alt.selection(type="interval", encodings=["x"])
    base = barplot(df, y, x)
    upper = base.encode(alt.X(x, scale=alt.Scale(domain=brush)))
    lower = base.mark_line().properties(height=120).add_selection(brush)
    combined = alt.vconcat(upper, lower)
    return combined


def append_credentials(new_dict):
    """Uses the path to the credentials to add or update dictionary keys"""
    with open(credentials_path, "r") as file:
        old_dict = json.load(file)
    old_dict.update(new_dict)
    with open(credentials_path, "w") as file:
        json.dump(old_dict, file, indent=4)


def get_twitter_credentials():
    """Get and store twitter credentials"""
    st.write("## Please enter your Twitter developer application credentials:")

    consumer_key = st.text_input("Please enter your consumer key",
                                 value=auth_dict["CONSUMER_KEY"])
    consumer_secret = st.text_input("Please enter your consumer secret key",
                                    value=auth_dict["CONSUMER_SECRET"])
    access_token = st.text_input("Please enter your access token",
                                 value=auth_dict["ACCESS_TOKEN"])
    secret_access_token = st.text_input(
        "Please enter your secret access token",
        value=auth_dict["ACCESS_TOKEN_SECRET"])
    environment = st.text_input("Please enter your environment name",
                                value=auth_dict["ENVIRONMENT"])

    if st.button("submit", key="Credentials"):
        twitter_credentials = {"CONSUMER_KEY": consumer_key,
                               "CONSUMER_SECRET": consumer_secret,
                               "ACCESS_TOKEN": access_token,
                               "ACCESS_TOKEN_SECRET": secret_access_token,
                               "ENVIRONMENT": environment}
        st.success("Twitter Credentials Updated!")
        append_credentials({"TWITTER": twitter_credentials})


def get_aws_credentials():
    """Get and store AWS user credentials and create an
    EC2 instance"""
    st.write("## Please enter your AWS credentials:")
    access_key = st.text_input("Please enter your access key")
    secret_key = st.text_input("Please enter your secret key")
    session_token = st.text_input("Please enter your session token")

    if st.button("submit", key="Credentials"):
        aws_credentials = {"access_key": access_key,
                           "secret_key": secret_key, "session_token": session_token}
        new_ip = aws.begin_creation(access_key, secret_key, session_token)
        st.success(f"Instance created. Instance IP {new_ip}")
        append_credentials({"AWS": aws_credentials})
        append_credentials({"ip_address": new_ip})

        upload_and_execute(new_ip)

    st.write("## OR add an accessible IP address:")
    input_ip_address = st.text_input("Please enter your instance's IP address")
    if st.button("submit", key="IP") and (not len(input_ip_address) == 0):
        append_credentials({"ip_address": input_ip_address})
        st.success("New IP Added!")
        # upload_and_execute(input_ip_address)


def upload_and_execute(ip_address):
    """Connect to the AWS instance, upload files, and run the scripts"""
    # NOTE: this assumes that the file is being run from repo root
    stdout, stderr = driver.upload(
        "ec2-auto", ip_address, upload_dir="./code/upload")
    st.warning(stdout)
    st.warning(stderr)
    driver.ssh_execute("ec2-auto", ip_address)


def get_current_ip():
    """Open the credentials file and return IP address"""
    with open(credentials_path, "r") as file:
        credentials_dict = json.load(file)
        if "ip_address" in credentials_dict.keys():
            return credentials_dict["ip_address"]
        else:
            return None


def get_twitter_dict():
    """Open the credentials file and return Twitter dictionary"""
    with open(credentials_path, "r") as file:
        credentials_dict = json.load(file)
        if "TWITTER" in credentials_dict.keys():
            return credentials_dict["TWITTER"]
        else:
            return None


def main():
    st.title("Stock Market and Twitter Sentiment Analysis")
    # Retrieve credentials from local Json
    # create empty json file if file does not exist
    if os.path.exists(credentials_path):
        with open(credentials_path, "r") as file:
            credentials_dict = json.load(file)
    else:
        credentials_dict = {}
        json.dump(credentials_dict, open(credentials_path, "w"))

    # ============= Sidebar handling================
    selection = st.sidebar.selectbox(
        "Please select an operation",
        options=["AWS Authentication", "Twitter Authentication"],
    )
    # Add a placeholder for textboxes and buttons
    placeholder = st.sidebar.empty()
    if selection == "AWS Authentication":
        with placeholder.beta_container():
            get_aws_credentials()

    if selection == "Twitter Authentication":
        with placeholder.beta_container():
            get_twitter_credentials()
    # ==============================================

    # ============== Stock information input ===========
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    stock_ticker = st.text_input("Please enter a stock ticker")
    start_date = st.date_input(
        "Enter Start Date", value=yesterday, max_value=yesterday)
    end_date = st.date_input(
        "Enter End Date", min_value=start_date + datetime.timedelta(days=1), max_value=today)
    if (today - start_date).days < 60:
        interval = st.selectbox(
            'Select a data interval', ("1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"))
    else:
        interval = st.selectbox(
            'Select a data interval', ("1d", "5d", "1wk", "1mo", "3mo"))

    if st.button("get info") and not(stock_ticker == ""):
        ticker_info = get_company_info(stock_ticker)

        stock_df = preprocess_stock_data(
            (get_individual_stock_data(stock_ticker, start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'), interval=interval)))

        col1, col2 = st.beta_columns(2)
        company_logo_url = ticker_info["logo_url"]
        company_name = ticker_info["shortName"]
        company_website = ticker_info["website"]
        with col1:
            st.write(f"### About [{company_name}]({company_website})")
        with col2:
            st.markdown(f"![Company Logo]({company_logo_url})")

        st.write(ticker_info["longBusinessSummary"])
        st.write("### Stock Charts:")
        st.write(stock_df)
        # st.altair_chart(barplot(stock_df, "Close", "Date"))
        st.altair_chart(lineplot(stock_df, "Close", "Date"))
        st.altair_chart(combined_area_plot(stock_df, "Close", "Date"))
        # st.altair_chart(combined_bar_line_plot(stock_df, "Close", "Date"))

        st.write("### Twitter Sentiment Charts:")
        # get weekely data if range is less than 7 days
        if (today - start_date).days <= 7:
            sentiment_df = get_weekly_tweet_sentiment(stock_ticker)
        else:
            st.warning("Searching twitter data from over a week ago requires Twitter Premium credentials and could result in an error if maximum monthly requests are reached")
            sentiment_df = get_range_sentiment(
                stock_ticker, start_date, end_date)

        st.altair_chart(lineplot(sentiment_df, "Sentiment", "Date"))
        st.write(sentiment_df)


def get_company_info(ticker):
    """get individual stock general information"""
    ip_address = get_current_ip()
    if ip_address == None:
        st.warning("IP not valid! Please Create an AWS instance or add valid IP")
        return

    response = requests.get(
        f"http://{ip_address}/stocks/info?ticker={ticker}"
    )
    data_dict = response.json()
    return data_dict


def get_range_sentiment(ticker, start_date, end_date):
    """Get weekly tweets from API and compute sentiment"""
    ip_address = get_current_ip()
    if ip_address == None:
        st.warning("IP not valid! Please Create an AWS instance or add valid IP")
        return
    auth_dict = get_twitter_dict()
    if auth_dict == None:
        st.warning("Twitter credentials not found! Please add your credentials")
        return
    num_per_day = 100

    tweets = {}
    for day_since_start in range((end_date - start_date).days):
        start_string = (start_date +
                        datetime.timedelta(days=day_since_start)).strftime("%Y%m%d%H%M")
        end_string = (start_date +
                      datetime.timedelta(days=day_since_start + 1)).strftime("%Y%m%d%H%M")
        request_string = f"http://{ip_address}/tweets?keyword={ticker}&start={start_string}&end={end_string}&num={num_per_day}"
        response = requests.post(
            request_string,
            data=json.dumps(auth_dict),
        )
        response_dict = response.json()
        tweets.update(response_dict)
        time.sleep(5)

    st.write(tweets)
    polarity_dict = {}
    # get average sentiment score of the date
    for k, v in tweets.items():
        score = 0
        for text in v:
            score += compute_sentiment_score(text)
        polarity_dict[k] = score / len(v)
    senti_dict = {"Date": polarity_dict.keys(
    ), "Sentiment": polarity_dict.values()}
    sentiment_df = pd.DataFrame.from_dict(senti_dict)

    # st.write(polarity_dict)

    return sentiment_df


def compute_sentiment_score(text: str):
    """return the polarity score of a sentence"""
    polarity = TextBlob(text).sentiment.polarity
    return polarity


def get_weekly_tweet_sentiment(stock_symbol: str):
    """Get weekly tweets from API and compute sentiment"""
    ip_address = get_current_ip()
    if ip_address == None:
        st.warning("IP not valid! Please Create an AWS instance or add valid IP")
        return
    auth_dict = get_twitter_dict()
    if auth_dict == None:
        st.warning("Twitter credentials not found! Please add your credentials")
        return
    response = requests.post(
        f"http://{ip_address}/weeklyTweets?keyword={stock_symbol}",
        data=json.dumps(auth_dict),
    )
    tweets = response.json()
    polarity_dict = {}
    # get average sentiment score of the date
    for k, v in tweets.items():
        score = 0
        for text in v:
            score += compute_sentiment_score(text)
        polarity_dict[k] = score / len(v)
    senti_dict = {"Date": polarity_dict.keys(
    ), "Sentiment": polarity_dict.values()}
    sentiment_df = pd.DataFrame.from_dict(senti_dict)

    return sentiment_df


if __name__ == "__main__":
    main()
