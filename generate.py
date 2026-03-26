import csv
import datetime
import os
import re
import time
from groq import Groq

GROQ_API_KEY = os.environ["GROQ_API_KEY"]
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

AFFILIATE_LINKS = {
    "n8n":       "https://n8n.io/?ref=YOUR_ID",
    "Hostinger": "https://hostinger.com/?ref=YOUR_ID",
    "Render":    "https://render.com/?ref=YOUR_ID",
}

PROMPT_EN = """Write an SEO blog post about: {title}
Target keyword: "{keyword}"

Structure:
- H1: use the target keyword naturally
- Intro (120 words): hook + what reader will learn
- 3 sections with H2 headers (practical, specific)
- Code example if relevant (Python or bash)
- Conclusion with CTA
- Section "Recommended tools" at the end

Rules:
- 900-1100 words total
- Conversational tone, no buzzwords
- No invented statistics
- Mention real tools: n8n, Render, Hostinger where relevant
"""

PROMPT_UK = """Напиши SEO-статтю для блогу на тему: {title}
Головний ключ: "{keyword}"

Структура:
- H1: використай ключове слово природно
- Вступ (120 слів): чіпляючий початок + що дізнається читач
- 3 секції з H2 заголовками (практичні, конкретні)
- Приклад коду якщо доречно (Python або bash)
- Висновок з CTA
- Секція "Рекомендовані інструменти" в кінці

Правила:
- 800-1000 слів
- Розмовний тон, без канцеляризмів
- Не вигадуй статистику
- Згадуй реальні інструменти: n8n, Render, Hostinger де доречно
"""

def load_next_topic(path="topics.csv"):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    pending = [r for r in rows if r["status"] == "pending"]
    if not pending:
        return None, rows
    pending[0]["status"] = "done"
    return pending[0], rows

def save_topics(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)

def generate_article(topic):
    lang = topic.get("lang", "en")
    prompt_tpl = PROMPT_UK if lang == "uk" else PROMPT_EN
    prompt = prompt_tpl.format(
        title=topic["title"],
        keyword=topic["keyword"]
    )

    client = Groq(api_key=os.environ["GROQ_API_KEY"])

    for attempt in range(3):
        try:
            chat = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.7
            )
            return chat.choices[0].message.content
        except Exception as e:
            print(f"Attempt {attempt+1} failed: {e}")
            if attempt < 2:
                time.sleep(30)
            else:
                raise

def inject_links(text):
    for tool, url in AFFILIATE_LINKS.items():
        text = re.sub(
            rf'\b{re.escape(tool)}\b',
            f'[{tool}]({url})',
            text, count=1
        )
    return text

def slugify(title):
    slug = title.lower()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    return slug[:55].strip('-')

def save_post(topic, content):
    date = datetime.date.today().isoformat()
    slug = slugify(topic["title"])
    lang = topic.get("lang", "en")
    os.makedirs("_posts", exist_ok=True)
    filename = f"_posts/{date}-{slug}.md"
    frontmatter = f"""---
layout: post
title: "{topic['title']}"
date: {date}
lang: {lang}
description: "Learn about {topic['keyword']} — practical guide with examples."
---

"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(frontmatter + content)
    print(f"Saved: {filename}")
    return filename

def main():
    topic, all_rows = load_next_topic()
    if not topic:
        print("No pending topics. Add more to topics.csv")
        return

    print(f"Generating: {topic['title']}")
    article = generate_article(topic)
    article = inject_links(article)
    save_post(topic, article)
    save_topics("topics.csv", all_rows)
    print("Done")

if __name__ == "__main__":
    main()