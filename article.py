#!/usr/bin/env python3
import argparse
import datetime
import os
import re

POST_DIR = "/Users/crispin/documents/personal/git/crispindeity.github.io/_posts"

def generate_front_matter(title, date, categories, tags, pin):
    categories_yaml = "\n".join([f"  - {c}" for c in categories])
    tags_yaml = "\n".join([f"  - {t}" for t in tags])

    front = (
        "---\n"
        f"title: {title}\n"
        f"date: {date}\n"
        f"modified: {date}\n"
        "categories:\n"
        f"{categories_yaml or '  -'}\n"
        "tags:\n"
        f"{tags_yaml or '  -'}\n"
        f"pin: {str(pin).lower()}\n"
        "---\n\n"
    )
    return front


def update_modified(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S +0900")

    new_content = re.sub(
        r"modified: .*",
        f"modified: {now}",
        content,
        count=1
    )

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"🔄 modified 시간 업데이트 완료: {filepath}")


def main():
    parser = argparse.ArgumentParser(description="Blog post generator")
    parser.add_argument("--title", required=True, help="Post title")
    parser.add_argument("--categories", nargs="*", default=[], help="List of categories")
    parser.add_argument("--tags", nargs="*", default=[], help="List of tags")
    parser.add_argument("--pin", action="store_true", help="Pin this post")
    parser.add_argument("--update", action="store_true", help="Update modified only")
    parser.add_argument("--date", help="Specify date manually")
    args = parser.parse_args()

    today = datetime.datetime.now().strftime("%Y-%m-%d")
    full_date = (
        args.date
        if args.date
        else datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S +0900")
    )

    safe_title = args.title.replace("/", "_")
    filename = f"{today}-{safe_title}.md"
    filepath = os.path.join(POST_DIR, filename)

    if args.update:
        if not os.path.exists(filepath):
            print(f"❌ 파일이 존재하지 않아 update 불가: {filepath}")
            return
        update_modified(filepath)
        return

    os.makedirs(POST_DIR, exist_ok=True)
    content = generate_front_matter(
        args.title, full_date, args.categories, args.tags, args.pin
    )

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"📄 생성 완료")


if __name__ == "__main__":
    main()

