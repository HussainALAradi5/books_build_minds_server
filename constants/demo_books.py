"""Illustrative catalog records for repeatable local demos.

The added titles, creators, publishers, and ISBNs are fictional test data.
"""
from datetime import date

BOOKS = [
    ("The Midnight Library", "9780525559474", "Matt Haig", "Viking", date(2020, 9, 29), 7.50),
    ("Atomic Habits", "9780735211292", "James Clear", "Avery", date(2018, 10, 16), 8.90),
    ("The Alchemist", "9780062315007", "Paulo Coelho", "HarperOne", date(2014, 4, 15), 5.25),
    ("Educated", "9780399590504", "Tara Westover", "Random House", date(2018, 2, 20), 9.75),
    ("Deep Work", "9781455586691", "Cal Newport", "Grand Central", date(2016, 1, 5), 6.80),
    ("Sapiens", "9780062316097", "Yuval Noah Harari", "Harper", date(2015, 2, 10), 10.20),
    ("The Lantern Archive", "9799001000010", "Leila Rahman", "Crescent Quill Press", date(2023, 3, 14), 6.40),
    ("The Map of Small Wonders", "9799001000027", "Leila Rahman", "Crescent Quill Press", date(2024, 8, 6), 7.10),
    ("Tides of Glass", "9799001000034", "Omar Al Nasser", "Blue Harbor Editions", date(2022, 5, 17), 8.25),
    ("The Last Harbor Bell", "9799001000041", "Omar Al Nasser", "Blue Harbor Editions", date(2025, 1, 21), 5.90),
    ("After the Rain Market", "9799001000058", "Maya Chen", "Northline Books", date(2021, 11, 9), 6.75),
    ("A Quiet Geometry", "9799001000065", "Maya Chen", "Northline Books", date(2024, 2, 27), 9.30),
    ("Orbiting Home", "9799001000072", "Elias Hart", "Northline Books", date(2023, 6, 20), 10.50),
    ("The Paper Observatory", "9799001000089", "Elias Hart", "Northline Books", date(2025, 4, 8), 7.80),
    ("Gardens in the Sky", "9799001000096", "Amina Yusuf", "Crescent Quill Press", date(2020, 7, 7), 5.60),
    ("The City of Green Steps", "9799001000102", "Amina Yusuf", "Crescent Quill Press", date(2022, 9, 13), 8.40),
    ("Notes from Tomorrow", "9799001000119", "Nikhil Rao", "Blue Harbor Editions", date(2023, 10, 3), 11.25),
    ("The Listening Machine", "9799001000126", "Nikhil Rao", "Blue Harbor Editions", date(2025, 6, 10), 9.10),
]

DEMO_BOOK_CONDITIONS = {
    "9799001000010": "new", "9799001000027": "good",
    "9799001000034": "fair", "9799001000041": "good",
    "9799001000058": "new", "9799001000065": "damaged",
    "9799001000072": "good", "9799001000089": "fair",
    "9799001000096": "good", "9799001000102": "new",
    "9799001000119": "fair", "9799001000126": "damaged",
}

DEMO_BOOK_COPIES = {
    "9799001000010": 4, "9799001000027": 3,
    "9799001000034": 2, "9799001000041": 4,
    "9799001000058": 5, "9799001000065": 2,
    "9799001000072": 3, "9799001000089": 2,
    "9799001000096": 4, "9799001000102": 5,
    "9799001000119": 2, "9799001000126": 1,
}
