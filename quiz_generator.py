import random
import emoji
import pandas as pd

def extract_emojis(text):
    return [c for c in text if c in emoji.EMOJI_DATA]

def generate_who_sent_question(df):
    try:
        filtered_df = df[df['user'] != 'group_notification']
        if filtered_df.empty:
            return None
        sample = filtered_df.sample(1).iloc[0]
        question = f'Who sent this message: "{sample["message"]}"?'
        users = df['user'].unique().tolist()
        correct = sample['user']
        options = random.sample([u for u in users if u != correct], min(3, len(users)-1)) + [correct]
        random.shuffle(options)
        return {'type': 'who_sent', 'question': question, 'options': options, 'answer': correct}
    except:
        return None

def generate_emoji_question(df):
    try:
        df = df.copy()
        df['emojis'] = df['message'].apply(extract_emojis)
        emoji_counts = df.explode('emojis').groupby('user')['emojis'].value_counts()
        if emoji_counts.empty:
            return None
        top_emoji = emoji_counts.groupby(level=1).sum().idxmax()
        
        # Fixed: Use xs to get cross-section of the MultiIndex
        top_users = emoji_counts.xs(top_emoji, level=1).nlargest(4).index.tolist()
        
        # Ensure at least 4 options (add random users if needed)
        all_users = df['user'].unique().tolist()
        additional_users = [u for u in all_users if u not in top_users]
        while len(top_users) < 4 and additional_users:
            top_users.append(additional_users.pop())
            
        question = f'Who uses the emoji "{top_emoji}" the most?'
        return {'type': 'emoji_usage', 'question': question, 'options': top_users[:4], 'answer': top_users[0]}
    except:
        return None


def generate_date_question(df):
    try:
        filtered_df = df[df['user'] != 'group_notification']
        if filtered_df.empty:
            return None
        sample = filtered_df.sample(1).iloc[0]
        question = f'Guess the date when this message was sent: "{sample["message"]}"?'
        correct = sample['only_date'].strftime('%d/%m/%Y')
        dates = df['only_date'].drop_duplicates().apply(lambda x: x.strftime('%d/%m/%Y')).tolist()
        dates = random.sample(dates, min(3, len(dates)))
        if correct not in dates:
            if len(dates) == 3:
                dates.pop()
            dates.append(correct)
        random.shuffle(dates)
        return {'type': 'date_guess', 'question': question, 'options': dates, 'answer': correct}
    except:
        return None

def generate_most_links_question(df):
    try:
        filtered_df = df[df['user'] != 'group_notification'].copy()
        filtered_df['num_links'] = filtered_df['message'].str.count('http')
        link_counts = filtered_df.groupby('user')['num_links'].sum().sort_values(ascending=False)
        if link_counts.empty or link_counts.iloc[0] == 0:
            return None
        users = link_counts.index.tolist()
        question = "Who shared the most links in the chat?"
        available_users = [u for u in filtered_df['user'].unique() if u not in users]
        options = users[:4] if len(users) >= 4 else users + random.sample(
            available_users, min(len(available_users), 4 - len(users))
        )
        correct = users[0]
        random.shuffle(options)
        return {'type': 'most_links', 'question': question, 'options': options, 'answer': correct}
    except:
        return None

def generate_most_messages_question(df):
    try:
        filtered_df = df[df['user'] != 'group_notification'].copy()
        msg_counts = filtered_df['user'].value_counts()
        if msg_counts.empty:
            return None
        users = msg_counts.index.tolist()
        question = "Who sent the most messages in the chat?"
        available_users = [u for u in filtered_df['user'].unique() if u not in users]
        options = users[:4] if len(users) >= 4 else users + random.sample(
            available_users, min(len(available_users), 4 - len(users))
        )
        correct = users[0]
        random.shuffle(options)
        return {'type': 'most_messages', 'question': question, 'options': options, 'answer': correct}
    except:
        return None

def generate_quiz(df, num_questions=5):
    question_generators = [
        (generate_who_sent_question, 0.3),
        (generate_emoji_question, 0.3),
        (generate_date_question, 0.1),
        (generate_most_links_question, 0.15),
        (generate_most_messages_question, 0.15)
    ]
    
    quiz = []
    attempts = 0
    max_attempts = num_questions * 3
    
    while len(quiz) < num_questions and attempts < max_attempts:
        # Weighted random selection of question types
        generator = random.choices(
            [g[0] for g in question_generators],
            weights=[g[1] for g in question_generators],
            k=1
        )[0]
        
        question = generator(df)
        if question and not any(q['question'] == question['question'] for q in quiz):
            quiz.append(question)
        attempts += 1

    return quiz[:num_questions]
