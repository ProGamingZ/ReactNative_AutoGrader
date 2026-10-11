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
*   **Code Parsing:** Background Node.js script using `@babel/parser` or Python-based JS parsers (`esprima-python`).
*   **Offline AI Engine:** Local LLM (e.g., Llama 3 or Mistral) running via `Ollama` or `llama-cpp-python`.

## 3. Application Workflow
1.  **Input Configuration:** User selects the grading rubric (Activity 2, 3, or 4), uploads the class list Excel file (`BSCS...Attendance.xlsx`), and selects the folder containing the extracted LMS ZIP file.
2.  **Folder Matching & Extraction:** The app uses fuzzy matching to map LMS folder names (`LastName_FirstName`) to the official IDs in the Excel sheet (starting from Row 3).
3.  **Code Parsing:** The app scans the `.js`/`.tsx` files inside the student's folder to verify React Native syntax and core component usage.
4.  **AI Evaluation:** The source code and rubric guidelines are passed to the local LLM to evaluate Flexbox architecture and visual design heuristics.
5.  **Report Generation:** The app compiles the grades and feedback, then writes them to a new Excel file.

## 4. AI Prompting Strategy
To ensure consistent and reliable grading from the offline AI, the application enforces the following constraints:
*   **Structured Output (JSON Schema):** The AI is forced to return a strict JSON format containing scores, deductions, and feedback.
*   **Zero Creativity:** The LLM temperature is set to `0.0` or `0.1` for deterministic, reproducible results.
*   **Rubric Anchors:** Prompts contain strict point anchors (e.g., "Assign 25 pts if `StyleSheet` uses `flexDirection`. Assign 15 pts if hardcoded dimensions are used.").

## 5. Excel Output Format
The final generated Excel file will append the grading results to the original class list format:

| Name | Matched Folder/Files | Component Usage (25) | Flexbox Layout (30) | UI Aesthetics (25) | Code Structure (20) | Final Score | AI Feedback & Deductions |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Abia, Renz Clint C. | Matched (3 files) | 25 | 28 | 22 | 19 | 94 | Clean Flexbox implementation; good spacing. |
| Albano, Andrew Wayne D. | Matched (1 file) | 15 | 10 | 10 | 10 | 45 | Relies on inline fixed dimensions. |
| Alpez, Graci May J. | Folder Missing | 0 | 0 | 0 | 0 | 0 | No submission folder found in the LMS archive. |

## 6. SOLID Design Principles Implementation
The codebase is structured to be scalable, flexible, and maintainable:
*   **S - Single Responsibility:** Separate modules for file matching (`StudentFolderMatcher`), parsing (`ASTParser`), AI prompting (`AIGrader`), and Excel generation (`ExcelReporter`).
*   **O - Open/Closed:** A base `BaseRubricEvaluator` interface is used. New rubrics (e.g., `Activity5Evaluator`) can be added without modifying the core scanning loop.
*   **L - Liskov Substitution:** All rubric evaluators return a standardized `GradeResult` object, making them fully interchangeable in the main engine.
*   **I - Interface Segregation:** Code parsing logic is separated from AI evaluation logic. Objective syntax checkers do not need to implement AI connection methods.
*   **D - Dependency Inversion:** The main pipeline depends on high-level abstractions like `ILLMClient`. Switching from Ollama to another AI engine only requires swapping the low-level client class.

## 7. UI/UX Principles
*   **Asynchronous Processing:** All grading runs on background threads to prevent the desktop UI from freezing.
*   **Progress Tracking:** A progress bar and status text (e.g., "Grading student 12 of 35...") keep the user informed.
*   **Fail-Safe Execution:** Strict `try-except` blocks isolate file errors (e.g., corrupted files) so one bad submission doesn't crash the entire grading batch.