import os
import time
import shutil
import io
import glob
from PIL import Image, ImageGrab
import win32clipboard
import win32con
import win32api
import win32gui
from datetime import datetime
import struct

class ScreenshotViewer:
    def __init__(self):
        # Common Windows screenshot locations
        self.screenshot_paths = [
            os.path.expanduser("~/Desktop"),
            os.path.expanduser("~/Pictures/Screenshots"),
            os.path.expanduser("~/Documents/Screenshots"),
            os.path.expanduser("~/OneDrive/Pictures/Screenshots"),
            os.path.join(os.environ.get('TEMP', ''), 'Screenshots')
        ]
        
        # Windows 10/11 default screenshot location
        self.win_screenshot_path = os.path.expanduser("~/Pictures/Screenshots")
        
    def find_screenshots(self):
        """Find all screenshot files in common locations"""
        screenshots = []
        
        # Common screenshot file extensions
        extensions = ['*.png', '*.jpg', '*.jpeg', '*.bmp', '*.gif']
        
        for path in self.screenshot_paths:
            if os.path.exists(path):
                for ext in extensions:
                    for file in glob.glob(os.path.join(path, ext)):
                        # Check if filename looks like a screenshot
                        filename = os.path.basename(file).lower()
                        if any(keyword in filename for keyword in ['screenshot', 'screen', 'capture', 'snip']):
                            screenshots.append(file)
        
        return screenshots
    
    def get_latest_screenshot(self):
        """Get the most recent screenshot"""
        screenshots = self.find_screenshots()
        
        if not screenshots:
            return None
        
        # Sort by modification time
        screenshots.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        return screenshots[0]
    
    def view_screenshot(self, path):
        """Open a screenshot with the default viewer"""
        try:
            os.startfile(path)
            return True
        except Exception as e:
            print(f"Error opening screenshot: {e}")
            return False
    
    def list_screenshots(self):
        """List all screenshots with details"""
        screenshots = self.find_screenshots()
        
        if not screenshots:
            print("No screenshots found in common locations.")
            return []
        
        print(f"Found {len(screenshots)} screenshots:")
        print(f"{'#':<3} {'Name':<40} {'Size':<10} {'Modified':<20}")
        print("-" * 75)
        
        for i, path in enumerate(screenshots, 1):
            name = os.path.basename(path)
            size = os.path.getsize(path) / (1024 * 1024)  # Size in MB
            modified = datetime.fromtimestamp(os.path.getmtime(path)).strftime('%Y-%m-%d %H:%M:%S')
            
            print(f"{i:<3} {name[:40]:<40} {size:.2f} MB {modified:<20}")
        
        return screenshots

class ClipboardManager:
    def __init__(self):
        self.clipboard_history = []
        
    def get_clipboard_text(self):
        """Get text content from clipboard"""
        try:
            win32clipboard.OpenClipboard()
            if win32clipboard.IsClipboardFormatAvailable(win32con.CF_TEXT):
                data = win32clipboard.GetClipboardData(win32con.CF_TEXT)
                return data.decode('utf-8', errors='ignore')
            elif win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
                data = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
                return data
            return None
        except Exception as e:
            print(f"Error getting clipboard text: {e}")
            return None
        finally:
            win32clipboard.CloseClipboard()
    
    def set_clipboard_text(self, text):
        """Set text content to clipboard"""
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(text, win32con.CF_UNICODETEXT)
            return True
        except Exception as e:
            print(f"Error setting clipboard text: {e}")
            return False
        finally:
            win32clipboard.CloseClipboard()
    
    def get_clipboard_image(self):
        """Get image content from clipboard"""
        try:
            win32clipboard.OpenClipboard()
            if win32clipboard.IsClipboardFormatAvailable(win32con.CF_DIB):
                data = win32clipboard.GetClipboardData(win32con.CF_DIB)
                
                # Parse the DIB header to get image dimensions
                dib_header = data[0:36]  # First 36 bytes contain header info
                width = struct.unpack('<I', dib_header[4:8])[0]
                height = struct.unpack('<I', dib_header[8:12])[0]
                
                # Extract the actual image data
                image_data = data[36:]  # Skip the header
                
                # Create PIL Image from raw data
                image = Image.frombytes('RGB', (width, height), image_data, 'raw', 'BGRX', 0, 1)
                return image
            return None
        except Exception as e:
            print(f"Error getting clipboard image: {e}")
            return None
        finally:
            win32clipboard.CloseClipboard()
    
    def set_clipboard_image(self, image_path):
        """Set image content to clipboard from file"""
        try:
            image = Image.open(image_path)
            
            # Convert to BMP format for clipboard
            output = io.BytesIO()
            image.save(output, 'BMP')
            data = output.getvalue()
            
            # Remove the BMP header (first 14 bytes) to get DIB data
            dib_data = data[14:]
            
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32con.CF_DIB, dib_data)
            return True
        except Exception as e:
            print(f"Error setting clipboard image: {e}")
            return False
        finally:
            win32clipboard.CloseClipboard()
    
    def save_clipboard_image(self, output_path):
        """Save clipboard image to file"""
        try:
            image = self.get_clipboard_image()
            if image:
                image.save(output_path)
                print(f"Clipboard image saved to: {output_path}")
                return True
            else:
                print("No image in clipboard")
                return False
        except Exception as e:
            print(f"Error saving clipboard image: {e}")
            return False
    
    def clear_clipboard(self):
        """Clear the clipboard"""
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            return True
        except Exception as e:
            print(f"Error clearing clipboard: {e}")
            return False
        finally:
            win32clipboard.CloseClipboard()
    
    def get_clipboard_content_type(self):
        """Check what type of content is in the clipboard"""
        try:
            win32clipboard.OpenClipboard()
            formats = []
            
            # Check for text
            if win32clipboard.IsClipboardFormatAvailable(win32con.CF_TEXT) or \
               win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
                formats.append("Text")
            
            # Check for image
            if win32clipboard.IsClipboardFormatAvailable(win32con.CF_DIB):
                formats.append("Image")
            
            # Check for file list
            if win32clipboard.IsClipboardFormatAvailable(win32con.CF_HDROP):
                formats.append("Files")
            
            win32clipboard.CloseClipboard()
            return formats
        except Exception as e:
            print(f"Error checking clipboard content: {e}")
            return []
    
    def display_clipboard_content(self):
        """Display the current content of the clipboard"""
        content_types = self.get_clipboard_content_type()
        
        if not content_types:
            print("Clipboard is empty")
            return
        
        print(f"Clipboard contains: {', '.join(content_types)}")
        
        if "Text" in content_types:
            text = self.get_clipboard_text()
            if text:
                print(f"Text content: {text[:100]}{'...' if len(text) > 100 else ''}")
        
        if "Image" in content_types:
            print("Clipboard contains an image")
            save_choice = input("Save clipboard image? (y/n): ")
            if save_choice.lower() == 'y':
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_path = os.path.expanduser(f"~/Desktop/clipboard_image_{timestamp}.png")
                self.save_clipboard_image(output_path)
        
        if "Files" in content_types:
            try:
                win32clipboard.OpenClipboard()
                files = win32clipboard.GetClipboardData(win32con.CF_HDROP)
                print(f"Clipboard contains {len(files)} file(s):")
                for file in files:
                    print(f"  {file}")
                win32clipboard.CloseClipboard()
            except Exception as e:
                print(f"Error getting file list: {e}")
    
    def monitor_clipboard(self, interval=1, duration=60):
        """Monitor clipboard changes over time"""
        print(f"Monitoring clipboard for {duration} seconds...")
        
        end_time = time.time() + duration
        last_content = self.get_clipboard_text()
        last_image = self.get_clipboard_image() is not None
        
        while time.time() < end_time:
            current_text = self.get_clipboard_text()
            has_image = self.get_clipboard_image() is not None
            
            text_changed = current_text and current_text != last_content
            image_changed = has_image != last_image
            
            if text_changed:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"[{timestamp}] Clipboard text changed: {current_text[:50]}...")
                self.clipboard_history.append({
                    'type': 'text',
                    'content': current_text,
                    'timestamp': timestamp
                })
                last_content = current_text
            
            if image_changed:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"[{timestamp}] Clipboard image {'added' if has_image else 'removed'}")
                self.clipboard_history.append({
                    'type': 'image',
                    'action': 'added' if has_image else 'removed',
                    'timestamp': timestamp
                })
                last_image = has_image
            
            time.sleep(interval)
        
        print("Clipboard monitoring stopped.")
        return self.clipboard_history


def main():
    """Main function to run the clipboard and screenshot viewer"""
    clipboard_mgr = ClipboardManager()
    screenshot_viewer = ScreenshotViewer()
    
    while True:
        print("\nClipboard & Screenshot Manager")
        print("1. Display clipboard content")
        print("2. List screenshots")
        print("3. View latest screenshot")
        print("4. Monitor clipboard changes")
        print("5. Clear clipboard")
        print("6. Get clipboard content type")
        print("7. Exit")
        
        choice = input("Enter your choice (1-7): ")
        
        if choice == '1':
            clipboard_mgr.display_clipboard_content()
        elif choice == '2':
            screenshot_viewer.list_screenshots()
        elif choice == '3':
            latest = screenshot_viewer.get_latest_screenshot()
            if latest:
                print(f"Latest screenshot: {latest}")
                screenshot_viewer.view_screenshot(latest)
            else:
                print("No screenshots found.")
        elif choice == '4':
            duration = input("Enter monitoring duration in seconds (default 60): ")
            try:
                duration = int(duration) if duration else 60
            except ValueError:
                duration = 60
            clipboard_mgr.monitor_clipboard(interval=1, duration=duration)
        elif choice == '5':
            if clipboard_mgr.clear_clipboard():
                print("Clipboard cleared.")
        elif choice == '6':
            content_types = clipboard_mgr.get_clipboard_content_type()
            if content_types:
                print(f"Clipboard contains: {', '.join(content_types)}")
            else:
                print("Clipboard is empty.")
        elif choice == '7':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()