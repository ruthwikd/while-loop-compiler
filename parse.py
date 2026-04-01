import re
import tkinter as tk
from tkinter import scrolledtext, font, ttk
from datetime import datetime

# ============================================================
# ALL COMPILER FUNCTIONS
# ============================================================
TOKEN_SPEC = [
    ('WHILE', r'\bwhile\b'), ('TRUE', r'\bTrue\b'), ('FALSE', r'\bFalse\b'),
    ('NUMBER', r'\d+'), ('ID', r'[a-zA-Z_]\w*'),
    ('LE', r'<='), ('GE', r'>='), ('EQ', r'=='), ('NEQ', r'!='),
    ('LT', r'<'), ('GT', r'>'), ('ASSIGN', r'='),
    ('INC', r'\+\+'), ('DEC', r'--'), ('PLUS', r'\+'), ('MINUS', r'-'),
    ('LPAREN', r'\('), ('RPAREN', r'\)'), ('LBRACE', r'\{'),
    ('RBRACE', r'\}'), ('SEMI', r';'), ('SKIP', r'[ \t\n]+'),
]

def tokenize(code):
    tokens = []
    pos = 0
    while pos < len(code):
        matched = False
        for tok_type, pattern in TOKEN_SPEC:
            m = re.compile(pattern).match(code, pos)
            if m:
                if tok_type != 'SKIP':
                    tokens.append((tok_type, m.group()))
                pos = m.end()
                matched = True
                break
        if not matched:
            raise SyntaxError(f"Unknown character: {code[pos]}")
    return tokens

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else ('EOF', '')

    def consume(self, expected=None):
        tok = self.tokens[self.pos]
        if expected and tok[0] != expected:
            raise SyntaxError(f"Expected {expected}, got {tok}")
        self.pos += 1
        return tok

    def parse_while(self):
        self.consume('WHILE'); self.consume('LPAREN')
        condition = self.parse_condition()
        self.consume('RPAREN'); self.consume('LBRACE')
        body = self.parse_body()
        self.consume('RBRACE')
        return {'condition': condition, 'body': body}

    def parse_condition(self):
        left = self.consume()
        if self.peek()[0] in ('LT','GT','LE','GE','EQ','NEQ'):
            op = self.consume(); right = self.consume()
            return {'left': left[1], 'op': op[1], 'right': right[1]}
        return {'left': left[1], 'op': None, 'right': None}

    def parse_body(self):
        stmts = []
        while self.peek()[0] != 'RBRACE':
            stmts.append(self.parse_statement())
        return stmts

    def parse_statement(self):
        name = self.consume('ID')[1]
        if self.peek()[0] == 'INC':
            self.consume('INC'); self.consume('SEMI')
            return {'type': 'Inc', 'var': name}
        elif self.peek()[0] == 'DEC':
            self.consume('DEC'); self.consume('SEMI')
            return {'type': 'Dec', 'var': name}
        elif self.peek()[0] == 'ASSIGN':
            self.consume('ASSIGN'); val = self.consume(); self.consume('SEMI')
            return {'type': 'Assign', 'var': name, 'value': val[1]}
        raise SyntaxError(f"Unexpected: {self.peek()}")

def analyze_loop(ast):
    c, body = ast['condition'], ast['body']
    warnings, suggestions = [], []
    if c['left'] in ('True', 'true') and not c['op']:
        warnings.append("WARNING: Condition is always True — guaranteed infinite loop")
        suggestions.append("SUGGESTION: Add a break statement or use a counter variable")
        return warnings, suggestions
    modified = set(s['var'] for s in body)
    if c['left'] not in modified:
        warnings.append(f"WARNING: '{c['left']}' is never modified inside the loop body")
        suggestions.append(f"SUGGESTION: Add '{c['left']}++' or modify '{c['left']}' inside the loop")
    if c['left'] in modified and c['op'] in ('<', '<='):
        for s in body:
            if s['var'] == c['left'] and s['type'] == 'Dec':
                warnings.append(f"WARNING: '{c['left']}' decrements but condition expects growth")
                suggestions.append(f"SUGGESTION: Change '{c['left']}--' to '{c['left']}++' or flip to '>'")
    if c['left'] in modified and c['op'] in ('>', '>='):
        for s in body:
            if s['var'] == c['left'] and s['type'] == 'Inc':
                warnings.append(f"WARNING: '{c['left']}' increments but condition expects shrink")
                suggestions.append(f"SUGGESTION: Change '{c['left']}++' to '{c['left']}--' or flip to '<'")
    return warnings, suggestions

def generate_TAC(ast):
    c, body = ast['condition'], ast['body']
    tac = ['L1:']
    if c['op']:
        tac.append(f"  if NOT ({c['left']} {c['op']} {c['right']}) goto L2")
    else:
        tac.append(f"  if NOT ({c['left']}) goto L2")
    for s in body:
        if s['type'] == 'Inc':   tac.append(f"  {s['var']} = {s['var']} + 1")
        elif s['type'] == 'Dec': tac.append(f"  {s['var']} = {s['var']} - 1")
        else:                    tac.append(f"  {s['var']} = {s['value']}")
    tac += ['  goto L1', 'L2:']
    return tac

# ============================================================
# COLORS & FONTS
# ============================================================
BG      = "#0f0e17"
SURF    = "#1a1a2e"
SURF2   = "#13121f"
SURF3   = "#16213e"
ACCENT  = "#6c63ff"
GREEN   = "#00d4aa"
AMBER   = "#fbbf24"
RED     = "#f87171"
PURPLE  = "#a78bfa"
MUTED   = "#8892a4"
FG      = "#e2e8f0"
DIM     = "#4a4a6a"

total_count = 0
safe_count  = 0
warn_count  = 0

def run_compiler(code=None):
    global total_count, safe_count, warn_count
    raw = code or input_box.get("1.0", tk.END).strip()
    if not raw:
        return

    out = output_box
    out.config(state=tk.NORMAL)
    out.delete("1.0", tk.END)

    def put(text, tag="n"):
        out.insert(tk.END, text, tag)

    try:
        put("  ┌─────────────────────────────────────────────────┐\n", "dim")
        put("  │  PHASE 1  —  LEXICAL ANALYSIS                  │\n", "ph1")
        put("  └─────────────────────────────────────────────────┘\n", "dim")
        tokens = tokenize(raw)
        kw_types = {'WHILE','TRUE','FALSE'}
        op_types = {'LT','GT','LE','GE','EQ','NEQ','ASSIGN','INC','DEC'}
        for t in tokens:
            put(f"    ({t[0]:<12}", "label")
            if t[0] in kw_types:
                put(f"  '{t[1]}')\n", "kw")
            elif t[0] == 'ID':
                put(f"  '{t[1]}')\n", "id_col")
            elif t[0] == 'NUMBER':
                put(f"  '{t[1]}')\n", "num_col")
            elif t[0] in op_types:
                put(f"  '{t[1]}')\n", "op_col")
            else:
                put(f"  '{t[1]}')\n", "n")

        put("\n  ┌─────────────────────────────────────────────────┐\n", "dim")
        put("  │  PHASE 2  —  SYNTAX ANALYSIS  (AST)            │\n", "ph2")
        put("  └─────────────────────────────────────────────────┘\n", "dim")
        parser = Parser(tokens)
        ast = parser.parse_while()
        c = ast['condition']
        put(f"    Condition  ", "label")
        put(f"left=", "n"); put(f"'{c['left']}'", "id_col")
        put(f"  op=", "n"); put(f"'{c['op']}'", "op_col")
        put(f"  right=", "n"); put(f"'{c['right']}'\n", "num_col")
        put(f"    Body       ", "label")
        put(f"{[s['type']+'('+s['var']+')' for s in ast['body']]}\n", "ast_col")

        put("\n  ┌─────────────────────────────────────────────────┐\n", "dim")
        put("  │  PHASE 3  —  SEMANTIC ANALYSIS                 │\n", "ph3")
        put("  └─────────────────────────────────────────────────┘\n", "dim")
        warnings, suggestions = analyze_loop(ast)
        safe = len(warnings) == 0
        if warnings:
            for w in warnings:
                put(f"    {w}\n", "warn")
        else:
            put(f"    No infinite loop detected — loop is safe\n", "safe")

        put("\n  ┌─────────────────────────────────────────────────┐\n", "dim")
        put("  │  PHASE 4  —  THREE ADDRESS CODE  (TAC)         │\n", "ph4")
        put("  └─────────────────────────────────────────────────┘\n", "dim")
        for line in generate_TAC(ast):
            if line.endswith(':'):
                put(f"    {line}\n", "tac_label")
            elif 'if NOT' in line or 'goto' in line:
                put(f"    {line}\n", "tac_inst")
            else:
                put(f"    {line}\n", "tac_var")

        put("\n  ┌─────────────────────────────────────────────────┐\n", "dim")
        put("  │  PHASE 5  —  FINAL OUTPUT                      │\n", "ph5")
        put("  └─────────────────────────────────────────────────┘\n", "dim")
        if suggestions:
            for s in suggestions:
                put(f"    {s}\n", "sug")
        else:
            put(f"    Loop looks safe — no warnings issued!\n", "safe")

        put("\n  ════════════════════════════════════════════════\n", "dim")
        if safe:
            put(f"  RESULT:  Loop is SAFE\n", "safe")
        else:
            put(f"  RESULT:  INFINITE LOOP DETECTED\n", "warn")
        put(f"  Time  :  {datetime.now().strftime('%H:%M:%S')}\n", "dim")
        put(f"  Input :  {raw}\n", "dim")
        put("  ════════════════════════════════════════════════\n", "dim")

        total_count += 1
        if safe: safe_count += 1
        else:    warn_count += 1
        lbl_total.config(text=str(total_count))
        lbl_safe.config(text=str(safe_count))
        lbl_warn.config(text=str(warn_count))
        lbl_tok.config(text=str(len(tokens)))

        history_list.insert(0, f"{'✓' if safe else '!'} {raw}")
        if history_list.size() > 8:
            history_list.delete(tk.END)

    except Exception as e:
        put(f"\n  ERROR: {e}\n", "warn")

    out.config(state=tk.DISABLED)

def preset(val):
    input_box.delete("1.0", tk.END)
    input_box.insert("1.0", val)
    run_compiler()

def clear_all():
    input_box.delete("1.0", tk.END)
    input_box.insert("1.0", "while (x < 10) { x++; }")
    output_box.config(state=tk.NORMAL)
    output_box.delete("1.0", tk.END)
    output_box.config(state=tk.DISABLED)

def run_all_tests():
    tests = [
        "while (x < 10) { x++; }",
        "while (x < 10) { x--; }",
        "while (count < 50) { y++; }",
        "while (True) { x++; }",
        "while (n < 100) { n++; }",
        "while (n < 100) { n--; }",
        "while (x > 0) { x--; }",
        "while (x > 0) { x++; }",
    ]
    for t in tests:
        input_box.delete("1.0", tk.END)
        input_box.insert("1.0", t)
        run_compiler(t)

def update_clock():
    clock_lbl.config(text=datetime.now().strftime("%H:%M:%S"))
    root.after(1000, update_clock)

# ============================================================
# WINDOW SETUP
# ============================================================
root = tk.Tk()
root.title("While Loop Compiler — Infinite Loop Detector")
root.geometry("950x820")
root.configure(bg=BG)
root.resizable(True, True)

mono   = font.Font(family="Courier New", size=10)
mono_b = font.Font(family="Courier New", size=10, weight="bold")
mono_l = font.Font(family="Courier New", size=11, weight="bold")
sans   = font.Font(family="Segoe UI", size=10)
sans_b = font.Font(family="Segoe UI", size=11, weight="bold")
sans_t = font.Font(family="Segoe UI", size=13, weight="bold")
tiny   = font.Font(family="Segoe UI", size=9)
tiny_b = font.Font(family="Segoe UI", size=9, weight="bold")

# ============================================================
# HEADER
# ============================================================
hdr = tk.Frame(root, bg=SURF, pady=12, padx=20)
hdr.pack(fill=tk.X)
tk.Label(hdr, text="</>", font=font.Font(family="Courier New", size=14, weight="bold"),
         bg=ACCENT, fg="#fff", width=3, pady=4).pack(side=tk.LEFT, padx=(0,12))
tk.Label(hdr, text="While Loop Compiler", font=sans_t, bg=SURF, fg=FG).pack(side=tk.LEFT)
tk.Label(hdr, text="  APP 7 · Automata Theory & Compiler Design · Infinite Loop Detector",
         font=tiny, bg=SURF, fg=MUTED).pack(side=tk.LEFT, pady=4)
clock_lbl = tk.Label(hdr, text="", font=mono, bg=SURF, fg=MUTED)
clock_lbl.pack(side=tk.RIGHT)
tk.Label(hdr, text="● READY  ", font=tiny_b, bg=SURF, fg=GREEN).pack(side=tk.RIGHT)

# ============================================================
# STATS BAR
# ============================================================
stats_bar = tk.Frame(root, bg=SURF2, pady=10, padx=16)
stats_bar.pack(fill=tk.X)

for title, key, color in [("Total Compiled","total",PURPLE),("Safe Loops","safe",GREEN),("Warnings","warn",RED),("Tokens Found","tok",AMBER)]:
    card = tk.Frame(stats_bar, bg=SURF, padx=16, pady=8, relief=tk.FLAT)
    card.pack(side=tk.LEFT, padx=6)
    tk.Label(card, text=title.upper(), font=tiny, bg=SURF, fg=MUTED).pack(anchor="w")
    lbl = tk.Label(card, text="0" if key!="tok" else "—", font=font.Font(family="Segoe UI",size=18,weight="bold"), bg=SURF, fg=color)
    lbl.pack(anchor="w")
    if key == "total":   lbl_total = lbl
    elif key == "safe":  lbl_safe  = lbl
    elif key == "warn":  lbl_warn  = lbl
    elif key == "tok":   lbl_tok   = lbl

# ============================================================
# MAIN AREA — LEFT + RIGHT
# ============================================================
main = tk.Frame(root, bg=SURF2)
main.pack(fill=tk.BOTH, expand=True, padx=0)

left  = tk.Frame(main, bg=SURF2, width=340)
left.pack(side=tk.LEFT, fill=tk.Y, padx=14, pady=12)
left.pack_propagate(False)

right = tk.Frame(main, bg=SURF2)
right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0,14), pady=12)

# ---- LEFT: INPUT ----
tk.Label(left, text="INPUT CODE", font=tiny_b, bg=SURF2, fg=MUTED).pack(anchor="w", pady=(0,4))
input_frame = tk.Frame(left, bg=SURF, bd=0)
input_frame.pack(fill=tk.X, pady=(0,10))
tk.Label(input_frame, text="● ● ●  while_loop.c", font=tiny, bg="#0f0e17", fg=MUTED, anchor="w", padx=10, pady=6).pack(fill=tk.X)
input_box = tk.Text(input_frame, height=3, font=mono, bg=SURF3, fg=FG,
                    insertbackground=ACCENT, relief=tk.FLAT, padx=12, pady=8, bd=0)
input_box.insert("1.0", "while (x < 10) { x++; }")
input_box.pack(fill=tk.X)

# ---- LEFT: PRESETS ----
tk.Label(left, text="QUICK TEST CASES", font=tiny_b, bg=SURF2, fg=MUTED).pack(anchor="w", pady=(4,4))
presets = [
    ("safe: x++",       "while (x < 10) { x++; }"),
    ("warn: x--",       "while (x < 10) { x--; }"),
    ("warn: not mod",   "while (count < 50) { y++; }"),
    ("warn: true",      "while (True) { x++; }"),
    ("safe: n++",       "while (n < 100) { n++; }"),
    ("warn: n--",       "while (n < 100) { n--; }"),
    ("safe: x-- desc",  "while (x > 0) { x--; }"),
    ("warn: x++ desc",  "while (x > 0) { x++; }"),
]
for label, code in presets:
    tk.Button(left, text=f"  {label}", font=tiny, bg=SURF, fg=MUTED,
              relief=tk.FLAT, anchor="w", padx=8, pady=4, cursor="hand2",
              activebackground=SURF3, activeforeground=PURPLE,
              command=lambda c=code: preset(c)).pack(fill=tk.X, pady=1)

# ---- LEFT: BUTTONS ----
tk.Frame(left, bg=MUTED, height=1).pack(fill=tk.X, pady=10)
tk.Button(left, text="  Compile", font=sans_b, bg=ACCENT, fg="#fff",
          relief=tk.FLAT, pady=9, cursor="hand2", command=run_compiler).pack(fill=tk.X, pady=2)
tk.Button(left, text="  Run All 8 Tests", font=sans, bg=SURF3, fg=AMBER,
          relief=tk.FLAT, pady=7, cursor="hand2", command=run_all_tests).pack(fill=tk.X, pady=2)
tk.Button(left, text="  Clear", font=sans, bg=SURF, fg=MUTED,
          relief=tk.FLAT, pady=7, cursor="hand2", command=clear_all).pack(fill=tk.X, pady=2)

# ---- LEFT: HISTORY ----
tk.Frame(left, bg=MUTED, height=1).pack(fill=tk.X, pady=10)
tk.Label(left, text="COMPILE HISTORY", font=tiny_b, bg=SURF2, fg=MUTED).pack(anchor="w", pady=(0,4))
history_list = tk.Listbox(left, font=font.Font(family="Courier New", size=9),
                           bg=SURF, fg=PURPLE, selectbackground=SURF3,
                           relief=tk.FLAT, height=8, bd=0)
history_list.pack(fill=tk.X)

# ---- RIGHT: OUTPUT ----
tk.Label(right, text="COMPILER OUTPUT — ALL 5 PHASES", font=tiny_b, bg=SURF2, fg=MUTED).pack(anchor="w", pady=(0,4))
output_box = scrolledtext.ScrolledText(right, font=mono, bg=BG, fg=FG,
                                        relief=tk.FLAT, padx=14, pady=12,
                                        state=tk.DISABLED, bd=0)
output_box.pack(fill=tk.BOTH, expand=True)

output_box.tag_config("ph1",      foreground="#89b4fa", font=mono_l)
output_box.tag_config("ph2",      foreground="#a78bfa", font=mono_l)
output_box.tag_config("ph3",      foreground="#00d4aa", font=mono_l)
output_box.tag_config("ph4",      foreground="#fbbf24", font=mono_l)
output_box.tag_config("ph5",      foreground="#f87171", font=mono_l)
output_box.tag_config("warn",     foreground=RED)
output_box.tag_config("safe",     foreground=GREEN)
output_box.tag_config("sug",      foreground=AMBER)
output_box.tag_config("label",    foreground=MUTED,  font=mono_b)
output_box.tag_config("tac_label",foreground=PURPLE, font=mono_b)
output_box.tag_config("tac_inst", foreground="#89ddff")
output_box.tag_config("tac_var",  foreground=FG)
output_box.tag_config("kw",       foreground="#c792ea")
output_box.tag_config("id_col",   foreground="#82aaff")
output_box.tag_config("num_col",  foreground="#f78c6c")
output_box.tag_config("op_col",   foreground="#89ddff")
output_box.tag_config("ast_col",  foreground="#c3e88d")
output_box.tag_config("dim",      foreground=DIM)
output_box.tag_config("n",        foreground=FG)

# ============================================================
# FOOTER
# ============================================================
foot = tk.Frame(root, bg=SURF, pady=6, padx=16)
foot.pack(fill=tk.X, side=tk.BOTTOM)
tk.Label(foot, text="While Loop Compiler · APP 7 · Automata Theory & Compiler Design",
         font=tiny, bg=SURF, fg=DIM).pack(side=tk.LEFT)
tk.Label(foot, text="Python · tkinter · Regex · Recursive Descent Parser",
         font=tiny, bg=SURF, fg=DIM).pack(side=tk.RIGHT)

update_clock()
root.mainloop()