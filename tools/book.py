"""The shape of the book: every file of book/ mapped to its pages in the PDF.

This is the one place that says how the edition is cut. extract.py reads it
to write book/ and art/; the other tools read the manifest that extract.py
writes. Page numbers are the printed page numbers of the edition, which are
also the PDF's own page numbers (page 1 is the cover).
"""

PDF = "edition/The-Geometry-of-Everything.pdf"

TITLE = "The Geometry of Everything"
SUBTITLE = "Earn Your Reality · A Manual for Life"
AUTHOR = "Massimo Vincent Panella"
EDITION = "Edition of November 2026"

# The parts of the book, in order. "plate" is the full-page painting that
# opens a Book (None for the opening and the back); "accent" is the colour
# the edition uses for that part.
PARTS = [
    dict(n=0, dir="0-opening", kicker="Before the Books", name="The Opening",
         plate=None, accent="#a8792b"),
    dict(n=1, dir="1-the-ground", kicker="Book One", name="The Ground",
         plate=27, accent="#a8792b"),
    dict(n=2, dir="2-the-light", kicker="Book Two", name="The Light",
         plate=51, accent="#2f4f95"),
    dict(n=3, dir="3-the-bond", kicker="Book Three", name="The Bond",
         plate=91, accent="#ad3f2a"),
    dict(n=4, dir="4-the-work", kicker="Book Four", name="The Work",
         plate=131, accent="#2c6b62"),
    dict(n=5, dir="5-the-becoming", kicker="Book Five", name="The Becoming",
         plate=157, accent="#674a87"),
    dict(n=6, dir="6-the-summit", kicker="The Summit", name="The Geometry",
         plate=183, accent="#a8792b"),
    dict(n=7, dir="7-at-the-back", kicker="After the Summit", name="At the Back",
         plate=None, accent="#a8792b"),
]

# Every file, in reading order: (first page, last page, part, file, title, kind)
#   kind "front"   the title pages, dedication and epigraphs
#        "section" a piece of the opening, the summit or the back
#        "opener"  the page that opens a Book; becomes that folder's README.md
#        "chapter" one of the twenty-six chapters
UNITS = [
    (1, 6, 0, "00-title-and-dedication.md", "Title and Dedication", "front"),
    (9, 11, 0, "01-how-to-carry-this-book.md", "How to Carry This Book", "section"),
    (12, 13, 0, "02-the-rivers-that-became-this-book.md", "The Rivers That Became This Book", "section"),
    (14, 16, 0, "03-the-first-principle.md", "The First Principle", "section"),
    (17, 18, 0, "04-the-kept-middle.md", "The Kept Middle", "section"),
    (19, 20, 0, "05-the-floor-and-the-ceiling.md", "The Floor and the Ceiling", "section"),
    (21, 24, 0, "06-the-model-of-change.md", "The Model of Change", "section"),
    (25, 26, 0, "07-the-architecture.md", "The Architecture", "section"),

    (28, 28, 1, "README.md", "The Ground", "opener"),
    (29, 34, 1, "01-existence-needs-no-permission.md", "Existence Needs No Permission", "chapter"),
    (35, 39, 1, "02-the-vessel.md", "The Vessel", "chapter"),
    (40, 44, 1, "03-the-appointment.md", "The Appointment", "chapter"),
    (45, 50, 1, "04-starry-heavens.md", "Starry Heavens", "chapter"),

    (52, 52, 2, "README.md", "The Light", "opener"),
    (53, 57, 2, "05-know-the-one-who-knows.md", "Know the One Who Knows", "chapter"),
    (58, 62, 2, "06-the-instrument.md", "The Instrument", "chapter"),
    (63, 67, 2, "07-where-attention-goes.md", "Where Attention Goes", "chapter"),
    (68, 73, 2, "08-the-open-door.md", "The Open Door", "chapter"),
    (74, 79, 2, "09-the-dark-half-with-the-lights-on.md", "The Dark Half, with the Lights On", "chapter"),
    (80, 84, 2, "10-the-lifelong-student.md", "The Lifelong Student", "chapter"),
    (85, 90, 2, "11-the-last-freedom.md", "The Last Freedom", "chapter"),

    (92, 92, 3, "README.md", "The Bond", "opener"),
    (93, 98, 3, "12-peace-the-unsent-letter.md", "Peace: The Unsent Letter", "chapter"),
    (99, 103, 3, "13-love-another-self.md", "Love: Another Self", "chapter"),
    (104, 108, 3, "14-the-root.md", "The Root", "chapter"),
    (109, 113, 3, "15-the-living-word.md", "The Living Word", "chapter"),
    (114, 118, 3, "16-unity-through-other-persons.md", "Unity: Through Other Persons", "chapter"),
    (119, 124, 3, "17-respect-the-floor-and-the-ceiling.md", "Respect: The Floor and the Ceiling", "chapter"),
    (125, 130, 3, "18-repair.md", "Repair", "chapter"),

    (132, 132, 4, "README.md", "The Work", "opener"),
    (133, 137, 4, "19-the-blade-that-stays-sharp.md", "The Blade That Stays Sharp", "chapter"),
    (138, 143, 4, "20-enough.md", "Enough", "chapter"),
    (144, 149, 4, "21-the-headland.md", "The Headland", "chapter"),
    (150, 156, 4, "22-the-book-of-earned-power.md", "The Book of Earned Power", "chapter"),

    (158, 158, 5, "README.md", "The Becoming", "opener"),
    (159, 164, 5, "23-becoming-without-erasing.md", "Becoming Without Erasing", "chapter"),
    (165, 170, 5, "24-the-wheel.md", "The Wheel", "chapter"),
    (171, 176, 5, "25-the-author.md", "The Author", "chapter"),
    (177, 182, 5, "26-the-daily-rite.md", "The Daily Rite", "chapter"),

    (184, 184, 6, "README.md", "The Geometry", "opener"),
    (185, 193, 6, "01-the-geometry-of-everything.md", "The Geometry of Everything", "section"),
    (194, 201, 6, "02-how-this-book-could-be-wrong.md", "How This Book Could Be Wrong", "section"),
    (202, 203, 6, "03-epilogue-the-sophont.md", "Epilogue: The Sophont", "section"),
    (204, 204, 6, "04-the-law-of-the-sophont.md", "The Law of the Sophont", "section"),

    (205, 206, 7, "01-the-ninety-day-trial.md", "The Ninety-Day Trial", "section"),
    (207, 207, 7, "02-the-monthly-reading-cycle.md", "The Monthly Reading Cycle", "section"),
    (208, 208, 7, "03-the-respect-ledger.md", "The Respect Ledger", "section"),
    (211, 212, 7, "04-index-of-situations.md", "Index of Situations", "section"),
    (213, 215, 7, "05-sources-and-translations.md", "Sources and Translations", "section"),
    (216, 217, 7, "06-colophon.md", "Colophon", "section"),
]

# Pages that are not carried into the Markdown, and why.
SKIPPED_PAGES = {
    2: "the half-title, which repeats the title page",
    7: "the printed table of contents; book/README.md replaces it",
    8: "the printed table of contents; book/README.md replaces it",
    209: "a blank continuation of the Respect Ledger",
    210: "a blank continuation of the Respect Ledger",
}

# Full-page paintings (the cover, the six Book plates, the back cover).
PAINTED_PAGES = [1, 27, 51, 91, 131, 157, 183, 217]

# The nine movements of every chapter, as the book names them.
MOVEMENTS = ["The Teaching", "The Five Scales", "The Witnesses", "The Tale", "The Energy",
             "The Reversal", "The Practice", "The Ledger", "The Song"]

# The three marks.
MARKS = {"◆": "Commitment", "●": "Evidence", "◇": "Analogy"}
