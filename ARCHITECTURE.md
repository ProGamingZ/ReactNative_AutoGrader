# Mobile Programming Auto-Grader (React Native)
**Project Overview:** A desktop application designed to automate the grading of React Native assignments (JavaScript/TypeScript). The app scans student submissions, evaluates code logic and UI aesthetics against specific rubrics, and generates an Excel report with scores and personalized AI feedback.

## 1. Core Architecture: The Hybrid Approach
The system uses a hybrid grading mechanism to balance 100% accuracy on objective requirements with qualitative analysis for design choices.

*   **Deterministic Parsing (AST/Regex):** Evaluates objective criteria (e.g., "Did the student use `<FlatList>`, `useState`, and `navigation.navigate()`?"). Ensures accurate baseline scoring without AI hallucination.
*   **Offline AI (Local LLM via Ollama):** Evaluates subjective and qualitative criteria (e.g., code cleanliness, Flexbox logic for UI aesthetics) and generates actionable feedback.

## 2. Tech Stack
*   **Core Logic & UI:** Python
    *   *UI Framework:* `CustomTkinter` or `PyQt` (Minimalist desktop interface).
    *   *Data Handling:* `pandas` and `openpyxl` (Reading attendance sheets, generating report sheets).
    *   *String Matching:* `thefuzz` (Fuzzy matching for matching student folders to Excel names).
*   **Code Parsing:** Native Python regex engine (`re`) with comment stripping, entry-point file prioritization (`App.tsx`, `index.js`, `_layout.tsx`), and directory/file counters.
*   **Offline AI Engine:** Local LLM (`phi3` or `llama3`) running via `Ollama` with native JSON mode (`format="json"`).

## 3. Application Workflow
1.  **Input Configuration:** User selects the Markdown grading rubric (`Activity2_Rubric.md`, `Activity3_Rubric.md`, or `Activity4_Rubric.md`), uploads the class list Excel file (`DATA` sheet, starting at Row 3), and selects the extracted LMS submissions folder and output directory.
2.  **Exclusive Folder Matching:** `StudentFolderMatcher` uses fuzzy matching (`thefuzz` `token_set_ratio` $\ge 80$) to map LMS folders to Excel student names, locking each matched folder so it cannot be claimed twice.
3.  **Prioritized Code Parsing:** `ReactNativeParser` counts submitted folders and valid `.js`/`.jsx`/`.ts`/`.tsx` files (`Folders/Files` ratio), strips comments, scans the full codebase for objective syntax flags (including modern alternatives like `FlashList`, `Zustand`, and `Expo Router`), and caps the LLM prompt payload at 12,000 characters with entry points loaded first.
4.  **AI Evaluation:** `AIGrader` populates integer scores strictly into the pre-extracted Markdown rubric columns and generates telegraphic feedback capped at 20 words or less.
5.  **Report Generation:** `ExcelReporter` writes the results into a formatted `.xlsx` workbook (`GRADES` sheet).

## 4. AI Prompting Strategy
To ensure consistent and reliable grading from the offline AI, the application enforces the following constraints:
*   **Pre-Allocated Rubric Schema:** Rubric category columns are parsed directly from the selected `.md` file prior to inference. The AI is restricted to filling integer values for those exact keys and cannot create new columns.
*   **Native JSON Enforcement:** Ollama is invoked with `format="json"`, `temperature: 0.1`, and `num_predict: 750` to prevent syntax errors or mid-response truncation.
*   **Hard 20-Word Feedback Cap:** Both the system prompt and Python post-processing strictly cap `AI Feedback` at $\le 20$ words for fast, telegraphic grading explanations.

## 5. Excel Output Format
The generated Excel file preserves the first 5 roster columns (`NO`, `ID`, `NAME`, `PROGRAM`, `YEAR`), followed by `Folder & Files` (`Folders/Files` count), the pre-allocated Markdown rubric columns, `Final Score`, and `AI Feedback`:

| NO | ID | NAME | PROGRAM | YEAR | Folder & Files | Component Usage & JSX Structure (Max: 25 pts) | Flexbox Layout & Responsiveness (Max: 30 pts) | UI Aesthetics & Visual Polish (Max: 25 pts) | Code Organization & Completeness (Max: 20 pts) | Final Score | AI Feedback |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | 2023-001 | Abia, Renz Clint C. | BSCS | 3 | 1/3 | 25 | 28 | 22 | 19 | 94 | Clean Flexbox layout and modular component structure; minor spacing inconsistency on header. |
| 2 | 2023-002 | Albano, Andrew Wayne D. | BSCS | 3 | 2/11 | 15 | 10 | 10 | 10 | 45 | Uses hardcoded pixel widths instead of responsive Flexbox properties. |
| 3 | 2023-003 | Alpez, Graci May J. | BSCS | 3 | 0/0 | 0 | 0 | 0 | 0 | 0 | Folder not found. |

## 6. Modular Design Principles
*   **Single Responsibility:** Separate modules handle folder matching (`StudentFolderMatcher`), code/flag extraction (`ReactNativeParser`), LLM evaluation (`AIGrader`), data transfer (`GradeResult`), and spreadsheet export (`ExcelReporter`).
*   **Open/Closed via Dynamic Markdown Rubrics:** New activities (e.g., Activities 5, 6, and 7) can be graded by loading a new `.md` rubric file without modifying the core grading loop or Excel reporter.
*   **Standardized Data Contract:** All grading outcomes (matched, empty folder, or missing submission) produce a uniform `GradeResult` dataclass consumed by `ExcelReporter`.

## 7. UI/UX & Concurrency Principles
*   **Thread-Safe Asynchronous UI:** Batch grading runs in a background daemon thread, while all `CustomTkinter` widget updates (`status_label`, `progress`, `btn_start`, and `TextBoxLogHandler`) are marshaled onto the main GUI thread via `.after(0, ...)`.
*   **Dual-Stream Logging:** High-level batch progress (`INFO`) streams to the built-in GUI terminal, while verbose diagnostics (`DEBUG`) write to a timestamped `.log` file with automatic file-handle teardown in a `finally` block.