import os
import re
import logging
logger = logging.getLogger("AutoGrader")
class ReactNativeParser:
    def __init__(self, folder_path):
        self.folder_path = folder_path
        self.raw_code = ""
        self.file_count = 0
        self._load_files()

    def _load_files(self):
        """Recursively reads React Native code files, excluding build/config clutter."""
        # Folders to completely ignore
        ignored_dirs = {'node_modules', '.expo', 'android', 'ios', 'build', 'dist', '.git'}
        # Config files that add prompt weight without grading value
        ignored_files = {'metro.config.js', 'babel.config.js', 'eslintrc.js', 'app.json', 'package.json', 'package-lock.json'}

        for root, dirs, files in os.walk(self.folder_path):
            # Prune ignored directories in-place
            dirs[:] = [d for d in dirs if d not in ignored_dirs]
                
            for file in files:
                if file.endswith(('.js', '.jsx', '.ts', '.tsx')) and file not in ignored_files:
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            self.raw_code += f"\n\n// --- File: {file} ---\n" + content
                            self.file_count += 1
                    except Exception as e:
                        print(f"Could not read {file}: {e}")

        # CAP PROMPT SIZE: Limit raw_code to 12,000 chars (~3,000 tokens) to ensure fast CPU inference
        if len(self.raw_code) > 12000:
            self.raw_code = self.raw_code[:12000] + "\n\n// [NOTE: Source code truncated for length]"

    def check_objective_rubric(self):
        """Scans code for mandatory syntax flags, embracing modern community alternatives."""
        code = self.raw_code
        flags = {
            # Activity 2: Styling (Accepts StyleSheet, styled-components, NativeWind/Tailwind, Tamagui)
            "has_core_ui": bool(re.search(r'<\s*(View|Text|Image|ScrollView)\b', code)),
            "has_stylesheet": bool(re.search(r'\b(StyleSheet\.create|styled|tw`|className=)\b', code)),
            
            # Activity 3: Lists & State (Accepts useState, useReducer, Zustand, Valtio, MobX)
            "has_usestate": bool(re.search(r'\b(useState|useReducer|create\(|proxy\()\b', code)),
            # Accepts FlatList, FlashList (Shopify), SectionList, or RecyclerListView
            "has_flatlist": bool(re.search(r'<\s*(FlatList|FlashList|SectionList|RecyclerListView)\b', code)),
            "has_textinput": bool(re.search(r'<\s*TextInput\b', code)),
            "has_touchable": bool(re.search(r'<\s*(TouchableOpacity|Pressable|TouchableHighlight|Button)\b', code)),
            
            # Activity 4: Navigation (Accepts React Navigation OR Expo Router)
            "has_nav_container": bool(re.search(r'\b(NavigationContainer|ExpoRoot|Stack)\b', code)),
            "has_navigate": bool(re.search(r'\b(navigate|push|replace)\s*\(', code)) or bool(re.search(r'<\s*Link\b', code)),
            "has_goback": bool(re.search(r'\b(goBack|back)\s*\(', code)),
            "has_route_params": bool(re.search(r'\b(route\.params|useLocalSearchParams|useGlobalSearchParams)\b', code)),

            # FUTURE PROOFING (Lessons 6, 7, 8)
            # Fetching: Native fetch, Axios, or React Query / SWR
            "has_data_fetch": bool(re.search(r'\b(fetch|axios|useQuery|useSWR)\b', code)),
            # Storage: AsyncStorage, MMKV, SQLite, or WatermelonDB
            "has_local_storage": bool(re.search(r'\b(AsyncStorage|MMKV|SQLite|Watermelon)\b', code))
        }
        
        logger.debug(f"Parser extracted {self.file_count} files. Total chars: {len(self.raw_code)}")
        logger.debug(f"Parser Flags: {flags}")
        return flags