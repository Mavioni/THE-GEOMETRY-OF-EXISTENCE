"""The shape of the book: every unit of the repository, mapped to its pages.

This is the single source of truth for how the edition PDF is cut into
Markdown files. ``extract_book.py`` reads it to write ``book/`` and ``art/``;
``build_site.py`` reads the manifest it produces to build the website.

Page numbers are the printed folios of the complete edition
(15 November 2026), which coincide with the PDF page indices + 1.
"""

PDF = "edition/The_Geometry_of_Existence_A_Manual_for_Life.pdf"

# Levels: directory, display name, the line under the name, accent colour.
LEVELS = [
    dict(n=0, dir="0-front", name="Front Matter", kicker="Before the levels",
         sub="five levels, five marks, one promise", accent="#c9a14a"),
    dict(n=1, dir="1-the-lines", name="The Lines", kicker="Level One",
         sub="for anyone, in one sitting", accent="#d9b25c"),
    dict(n=2, dir="2-the-manual", name="The Manual", kicker="Level Two",
         sub="for the one who will practise", accent="#c9a14a"),
    dict(n=3, dir="3-the-degree", name="The Degree", kicker="Level Three",
         sub="for the one who weighs", accent="#d9774a"),
    dict(n=4, dir="4-the-principle", name="The Principle", kicker="Level Four",
         sub="for the one who asks why", accent="#8f7fd0"),
    dict(n=5, dir="5-the-proof", name="The Proof and Its Limits", kicker="Level Five",
         sub="for the one who checks", accent="#3e8e89"),
    dict(n=6, dir="6-back-matter", name="Back Matter", kicker="After the levels",
         sub="the discipline, the lineage, the corrections, the checks", accent="#8c879a"),
]

# Units, in reading order.
#   (first page, last page, level, path inside book/, title, kind)
# kind: "level"   — the level's opening plate (and any intro); becomes README.md
#       "part"    — a part divider plate
#       "chapter" — a numbered chapter (plate + text)
#       "section" — any other unit of text
UNITS = [
    (2, 3, 0, "0-front/01-title-page.md", "Title Page", "section"),
    (4, 5, 0, "0-front/02-how-this-book-is-built.md", "How This Book Is Built", "section"),

    (8, 8, 1, "1-the-lines/README.md", "Level One · The Lines", "level"),
    (9, 9, 1, "1-the-lines/01-the-first-principle.md", "The First Principle", "section"),
    (10, 10, 1, "1-the-lines/02-the-stance.md", "The Stance", "section"),
    (11, 11, 1, "1-the-lines/03-in-plain-words.md", "In Plain Words", "section"),

    (12, 13, 2, "2-the-manual/README.md", "Level Two · The Manual", "level"),
    (14, 14, 2, "2-the-manual/part-1-the-ground.md", "Part I · The Ground", "part"),
    (15, 18, 2, "2-the-manual/01-the-three-and-the-zero.md", "The Three and the Zero", "chapter"),
    (19, 23, 2, "2-the-manual/02-the-given.md", "The Given", "chapter"),
    (24, 29, 2, "2-the-manual/03-attention.md", "Attention", "chapter"),
    (30, 34, 2, "2-the-manual/04-witness.md", "Witness", "chapter"),
    (35, 35, 2, "2-the-manual/part-2-the-practice.md", "Part II · The Practice", "part"),
    (36, 40, 2, "2-the-manual/05-name-the-binary.md", "Name the Binary", "chapter"),
    (41, 46, 2, "2-the-manual/06-construct-the-third.md", "Construct the Third", "chapter"),
    (47, 52, 2, "2-the-manual/07-own-the-ground.md", "Own the Ground", "chapter"),
    (53, 57, 2, "2-the-manual/08-keep-the-middle.md", "Keep the Middle", "chapter"),
    (58, 63, 2, "2-the-manual/09-refuse-the-waiting-room.md", "Refuse the Waiting Room", "chapter"),
    (64, 64, 2, "2-the-manual/part-3-the-weight.md", "Part III · The Weight", "part"),
    (65, 70, 2, "2-the-manual/10-the-asymmetry.md", "The Asymmetry", "chapter"),
    (71, 76, 2, "2-the-manual/11-continuity.md", "Continuity", "chapter"),
    (77, 82, 2, "2-the-manual/12-the-losable-claim.md", "The Losable Claim", "chapter"),
    (83, 83, 2, "2-the-manual/part-4-the-care.md", "Part IV · The Care", "part"),
    (84, 89, 2, "2-the-manual/13-empathy-as-catalyst.md", "Empathy as Catalyst", "chapter"),
    (90, 96, 2, "2-the-manual/14-the-inviolate.md", "The Inviolate", "chapter"),
    (97, 102, 2, "2-the-manual/15-the-long-reclamation.md", "The Long Reclamation", "chapter"),
    (103, 104, 2, "2-the-manual/16-the-fifteen-lines.md", "The Fifteen Lines", "section"),

    (105, 105, 3, "3-the-degree/README.md", "Level Three · The Degree", "level"),
    (106, 110, 3, "3-the-degree/16-the-degree.md", "The Degree", "chapter"),
    (111, 114, 3, "3-the-degree/17-the-weakest-link.md", "The Weakest Link", "chapter"),
    (115, 118, 3, "3-the-degree/18-act-crisp.md", "Act Crisp", "chapter"),
    (119, 120, 3, "3-the-degree/19-the-graded-audits.md", "The Graded Audits", "section"),

    (121, 121, 4, "4-the-principle/README.md", "Level Four · The Principle", "level"),
    (122, 125, 4, "4-the-principle/19-existence-is-sufficient.md", "Existence Is Sufficient", "chapter"),
    (126, 129, 4, "4-the-principle/20-three-relationships.md", "Three Relationships, Not Three Requirements", "chapter"),
    (130, 133, 4, "4-the-principle/21-change-without-erasure.md", "Change Without Erasure", "chapter"),
    (134, 137, 4, "4-the-principle/22-dignity-is-owed.md", "Dignity Is Owed, Respect Is Earned", "chapter"),

    (138, 138, 5, "5-the-proof/README.md", "Level Five · The Proof and Its Limits", "level"),
    (139, 140, 5, "5-the-proof/sophonticism/README.md", "Sophonticism: The Research Book", "section"),
    (141, 146, 5, "5-the-proof/sophonticism/1-ground.md", "Part I — Ground (§1–§4)", "section"),
    (147, 155, 5, "5-the-proof/sophonticism/2-the-established-bridges.md", "Part II — The Established Bridges (§5–§11)", "section"),
    (156, 171, 5, "5-the-proof/sophonticism/3-the-third-state-and-consequence.md", "Part III — The Third State and Consequence (§12–§17)", "section"),
    (172, 179, 5, "5-the-proof/sophonticism/4-the-frontier.md", "Part IV — The Frontier (§18–§22)", "section"),
    (180, 187, 5, "5-the-proof/sophonticism/5-appendices.md", "Appendices A–D", "section"),
    (188, 193, 5, "5-the-proof/23-the-program-preregistered.md", "The Program, Preregistered", "chapter"),
    (194, 197, 5, "5-the-proof/24-what-the-axiom-does-not-prove.md", "What the Axiom Does Not Prove", "chapter"),
    (198, 202, 5, "5-the-proof/25-beyond-logic.md", "Beyond Logic", "chapter"),

    (203, 204, 6, "6-back-matter/01-the-discipline-in-one-page.md", "The Discipline in One Page", "section"),
    (205, 207, 6, "6-back-matter/02-the-lineage.md", "The Lineage", "section"),
    (208, 209, 6, "6-back-matter/03-glossary-of-the-pure-terms.md", "Glossary of the Pure Terms", "section"),
    (210, 211, 6, "6-back-matter/04-corrections-and-open-accounts.md", "Corrections and Open Accounts", "section"),
    (212, 213, 6, "6-back-matter/05-the-checks.md", "The Checks", "section"),
    (214, 214, 6, "6-back-matter/06-colophon.md", "Colophon", "section"),
]

# Chapter numbers in words, as the book prints them on its plates.
CHAPTER_NUMBERS = {
    "01-the-three-and-the-zero": 1, "02-the-given": 2, "03-attention": 3, "04-witness": 4,
    "05-name-the-binary": 5, "06-construct-the-third": 6, "07-own-the-ground": 7,
    "08-keep-the-middle": 8, "09-refuse-the-waiting-room": 9, "10-the-asymmetry": 10,
    "11-continuity": 11, "12-the-losable-claim": 12, "13-empathy-as-catalyst": 13,
    "14-the-inviolate": 14, "15-the-long-reclamation": 15, "16-the-degree": 16,
    "17-the-weakest-link": 17, "18-act-crisp": 18, "19-existence-is-sufficient": 19,
    "20-three-relationships": 20, "21-change-without-erasure": 21, "22-dignity-is-owed": 22,
    "23-the-program-preregistered": 23, "24-what-the-axiom-does-not-prove": 24,
    "25-beyond-logic": 25,
}
