"""Seed demo data for local UI testing (idempotent-ish: clears activity data first)."""
import os
import sys

import django
from django.core.files.base import ContentFile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth.models import User  # noqa: E402
from activities.models import Activity, ActivityTag, Category, Material, Tag  # noqa: E402


def make_pdf(text):
    objs = [
        b"<</Type/Catalog/Pages 2 0 R>>",
        b"<</Type/Pages/Kids[3 0 R]/Count 1>>",
        b"<</Type/Page/Parent 2 0 R/MediaBox[0 0 340 130]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>",
    ]
    stream = b"BT /F1 20 Tf 24 64 Td (" + text.encode("latin-1", "replace") + b") Tj ET"
    objs.append(b"<</Length " + str(len(stream)).encode() + b">>\nstream\n" + stream + b"\nendstream")
    objs.append(b"<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>")
    out = b"%PDF-1.4\n"
    offsets = []
    for i, body in enumerate(objs, start=1):
        offsets.append(len(out))
        out += str(i).encode() + b" 0 obj\n" + body + b"\nendobj\n"
    xref_pos = len(out)
    out += b"xref\n0 " + str(len(objs) + 1).encode() + b"\n0000000000 65535 f \n"
    for off in offsets:
        out += ("%010d 00000 n \n" % off).encode()
    out += b"trailer\n<</Size " + str(len(objs) + 1).encode() + b"/Root 1 0 R>>\nstartxref\n" + str(xref_pos).encode() + b"\n%%EOF"
    return out


# Reset activity-related data (keep users)
Material.objects.all().delete()
ActivityTag.objects.all().delete()
Activity.objects.all().delete()
Tag.objects.all().delete()
Category.objects.all().delete()

cats = {}
for name, desc in [
    ("Group Activity", "Collaborative activities for small teams and whole classes."),
    ("Individual or Group Activity", "Flexible activities that work solo or in groups."),
    ("Icebreakers", "Quick warm-ups to build rapport at the start of a course."),
    ("Discussion", "Structured conversations and debates."),
    ("Project", "Longer, deliverable-based work."),
]:
    cats[name] = Category.objects.create(name=name, description=desc)

tag_names = [
    "Communication Skills", "Group", "Outside Classroom", "Perspective",
    "Presentation", "Single Class", "Civic And Global Responsibility",
    "Critical And Creative Thinking", "Individual", "Research",
    "Team Building", "Problem Solving",
]
tags = {n: Tag.objects.create(name=n.lower()) for n in tag_names}


def add(title, category, description, tag_list, materials):
    a = Activity.objects.create(title=title, category=cats[category], description=description)
    for t in tag_list:
        ActivityTag.objects.create(activity=a, tag=tags[t])
    for m in materials:
        mat = Material.objects.create(activity=a, title=m["title"], material_type=m["type"])
        if m.get("pdf"):
            mat.file.save(m["pdf"], ContentFile(make_pdf(m.get("pdf_text", title))), save=True)
        elif m.get("word"):
            mat.file.save(m["word"], ContentFile(b"Demo Word document placeholder for " + title.encode()), save=True)
            if m.get("preview_pdf"):
                mat.preview_pdf.save(m["preview_pdf"], ContentFile(make_pdf(title + " preview")), save=True)
    return a


add("Recruitment", "Group Activity",
    "Students will go outside of the classroom to find people to “interview” for a position in their chosen field or profession.\nTime: 45-90 Minutes",
    ["Communication Skills", "Group", "Outside Classroom", "Perspective", "Presentation", "Single Class"],
    [
        {"title": "Recruitment Worksheet PDF", "type": "worksheet", "pdf": "recruitment-worksheet.pdf", "pdf_text": "Recruitment Worksheet"},
        {"title": "Recruitment Worksheet Word", "type": "worksheet", "word": "recruitment-worksheet.docx"},
    ])

add("Issue Analysis", "Individual or Group Activity",
    "Students will identify and analyze different types of issues and explore how they can be reframed from alternative perspectives. This activity encourages critical thinking, creativity, and an understanding of how arguments and messaging can shift depending on framing.\nTime: 60 Minutes",
    ["Civic And Global Responsibility", "Critical And Creative Thinking", "Group", "Individual", "Presentation", "Single Class"],
    [
        {"title": "Issue Analysis Guide", "type": "instructions", "pdf": "issue-analysis-guide.pdf", "pdf_text": "Issue Analysis Guide"},
        {"title": "Framing Examples", "type": "example", "word": "framing-examples.docx", "preview_pdf": "framing-examples-preview.pdf"},
    ])

add("Two Truths and a Lie", "Icebreakers",
    "A fast, low-stakes warm-up where each student shares two true statements and one false one; the group guesses which is the lie.\nTime: 15 Minutes",
    ["Communication Skills", "Group", "Single Class", "Team Building"],
    [
        {"title": "Facilitation Notes", "type": "instructions", "pdf": "two-truths-notes.pdf", "pdf_text": "Two Truths and a Lie"},
    ])

add("Perspective Debate", "Discussion",
    "Assign opposing viewpoints on a current topic and have students argue a side they may not personally hold, then debrief on what shifted.\nTime: 50 Minutes",
    ["Critical And Creative Thinking", "Perspective", "Communication Skills", "Group", "Single Class"],
    [
        {"title": "Debate Prompt Deck", "type": "example", "word": "debate-prompts.docx", "preview_pdf": "debate-prompts-preview.pdf"},
    ])

add("Field Research Sprint", "Project",
    "Small teams design and run a mini research study over one week, from question to a short findings presentation.\nTime: 1 Week",
    ["Research", "Group", "Presentation", "Problem Solving", "Outside Classroom"],
    [
        {"title": "Research Sprint Handout", "type": "worksheet", "pdf": "research-sprint-handout.pdf", "pdf_text": "Field Research Sprint"},
        {"title": "Presentation Rubric", "type": "instructions", "word": "presentation-rubric.docx"},
    ])

add("Design Thinking Challenge", "Group Activity",
    "Teams move through empathize, define, ideate, and prototype phases to solve a real campus problem in a single session.\nTime: 90 Minutes",
    ["Problem Solving", "Critical And Creative Thinking", "Team Building", "Group", "Presentation"],
    [
        {"title": "Challenge Brief", "type": "instructions", "pdf": "design-challenge-brief.pdf", "pdf_text": "Design Thinking Challenge"},
        {"title": "Prototype Template", "type": "worksheet", "word": "prototype-template.docx"},
    ])

# Demo faculty account for testing preview/download (logged-in state)
if not User.objects.filter(username="demo@university.edu").exists():
    User.objects.create_user(username="demo@university.edu", email="demo@university.edu", password="teachorange123")

print("Seeded:", Activity.objects.count(), "activities,", Tag.objects.count(), "tags,",
      Category.objects.count(), "categories,", Material.objects.count(), "materials.")
