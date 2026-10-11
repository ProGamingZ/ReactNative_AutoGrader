import os
import re

class ReactNativeParser:
    def __init__(self, folder_path):
        self.folder_path = folder_path
        self.raw_code = ""
        self.file_count = 0
        self._load_files()

    def _load_files(self):
        """Recursively reads all React Native code files in the student's folder."""
        for root, dirs, files in os.walk(self.folder_path):
            # Ignore heavy/unnecessary folders if students accidentally uploaded them
            if 'node_modules' in dirs:
                dirs.remove('node_modules')
            if '.expo' in dirs:
                dirs.remove('.expo')
                
            for file in files:
                if file.endswith(('.js', '.jsx', '.ts', '.tsx')):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # Append the filename as a header so the AI knows which file is which later
                            self.raw_code += f"\n\n// --- File: {file} ---\n" + content
                            self.file_count += 1
                    except Exception as e:
                        print(f"Could not read {file}: {e}")

    def check_objective_rubric(self):
        """
        Scans the extracted code for mandatory React Native syntax.
        Returns a dictionary of boolean flags.
        """
        code = self.raw_code
        
        # We use regex \b (word boundaries) and <\s* (optional spaces) to catch different coding styles
        return {
            "has_usestate": bool(re.search(r'\buseState\b', code)),
            "has_flatlist": bool(re.search(r'<\s*FlatList\b', code)),
            "has_textinput": bool(re.search(r'<\s*TextInput\b', code)),
            "has_touchable": bool(re.search(r'<\s*(TouchableOpacity|Pressable|TouchableHighlight)\b', code)),
            "has_stylesheet": bool(re.search(r'\bStyleSheet\.create\b', code)),
            "has_navigation": bool(re.search(r'\bnavigate\s*\(', code)) or bool(re.search(r'\bNavigationContainer\b', code)),
            "has_goback": bool(re.search(r'\bgoBack\s*\(', code))
        }