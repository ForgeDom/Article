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

def get_client():
    return Groq(api_key=os.environ["GROQ_API_KEY"])

def generate_section(client, prompt, max_tokens=500):
    for attempt in range(3):
        try:
            chat = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.8
            )
            return chat.choices[0].message.content.strip()
        except Exception as e:
            print(f"Attempt {attempt+1} failed: {e}")
            if attempt < 2:
                time.sleep(30)
            else:
                raise

def generate_article(topic):
    client = get_client()
    title = topic["title"]
    keyword = topic["keyword"]
    lang = topic.get("lang", "en")

    print(f"  Generating intro...")
    if lang == "uk":
        intro = generate_section(client,
            f"Ти досвідчений розробник. Напиши вступ (2 абзаци) для статті '{title}'. "
            f"Починай з конкретного болю читача або несподіваного факту. "
            f"Тон: розмовний, як пояснюєш колезі. Без канцеляризмів і buzzwords."
        )
    else:
        intro = generate_section(client,
            f"You are an experienced developer. Write a 2-paragraph intro for '{title}'. "
            f"Start with a relatable pain point or surprising fact. "
            f"Tone: conversational, like explaining to a colleague. No buzzwords."
        )

    time.sleep(2)
    print(f"  Generating problem section...")
    if lang == "uk":
        problem = generate_section(client,
            f"Напиши 2 абзаци про проблему яку вирішує '{title}'. "
            f"Ключове слово: '{keyword}'. "
            f"Будь конкретним. Використовуй 'ти напевно...' або 'знайомо?'. "
            f"Без вступних фраз — одразу до суті."
        )
    else:
        problem = generate_section(client,
            f"Write 2 paragraphs about the problem that '{title}' solves. "
            f"Target keyword: '{keyword}'. "
            f"Be specific. Use 'you've probably...' or 'sound familiar?' style. "
            f"No intro phrases — get straight to the point."
        )

    time.sleep(2)
    print(f"  Generating how-to section...")
    if lang == "uk":
        howto = generate_section(client,
            f"Напиши покроковий розділ для статті '{title}'. "
            f"4-5 нумерованих кроків. Кожен крок: що робити + чому важливо (1-2 речення). "
            f"Додай реальний приклад коду на Python або bash якщо доречно. "
            f"Код має бути робочим з коментарями.",
            max_tokens=800
        )
    else:
        howto = generate_section(client,
            f"Write a step-by-step how-to section for '{title}'. "
            f"4-5 numbered steps. Each step: what to do + why it matters (1-2 sentences). "
            f"Include a real Python or bash code example if relevant. "
            f"Code must be runnable with comments.",
            max_tokens=800
        )

    time.sleep(2)
    print(f"  Generating mistakes section...")
    if lang == "uk":
        mistakes = generate_section(client,
            f"Напиши 3-4 типові помилки які роблять люди з '{keyword}'. "
            f"Будь прямим і відвертим. "
            f"Формат: кожна помилка з поясненням чому це погано і як правильно. "
            f"Починай не з 'Ось помилки' а одразу з першої помилки."
        )
    else:
        mistakes = generate_section(client,
            f"Write 3-4 common mistakes people make with '{keyword}'. "
            f"Be direct and opinionated. "
            f"Format: each mistake with explanation of why it's wrong and what to do instead. "
            f"Start directly with the first mistake, no intro sentence."
        )

    time.sleep(2)
    print(f"  Generating comparison section...")
    if lang == "uk":
        comparison = generate_section(client,
            f"Порівняй головний інструмент для '{keyword}' з 2 альтернативами. "
            f"Формат для кожного: **Назва інструменту** — найкраще для [тип користувача]. "
            f"Плюси: [2-3 пункти]. Мінуси: [1-2 пункти]. "
            f"В кінці: 2 речення твоєї чесної думки коли що використовувати."
        )
    else:
        comparison = generate_section(client,
            f"Compare the main tool for '{keyword}' with 2 alternatives. "
            f"Format for each: **Tool name** — best for [type of user]. "
            f"Pros: [2-3 points]. Cons: [1-2 points]. "
            f"End with: 2 sentences of your honest take on when to use which."
        )

    time.sleep(2)
    print(f"  Generating quick wins...")
    if lang == "uk":
        quickwins = generate_section(client,
            f"Напиши 3 конкретні дії які можна зробити сьогодні щодо '{keyword}'. "
            f"Кожна дія на новому рядку починається з '- '. "
            f"Дії мають бути конкретними і виконуваними за 30 хвилин. "
            f"Без вступу — одразу список."
        )
    else:
        quickwins = generate_section(client,
            f"Write 3 specific actions someone can take today related to '{keyword}'. "
            f"Each action on a new line starting with '- '. "
            f"Actions must be concrete and doable in under 30 minutes. "
            f"No intro — start directly with the list."
        )

    time.sleep(2)
    print(f"  Generating FAQ...")
    if lang == "uk":
        faq = generate_section(client,
            f"Напиши 3 питання і відповіді про '{keyword}'. "
            f"Формат: **Q: питання?** A: відповідь (максимум 3 речення). "
            f"Питання мають бути реальними — які справді гуглять люди. "
            f"Відповіді прямі і без води."
        )
    else:
        faq = generate_section(client,
            f"Write 3 FAQ questions and answers about '{keyword}'. "
            f"Format: **Q: question?** A: answer (max 3 sentences). "
            f"Questions must be real — things people actually Google. "
            f"Answers direct and no fluff."
        )

    time.sleep(2)
    print(f"  Generating conclusion...")
    if lang == "uk":
        conclusion = generate_section(client,
            f"Напиши висновок (2 абзаци) для статті '{title}'. "
            f"Перший абзац: підсумуй головну думку. "
            f"Другий абзац: чіткий заклик до дії — що зробити прямо зараз. "
            f"Тон: мотивуючий але не пафосний."
        )
    else:
        conclusion = generate_section(client,
            f"Write a conclusion (2 paragraphs) for '{title}'. "
            f"First paragraph: summarize the key takeaway. "
            f"Second paragraph: clear call to action — what to do right now. "
            f"Tone: motivating but not cheesy."
        )

    if lang == "uk":
        article = f"""# {title}

{intro}

## Проблема

{problem}

## Як це зробити

{howto}

## Помилки яких варто уникати

{mistakes}

## Порівняння інструментів

{comparison}

## Що зробити вже сьогодні

{quickwins}

## Часті питання

{faq}

## Висновок

{conclusion}
"""
    else:
        article = f"""# {title}

{intro}

## The Problem

{problem}

## How to Get Started

{howto}

## Mistakes to Avoid

{mistakes}

## Tool Comparison

{comparison}

## Quick Wins for Today

{quickwins}

## FAQ

{faq}

## Bottom Line

{conclusion}
"""
    return article

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