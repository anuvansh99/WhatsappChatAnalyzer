from flask import Flask, request, jsonify, render_template
import preprocessor, helper
import matplotlib
matplotlib.use('Agg')  # Set backend before importing pyplot
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
from summarizer import summarize_last_300_messages, generate_300_message_taglines

app = Flask(__name__)

def fig_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img_base64

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    try:
        data = file.read().decode('utf-8')
        df = preprocessor.preprocess(data)

        # User list
        user_list = df['user'].unique().tolist()
        if 'group_notification' in user_list:
            user_list.remove('group_notification')
        user_list.sort()
        user_list.insert(0, 'Overall')

        selected_user = request.form.get('selected_user', 'Overall')

        # Stats
        num_messages, words, num_media_messages, num_links = helper.fetch_stats(selected_user, df)

        # Plots dictionary to store all images
        plots = {}

        # Monthly Timeline
        timeline = helper.monthly_timeline(selected_user, df)
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(timeline['time'], timeline['message'], color='green', marker='o')
        ax.set_title("Messages Over Time")
        plt.xticks(rotation=45)
        plots['monthly_timeline'] = fig_to_base64(fig)

        # Daily Timeline
        daily_timeline = helper.daily_timeline(selected_user, df)
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(daily_timeline['only_date'], daily_timeline['message'], color='blue', marker='o')
        ax.set_title("Messages Per Day")
        plt.xticks(rotation=45)
        plots['daily_timeline'] = fig_to_base64(fig)

        # Activity Maps
        busy_day = helper.week_activity_map(selected_user, df)
        fig, ax = plt.subplots()
        ax.bar(busy_day.index, busy_day.values, color='purple')
        ax.set_title("Most Active Days")
        plt.xticks(rotation=45)
        plots['busy_day'] = fig_to_base64(fig)

        busy_month = helper.month_activity_map(selected_user, df)
        fig, ax = plt.subplots()
        ax.bar(busy_month.index, busy_month.values, color='orange')
        ax.set_title("Most Active Months")
        plt.xticks(rotation=45)
        plots['busy_month'] = fig_to_base64(fig)

        # Heatmap
        user_heatmap = helper.activity_heatmap(selected_user, df)
        if user_heatmap is not None and not user_heatmap.empty:
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.heatmap(user_heatmap, annot=True, fmt=".0f", cmap="YlGnBu", ax=ax)
            ax.set_title("Activity Heatmap")
            plots['heatmap'] = fig_to_base64(fig)

        # Most Busy Users
        most_busy_users_img = None
        most_busy_users_df = None
        if selected_user == 'Overall':
            x, new_df = helper.most_busy_users(df)
            fig, ax = plt.subplots()
            ax.bar(x.index, x.values, color='red')
            ax.set_title("User Activity")
            plt.xticks(rotation=45)
            plots['most_busy_users'] = fig_to_base64(fig)
            most_busy_users_df = new_df.to_dict(orient='records')

        # WordCloud
        df_wc = helper.create_wordcloud(selected_user, df)
        fig, ax = plt.subplots()
        ax.imshow(df_wc, interpolation='bilinear')
        ax.axis('off')
        plots['wordcloud'] = fig_to_base64(fig)

        # Most Common Words (Bar Chart)
        most_common_df = helper.most_common_words(selected_user, df)
        fig, ax = plt.subplots()
        ax.barh(most_common_df[0], most_common_df[1], color='skyblue')
        ax.set_title("Top Words")
        plt.xticks(rotation=45)
        plots['common_words_bar'] = fig_to_base64(fig)

        # Emoji Analysis (Pie Chart)
        emoji_df = helper.emoji_helper(selected_user, df)
        fig, ax = plt.subplots()
        ax.pie(emoji_df[1].head(), 
               labels=emoji_df[0].head(), 
               autopct="%0.2f", 
               startangle=140, 
               colors=sns.color_palette("pastel"))
        ax.set_title("Top Emojis")
        plots['emoji_pie'] = fig_to_base64(fig)

        # Summary and taglines
        summary = summarize_last_300_messages(df)
        taglines = generate_300_message_taglines(df)

        return jsonify({
            'users': user_list,
            'stats': {
                'num_messages': num_messages,
                'words': words,
                'num_media_messages': num_media_messages,
                'num_links': num_links
            },
            'plots': plots,
            'most_busy_users_df': most_busy_users_df,
            'summary': summary,
            'taglines': taglines
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
