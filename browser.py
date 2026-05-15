import os
import sqlite3
import datetime
from pathlib import Path
import platform

def get_chrome_history():
    """Get Chrome browser history"""
    history_path = ""
    
    if platform.system() == "Windows":
        history_path = os.path.join(os.environ['USERPROFILE'], 
                                   'AppData\\Local\\Google\\Chrome\\User Data\\Default\\History')
    elif platform.system() == "Darwin":  # macOS
        history_path = os.path.join(os.environ['HOME'], 
                                   'Library/Application Support/Google/Chrome/Default/History')
    elif platform.system() == "Linux":
        history_path = os.path.join(os.environ['HOME'], 
                                   '.config/google-chrome/Default/History')
    
    if not os.path.exists(history_path):
        print("Chrome history database not found")
        return []
    
    # Create a copy to avoid database lock issues
    temp_path = os.path.join(os.path.dirname(history_path), "history_copy.db")
    try:
        import shutil
        shutil.copy2(history_path, temp_path)
    except Exception as e:
        print(f"Error copying Chrome history: {e}")
        return []
    
    try:
        conn = sqlite3.connect(temp_path)
        cursor = conn.cursor()
        
        # Query to get URL, title, and visit time
        query = "SELECT url, title, datetime(last_visit_time/1000000-11644473600, 'unixepoch', 'localtime') AS visit_date FROM urls ORDER BY last_visit_time DESC"
        cursor.execute(query)
        
        history = cursor.fetchall()
        conn.close()
        
        # Clean up temp file
        os.remove(temp_path)
        
        return history
    except Exception as e:
        print(f"Error reading Chrome history: {e}")
        return []

def get_firefox_history():
    """Get Firefox browser history"""
    profiles_path = ""
    
    if platform.system() == "Windows":
        profiles_path = os.path.join(os.environ['APPDATA'], 
                                    'Mozilla\\Firefox\\Profiles')
    elif platform.system() == "Darwin":  # macOS
        profiles_path = os.path.join(os.environ['HOME'], 
                                    'Library/Application Support/Firefox/Profiles')
    elif platform.system() == "Linux":
        profiles_path = os.path.join(os.environ['HOME'], 
                                    '.mozilla/firefox')
    
    if not os.path.exists(profiles_path):
        print("Firefox profiles directory not found")
        return []
    
    # Find the default profile
    profile_dir = None
    for item in os.listdir(profiles_path):
        if item.endswith('.default') or item.endswith('.default-release'):
            profile_dir = os.path.join(profiles_path, item)
            break
    
    if not profile_dir:
        print("Firefox default profile not found")
        return []
    
    history_path = os.path.join(profile_dir, 'places.sqlite')
    
    if not os.path.exists(history_path):
        print("Firefox history database not found")
        return []
    
    # Create a copy to avoid database lock issues
    temp_path = os.path.join(profile_dir, "places_copy.db")
    try:
        import shutil
        shutil.copy2(history_path, temp_path)
    except Exception as e:
        print(f"Error copying Firefox history: {e}")
        return []
    
    try:
        conn = sqlite3.connect(temp_path)
        cursor = conn.cursor()
        
        # Query to get URL, title, and visit time
        query = "SELECT url, title, datetime(visit_date/1000000, 'unixepoch', 'localtime') AS visit_date FROM moz_places JOIN moz_historyvisits ON moz_places.id = moz_historyvisits.place_id ORDER BY visit_date DESC"
        cursor.execute(query)
        
        history = cursor.fetchall()
        conn.close()
        
        # Clean up temp file
        os.remove(temp_path)
        
        return history
    except Exception as e:
        print(f"Error reading Firefox history: {e}")
        return []

def get_safari_history():
    """Get Safari browser history (macOS only)"""
    if platform.system() != "Darwin":
        print("Safari is only available on macOS")
        return []
    
    history_path = os.path.join(os.environ['HOME'], 
                               'Library/Safari/History.db')
    
    if not os.path.exists(history_path):
        print("Safari history database not found")
        return []
    
    # Create a copy to avoid database lock issues
    temp_path = os.path.join(os.path.dirname(history_path), "history_copy.db")
    try:
        import shutil
        shutil.copy2(history_path, temp_path)
    except Exception as e:
        print(f"Error copying Safari history: {e}")
        return []
    
    try:
        conn = sqlite3.connect(temp_path)
        cursor = conn.cursor()
        
        # Query to get URL, title, and visit time
        query = "SELECT url, title, datetime(visit_time + 978307200, 'unixepoch', 'localtime') AS visit_date FROM history_visits JOIN history_items ON history_visits.history_item = history_items.id ORDER BY visit_time DESC"
        cursor.execute(query)
        
        history = cursor.fetchall()
        conn.close()
        
        # Clean up temp file
        os.remove(temp_path)
        
        return history
    except Exception as e:
        print(f"Error reading Safari history: {e}")
        return []

def get_edge_history():
    """Get Edge browser history"""
    history_path = ""
    
    if platform.system() == "Windows":
        history_path = os.path.join(os.environ['USERPROFILE'], 
                                   'AppData\\Local\\Microsoft\\Edge\\User Data\\Default\\History')
    elif platform.system() == "Darwin":  # macOS
        history_path = os.path.join(os.environ['HOME'], 
                                   'Library/Application Support/Microsoft Edge/Default/History')
    elif platform.system() == "Linux":
        history_path = os.path.join(os.environ['HOME'], 
                                   '.config/microsoft-edge/Default/History')
    
    if not os.path.exists(history_path):
        print("Edge history database not found")
        return []
    
    # Create a copy to avoid database lock issues
    temp_path = os.path.join(os.path.dirname(history_path), "history_copy.db")
    try:
        import shutil
        shutil.copy2(history_path, temp_path)
    except Exception as e:
        print(f"Error copying Edge history: {e}")
        return []
    
    try:
        conn = sqlite3.connect(temp_path)
        cursor = conn.cursor()
        
        # Query to get URL, title, and visit time
        query = "SELECT url, title, datetime(last_visit_time/1000000-11644473600, 'unixepoch', 'localtime') AS visit_date FROM urls ORDER BY last_visit_time DESC"
        cursor.execute(query)
        
        history = cursor.fetchall()
        conn.close()
        
        # Clean up temp file
        os.remove(temp_path)
        
        return history
    except Exception as e:
        print(f"Error reading Edge history: {e}")
        return []

def display_history(history, limit=50):
    """Display browser history in a formatted table"""
    if not history:
        print("No history found")
        return
    
    print(f"{'URL':<60} {'Title':<50} {'Visit Date':<20}")
    print("-" * 130)
    
    for i, (url, title, visit_date) in enumerate(history[:limit]):
        # Truncate long URLs and titles
        url = url[:57] + "..." if len(url) > 60 else url
        title = title[:47] + "..." if len(title) > 50 else title
        
        print(f"{url:<60} {title:<50} {visit_date:<20}")

def main():
    """Main function to run the browser history viewer"""
    while True:
        print("\nBrowser History Viewer")
        print("1. View Chrome history")
        print("2. View Firefox history")
        print("3. View Safari history (macOS only)")
        print("4. View Edge history")
        print("5. Exit")
        
        choice = input("Enter your choice (1-5): ")
        
        if choice == '1':
            history = get_chrome_history()
            display_history(history)
        elif choice == '2':
            history = get_firefox_history()
            display_history(history)
        elif choice == '3':
            history = get_safari_history()
            display_history(history)
        elif choice == '4':
            history = get_edge_history()
            display_history(history)
        elif choice == '5':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()