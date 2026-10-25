import os
import re
import logging

logger = logging.getLogger("AutoGrader")

class ReactNativeParser:
    def __init__(self, folder_path):
        self.folder_path = folder_path
        self.raw_code = ""
        self.full_code = ""
        self.folder_count = 0
        self.file_count = 0
        self._load_files()

    def _file_priority(self, rel_path: str) -> tuple:
        """Prioritizes main entry points and screen components before utility/data files."""
        filename = os.path.basename(rel_path).lower()
        if filename in {'app.tsx', 'app.jsx', 'app.ts', 'app.js', '_layout.tsx', '_layout.js', 'index.tsx', 'index.js'}:
            return (0, rel_path.lower())
        if any(folder in rel_path.lower() for folder in ('screens', 'app', 'components')):
            return (1, rel_path.lower())
        return (2, rel_path.lower())

    def _load_files(self):
        """Recursively reads React Native code files, excluding build/config clutter."""
        ignored_dirs = {'node_modules', '.expo', 'android', 'ios', 'build', 'dist', '.git'}
        ignored_files = {'metro.config.js', 'babel.config.js', 'eslintrc.js', 'app.json', 'package.json', 'package-lock.json'}

        matched_files = []
        for root, dirs, files in os.walk(self.folder_path):
            dirs[:] = [d for d in dirs if d not in ignored_dirs]
            self.folder_count += 1
                
            for file in files:
                if file.endswith(('.js', '.jsx', '.ts', '.tsx')) and file not in ignored_files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, self.folder_path)
                    matched_files.append((rel_path, full_path))

        matched_files.sort(key=lambda item: self._file_priority(item[0]))

        file_contents = []
        for rel_path, file_path in matched_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.full_code += f"\n\n// --- File: {rel_path} ---\n" + content
                    file_contents.append((rel_path, content))
                    self.file_count += 1
            except Exception as e:
                logger.warning(f"Could not read {rel_path}: {e}")

        # Build AI prompt payload: ensure every file gets represented if total > 8,000 chars
        max_total_chars = 8000
        if len(self.full_code) <= max_total_chars:
            self.raw_code = self.full_code
        else:
            manifest = "// Submitted Files: " + ", ".join(r for r, _ in file_contents) + "\n"
            per_file_budget = max(800, (max_total_chars - len(manifest)) // max(1, len(file_contents)))
            chunks = [manifest]
            for rel_path, content in file_contents:
                header = f"\n// --- File: {rel_path} ---\n"
                if len(content) > per_file_budget:
                    chunks.append(header + content[:per_file_budget] + "\n// [File truncated...]")
                else:
                    chunks.append(header + content)
            self.raw_code = "".join(chunks)[:max_total_chars] + "\n\n// [NOTE: Source code truncated for length]"

    def _strip_comments(self, text: str) -> str:
        """Removes /* ... */ block comments and // single-line comments without breaking URLs."""
        return re.sub(r'/\*[\s\S]*?\*/|(?<!:)//.*', '', text)

    def check_objective_rubric(self, rubric_text: str = "") -> dict:
        """Scans uncommented code for mandatory syntax flags filtered to the active rubric."""
        code = self._strip_comments(self.full_code)
        rubric_lower = rubric_text.lower()

        all_flags = {
            # Core & Styling (Activity 2)
            "has_core_ui": bool(re.search(r'<\s*(View|Text|Image|ScrollView|SafeAreaView)\b', code)),
            "has_stylesheet": bool(re.search(r'\b(StyleSheet\.create|styled|tw`|className=)\b', code)),
            "has_flexbox_props": bool(re.search(r'\b(flex|flexDirection|justifyContent|alignItems)\s*:', code)) or bool(re.search(r'\bclassName=', code)),
            "has_inline_style_objects": bool(re.search(r'style=\{\{\s*[a-zA-Z]+', code)),

            # Lists & State (Activity 3)
            "has_usestate": bool(re.search(r'\b(useState|useReducer|create\(|proxy\()\b', code)),
            "has_flatlist": bool(re.search(r'<\s*(FlatList|FlashList|SectionList|RecyclerListView)\b', code)),
            "has_textinput": bool(re.search(r'<\s*TextInput\b', code)),
            "has_touchable": bool(re.search(r'<\s*(TouchableOpacity|Pressable|TouchableHighlight|Button)\b', code)),

            # Navigation (Activity 4)
            "has_nav_container": bool(re.search(r'\b(NavigationContainer|ExpoRoot|createNativeStackNavigator|Stack\.Navigator)\b', code)),
            "has_navigate": bool(re.search(r'\b(navigate|push|replace)\s*\(', code)) or bool(re.search(r'<\s*Link\b', code)),
            "has_goback": bool(re.search(r'\b(goBack|back)\s*\(', code)),
            "has_route_params": bool(re.search(r'\b(route\.params|useLocalSearchParams|useGlobalSearchParams)\b', code)),

            # Future Lessons (Activities 5, 6, 7)
            "has_data_fetch": bool(re.search(r'\b(fetch|axios|useQuery|useSWR)\b', code)),
            "has_local_storage": bool(re.search(r'\b(AsyncStorage|MMKV|SQLite|Watermelon)\b', code))
        }

        # Filter flags so the AI only sees flags relevant to the loaded rubric
        if "activity 2" in rubric_lower or "static single-page" in rubric_lower:
            keys = ["has_core_ui", "has_stylesheet", "has_flexbox_props", "has_inline_style_objects"]
        elif "activity 3" in rubric_lower or "dynamic list" in rubric_lower:
            keys = ["has_core_ui", "has_stylesheet", "has_usestate", "has_flatlist", "has_textinput", "has_touchable"]
        elif "activity 4" in rubric_lower or "multi-screen navigation" in rubric_lower:
            keys = ["has_core_ui", "has_stylesheet", "has_nav_container", "has_navigate", "has_goback", "has_route_params"]
        else:
            keys = list(all_flags.keys())

        filtered_flags = {k: all_flags[k] for k in keys}
        logger.debug(f"Parser extracted {self.file_count} files ({self.folder_count} folders). Sent chars: {len(self.raw_code)}")
        logger.debug(f"Filtered Parser Flags: {filtered_flags}")
        return filtered_flags