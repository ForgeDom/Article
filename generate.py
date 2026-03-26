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

PROMPT_EN = """Write a detailed SEO blog post about: {title}
Target keyword: "{keyword}"

Structure (follow exactly):
# [H1 with keyword]

[Intro: 2 paragraphs, hook + what reader will learn]

## What is [topic] and why it matters
[2-3 paragraphs, explain the problem this solves]

## Step-by-step: [main action]
[Numbered steps, each with explanation]
[Include a real code example in Python or bash if relevant]

## Common mistakes to avoid
[3-5 bullet points with real mistakes and fixes]

## [Tool/approach] vs alternatives
| Feature | [Main tool] | Alternative 1 | Alternative 2 |
|---------|------------|---------------|---------------|
[Fill 4-5 rows with real comparisons]

## FAQ
**Q: [Common question 1]?**
A: [Concise answer]

**Q: [Common question 2]?**
A: [Concise answer]

**Q: [Common question 3]?**
A: [Concise answer]

## Recommended tools
- [Tool 1] — [one line description]
- [Tool 2] — [one line description]

## Conclusion
[2 paragraphs, summarize key points + CTA]

Rules:
- 1200-1500 words total
- Conversational tone, no buzzwords
- No invented statistics — only say "according to" if you're certain
- Every code example must be real and runnable
- Mention n8n, Render, Hostinger naturally where relevant
"""

PROMPT_UK = """Напиши детальну SEO-статтю на тему: {title}
Головний ключ: "{keyword}"

Структура (дотримуйся точно):
# [H1 з ключовим словом]

[Вступ: 2 абзаци, чіпляючий початок + що дізнається читач]

## Що таке [тема] і навіщо це потрібно
[2-3 абзаци, поясни яку проблему це вирішує]

## Покроково: [основна дія]
[Нумеровані кроки з поясненням]
[Додай реальний приклад коду на Python або bash якщо доречно]

## Типові помилки яких варто уникати
[3-5 пунктів з реальними помилками і як їх виправити]

## [Інструмент] vs альтернативи
| Критерій | [Головний інструмент] | Альтернатива 1 | Альтернатива 2 |
|----------|----------------------|----------------|----------------|
[Заповни 4-5 рядків реальними порівняннями]

## Часті питання
**Q: [Часте питання 1]?**
A: [Коротка відповідь]

**Q: [Часте питання 2]?**
A: [Коротка відповідь]

**Q: [Часте питання 3]?**
A: [Коротка відповідь]

## Рекомендовані інструменти
- [Інструмент 1] — [один рядок опису]
- [Інструмент 2] — [один рядок опису]

## Висновок
[2 абзаци, підсумок + CTA]

Правила:
- 1100-1400 слів
- Розмовний тон, без канцеляризмів
- Не вигадуй статистику
- Кожен приклад коду має бути реальним і робочим
- Згадуй n8n, Render, Hostinger природно де доречно
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