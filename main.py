import json
import os
import re
import sqlite3 as sq3
from time import sleep


MENU = """
Akiko's DB
==========
[a] Artist search
[s] Song search
[x] Exit
"""


def clear():
    os.system("cls" if os.name == "nt" else "clear")
    return None


def display2search(disp):
    name = re.sub(r'\s+', '_', disp)
    return re.sub(r'\W', '', name, re.A).lower()

def display_prompt(disp, prompt):
    print(disp)
    return display2search(input(prompt))


if __name__ == "__main__":
    con = sq3.connect("akikos.db")
    cur = con.cursor()
    try:
        # Setup
        with con:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS artist(
                    id INTEGER PRIMARY KEY,
                    display TEXT,
                    search TEXT
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS song(
                    id INTEGER PRIMARY KEY,
                    artist_id INTEGER,
                    display TEXT,
                    search TEXT,
                    
                    FOREIGN KEY(artist_id) REFERENCES artist(id)
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_artist ON artist(search)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_song ON song(search)")
            cur.execute("SELECT COUNT(*) FROM artist")
            a_count = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM song")
            s_count = cur.fetchone()[0]
            if a_count == 0 or s_count == 0:
                cur.execute("DELETE FROM artist")
                cur.execute("DELETE FROM song")
                with open('akikos.json') as f:
                    for k, v in json.load(f).items():
                        cur.execute("INSERT INTO artist(display, search) VALUES (?, ?)", [k, display2search(k)])
                        a_id = cur.lastrowid
                        for val in v:
                            cur.execute("INSERT INTO song(artist_id, display, search) VALUES (?, ?, ?)", [a_id, val, display2search(val)])
        while True:
            inp = display_prompt(MENU, "\nChoose an option:  ")
            if inp == "a":
                while True:
                    clear()
                    inp = input("Search for an artist or press enter to return to main menu:  ")
                    if inp == "":
                        break
                    print("\nResults below:\n")
                    with con:
                        cur.execute("""
                            SELECT
                                a.id,
                                a.display
                            FROM artist AS a
                            WHERE a.search LIKE ?
                        """, [f"%{display2search(inp)}%"])
                        artists = cur.fetchall()
                        for i, artist in enumerate(artists):
                            print(f"[{i+1}]  {artist[1]}")
                    inp = display2search(input("\nEnter a number to see songs by artist or press enter to clear search:  "))
                    if re.match('\d+$', inp):
                        choice = int(inp) - 1
                        if -1 < choice < len(artists):
                            clear()
                            print(f"Songs by {artists[choice][1]} below; press enter to return to artist search.\n")
                            with con:
                                cur.execute("""
                                    SELECT
                                        s.display
                                    FROM song AS s
                                    WHERE s.artist_id LIKE ?
                                """, [artists[choice][0]])
                                for result in cur.fetchall():
                                    print(f"\"{result[0]}\"")
                            input()
            elif inp == "s":
                while True:
                    clear()
                    inp = input("Search for a song or press enter to return to main menu:  ")
                    if inp == "":
                        break
                    print("\nResults below; press enter to clear search:\n")
                    with con:
                        cur.execute("""
                            SELECT
                                s.display,
                                a.display
                            FROM song AS s
                            INNER JOIN artist AS a ON s.artist_id = a.id
                            WHERE s.search LIKE ?
                        """, [f"%{display2search(inp)}%"])
                        for result in cur.fetchall():
                            print(f"\"{result[0]}\" by {result[1]}")
                    input()
            elif inp == "x":
                break
            else:
                input("\nBad input; try again.")
            clear()
        clear()
        print("Exiting application in three seconds...")
        sleep(3)
    finally:
        cur.close()
        con.close()
