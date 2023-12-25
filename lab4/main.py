'''
Example input:
    @ru2ch, @rian_ru, @meduzalive, @varlamov_news, @SolovievLive, @lentachold, @vcnews, @rtnews
    112510789, 15755094, 26284064, 31480508, 22751485, 18901857
'''
import re
import json
import requests
import threading
import multiprocessing
import string
import nltk
import tkinter as tk
from pyrogram import Client
from nltk.corpus import stopwords
from collections import Counter

from constants import *


DATA = {
        'vk': {},
        'telegram': {}
        }


bad_symb = set(['❤️', '❤', ':', 'https', 'это'])

stop_words = set(stopwords.words('russian')).union(set(stopwords.words('english'))).union(bad_symb)

def get_channel_messages(api_id, api_hash, channel_names):
    data = {}
    with Client("acc", api_id, api_hash) as app:
        for channel in channel_names:
            data[channel] = []
            channel_info = app.get_chat(channel)
            for post in app.get_chat_history(channel_info.id, limit=100):
                if post.caption:
                    data[channel].append(post.caption)
    DATA['telegram'] = data


def get_group_messages(access_token, group_ids):
    messages = {}
    for group in group_ids:
        messages[group] = []
        response = requests.get(f"https://api.vk.com/method/wall.get?owner_id=-{group}&access_token={access_token}&v=5.131")
        if response.status_code == 200:
            data = response.json()
            for item in data["response"]["items"]:
                messages[group].append(item["text"])
    DATA['vk'] = messages


def get_data_in_parallel(telegram_func, *functions):
    threads = []
    telegram_func()
    for function in functions:
        thread = threading.Thread(target=function)
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()


def remove_stopwords(text):
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'http\S+', '', text)
    words = text.split()
    filtered_words = [word for word in words 
                      if word.strip().lower() not in stop_words]
    return ' '.join(filtered_words)


def remove_punctuation_test(text):
    translator = str.maketrans('', '', string.punctuation)
    return text.translate(translator)

def remove_punctuation(text):
    words = nltk.word_tokenize(text)
    words_without_punct = [word for word in words if word.isalnum()]
    return ' '.join(words_without_punct)



def process_messages(messages):
    return [remove_punctuation(remove_stopwords(message)) for message in messages]


def process_data(data):
    with multiprocessing.Pool() as pool:
        for source, messages in data.items():
            for key, value in messages.items():
                messages[key] = pool.map(process_messages, [value])[0]


def analyze_messages(messages, sort=True):
    text = ' '.join(messages)
    
    words = nltk.tokenize.word_tokenize(text)
    
    hashtags = [word[1:] for word in words if word.startswith('#')]
    keywords = [word for word in words if word.lower() not in hashtags]
    
    hashtag_counts = Counter(hashtags)
    keyword_counts = Counter(keywords)
    
    topics = [topic for topic, count in keyword_counts.most_common(10)]

    if sort:
        return {
            'hashtags': dict(hashtag_counts.most_common()),
            'keywords': dict(keyword_counts.most_common()),
            'topics': topics
        }

    
    return {
        'hashtags': dict(hashtag_counts),
        'keywords': dict(keyword_counts),
        'topics': topics
    }


def analyze(data):
    result = {
            "common_keywords": Counter(),
            "common_hashtags": Counter()
            }
    for media, source in data.items():
        result[media] = {
                "common_keywords": Counter(),
                "common_hashtags": Counter()
                }
        for channel, messages in source.items():
            analyzed_messages = analyze_messages(messages)
            result[media][channel] = analyzed_messages
            result[media]['common_keywords'] += Counter(analyzed_messages['keywords'])
            result[media]['common_hashtags'] += Counter(analyzed_messages['hashtags'])

        
        result['common_keywords'] += result[media]['common_keywords']
        result['common_hashtags'] += result[media]['common_hashtags']

        result[media]['common_topics'] = [topic for topic, count in result[media]['common_keywords'].most_common(10)]
        result[media]['common_keywords'] = dict(result[media]['common_keywords'].most_common())
        result[media]['common_hashtags'] = dict(result[media]['common_hashtags'].most_common())
    result['common_topics'] = [topic for topic, count in result['common_keywords'].most_common(10)]
    result['common_keywords'] = dict(result['common_keywords'].most_common())
    result['common_hashtags'] = dict(result['common_hashtags'].most_common())

    return result

def save_res_to_file(data, filename):
    with open(f'{filename}.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_input_id_list(s):
    return [int(i.strip()) for i in s.split(',')]

def get_input_channel_list(s):
    return [i.strip() for i in s.split(',')]

def start():
    result_text.delete(1.0, tk.END)
    if entry1.get():
        tg_ch = get_input_channel_list(entry1.get())
    else:
        result_text.insert(tk.END, "Введите название tg каналов через @")

    if entry2.get():
        vk_id = get_input_id_list(entry2.get())
    else:
        result_text.insert(tk.END, "Введите название id вк групп")

    vk_messages = lambda: get_group_messages(vk_token, vk_id)

    tele_messages = lambda: get_channel_messages(teleapi_id, teleapi_hash, tg_ch)
    get_data_in_parallel(tele_messages, vk_messages)
    process_data(DATA)
    
    result = analyze(DATA)
    save_res_to_file(result, 'dump')
    result_str = "- Common Topics:\n" + '\n'.join(result["common_topics"]) + "\n- Common Topics vk:\n" + '\n'.join(result['vk']["common_topics"]) + "\n- Common Topics telegram:\n" + '\n'.join(result['telegram']["common_topics"])

    result_text.insert(tk.END, result_str)


if __name__ == '__main__':
    root = tk.Tk()

    # Создаем два лейбла
    label1 = tk.Label(root, text="Введите tg каналы:")
    label2 = tk.Label(root, text="Введите id вк групп:")

    # Создаем два поля ввода
    entry1 = tk.Entry(root)
    entry2 = tk.Entry(root)

    # Создаем кнопку "начать"
    button = tk.Button(root, text="Начать", command=start)

    result_text = tk.Text(root, height=10, width=50)

    # Размещаем виджеты на экране
    label1.pack()
    entry1.pack()
    label2.pack()
    entry2.pack()
    button.pack()
    result_text.pack()

    root.mainloop()

