import streamlit as st
import preprocessor, helper
import matplotlib.pyplot as plt
import seaborn as sns
from summarizer import summarize_last_300_messages, generate_300_message_taglines


# Set page configuration
st.set_page_config(page_title="WP Wrapped", layout="wide")

# Sidebar title
st.sidebar.title("📊 WP Wrapped")
st.sidebar.write("Your whatsapp chat analyser!")

# File uploader
uploaded_file = st.sidebar.file_uploader("📂 Upload a WhatsApp chat file")

if uploaded_file is not None:
    # Preprocess uploaded data
    bytes_data = uploaded_file.getvalue()
    data = bytes_data.decode("utf-8")
    df = preprocessor.preprocess(data)

    # User selection
    user_list = df['user'].unique().tolist()
    user_list.remove('group_notification')
    user_list.sort()
    user_list.insert(0, "Overall")
    selected_user = st.sidebar.selectbox("👤 Analyze data for:", user_list)

    if st.sidebar.button("🔍 Show Analysis"):
        # Main page layout
        st.title(f"📈 Analysis for {'Overall Chat' if selected_user == 'Overall' else selected_user}")

        # Stats Section
        st.subheader("💡 Key Statistics")
        num_messages, words, num_media_messages, num_links = helper.fetch_stats(selected_user, df)

        # Display statistics in a 4-column layout
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📝 Total Messages", num_messages)
        col2.metric("🔤 Total Words", words)
        col3.metric("🖼️ Media Shared", num_media_messages)
        col4.metric("🔗 Links Shared", num_links)

        # Monthly Timeline
        st.subheader("📅 Monthly Timeline")
        timeline = helper.monthly_timeline(selected_user, df)
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(timeline['time'], timeline['message'], color='green', marker='o')
        ax.set_title("Messages Over Time")
        plt.xticks(rotation=45)
        st.pyplot(fig)

        # Daily Timeline
        st.subheader("📆 Daily Timeline")
        daily_timeline = helper.daily_timeline(selected_user, df)
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(daily_timeline['only_date'], daily_timeline['message'], color='blue', marker='o')
        ax.set_title("Messages Per Day")
        plt.xticks(rotation=45)
        st.pyplot(fig)

        # Activity Maps
        st.subheader("📊 Activity Maps")
        col1, col2 = st.columns(2)

        with col1:
            busy_day = helper.week_activity_map(selected_user, df)
            fig, ax = plt.subplots()
            ax.bar(busy_day.index, busy_day.values, color='purple')
            ax.set_title("Most Active Days")
            plt.xticks(rotation=45)
            st.pyplot(fig)

        with col2:
            busy_month = helper.month_activity_map(selected_user, df)
            fig, ax = plt.subplots()
            ax.bar(busy_month.index, busy_month.values, color='orange')
            ax.set_title("Most Active Months")
            plt.xticks(rotation=45)
            st.pyplot(fig)

        # Heatmap
        st.subheader("🗓️ Weekly Activity Heatmap")

        # Call the heatmap function
        user_heatmap = helper.activity_heatmap(selected_user, df)

        # Check if the result is valid and non-empty
        if user_heatmap is not None and not user_heatmap.empty:
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.heatmap(user_heatmap, annot=True, fmt=".0f", cmap="YlGnBu", ax=ax)
            ax.set_title("Activity Heatmap")
            st.pyplot(fig)
        else:
            st.warning("No activity data available to display heatmap.")



        # Most Busy Users
        if selected_user == 'Overall':
            st.subheader("👥 Most Active Users")
            x, new_df = helper.most_busy_users(df)

            col1, col2 = st.columns(2)
            with col1:
                fig, ax = plt.subplots()
                ax.bar(x.index, x.values, color='red')
                ax.set_title("User Activity")
                plt.xticks(rotation=45)
                st.pyplot(fig)

            with col2:
                st.dataframe(new_df)

        # WordCloud
        st.subheader("☁️ WordCloud")
        df_wc = helper.create_wordcloud(selected_user, df)
        fig, ax = plt.subplots()
        ax.imshow(df_wc, interpolation='bilinear')
        ax.axis('off')
        st.pyplot(fig)

        # Most Common Words
        st.subheader("📜 Most Common Words")
        most_common_df = helper.most_common_words(selected_user, df)
        fig, ax = plt.subplots()
        ax.barh(most_common_df[0], most_common_df[1], color='skyblue')
        ax.set_title("Top Words")
        plt.xticks(rotation=45)
        st.pyplot(fig)

        # Emoji Analysis
        st.subheader("😀 Emoji Analysis")
        emoji_df = helper.emoji_helper(selected_user, df)

        col1, col2 = st.columns(2)
        with col1:
            st.dataframe(emoji_df)
        with col2:
            fig, ax = plt.subplots()
            ax.pie(emoji_df[1].head(), labels=emoji_df[0].head(), autopct="%0.2f", startangle=140, colors=sns.color_palette("pastel"))
            ax.set_title("Top Emojis")
            st.pyplot(fig)


        st.header("Chat Summary and Member Taglines (Powered by Llama)")

        # Assuming your preprocessed DataFrame is named 'df'
        with st.spinner("Generating chat summary..."):
            summary = summarize_last_300_messages(df)
            st.subheader("Summary of Last 300 Messages")
            st.write(summary)

        with st.spinner("Generating funny taglines for members..."):
            taglines = generate_300_message_taglines(df)
            st.subheader("Funny Taglines for Each Member")
            for user, tagline in taglines.items():
                st.markdown(f"**{user}:** {tagline}")