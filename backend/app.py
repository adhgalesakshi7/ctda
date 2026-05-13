from flask import Flask, jsonify, send_file, request
from flask_cors import CORS
from werkzeug.exceptions import NotFound
# import pandas as pd
import matplotlib
matplotlib.use('Agg') # Set non-GUI backend
import matplotlib.pyplot as plt
    # matplotlib.use('Agg') sets the backend for Matplotlib to Agg, which is a non-GUI backend
    # that renders plots as image files (PNG, etc.) instead of displaying them in a window.
import mpld3
from preprocessing import preprocess
import stats
import charts
import nlp_charts
import plotly.io as pio


app = Flask(__name__)           # Flask constructor takes the name of current module (__name__) as argument.
cors = CORS(app,origins='*')    # set app to send/accepts requests in localhost as well

# Favicon route to prevent 404 errors
@app.route('/favicon.ico')
def favicon():
    return '', 204  # Return empty response with 204 No Content status

# The route() function of the Flask class is a decorator, 
# mapping the URLs to a specific function that will handle the logic for that URL.
@app.route('/')
def default():
    return "konichiwa bitch"

# NOTE : When we define df, user_list, and user at the top, they are module-level variables. 
# However, in the /upload and /set-user routes, we are assigning new values to them, but they are only modified within the local scope of those specific route functions.
# so we need to explicitly decalre them as global (which is yee ass and lot of code-refactoring) 
# We avoid having to declare globals in every route by encapsulating your shared data in a dedicated object.
# All your routes can access and update the same object without redeclaring the variables as global.

# Class to hold shared data
class AppData:
    def __init__(self):
        self.df = None
        self.user_list = None
        self.user = None
# Single instance of AppData that will be shared across routes
data_store = AppData()


@app.route("/upload", methods=["POST"])
def upload_file():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file part"}), 400

        file = request.files["file"]

        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400

        if file and file.filename.endswith(".txt"):
            data = file.read().decode("utf-8")      # Read file contents
            print(f"[DEBUG] Uploading file: {file.filename}")
            print(f"[DEBUG] File size: {len(data)} bytes")
            
            data_store.df, data_store.user_list = preprocess(data)  # Update our shared data after processing and converting into dataframe
            
            print(f"[DEBUG] Preprocessing complete. Users found: {len(data_store.user_list)}")
            print(f"[DEBUG] DataFrame shape: {data_store.df.shape}")
            
            return jsonify({"users": data_store.user_list})        # Return the list of users
        
        return jsonify({"error": "Invalid file type. Please upload a .txt file"}), 400
    except Exception as e:
        print(f"[ERROR] Upload failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500
    

@app.route('/set-user', methods=['POST'])  
def set_user():
    data = request.get_json()
    data_store.user = data.get("user")   # Update the user in shared data
    
    if data_store.user:
        return jsonify({"message": f"User '{data_store.user}' set successfully!"})
    return jsonify({"error": "User not provided"}), 400


# 1 : numerical stats - num of messages, links etc
@app.route('/top-stats')
def serve_top_stats():
    try:
        if data_store.df is not None and data_store.user is not None:
            if data_store.df.empty:
                return jsonify({"num_messages": 0, "num_words": 0, "num_media_messages": 0, "num_links": 0})
            return jsonify(stats.top_stats(data_store.df, data_store.user))
        return jsonify({"error": "No data available"}), 400
    except Exception as e:
        print(f"[ERROR] Top stats failed: {str(e)}")
        return jsonify({"num_messages": 0, "num_words": 0, "num_media_messages": 0, "num_links": 0})


# 2 : temporal stats - busiest day, week, month
@app.route('/temporal-stats')
def serve_temporal_stats():
    try:
        if data_store.df is not None and data_store.user is not None:
            if data_store.df.empty:
                return jsonify({"busiest_day": "N/A", "busiest_day_message_count": 0, "busiest_month": "N/A", "busiest_month_message_count": 0, "busiest_week": "N/A", "busiest_week_message_count": 0})
            return jsonify(stats.top_temporal_stats(data_store.df, data_store.user))
        return jsonify({"error": "No data available"}), 400
    except Exception as e:
        print(f"[ERROR] Temporal stats failed: {str(e)}")
        return jsonify({"busiest_day": "N/A", "busiest_day_message_count": 0, "busiest_month": "N/A", "busiest_month_message_count": 0, "busiest_week": "N/A", "busiest_week_message_count": 0})


# 3 : dataframe of users and their chat contribution in %
@app.route('/contributions')
def serve_contributions():
    if data_store.df is not None:
        user_contribution_df = stats.user_contribution(data_store.df)
        return user_contribution_df.to_json(orient='columns')
    return jsonify({"error": "No data available"}), 400


# 4 : bar graph of top 5 users with message counts
@app.route('/top-users')
def serve_buzy_users():
    try:
        if data_store.df is not None:
            fig = charts.top_users(data_store.df)
            return pio.to_json(fig)
        empty_fig = px.bar(title='Busiest Users', labels={'x': 'Message counts', 'y': 'User names'})
        return pio.to_json(empty_fig)
    except Exception as e:
        print(f"[ERROR] Top users failed: {str(e)}")
        import traceback
        traceback.print_exc()
        empty_fig = px.bar(title='Busiest Users', labels={'x': 'Message counts', 'y': 'User names'})
        return pio.to_json(empty_fig)


# 5 : horizontal bar graph of top 10 (or less) most common words with occurrence
@app.route('/top-words')
def serve_top_words():
    try:
        if data_store.df is not None and data_store.user is not None:
            fig = charts.top_words(data_store.df, data_store.user)
            return pio.to_json(fig)
        empty_fig = px.bar(title='Top Words', labels={'x': 'Message counts', 'y': 'Words'})
        return pio.to_json(empty_fig)
    except Exception as e:
        print(f"[ERROR] Top words failed: {str(e)}")
        import traceback
        traceback.print_exc()
        empty_fig = px.bar(title='Top Words', labels={'x': 'Message counts', 'y': 'Words'})
        return pio.to_json(empty_fig)


# 6 : dataframe of top 10 (or less) common emojis with occurrence
@app.route('/top-emojis')
def serve_top_emojis():
    try:
        if data_store.df is not None and data_store.user is not None:
            emoji_df = stats.top_emojis(data_store.df, data_store.user)
            if emoji_df.empty:
                return jsonify({})
            return emoji_df.to_json(orient='columns')
        return jsonify({})
    except Exception as e:
        print(f"[ERROR] Top emojis failed: {str(e)}")
        return jsonify({})


# 7 : timeline of chats from group creation, wrt no of messages
@app.route('/timeline')
def serve_timeline():
    try:
        if data_store.df is not None and data_store.user is not None:
            fig = charts.timeline(data_store.df, data_store.user)
            return pio.to_json(fig)
        empty_fig = px.line(title='Timeline', labels={'x': 'Date', 'y': 'Messages'})
        return pio.to_json(empty_fig)
    except Exception as e:
        print(f"[ERROR] Timeline failed: {str(e)}")
        import traceback
        traceback.print_exc()
        empty_fig = px.line(title='Timeline', labels={'x': 'Date', 'y': 'Messages'})
        return pio.to_json(empty_fig)


# 8 : busiest days wrt message counts (monday, tuesday, ...)
@app.route('/buzy-days/<type>')
def serve_buzy_days(type):
    try:
        if data_store.df is not None and data_store.user is not None:
            bar, pie = charts.busiest_days(data_store.df, data_store.user)
            if type == "pie":
                return pio.to_json(pie)
            elif type == "bar":
                return pio.to_json(bar)
            else:
                return "Invalid type. Expected 'bar' or 'pie'"
        empty_fig = px.bar(title='Busiest Days', labels={'x': 'Day', 'y': 'Messages'})
        return pio.to_json(empty_fig)
    except Exception as e:
        print(f"[ERROR] Busiest days failed: {str(e)}")
        import traceback
        traceback.print_exc()
        empty_fig = px.bar(title='Busiest Days', labels={'x': 'Day', 'y': 'Messages'})
        return pio.to_json(empty_fig)


# 9 : days and their word counts (amt of content shared) (monday, tuesday, ...)
@app.route('/daily-wordcount/<type>')
def serve_daily_wordcount(type):
    try:
        if data_store.df is not None and data_store.user is not None:
            bar, pie = charts.daily_wordcount(data_store.df, data_store.user)
            if type == "pie":
                return pio.to_json(pie)
            elif type == "bar":
                return pio.to_json(bar)
            else:
                return "Invalid type. Expected 'bar' or 'pie'"
        empty_fig = px.bar(title='Daily Word Count', labels={'x': 'Day', 'y': 'Words'})
        return pio.to_json(empty_fig)
    except Exception as e:
        print(f"[ERROR] Daily wordcount failed: {str(e)}")
        import traceback
        traceback.print_exc()
        empty_fig = px.bar(title='Daily Word Count', labels={'x': 'Day', 'y': 'Words'})
        return pio.to_json(empty_fig)


# 10 : busiest months wrt message counts (jan, feb, ...)
@app.route('/buzy-months/<type>')
def serve_buzy_months(type):
    try:
        if data_store.df is not None and data_store.user is not None:
            bar, pie = charts.busiest_months(data_store.df, data_store.user)
            if type == "pie":
                return pio.to_json(pie)
            elif type == "bar":
                return pio.to_json(bar)
            else:
                return "Invalid type. Expected 'bar' or 'pie'"
        empty_fig = px.bar(title='Busiest Months', labels={'x': 'Month', 'y': 'Messages'})
        return pio.to_json(empty_fig)
    except Exception as e:
        print(f"[ERROR] Busiest months failed: {str(e)}")
        import traceback
        traceback.print_exc()
        empty_fig = px.bar(title='Busiest Months', labels={'x': 'Month', 'y': 'Messages'})
        return pio.to_json(empty_fig)


# 11 : months and their word counts (amt of content shared) (jan, feb, ...)
@app.route('/monthly-wordcount/<type>')
def serve_monthly_wordcount(type):
    try:
        if data_store.df is not None and data_store.user is not None:
            bar, pie = charts.monthy_wordcount(data_store.df, data_store.user)
            if type == "pie":
                return pio.to_json(pie)
            elif type == "bar":
                return pio.to_json(bar)
            else:
                return "Invalid type. Expected 'bar' or 'pie'"
        empty_fig = px.bar(title='Monthly Word Count', labels={'x': 'Month', 'y': 'Words'})
        return pio.to_json(empty_fig)
    except Exception as e:
        print(f"[ERROR] Monthly wordcount failed: {str(e)}")
        import traceback
        traceback.print_exc()
        empty_fig = px.bar(title='Monthly Word Count', labels={'x': 'Month', 'y': 'Words'})
        return pio.to_json(empty_fig)


# 12 : busiest hours wrt message counts (0, 1, 2, ...)
@app.route('/buzy-hours')
def serve_busiest_hours():
    try:
        if data_store.df is not None and data_store.user is not None:
            fig = charts.busiest_hours(data_store.df, data_store.user)
            return pio.to_json(fig)
        empty_fig = px.bar(title='Busiest Hours', labels={'x': 'Hour', 'y': 'Messages'})
        return pio.to_json(empty_fig)
    except Exception as e:
        print(f"[ERROR] Busiest hours failed: {str(e)}")
        import traceback
        traceback.print_exc()
        empty_fig = px.bar(title='Busiest Hours', labels={'x': 'Hour', 'y': 'Messages'})
        return pio.to_json(empty_fig)


# 13 : Overall Heatmap
@app.route('/heatmap', methods=['GET'])
def serve_activity_heatmap():
    try:
        if data_store.df is not None and data_store.user is not None:
            heatmap_data = charts.activity_heatmap(data_store.df, data_store.user)
            if not heatmap_data.get("x") or not heatmap_data.get("y"):
                return jsonify({})
            return jsonify(heatmap_data)
        return jsonify({})
    except Exception as e:
        print(f"[ERROR] Heatmap failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({})


# 14 : Overall Wordcloud
@app.route('/wordcloud')
def serve_wordcloud():
    try:
        if data_store.df is not None and data_store.user is not None:
            wc_str = charts.wordcloud(data_store.df, data_store.user)
            if wc_str is None:
                return jsonify({"wordcloud_image": None})
            return jsonify({"wordcloud_image": wc_str})
        return jsonify({"wordcloud_image": None})
    except Exception as e:
        print(f"[ERROR] Wordcloud failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"wordcloud_image": None})


# NLP charts' routes

# 15 : timeline of chats from group creation, wrt specific sentiment and no of messages
@app.route('/sen-timeline/<int:k>')
def serve_sentiment_timeline(k):
    try:
        if data_store.df is not None and data_store.user is not None:
            fig = nlp_charts.daily_timeline(data_store.df, data_store.user, k)
            if fig is None:
                return jsonify({})
            return pio.to_json(fig)
        return jsonify({})
    except Exception as e:
        print(f"[ERROR] Sentiment timeline failed: {str(e)}")
        return jsonify({})


# 16 : dataframe of users and their chat contribution in % wrt specific sentiment
@app.route('/sen-contribution/<int:k>')
def serve_sentiment_precent_contribution(k):
    try:
        if data_store.df is not None:
            sen_df = stats.sen_percentage(data_store.df, k)
            if sen_df.empty:
                return jsonify({})
            return sen_df.to_json(orient='columns')
        return jsonify({})
    except Exception as e:
        print(f"[ERROR] Sentiment contribution failed: {str(e)}")
        return jsonify({})


# 17 : dataframe of most common words wrt specific sentiment
@app.route('/sen-common-words/<int:k>')
def serve_sentiment_common_words(k):
    try:
        if data_store.df is not None and data_store.user is not None:
            fig = nlp_charts.most_common_words(data_store.df, data_store.user, k)
            if fig is None:
                return jsonify({})
            return pio.to_json(fig)
        return jsonify({})
    except Exception as e:
        print(f"[ERROR] Sentiment common words failed: {str(e)}")
        return jsonify({})


# 18 : day-wise activity map wrt specific sentiment (mon, tue, wed, ...)
@app.route('/sen-activity-map/<int:k>')
def serve_sen_activity_map(k):
    try:
        if data_store.df is not None and data_store.user is not None:
            fig = nlp_charts.week_activity_map(data_store.df, data_store.user, k)
            if fig is None:
                return jsonify({})
            return pio.to_json(fig)
        return jsonify({})
    except Exception as e:
        print(f"[ERROR] Sentiment activity map failed: {str(e)}")
        return jsonify({})



# 19 : RESET ROUTE
@app.route('/reset', methods=['POST'])
def reset_data():
    data_store.df = None
    data_store.user_list = None
    data_store.user = None

    return jsonify({"message": "Data reset successfully!"})


# main driver function
if __name__ == '__main__':

    # run() method of Flask class runs the application 
    # on the local development server.
    app.run(debug=True, host='127.0.0.1', port=5000)

# f = open("WhatsApp Chat with BE IT A Official 2024-25.txt",'r',encoding='utf-8')    # reading file
# data = f.read() 
# df, user_list = preprocess(data)   # processing and converting into dataframe
# user = "Overall"

# # 1 : numerical stats - num of messages, links etc
# @app.route('/top-stats')
# def serve_top_stats():
#     return jsonify(stats.top_stats(df,user))

# # 2 : temporal stats - busiest day,week,month
# @app.route('/temporal-stats')
# def serve_temporal_stats():
#     return jsonify(stats.top_temporal_stats(df,user))

# # 3 : dataframe of users and their chat contribution in %
# @app.route('/contributions')
# def serve_contributions():
#     user_contribution_df = stats.user_contribution(df)
#     return user_contribution_df.to_json(orient='columns')

# # 4 : bar graph of top 5 users with message counts
# @app.route('/top-users')
# def serve_buzy_users():
#     return pio.to_json(charts.top_users(df)) 

# # 5 : horizontal bar graph of top 10(or less) most common words with occourance
# @app.route('/top-words')
# def serve_top_words():
#     return pio.to_json(charts.top_words(df,user)) 
#     # return covert_to_json(*charts.top_words(df,user))

# # 6 dataframe of top 10(or less) common emojis with occourance
# @app.route('/top-emojis')
# def serve_top_emojis():
#     emoji_df = stats.top_emojis(df,user)
#     return emoji_df.to_json(orient='columns')

# # 7 : timeline of chats from group creation, wrt no of messages
# @app.route('/timeline')
# def serve_timeline():
#     return pio.to_json(charts.timeline(df,user)) 

# # 8 : busiest days wrt message counts (monday, tuesday, ...)
# @app.route('/buzy-days/<type>')
# def serve_buzy_days(type):
#     bar,pie = charts.busiest_days(df,user)
#     if(type == "pie"):
#         return pio.to_json(pie)
#     elif(type == "bar"):
#         return pio.to_json(bar)
#     else:
#         return "Invalid type. Expected 'bar' or 'pie'"

# # 9 : days and their word counts (amt of content shared) (monday, tuesday, ...)
# @app.route('/daily-wordcount/<type>')
# def serve_daily_wordcount(type):
#     bar,pie = charts.daily_wordcount(df,user)
#     if(type == "pie"):
#         return pio.to_json(pie)
#     elif(type == "bar"):
#         return pio.to_json(bar)
#     else:
#         return "Invalid type. Expected 'bar' or 'pie'"

# # 10 : busiest months wrt message counts (jan, feb, ...)
# @app.route('/buzy-months/<type>')
# def serve_buzy_months(type):
#     bar,pie = charts.busiest_months(df,user)
#     if(type == "pie"):
#         return pio.to_json(pie)
#     elif(type == "bar"):
#         return pio.to_json(bar)
#     else:
#         return "Invalid type. Expected 'bar' or 'pie'"
    
# # 11 : months and their word counts (amt of content shared) (jan, feb, ...)
# @app.route('/monthly-wordcount/<type>')
# def serve_monthly_wordcount(type):
#     bar,pie = charts.monthy_wordcount(df,user)
#     if(type == "pie"):
#         return pio.to_json(pie)
#     elif(type == "bar"):
#         return pio.to_json(bar)
#     else:
#         return "Invalid type. Expected 'bar' or 'pie'"
    
# # 12 : busiest hours wrt message counts (0, 1, 2, ...)
# @app.route('/buzy-hours')
# def serve_busiest_hours():
#     return pio.to_json(charts.busiest_hours(df,user))

# # 13 : Overall Heatmap
# @app.route('/heatmap', methods=['GET'])
# def serve_activity_heatmap():
#     return jsonify(charts.activity_heatmap(df,user))

# # 14 : Overall Wordcloud
# @app.route('/wordcloud')
# def serve_wordcloud():
#     wc_str = charts.wordcloud(df,user)
#     return jsonify({"wordcloud_image": wc_str})


# # NLP charts' routes

# # 15 : timeline of chats from group creation, wrt specific sentiment and no of messages
# @app.route('/sen-timeline/<int:k>')
# def serve_sentiment_timeline(k):
#     return pio.to_json(nlp_charts.daily_timeline(df,user,k))

# # 16 : dataframe of users and their chat contribution in % wrt specific sentiment
# @app.route('/sen-contribution/<int:k>')
# def serve_sentiment_precent_contribution(k):
#     sen_df = stats.sen_percentage(df,k)
#     return sen_df.to_json(orient='columns')

# # 17 : dataframe of most common words wrt to specific sentiment
# @app.route('/sen-common-words/<int:k>')
# def serve_sentiment_common_words(k):
#     return pio.to_json(nlp_charts.most_common_words(df,user,k))    

# # 18 : day wise activity map wrt specific sentiment (mon, tue, wed, ...)
# @app.route('/sen-activity-map/<int:k>')
# def serve_sen_activity_map(k):
#     return pio.to_json(nlp_charts.week_activity_map(df,user,k))