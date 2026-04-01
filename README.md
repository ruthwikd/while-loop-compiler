# While Loop Compiler with Infinite Loop Detection

## 📌 Project Overview

This project is a mini compiler developed using Python that analyzes while loop constructs and detects potential infinite loops. It simulates all major phases of compiler design and provides correction suggestions for identified issues.

---

## 🎯 Objectives

* To parse while loop structures
* To perform lexical, syntax, and semantic analysis
* To generate intermediate code (Three Address Code - TAC)
* To detect infinite loops
* To suggest corrections for loop errors

---

## ⚙️ Features

* Lexical Analysis using Regular Expressions
* Syntax Analysis using Recursive Descent Parsing
* Semantic Analysis for logical validation
* Infinite Loop Detection System
* Suggestion Engine for correcting loops
* Three Address Code (TAC) Generation

---

## 🧠 Infinite Loop Detection Cases

The system detects the following types of infinite loops:

1. Condition always true → `while(True)`
2. Loop variable not updated
3. Wrong update direction (e.g., decrement instead of increment)

---

## 🏗️ Compiler Phases Implemented

1. Lexical Analysis
2. Syntax Analysis
3. Semantic Analysis
4. Intermediate Code Generation (TAC)
5. Output Generation (Warnings & Suggestions)

---

## 💻 Technologies Used

* Python 3
* Tkinter (for GUI)
* Regular Expressions

---

## ▶️ How to Run

```bash
python main.py
```

---

## 🧪 Sample Input

```
while (x < 10) { x--; }
```

## ⚠️ Sample Output

```
WARNING: Possible infinite loop — 'x' decrements but condition expects it to grow
SUGGESTION: Change 'x--' to 'x++'
```

---

## 🚀 Project Highlights

* Implements complete compiler workflow
* Detects logical errors (not just syntax errors)
* Provides intelligent correction suggestions

---

## 👨‍💻 Author

**D Sai Ruthwik Chandra**
Roll No: CH.SC.U4CYS23006
Amrita Vishwa Vidyapeetham

---
