import csv
import datetime
import os
import re
import time
from groq import Groq

AFFILIATE_LINKS = {
    "n8n":       "https://n8n.io/?ref=YOUR_ID",
    "Hostinger": "https://hostinger.com/?ref=YOUR_ID",
    "Render":    "https://render.com/?ref=YOUR_ID",
}

PROMPT_EN = """You are an experienced developer writing for other developers.
Write a blog post about: {title}
Target keyword: "{keyword}"

Your writing style:
- Write like you're explaining to a colleague over coffee
- Use "you" and "I" — be personal
- Start sections with a surprising fact, question, or counterintuitive statement
- Add occasional dry humor where natural
- Be opinionated — say what actually works and what doesn't

Structure (follow exactly):

# [Catchy H1 — not just the keyword, make it interesting]

> [One sentence that captures why this matters. Make it punchy.]

[Intro: Start with a relatable pain point or surprising fact. 2 paragraphs.]

## [Problem this solves — phrased as a question or bold claim]

[2 paragraphs. Be specific about the pain. Use "you've probably..." or "sound familiar?"]

## [Main how-to section — action verb first]

[Numbered steps. Each step has:]
- What to do (one clear sentence)
- Why it matters (one sentence)
- Code example if relevant
```python or bash
# Real, runnable code with comments
```

## The part everyone gets wrong

[3-4 common mistakes. Be direct. "Most tutorials tell you X — that's wrong because..."]

## [Tool] vs the alternatives — honest comparison

| | [Tool] | [Alt 1] | [Alt 2] |
|---|---|---|---|
| Free tier | ✅ Yes | ❌ No | ⚠️ Limited |
| Setup time | 5 min | 30 min | 15 min |
| Best for | Developers | Non-tech | Enterprise |
| Learning curve | Low | Medium | High |

[2 sentences with your honest take on when to use which]

## Quick wins you can implement today

- ✅ [Actionable tip 1 — specific and immediate]
- ✅ [Actionable tip 2 — specific and immediate]
- ✅ [Actionable tip 3 — specific and immediate]

## FAQ

**Q: [Question a beginner would actually ask]?**
A: [Direct answer, no fluff. Max 2 sentences.]

**Q: [Question an intermediate would ask]?**
A: [Direct answer with nuance.]

**Q: [Gotcha question — something that trips people up]?**
A: [Honest answer even if the answer is "it depends, here's why"]

## Bottom line

[2 paragraphs. What's the one thing to remember? What should they do right now?]

---
*Tools mentioned in this post: list them with one-line descriptions and links*

Rules:
- 1300-1600 words
- Every code example must actually work
- No invented statistics — if you're not sure, don't say it
- Mention n8n, Render, or Hostinger only where genuinely relevant
- End every section with momentum — reader should want to scroll down
"""

PROMPT_UK = """Ти досвідчений розробник який пише для інших розробників.
Напиши статтю на тему: {title}
Головний ключ: "{keyword}"

Стиль написання:
- Пиши як пояснюєш колезі за кавою
- Використовуй "ти" і "я" — будь особистим
- Починай секції з несподіваного факту або провокаційного твердження
- Будь відвертим — говори що реально працює, а що ні
- Іноді додавай легкий гумор де це доречно

Структура (дотримуйся точно):

# [Цікавий H1 — не просто ключове слово, зроби його інтригуючим]

> [Одне речення чому це важливо. Коротко і влучно.]

[Вступ: Почни з болю читача або несподіваного факту. 2 абзаци.]

## [Проблема — сформульована як питання або сміливе твердження]

[2 абзаци. Конкретно про біль. Використовуй "ти напевно..." або "знайомо?"]

## [Основна інструкція — починай з дієслова дії]

[Нумеровані кроки. Кожен крок містить:]
- Що робити (одне чітке речення)
- Чому це важливо (одне речення)
- Приклад коду якщо доречно
```python або bash
# Реальний робочий код з коментарями
```

## Помилка яку роблять всі

[3-4 типові помилки. Будь прямим. "Більшість туторіалів кажуть X — це хибно тому що..."]

## [Інструмент] vs альтернативи — чесне порівняння

| | [Інструмент] | [Альт 1] | [Альт 2] |
|---|---|---|---|
| Безкоштовний | ✅ Так | ❌ Ні | ⚠️ Обмежено |
| Налаштування | 5 хв | 30 хв | 15 хв |
| Для кого | Розробники | Нетехнічні | Бізнес |
| Складність | Низька | Середня | Висока |

[2 речення з твоєю чесною думкою коли що використовувати]

## Що можна зробити вже сьогодні

- ✅ [Конкретна дія 1 — негайно виконувана]
- ✅ [Конкретна дія 2 — конкретна і практична]
- ✅ [Конкретна дія 3 — конкретна і практична]

## Часті питання

**Q: [Питання початківця]?**
A: [Пряма відповідь без води. Максимум 2 речення.]

**Q: [Питання середнього рівня]?**
A: [Відповідь з нюансами.]

**Q: [Каверзне питання — те що всіх плутає]?**
A: [Чесна відповідь навіть якщо "залежить від ситуації"]

## Головне

[2 абзаци. Що одне варто запам'ятати? Що зробити прямо зараз?]

---
*Інструменти згадані в статті: список з однорядковими описами*

Правила:
- 1200-1500 слів
- Кожен приклад коду має реально працювати
- Не вигадуй статистику
- Згадуй n8n, Render, Hostinger тільки де справді доречно
- Кожна секція має закінчуватись так щоб хотілось читати далі
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
                max_tokens=2500,
                temperature=0.8
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