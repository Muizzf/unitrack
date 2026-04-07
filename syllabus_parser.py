import pdfplumber
import re
from dateutil.parser import parse as parse_date


TASK_KEYWORDS = [
    "assignment", "project", "midterm", "exam",
    "quiz", "test", "term test", "final"
]

MONTH_REGEX = r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*"


def extract_date(text):
    patterns = [
        rf"{MONTH_REGEX}\s+\d{{1,2}}",
        rf"\d{{1,2}}\s+{MONTH_REGEX}"
    ]

    for p in patterns:
        match = re.search(p, text, re.IGNORECASE)
        if match:
            try:
                return parse_date(match.group(), fuzzy=False).date()
            except:
                pass
    return "Unknown"


def extract_weight(text):
    match = re.search(r"(\d+)\s*%", text)
    return float(match.group(1)) if match else None


def extract_assignment_code(text):
    match = re.search(r"\bA\d+\b", text)
    return match.group() if match else None


def clean_title(text):
    code = extract_assignment_code(text)
    if code:
        return code

    lower = text.lower()

    if "term test" in lower:
        match = re.search(r"term test\s*\d+", lower)
        return match.group().title() if match else "Term Test"

    if "midterm" in lower:
        match = re.search(r"midterm\s*\d+", lower)
        return match.group().title() if match else "Midterm"

    if "final" in lower:
        return "Final Exam"

    if "quiz" in lower:
        return "Quizzes"

    return text.strip(" -:,.@")


def is_noise(text):
    lower = text.lower()

    noise_words = [
        "learning", "objective", "lecture", "policy",
        "grading", "component", "example", "pass",
        "fail", "autograder", "copyright"
    ]

    if len(text.split()) > 20:
        return True

    if any(w in lower for w in noise_words):
        return True

    return False


def looks_like_task(text):
    lower = text.lower()

    if any(k in lower for k in TASK_KEYWORDS):
        return True

    if re.search(r"\bA\d+\b", text):
        return True

    return False



def parse_tables(page):
    tasks = []
    tables = page.extract_tables()

    if not tables:
        return tasks

    for table in tables:
        for row in table:
            if not row:
                continue

            row_text = " ".join([str(c) for c in row if c])

            if not looks_like_task(row_text):
                continue

            title = clean_title(row_text)
            weight = extract_weight(row_text)
            due_date = extract_date(row_text)

            if weight is None or weight == 0:
                continue

            tasks.append({
                "title": title,
                "due_date": due_date,
                "weight": weight
            })

    return tasks


def parse_text(lines):
    tasks = []
    current_task = None

    for i in range(len(lines)):
        line = lines[i].strip()
        if not line:
            continue

        if i + 1 < len(lines) and len(lines[i+1].split()) < 6:
            line += " " + lines[i+1].strip()

        if is_noise(line):
            continue

        if looks_like_task(line):
            title = clean_title(line)
            weight = extract_weight(line)
            due_date = extract_date(line)

            if weight and due_date != "Unknown":
                tasks.append({
                    "title": title,
                    "due_date": due_date,
                    "weight": weight
                })
                continue

            current_task = {
                "title": title,
                "due_date": due_date,
                "weight": weight
            }
            continue

        if current_task:
            if current_task["due_date"] == "Unknown":
                date = extract_date(line)
                if date != "Unknown":
                    current_task["due_date"] = date

            if current_task["weight"] is None:
                weight = extract_weight(line)
                if weight:
                    current_task["weight"] = weight

            if current_task["weight"]:
                tasks.append({
                    "title": current_task["title"],
                    "due_date": current_task["due_date"],
                    "weight": current_task["weight"]
                })
                current_task = None

    return tasks


from datetime import date

def is_real_date(d):
    return isinstance(d, date)

def deduplicate_tasks(tasks):
    best = {}

    for t in tasks:
        key = t["title"].lower()

        if key not in best:
            best[key] = t
            continue

        existing = best[key]

        if is_real_date(t["due_date"]) and not is_real_date(existing["due_date"]):
            best[key] = t
            continue

        if (t["weight"] or 0) > (existing["weight"] or 0):
            best[key] = t
            continue

    return list(best.values())


def extract_tasks_from_pdf(pdf_path):
    tasks = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:

            tasks.extend(parse_tables(page))

            text = page.extract_text()
            if text:
                lines = text.split("\n")
                tasks.extend(parse_text(lines))
            agg_tasks = extract_aggregated_tasks(text)
            for t in agg_tasks:
                tasks.append(t)
                print(f"Task (aggregate): {t['title']}")
                print(f"  → Due: {t['due_date']}, Weight: {t['weight']}%")

    tasks = deduplicate_tasks(tasks)

    from datetime import date

    tasks.sort(
        key=lambda x: x["due_date"] if isinstance(x["due_date"], date) else date(9999, 12, 31)
    )

    return tasks

def extract_aggregated_tasks(text):
    tasks = []

    lines = text.split("\n")

    for line in lines:
        line = line.strip()

        match = re.search(r"(\d+)\s+(assignments|labs|lab exercises)\s*\(([\d.]+)% each\)", line, re.IGNORECASE)
        if match:
            count = int(match.group(1))
            kind = match.group(2).lower()
            weight_each = float(match.group(3))

            for i in range(1, count + 1):
                tasks.append({
                    "title": f"{kind[:-1].capitalize()} {i}",
                    "due_date": "Unknown",
                    "weight": weight_each
                })

        match = re.search(r"(midterm|final exam)\s*(\d+)%", line, re.IGNORECASE)
        if match:
            title = match.group(1).title()
            weight = float(match.group(2))

            tasks.append({
                "title": title,
                "due_date": "Unknown",
                "weight": weight
            })

    return tasks


if __name__ == "__main__":
    pdf_file = "syllabus.pdf"

    tasks = extract_tasks_from_pdf(pdf_file)

    print("\n=== FINAL TASK LIST ===")
    for i, t in enumerate(tasks, 1):
        print(f"{i}. {t['title']}")
        print(f"   Due: {t['due_date']}, Weight: {t['weight']}%")