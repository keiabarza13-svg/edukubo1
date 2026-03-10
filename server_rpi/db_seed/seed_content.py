import sys
import os

# 1. Add the parent directory to the system path so we can find 'database.py'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import get_connection

def seed_stories():
    conn = get_connection()
    cursor = conn.cursor()
    
    # --- Stories ---
    stories = [
        {
            "title": "Si Pagong at si Matsing (The Turtle and the Monkey)",
            "grade_level": 1,
            "difficulty_level": 0.5, # Easy (Low Theta)
            "content": """
            Isang araw, nagkita sina Pagong at Matsing. Nakakita sila ng puno ng saging na palutang-lutang sa ilog.
            'Hatiin natin ang puno!' sabi ni Matsing. Kinuha ni Matsing ang taas na bahagi na may mga dahon dahil akala niya tutubo ito agad. Ibinigay niya kay Pagong ang ibabang bahagi na may ugat.
            Itinanim ni Pagong ang ugat at ito ay lumaki at namunga. Ang kay Matsing ay nalanta at namatay. 
            Umakyat si Matsing sa puno ni Pagong at kinain lahat ng saging! Pero nilagyan ni Pagong ng tinik ang puno. Aray! Nasaktan si Matsing pagbaba niya.
            """
        },
        {
            "title": "Ang Alamat ng Pinya (The Legend of the Pineapple)",
            "grade_level": 2,
            "difficulty_level": 1.0, # Medium
            "content": """
            Noong unang panahon, may isang batang babae na nagngangalang Pinang. Mahal siya ng kanyang ina, ngunit si Pinang ay tamad.
            Isang araw, nagkasakit ang kanyang ina. 'Pinang, ipagluto mo ako ng lugaw,' utos ng ina.
            'Hindi ko makita ang sandok!' sigaw ni Pinang, kahit hindi naman siya naghahanap.
            Nagalit ang kanyang ina at sumigaw, 'Sana ay magkaroon ka ng maraming mata para makita mo ang lahat ng bagay!'
            Pagkatapos noon, nawala si Pinang. Sa bakuran, may tumubong kakaibang halaman na hugis ulo at maraming mata. Tinawag itong 'Pinya'.
            """
        },
        {
            "title": "Ang Gamugamo at ang Lampara (The Moth and the Flame)",
            "grade_level": 3,
            "difficulty_level": 2.0, # Hard (High Theta)
            "content": """
            Isang gabi, nagkukwento ang inang gamugamo sa kanyang anak. Nakakita ang batang gamugamo ng isang lampara.
            'Huwag kang lalapit sa apoy,' babala ng ina. 'Ito ay maganda ngunit mapanganib.'
            Pero naakit ang batang gamugamo sa liwanag. Lumipad siya palapit nang palapit. 'Ang init ay masarap sa pakiramdam,' isip niya.
            Sa huli, nasunog ang kanyang pakpak at siya ay nahulog. Natutunan niya na hindi lahat ng nakakaakit ay mabuti.
            """
        }
    ]

    print("Seeding Database with Stories...")
    
    for story in stories:
        try:
            # Check if story already exists to prevent duplicates
            exists = cursor.execute("SELECT 1 FROM stories WHERE title = ?", (story['title'],)).fetchone()
            
            if not exists:
                cursor.execute("""
                    INSERT INTO stories (title, grade_level, difficulty_level, content)
                    VALUES (?, ?, ?, ?)
                """, (story['title'], story['grade_level'], story['difficulty_level'], story['content']))
                print(f"Added: {story['title']}")
            else:
                print(f"Skipped (Already exists): {story['title']}")
                
        except Exception as e:
            print(f"Error adding {story['title']}: {e}")

    conn.commit()
    conn.close()
    print("Database seeding complete!")

if __name__ == "__main__":
    seed_stories()