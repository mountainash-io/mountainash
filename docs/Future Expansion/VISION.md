# mountainash-expressions: Project Vision & Strategy

**Date:** 2025-01-09
**Status:** Strategic Direction Document
**Purpose:** Honest assessment and strategic guidance for project development

---

## Executive Summary

mountainash-expressions is a **specialized, high-quality library for cross-backend DataFrame expression evaluation** with a unique focus on **type-safe filtering logic** and **NULL-aware ternary semantics**.

**Realistic goal:** Become the go-to solution for **portable DataFrame filtering and expression logic**, particularly for library authors and data platform teams who need to abstract backend implementation from business logic.

**Not trying to be:** A complete DataFrame API, a SQL compiler, or a replacement for Polars/Pandas/Ibis.

---

## The Problem We Solve

### The Real Pain Point

**DataFrame code is not portable across backends.**

When you write filtering/transformation logic in Polars, you can't run it on Pandas, DuckDB, or SQLite without rewriting. This hurts:

1. **Library developers** - Can't support multiple backends without maintaining parallel implementations
2. **Data platform teams** - Can't abstract execution engine from business logic
3. **Migration scenarios** - Switching from Pandas to Polars requires rewriting thousands of lines
4. **Multi-environment applications** - Same logic needs to run on laptop (Polars) and warehouse (DuckDB)

### Current Landscape

| Solution | Approach | Strength | Gap |
|----------|----------|----------|-----|
| **Polars** | Native Rust-backed API | Fast, expressive | Polars-only |
| **Pandas** | NumPy-based API | Mature, ubiquitous | Slow, Pandas-only |
| **Ibis** | Universal SQL compiler | Many backends | Complex, SQL-centric, steep learning curve |
| **Narwhals** | Polars/Pandas abstraction | Simple, works today | Only 2 backends, limited operations |
| **Native code** | Backend-specific | Full power | Zero portability |

**Our position:** More expressive than Narwhals, more focused than Ibis, intentionally portable.

---

## Our Unique Value Proposition

### What Makes Us Different

1. **Ternary Logic (TRUE/FALSE/UNKNOWN)**
   - Proper NULL handling in filtering logic
   - SQL three-valued logic semantics
   - No other Python library does this well
   - **This is our killer feature once implemented**

2. **Natural Language Temporal Helpers**
   ```python
   within_last(col("timestamp"), "10 minutes")  # Like journalctl
   older_than(col("modified"), "7 days")        # Like find -mtime
   time_ago("2 hours")                          # Intuitive
   ```

3. **Clean, Focused API**
   - Not trying to be a complete DataFrame library
   - Just filtering, expressions, and basic transformations
   - Type-safe, composable, testable

4. **Cross-Backend Expression Trees**
   - Write once, compile to any backend
   - Backend-agnostic business logic
   - Easy to test (mock backends)

### What We're NOT

- ❌ Not a complete DataFrame API (use Polars/Pandas for that)
- ❌ Not a SQL compiler (use Ibis for that)
- ❌ Not trying to match every backend feature
- ❌ Not optimizing for raw performance (backends handle that)

---

## Target Audience

### Primary: Internal Mountain Ash Tools

**Success metric:** 50%+ of Mountain Ash data tools use mountainash-expressions

**Use cases:**
- Data quality rules (ternary logic shines here)
- Cross-environment pipelines (dev on Polars, prod on DuckDB)
- Filtering abstractions
- ML feature engineering (portable across backends)

**Value:** Proven internal adoption validates the approach and drives development.

### Secondary: Library Authors

**Profile:** Building libraries/frameworks that work with DataFrames

**Use cases:**
- Data validation libraries (Great Expectations alternative)
- Business rule engines
- Data quality frameworks
- ETL/ELT orchestration tools

**Value:** Write library once, users choose their backend.

### Tertiary: Data Platform Teams

**Profile:** Building internal data platforms abstracting execution from logic

**Use cases:**
- Multi-backend query engines
- Data catalog integration (filter pushdown)
- Portability layer for warehouse migrations

**Value:** Decouple business logic from infrastructure choices.

---

## Realistic Adoption Expectations

### Success Looks Like (2-3 years)

**Optimistic scenario (30% probability):**
- 50+ external organizations using it
- 3-5 active external contributors
- Mentioned in Polars/Ibis ecosystem
- Known as "the ternary logic library"
- 100+ GitHub stars, steady growth

**Most likely scenario (60% probability):**
- Primarily internal Mountain Ash usage
- 5-10 external users/organizations
- Occasional external contributions
- Small but engaged community
- 30-50 GitHub stars, stable

**We're NOT expecting:**
- Mass adoption (thousands of users)
- Competing with Polars/Pandas on popularity
- Becoming "the standard" for DataFrame operations
- Venture funding or commercial support

### Why This is Okay

**Specialized tools can be highly valuable without mass adoption.**

Success = solving a real problem well for a specific audience, not popularity contest.

Examples of successful niche tools:
- Hypothesis (property-based testing) - niche but essential
- attrs/dataclasses - focused, well-designed, widely used
- Click (CLI framework) - does one thing extremely well

---

## Strategic Priorities

### Phase 0: Foundation (Immediate)

**Priority: CRITICAL**

1. **Add Alias Node** (1-2 days)
   - Users need this for basic operations
   - Infrastructure exists, just implement it
   - Completes core primitive set

2. **Backend Refactoring** (3-4 weeks)
   - Eliminate god classes (663-883 lines → 8 mixins of 50-200 lines)
   - Improves maintainability before major expansion
   - Can run in parallel with Phase 1

3. **Polish README** (1-2 days)
   - Real-world examples
   - Clear value proposition
   - "Why this instead of X?" section
   - Installation and quick start

**Deliverable:** Solid foundation, clear messaging, missing functionality added

---

### Phase 1-2: Core Operations (Weeks 1-6)

**Priority: HIGH**

**Math Operations** (Phase 1, 2-3 weeks)
- 12 basic math functions (ABS, SQRT, ROUND, LOG, etc.)
- Quick win, high value
- Gets to ~50% operation coverage

**Advanced Conditionals** (Phase 2, 1-2 weeks)
- CASE expressions
- NULLIF, LEAST, GREATEST
- Enables more complex logic

**Rationale:** These are frequently needed, easy to implement, high value.

---

### Phase 3-5: Essential Expansion (Weeks 6-15)

**Priority: MEDIUM-HIGH**

**String Enhancements** (Phase 3, 2-3 weeks)
- +10 string operations (SPLIT, FIND, PAD, etc.)
- Common operations users expect

**Temporal Split + Expansion** (Phase 4, 3-4 weeks)
- **CRITICAL:** Split temporal node (prevents mega-node)
- +17 temporal operations (construction, parsing, constants)
- High value for time-series work

**Advanced Math** (Phase 5, 2-3 weeks)
- +14 trigonometric and advanced math
- Completes math story (26 total operations)

**Rationale:** Breadth of coverage, frequently requested operations.

---

### Phase 6-7: Specialized Features (Weeks 15-22)

**Priority: MEDIUM**

**Array Operations** (Phase 6, 4-6 weeks)
- 18 array/list operations
- High value for nested data
- **Caveat:** Limited backend support (Polars/DuckDB mainly)

**Bitwise + Specialized** (Phase 7, 1-2 weeks)
- 12 specialized operations
- Fills specific gaps

**Rationale:** Expands capability to specialized use cases.

---

### Phase 8: Window Functions (Weeks 22-27)

**Priority: HIGH** (97% coverage enabler)

**Window/Analytic Functions** (3-5 weeks)
- 17 window operations (RANK, LAG, LEAD, CUMSUM, etc.)
- Complex architecture required
- Critical for analytic queries

**Rationale:** Major capability unlock, needed for comprehensive coverage.

**Risk:** High complexity, backend translation challenges.

---

### Phase 9: Ternary Logic + ML Metrics (Weeks 27-34)

**Priority: CRITICAL** (differentiator)

**Ternary Logic Implementation** (2-3 weeks)
- TRUE/FALSE/UNKNOWN semantics
- NULL-aware filtering
- SQL three-valued logic
- **This is our unique selling point**

**ML Metrics** (Phase 9, 4-7 weeks)
- 12 ML/statistical metrics
- Classification, ranking, credit risk
- Domain-specific value

**Rationale:** Ternary logic is what makes us special. ML metrics serve specific user needs.

---

## What We're Explicitly NOT Doing

### Out of Scope

1. **Complete DataFrame API**
   - Not implementing joins, groupby, pivot, etc.
   - Users should use Polars/Pandas native APIs for that
   - We focus on expressions, not full DataFrames

2. **SQL Compiler**
   - Not building a query planner
   - Not optimizing SQL generation
   - Ibis does this well, we don't need to

3. **Performance Optimization**
   - Backend handles performance
   - We focus on correctness and portability
   - Some overhead is acceptable tradeoff

4. **Every Possible Backend**
   - Focus on Polars, Narwhals, Ibis (Polars/DuckDB)
   - Pandas detection exists but limited
   - SQLite has limitations (document them)
   - Not chasing every new backend

5. **Perfect Documentation**
   - Good enough > perfect
   - Focus on usage examples, not exhaustive API docs
   - Architecture docs for contributors, examples for users

6. **Every Possible Operation**
   - 80/20 rule: 80% of value from 20% of operations
   - Prioritize frequently used operations
   - Native escape hatch for edge cases

### Strategic Discipline

**When users request features, ask:**
1. Is this core to expression evaluation? (Yes → consider)
2. Does this require backend-specific knowledge? (Yes → out of scope)
3. Is this frequently needed? (No → defer or reject)
4. Can users work around with native backend? (Yes → deprioritize)

**Example rejections:**
- ❌ "Add support for Apache Arrow tables" → Use Ibis
- ❌ "Optimize query planning" → Backend handles this
- ❌ "Support every Polars string method" → 80/20 rule
- ❌ "Add DataFrame join operations" → Use native backend

---

## Success Metrics

### Technical Quality

- ✅ All tests passing (703+ as we expand)
- ✅ Type checking passing (mypy)
- ✅ Clean architecture (no god classes after refactoring)
- ✅ Backend compatibility maintained
- ✅ Test coverage > 90%

### Adoption Metrics

**Internal (Primary):**
- ✅ 50%+ of Mountain Ash tools use it
- ✅ Active internal development
- ✅ Proven value in production

**External (Secondary):**
- ✅ 5-10 external organizations using it
- ✅ 30-50 GitHub stars
- ✅ 2-3 external contributors
- ✅ Mentioned in Polars/Ibis communities

**Community (Tertiary):**
- ✅ Regular issue activity
- ✅ Questions on Stack Overflow
- ✅ Blog posts from users
- ✅ Conference talks mentioning it

### Feature Metrics

- ✅ Ternary logic implemented (differentiator)
- ✅ 80+ operations (80% of common needs)
- ✅ Natural language temporal helpers
- ✅ Window functions (analytic capability)
- ✅ ML metrics (domain-specific value)

---

## Critical Success Factors

### Must Haves

1. **Ternary Logic Implementation**
   - This is what makes us unique
   - No other Python library does this well
   - Critical for data quality use cases

2. **Internal Mountain Ash Adoption**
   - Proves real-world value
   - Drives development priorities
   - Validates the approach

3. **Maintenance Commitment**
   - 2+ active maintainers
   - Keep up with backend API changes (Polars especially)
   - Regular releases (quarterly minimum)

4. **Clear Documentation**
   - Why this instead of X?
   - Real-world examples
   - Migration guides
   - Limitations clearly stated

5. **Scope Discipline**
   - Resist feature creep
   - Stay focused on expression evaluation
   - Say "no" to non-core features

### Nice to Haves

- External contributors
- Community engagement
- Conference talks
- Blog posts
- Integration with popular tools

---

## What Good Looks Like (2-3 Years)

### Technical State

- ✅ 80-100 operations implemented (80% coverage of common needs)
- ✅ Ternary logic fully implemented and documented
- ✅ Clean, maintainable architecture (backend mixins, focused nodes)
- ✅ Excellent test coverage (90%+)
- ✅ Compatibility with latest Polars, Ibis, Narwhals
- ✅ Backend capability system (graceful degradation)

### Adoption State

- ✅ 50%+ of Mountain Ash tools using it
- ✅ 5-10 external organizations using it
- ✅ Known in Polars/Ibis communities
- ✅ "The ternary logic library" reputation
- ✅ 30-50 GitHub stars
- ✅ Stable user base (not massive, but engaged)

### Community State

- ✅ 2-3 active maintainers
- ✅ Quarterly releases
- ✅ Responsive to issues
- ✅ Clear roadmap
- ✅ Good documentation
- ✅ Examples and guides

### Recognition

- ✅ Mentioned in Polars/Ibis documentation or community
- ✅ 1-2 conference talks or blog posts
- ✅ Used by at least one popular library
- ✅ Recommended for specific use cases (ternary logic, portable filtering)

---

## What Bad Looks Like (Warning Signs)

### Technical Debt

- ❌ Test failures ignored
- ❌ Backend compatibility broken
- ❌ God classes remain
- ❌ Deprecated code piling up
- ❌ Type checking ignored

### Adoption Failure

- ❌ Mountain Ash tools don't use it
- ❌ No external users
- ❌ No community engagement
- ❌ Stale repository (no commits for months)
- ❌ No issues/questions (no one cares)

### Scope Creep

- ❌ Trying to match Ibis feature-for-feature
- ❌ Adding DataFrame operations (joins, groupby, pivot)
- ❌ Supporting obscure backends with limited use
- ❌ Perfect documentation obsession
- ❌ Feature bloat (150+ operations, most unused)

### Maintenance Burden

- ❌ One maintainer (bus factor = 1)
- ❌ Can't keep up with Polars API changes
- ❌ Backends diverging (Polars works, Ibis broken)
- ❌ Technical debt accumulating
- ❌ No time for new features (just maintenance)

---

## Recommendations for Success

### Short-Term (Next 3 Months)

1. **Add Alias node** (1-2 days) - critical missing functionality
2. **Backend refactoring** (3-4 weeks) - eliminate technical debt
3. **Polish README** (1-2 days) - clear messaging
4. **Phase 1: Math operations** (2-3 weeks) - quick win, high value
5. **Internal adoption push** - get Mountain Ash tools using it

### Medium-Term (3-12 Months)

6. **Phase 2-5: Core operations** (12 weeks) - breadth of coverage
7. **Ternary logic implementation** (2-3 weeks) - differentiator
8. **Documentation overhaul** - user-focused guides
9. **Case studies** - document real-world usage
10. **Community engagement** - Polars/Ibis communities

### Long-Term (1-3 Years)

11. **Phase 8: Window functions** (3-5 weeks) - major capability
12. **Phase 9: ML metrics** (4-7 weeks) - domain-specific value
13. **Stability and maintenance** - keep up with backends
14. **Ecosystem integration** - mentioned in docs, talks, posts
15. **Sustained internal adoption** - 50%+ of Mountain Ash tools

---

## Key Decisions & Philosophy

### Design Philosophy

1. **Portability over performance** - Some overhead is acceptable for cross-backend compatibility
2. **Correctness over completeness** - Better to have 50 operations that work perfectly than 150 with quirks
3. **Focused over comprehensive** - Expression evaluation, not full DataFrame API
4. **Type-safe over convenient** - Explicit is better than implicit
5. **Tested over assumed** - Cross-backend testing is non-negotiable

### Strategic Choices

1. **Ternary logic is our differentiator** - Invest in making this excellent
2. **Internal adoption proves value** - If Mountain Ash doesn't use it, why would anyone else?
3. **Quality over quantity** - 80 well-tested operations > 170 partially working
4. **Scope discipline** - Say "no" to features outside core mission
5. **Sustainable pace** - Better slow and steady than burnout

### Trade-offs We Accept

1. **Some overhead vs raw performance** - Abstraction has cost, backends optimize execution
2. **Limited backends vs universal support** - Focus on Polars/Ibis, not every backend
3. **Focused scope vs complete solution** - Filtering/expressions only, not full DataFrame API
4. **Niche audience vs mass adoption** - Specialized tool for specific use cases
5. **Maintainability vs features** - Refactoring takes time but pays off

---

## Conclusion

mountainash-expressions is **not trying to be the next Pandas or replace Polars.**

It's a **focused, high-quality library for portable DataFrame expression evaluation** with unique features (ternary logic, natural language temporal helpers) that solve real problems for a specific audience (library authors, platform teams, Mountain Ash tools).

**Success = being the best at what we do, not being the biggest.**

Our goal is to be:
- The go-to solution for **ternary logic** in Python DataFrames
- A **reliable abstraction** for cross-backend expression evaluation
- A **well-maintained, thoughtfully designed** specialized tool
- **Proven valuable** through internal Mountain Ash adoption
- **Known and respected** in the Polars/Ibis ecosystem

**Not:**
- A complete DataFrame library
- A SQL compiler
- A mass-market tool
- Competing with Polars/Ibis on features

**Our mantra:** Focus, quality, and sustainability over growth, features, and popularity.

---

**Let's build something focused, excellent, and genuinely useful.**

**Document Complete** ✅
