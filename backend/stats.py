from urlextract import URLExtract
import pandas as pd
from collections import Counter
import emoji

extract = URLExtract()

def top_stats(df,user):
    if user != 'Overall':
        df = df[df['user'] == user]

    if df.empty:
        return {"num_messages": 0, "num_words": 0, "num_media_messages": 0, "num_links": 0}

    num_messages = df.shape[0]

    # fetch the total number of words
    word_list = []
    for message in df['message']:
        word_list.extend(message.split())
    num_words = len(word_list)

    # fetch number of media messages
    num_media_messages = df[df['message'] == '<Media omitted>\n'].shape[0]

    # fetch number of links shared
    link_list = []
    for message in df['message']:
        link_list.extend(extract.find_urls(message))
    num_links = len(link_list)

    stats = {"num_messages" : num_messages,
                 "num_words" : num_words,
                 "num_media_messages" : num_media_messages,
                 "num_links" : num_links}

    return stats


def top_temporal_stats(df,user):
    if user != 'Overall':
        df = df[df['user'] == user]

    if df.empty:
        return {"busiest_day": "N/A", "busiest_day_message_count": 0, "busiest_month": "N/A", "busiest_month_message_count": 0, "busiest_week": "N/A", "busiest_week_message_count": 0}

    daily_counts = df['only_date'].value_counts()
    if daily_counts.empty:
        busiest_day = "N/A"
        busiest_day_msgs = 0
    else:
        busiest_day = daily_counts.idxmax().strftime('%d/%m/%Y')    #idxmax() returns the index (label) of the maximum value.
        busiest_day_msgs = int(daily_counts.max())

    df['month_year'] = df['date'].dt.to_period('M')             # Group messages by Month and Year, Example: 2024-03
    monthly_counts = df['month_year'].value_counts()
    if monthly_counts.empty:
        busiest_month = "N/A"
        busiest_month_msgs = 0
    else:
        busiest_month = monthly_counts.idxmax().strftime('%m/%y')
        busiest_month_msgs = int(monthly_counts.max())  

    # Get the start of each ISO week (Monday at 00:00:00) If you group messages using ISO weeks, your data aligns with how business and global reports define weeks.
    # .normalize() sets the time component to 00:00:00. For any Monday, whether a message arrived at 10:49 or 15:17, they’ll share the same date “YYYY-MM-DD 00:00:00.”
    df['week_start'] = (df['date'] - pd.to_timedelta(df['date'].dt.weekday, unit='D')).dt.normalize()
    weekly_counts = df.groupby('week_start').size()     # Count messages per 'week_start'
    if weekly_counts.empty:
        week_range = "N/A"
        busiest_week_msgs = 0
    else:
        busiest_week_start = weekly_counts.idxmax()
        busiest_week_msgs = int(weekly_counts.max()) 
        busiest_week_end = busiest_week_start + pd.Timedelta(days=6)
        week_range = f"{busiest_week_start.strftime('%d/%m/%Y')} - {busiest_week_end.strftime('%d/%m/%Y')}" # Format output

    stats = {
        "busiest_day" : busiest_day,
        "busiest_day_message_count" : busiest_day_msgs,
        "busiest_month" : busiest_month,
        "busiest_month_message_count" : busiest_month_msgs,
        "busiest_week" : week_range,
        "busiest_week_message_count" : busiest_week_msgs
    }

    return stats

def user_contribution(df):
    if df.empty:
        return pd.DataFrame(columns=['name', 'percent'])
    
    contribution_percent_df = round((df['user'].value_counts() / df.shape[0]) * 100, 2).reset_index().rename(
    columns={'index': 'name', 'user': 'percent'})

    return contribution_percent_df

def top_emojis(df,user):

    if user != 'Overall':
        df = df[df['user'] == user]

    if df.empty:
        return pd.DataFrame(columns=[0, 1])

    emojis = []
    for message in df['message']:
        emojis.extend([c for c in message if c in emoji.EMOJI_DATA])

    if not emojis:
        return pd.DataFrame(columns=[0, 1])

    emoji_df = pd.DataFrame(Counter(emojis).most_common(10))

    # emoji_df_fig,ax = plt.subplots()
    # ax.barh(emoji_df[0],emoji_df[1])

    return emoji_df

def sen_percentage(df,k):
    sentiment_df = df[df['value']==k]
    if sentiment_df.empty:
        return pd.DataFrame(columns=['name', 'percent'])
    
    result_df = round((sentiment_df['user'].value_counts() / sentiment_df.shape[0]) * 100, 2).reset_index().rename(
        columns={'index': 'name', 'user': 'percent'})
    return result_df.head(10)
