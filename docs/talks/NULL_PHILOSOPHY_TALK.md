# Conference Talk: NULL is Not a Value, It's a Confession of Ignorance

## Talk Title Options

1. **"NULL is Not a Value, It's a Confession of Ignorance"** (recommended)
2. **"Kleene, Codd, and the Disappearing Middle: A History of UNKNOWN"**
3. **"The Epistemology of NULL: What Databases Learned from Philosophy"**
4. **"From Aristotle to SQL: The 2,400-Year Battle Over the Third Truth Value"**
5. **"Boolean Logic is a Lie (And Kleene Knew It in 1938)"**

---

## Talk Abstract (300 words)

> In 334 BC, Aristotle declared: "Everything must either be or not be." The Law of Excluded Middle. True or false. No third option.
>
> In 1938, Stephen Cole Kleene—a mathematician working on computability theory—quietly disagreed. He introduced a third truth value: UNKNOWN. Not "maybe." Not "partially true." A formal admission that *we don't have enough information to decide*.
>
> In 1970, E.F. Codd borrowed Kleene's logic for his relational model. NULL was born—not as a value, but as a *confession of ignorance*.
>
> And then we forgot.
>
> Today, most programmers treat NULL as "empty" or "missing" or "zero." Our DataFrame libraries collapse three-valued logic back to binary. We write `if x > 5` and expect TRUE or FALSE, forgetting that the honest answer might be "I don't know."
>
> This talk traces the 2,400-year philosophical war between those who believe all propositions are decidable and those who accept that some questions have no answer (yet). We'll meet:
>
> - **Aristotle** and his excluded middle
> - **Brouwer** and the intuitionists who rejected it
> - **Łukasiewicz** who formalized the third value in 1920
> - **Kleene** who gave us the truth tables we still use
> - **Codd** who brought it to databases
> - **Us** who keep forgetting it
>
> You'll learn why NULL isn't a bug to be handled—it's an epistemological statement. Why `NULL = NULL` returning UNKNOWN is philosophically correct (and practically maddening). And why every time you write `WHERE x > 5`, you're taking a position in a debate that began in ancient Greece.
>
> Philosophy has consequences. In databases, those consequences are measured in dollars.

---

## Talk Outline (40-45 minutes)

### Prologue: The Sea Battle (3 minutes)

*[Open with Aristotle's famous puzzle]*

> "There will be a sea battle tomorrow."
>
> Is this statement true or false?

Aristotle, 334 BC. *De Interpretatione*, Chapter 9.

If it's TRUE now, then the sea battle is inevitable—fate is sealed.
If it's FALSE now, then no sea battle can occur—fate is equally sealed.

But surely, *right now*, we simply don't know?

Aristotle squirmed. He believed in the Law of Excluded Middle—every proposition is either true or false. But future contingents seemed... different.

*[Beat]*

2,400 years later, your database faces the same problem:

```sql
SELECT * FROM naval_operations WHERE battle_date = '2025-12-01';
```

Is there a battle tomorrow? The honest answer: **UNKNOWN**.

---

### Act 1: The Classical World (8 minutes)

#### Aristotle's Excluded Middle (3 min)

**The Law of Excluded Middle (LEM):**
> For any proposition P, either P is true or NOT P is true. There is no middle ground.

This seems obvious. A coin is heads or tails. A person is alive or dead. A number is even or odd.

```
P ∨ ¬P = TRUE  (always)
```

Classical logic. Boolean logic. The foundation of mathematics, computer science, and every `if` statement you've ever written.

**Why it's powerful:**
- Proof by contradiction works
- Every decision is decidable
- Code paths are exhaustive: `if/else` covers all cases

**The hidden assumption:**
> We have perfect information about the world.

#### The Cracks Appear (3 min)

**The Liar's Paradox:**
> "This statement is false."

If true → it's false. If false → it's true. Neither works.

**Russell's Paradox (1901):**
> The set of all sets that don't contain themselves.

Does it contain itself? If yes → no. If no → yes.

**Gödel's Incompleteness (1931):**
> There are true statements that cannot be proven within any consistent formal system.

The cracks in classical logic were showing. Some propositions resist binary classification.

#### The Revolt: Intuitionism (2 min)

**L.E.J. Brouwer** (1908): "The Law of Excluded Middle is not universally valid."

Brouwer founded **intuitionist logic**: a proposition is only true if we can *construct* a proof. "NOT false" doesn't mean "true"—it means we haven't found a contradiction *yet*.

```
Classical:    P ∨ ¬P = TRUE (always)
Intuitionist: P ∨ ¬P = ??? (until proven)
```

This was heresy. Hilbert called it "taking away the mathematician's telescope."

But Brouwer had a point: **you can't always decide**.

---

### Act 2: The Third Value is Born (10 minutes)

#### Jan Łukasiewicz: The Pioneer (3 min)

**Poland, 1920.** Philosopher Jan Łukasiewicz introduces **three-valued logic**.

His motivation: Aristotle's sea battle. Future contingents.

```
Truth values:
  1 = TRUE
  ½ = INDETERMINATE (neither true nor false YET)
  0 = FALSE
```

For the first time, "I don't know" had a formal seat at the table.

**Łukasiewicz's insight:**
> The third value isn't "sort of true" or "probably true."
> It's "the truth value is currently undefined."

```
Tomorrow there will be a sea battle = ½
(We'll know tomorrow. Not today.)
```

#### Stephen Cole Kleene: The Systematizer (4 min)

**Princeton, 1938.** Mathematician Stephen Kleene is working on computability theory—what can algorithms decide?

He encounters **partial functions**: functions that don't return a value for all inputs. What's the "truth value" of a computation that never halts?

Kleene formalizes **strong three-valued logic (K3)**:

```
Values:
  T = TRUE      (definitely true)
  U = UNKNOWN   (cannot be determined)
  F = FALSE     (definitely false)
```

**Kleene's Truth Tables:**

AND (minimum semantics):
```
∧    | T | U | F
-----+---+---+---
  T  | T | U | F
  U  | U | U | F
  F  | F | F | F
```

OR (maximum semantics):
```
∨    | T | U | F
-----+---+---+---
  T  | T | T | T
  U  | T | U | U
  F  | T | U | F
```

NOT:
```
¬T = F
¬U = U  ← KEY INSIGHT
¬F = T
```

**The crucial innovation:** NOT UNKNOWN = UNKNOWN.

If I don't know whether it's raining, I also don't know whether it's *not* raining.

#### Two Interpretations of UNKNOWN (3 min)

Kleene actually defined **two** three-valued logics:

**Strong Kleene (K3):** "Unknown now, might be known later"
- If any operand is UNKNOWN, result *might* be UNKNOWN
- Used for: partial information, databases, future contingents

**Weak Kleene (K3w):** "Meaningless / nonsensical"
- If any operand is UNKNOWN, result *is always* UNKNOWN
- Used for: type errors, undefined operations, division by zero

```
Strong: TRUE OR UNKNOWN = TRUE   (doesn't matter what U is)
Weak:   TRUE OR UNKNOWN = UNKNOWN (the whole expression is tainted)
```

**SQL uses Strong Kleene.** `TRUE OR NULL = TRUE`.

But watch out: `TRUE AND NULL = NULL`. The UNKNOWN *might* make the whole thing false.

---

### Act 3: NULL Enters the Database (8 minutes)

#### E.F. Codd and the Relational Model (3 min)

**IBM, 1970.** Edgar F. Codd publishes "A Relational Model of Data for Large Shared Data Banks."

He needs to represent **missing information**. A customer's phone number we don't have. A measurement not yet taken. A field that doesn't apply.

Codd borrows Kleene's UNKNOWN. He calls it **NULL**.

> "NULL represents the absence of a value. It is not the same as zero, empty string, or any other value."

**Crucially:** NULL is not a value. It's the **absence** of a value.

```sql
-- This is UNKNOWN, not FALSE
NULL = NULL → UNKNOWN

-- This is how you test for absence
x IS NULL → TRUE or FALSE
```

#### The Philosophy of NULL (3 min)

Codd was making an epistemological statement:

> "We don't know this customer's age."

This is not:
- Age = 0 (that's a known value)
- Age = "" (that's a known empty string)
- Age = "N/A" (that's a known sentinel)

It's: **We have no information about age.**

When you compare UNKNOWN to anything:

```sql
NULL > 18  → UNKNOWN
NULL = 18  → UNKNOWN
NULL = NULL → UNKNOWN  -- We don't know if two unknowns are the same!
```

**The last one trips everyone up.**

Are two unknown phone numbers the same phone number? We don't know! They might be. They might not be. Returning TRUE or FALSE would be claiming knowledge we don't have.

#### Codd's Later Regret (2 min)

By 1979, Codd realized one NULL wasn't enough. He proposed **two** null markers:

- **A-mark:** "Applicable but absent" (we should have this, but don't)
- **I-mark:** "Inapplicable" (this field doesn't apply to this entity)

```
Employee.commission:
  - Salesperson: NULL means "not yet calculated" (A-mark)
  - Engineer: NULL means "engineers don't get commission" (I-mark)
```

These need different handling! But SQL never implemented this.

We collapsed two distinct meanings into one NULL—and we've been paying for it ever since.

---

### Act 4: The Great Forgetting (8 minutes)

#### Boolean Logic Wins (3 min)

Despite Kleene, despite Codd, **boolean logic became the default**:

- Programming languages: `if/else` (no third branch)
- Hardware: transistors are on/off
- Data types: `bool` is true/false
- Mental models: yes/no questions

Three-valued logic survived in databases. Nowhere else.

```python
# Python: no third option
if x > 5:
    print("big")
else:
    print("small")  # What if we don't know x?
```

**The Law of Excluded Middle reasserted itself.**

Why? Simplicity. Performance. Cognitive ease.

Binary is *fast*. Binary is *simple*. Binary fits in one bit.

#### DataFrames Inherit the Forgetting (3 min)

When DataFrames emerged (Pandas 2008, Polars 2020s), they inherited programming language assumptions:

**Pandas (worst):**
```python
pd.Series([5, None, 10]) > 7
# Returns: [False, False, True]
# NULL > 7 = FALSE ???
```

Pandas collapsed Kleene logic at the **comparison** level. The third value is destroyed before you can reason about it.

**Polars (better, but still problematic):**
```python
pl.Series([5, None, 10]) > 7
# Returns: [False, None, True]  ← Preserves UNKNOWN

df.filter(pl.col("x") > 7)
# Silently excludes NULLs ← Forgets it at filter time
```

**SQL (most faithful to Kleene, but bad ergonomics):**
```sql
SELECT * FROM t WHERE x > 7
-- Excludes NULLs (explicit in spec, but not in syntax)

SELECT * FROM t WHERE x > 7 OR x IS NULL
-- Manual rehabilitation of the third value
```

#### The Cognitive Trap (2 min)

Why do we keep forgetting?

**1. Binary intuition:** Humans evolved for fight/flight, yes/no, safe/dangerous

**2. Educational failure:** Programming teaches bool first, NULL as "advanced topic"

**3. Language design:** No mainstream language has first-class UNKNOWN

**4. The Rashomon problem:** Everyone interprets NULL differently
   - "Missing"
   - "Empty"
   - "Default"
   - "N/A"
   - "Error"
   - "Not yet loaded"

Kleene meant one thing. We use NULL for all of them.

---

### Act 5: Reclaiming the Third Value (8 minutes)

#### The Philosophical Case (2 min)

NULL is not a bug. It's not a edge case. It's not a code smell.

**NULL is an epistemological statement:**
> "We acknowledge the limits of our knowledge."

This is *honesty*. Claiming TRUE or FALSE when we don't know is a *lie*.

Every time you write code that treats NULL as FALSE, you're making a philosophical claim:
> "The absence of information is equivalent to a negative answer."

Sometimes that's appropriate (closed-world assumption). Often it's not.

#### Making Epistemology Explicit (3 min)

The solution isn't eliminating NULL. It's making our epistemological stance explicit:

```python
import mountainash_expressions as ma

# The comparison preserves Kleene logic
expr = ma.col("age").t_gt(18)  # Returns TRUE / UNKNOWN / FALSE

# Now CHOOSE your epistemology:

# Closed-world assumption: "Unknown = False"
df.filter(expr.is_true().compile(df))

# Open-world assumption: "Unknown = Maybe True"
df.filter(expr.maybe_true().compile(df))

# Skeptical: "Only accept what we can prove"
df.filter(expr.is_true().compile(df))

# Credulous: "Accept unless we can disprove"
df.filter(expr.maybe_true().compile(df))

# Data quality focus: "Show me what we don't know"
df.filter(expr.is_unknown().compile(df))
```

Each of these is a **legitimate philosophical position**. The framework forces you to choose, rather than choosing for you silently.

#### The Booleanizers as Epistemological Stances (3 min)

| Method | Epistemology | Philosophy |
|--------|--------------|------------|
| `.is_true()` | Closed-world | Only accept proven facts |
| `.is_false()` | Closed-world | Only accept proven negatives |
| `.is_unknown()` | Meta-epistemic | Identify our ignorance |
| `.is_known()` | Exclude uncertainty | Act only on solid ground |
| `.maybe_true()` | Open-world / Credulous | Don't exclude possibilities |
| `.maybe_false()` | Open-world / Skeptical | Don't exclude risks |

```python
# Promotional campaign: Don't exclude potential customers
eligible = age_check.maybe_true()  # Credulous

# Security check: Don't grant access to unknowns
authorized = role_check.is_true()  # Skeptical

# Data quality audit: What don't we know?
gaps = age_check.is_unknown()  # Meta-epistemic
```

**Different questions deserve different epistemologies.**

---

### Closing: The Confession (3 minutes)

#### What NULL Really Means

When you write:
```sql
INSERT INTO customers (name, age) VALUES ('Alice', NULL);
```

You're not saying "Alice has no age."
You're not saying "Alice's age is zero."
You're not saying "Alice's age is empty."

You're saying:
> "We have a customer named Alice. We don't know her age. We're honest about that."

**NULL is a confession of ignorance.** And that's not weakness—it's intellectual honesty.

#### The Legacy of Kleene

Stephen Cole Kleene died in 1994. He never used SQL. He never debugged a NULL pointer exception. He was thinking about computability, about what algorithms can and cannot decide.

But his truth tables—scribbled in 1938—are running in every database on Earth.

Every time `NULL AND TRUE` returns `NULL`, that's Kleene.
Every time `NOT NULL` returns `NULL`, that's Kleene.
Every time you rage at `NULL = NULL` returning `NULL`, that's Kleene.

He was right. We keep forgetting.

#### The Call

Stop treating NULL as a bug to be eliminated.
Start treating it as information to be preserved.

Stop asking "how do I handle NULLs?"
Start asking "what do I *believe* about things I don't know?"

The Law of Excluded Middle is useful. But it's not universal.

Some questions don't have answers yet.
Some data isn't available yet.
Some computations don't terminate.

**And that's okay.**

The third truth value isn't a problem to be solved.
It's wisdom to be embraced.

*[Beat]*

Aristotle asked: "Will there be a sea battle tomorrow?"

Kleene answered: "I don't know. And that's a valid answer."

Codd gave us NULL.

Now it's our turn to use it honestly.

---

## Supplementary Materials

### Timeline Slide

```
384-322 BC  Aristotle - Law of Excluded Middle
    ↓
1908        Brouwer - Intuitionism challenges LEM
    ↓
1920        Łukasiewicz - First formal 3-valued logic
    ↓
1938        Kleene - Strong 3-valued logic (K3)
    ↓
1970        Codd - NULL in relational model
    ↓
1979        Codd - Proposes A-marks and I-marks (ignored)
    ↓
1986        SQL-86 - NULL standardized (one marker only)
    ↓
2008        Pandas - Collapses NULL to False
    ↓
2020s       Polars - Preserves NULL in comparisons
    ↓
Now         Still fighting the same battle
```

### The Truth Table Reference

**Kleene Strong (K3) - Used by SQL:**

```
NOT:          AND:          OR:
¬T = F        T∧T = T       T∨T = T
¬U = U        T∧U = U       T∨U = T
¬F = T        T∧F = F       T∨F = T
              U∧U = U       U∨U = U
              U∧F = F       U∨F = U
              F∧F = F       F∨F = F
```

**Key insight:** `T OR U = T` (if one is true, whole is true regardless of unknown)
**But:** `T AND U = U` (the unknown *might* make it false)

### The NULL Equality Trap

```sql
-- Why does this return no rows?
SELECT * FROM customers WHERE age = NULL;

-- Because:
age = NULL
↓
UNKNOWN = UNKNOWN
↓
UNKNOWN (not TRUE!)
↓
Row excluded

-- You need:
SELECT * FROM customers WHERE age IS NULL;
```

`IS NULL` is a meta-level question: "Is this value absent?"
`= NULL` is an object-level question: "Is this value equal to [nothing]?"

The first makes sense. The second is a category error.

### Codd's Two-Marker Proposal (1979)

**A-mark (Applicable missing):**
- "We should have this information but don't"
- Example: Customer phone number not yet collected
- Appropriate handling: Request the data, use defaults

**I-mark (Inapplicable):**
- "This field doesn't apply to this entity"
- Example: Commission for non-sales employee
- Appropriate handling: Exclude from calculations, not "missing"

```sql
-- Codd wanted:
employee.commission = A-NULL  -- Sales person, not yet calculated
employee.commission = I-NULL  -- Engineer, N/A

-- We got:
employee.commission = NULL    -- Could mean either!
```

This conflation causes bugs to this day.

### Philosophers Referenced

| Philosopher | Dates | Contribution |
|-------------|-------|--------------|
| Aristotle | 384-322 BC | Law of Excluded Middle, Sea Battle paradox |
| L.E.J. Brouwer | 1881-1966 | Intuitionist logic, rejected LEM |
| Jan Łukasiewicz | 1878-1956 | First formal three-valued logic (1920) |
| Stephen Cole Kleene | 1909-1994 | Strong/Weak K3, computability theory |
| E.F. Codd | 1923-2003 | Relational model, NULL |
| Kurt Gödel | 1906-1978 | Incompleteness theorems |
| Bertrand Russell | 1872-1970 | Russell's Paradox |

---

## Conference Submission Notes

### Target Conferences

- **Strange Loop** - Perfect fit: philosophy + code
- **SIGMOD/VLDB** - Database theory audience
- **POPL** - Programming language theory
- **Curry On** - PL + philosophy crossover
- **Papers We Love** - Historical/foundational content
- **!!Con** - Engaging storytelling (shorter version)

### Talk Format

- **Preferred:** 40-45 minutes (full philosophical arc)
- **Condensed:** 25 minutes (skip intuitionism, focus Kleene→Codd→Today)
- **Lightning:** 5 minutes (Sea Battle → NULL → "it's epistemology")

### Why This Talk?

1. **Unique angle** - Nobody tells the Kleene→Codd story
2. **Deep roots** - 2,400 years of context
3. **Practical implications** - Philosophy → real bugs → real solutions
4. **Memorable narrative** - Sea battles, heretics, regretful inventors
5. **Quotable** - "NULL is a confession of ignorance"

### Speaker Bio Elements

- Interest in philosophy of computing
- Building tools that make epistemology explicit
- Connecting historical theory to practical engineering

---

## Bonus: The Paradoxes of NULL

### Identity Crisis

```sql
-- Is this TRUE, FALSE, or UNKNOWN?
NULL = NULL

-- Answer: UNKNOWN
-- Because: We don't know if two unknowns are the same unknown!
```

**Philosophical parallel:** Are two unnamed things the same thing? We can't know without identifying them.

### The Excluded Fourth

```sql
-- Excluded middle says: P OR NOT P = TRUE

-- But in SQL:
(NULL > 5) OR NOT (NULL > 5)
= UNKNOWN OR UNKNOWN
= UNKNOWN

-- The excluded middle is... excluded!
```

Kleene logic violates LEM. This is a feature, not a bug.

### The NOT NOT Problem

```sql
-- Classical logic: NOT NOT P = P

-- In SQL:
NOT NOT (NULL > 5)
= NOT UNKNOWN
= UNKNOWN

-- NOT NOT NULL ≠ NULL's "value"
```

Double negation doesn't eliminate uncertainty. You can't reason your way out of not knowing.

### Codd's Paradox

```sql
-- Count all customers
SELECT COUNT(*) FROM customers;  -- Returns 100

-- Count customers with known age + unknown age
SELECT COUNT(*) FROM customers WHERE age IS NOT NULL;  -- 80
SELECT COUNT(*) FROM customers WHERE age IS NULL;       -- 20
-- Sum: 100 ✓

-- But:
SELECT COUNT(*) FROM customers WHERE age > 18;          -- 60
SELECT COUNT(*) FROM customers WHERE age <= 18;         -- 20
-- Sum: 80 ≠ 100!

-- Where did 20 customers go?
-- They're not > 18. They're not <= 18. They're UNKNOWN.
```

The Law of Excluded Middle doesn't hold for partial information.
