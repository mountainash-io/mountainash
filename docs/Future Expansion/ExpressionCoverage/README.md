# Future Expansion Documentation

This directory contains strategic planning documents for expanding mountainash-expressions to achieve feature parity with Ibis-Polars expression operations.

## Documents Overview

### 1. [Ibis-Polars-Comparison.md](./Ibis-Polars-Comparison.md)
**Comprehensive comparison analysis**

- Detailed category-by-category comparison
- Operation tables with implementation status
- Gap analysis with priorities
- Backend compatibility considerations
- ~11,000 words

**Use this for:**
- Understanding what operations exist in Ibis
- Detailed gap analysis
- Backend compatibility research
- Reference when implementing specific operations

### 2. [Implementation-Roadmap.md](./Implementation-Roadmap.md)
**7-phase implementation plan**

- Phase-by-phase breakdown
- Detailed implementation checklists
- Success criteria for each phase
- Timeline estimates (14-22 weeks total)
- Risk management

**Use this for:**
- Project planning
- Tracking implementation progress
- Understanding dependencies
- Resource allocation

### 3. [Quick-Gap-Reference.md](./Quick-Gap-Reference.md)
**Quick lookup guide**

- Summary tables
- Priority matrix
- Common questions
- Decision guide
- ~3,000 words

**Use this for:**
- Quick lookups during development
- Understanding priorities
- Making implementation decisions
- Status updates to stakeholders

---

## Key Findings Summary

### Current State (as of 2025-01-09)

**Coverage:** ~38-42% of Ibis-Polars expression operations

**Strengths:**
- ✅ Boolean/Logical: 100%+ (unique features)
- ✅ Arithmetic: 87.5%
- ✅ String (Basic): 100%
- ✅ Pattern/Regex: 100%+
- ✅ Temporal Arithmetic: 86%

**Critical Gaps:**
- ❌ Math Operations: 0% (26 operations missing)
- ❌ Window Functions: 0% (17 operations missing)
- ❌ Array Operations: 0% (18 operations missing)
- ❌ Temporal Construction/Parsing: 0% (12 operations missing)

**Total Gap:** 105 operations (to Ibis-Polars parity)

**Beyond Parity:**
- 🟡 ML/Statistical Metrics: +12 operations (Phase 9)
- Enables model evaluation and credit risk analytics

---

## Implementation Priority

### Phase 1: Essential Math (2-3 weeks) 🔴 CRITICAL
**Impact:** Enables analytical/scientific workloads
**Operations:** 12
- Basic: abs, sign, sqrt, round, floor, ceil
- Logarithms: ln, log, log10, log2, exp
- Checks: is_nan, is_inf

### Phase 2: Advanced Conditionals (1-2 weeks) 🔴 HIGH
**Impact:** Supports complex business logic
**Operations:** 5
- case(), least(), greatest(), nullif()

### Phase 3: String Enhancements (1-2 weeks) 🟡 MEDIUM
**Impact:** Enhances text processing
**Operations:** 10
- split(), find(), regex_extract(), capitalize(), etc.

### Phase 4: Temporal Construction & Parsing (2-3 weeks) 🟡 MEDIUM-HIGH
**Impact:** Essential for ETL workflows
**Operations:** 12
- date_from_ymd(), string_to_date(), strftime(), now(), etc.

### Phase 5: Advanced Math (2-3 weeks) 🟡 MEDIUM
**Impact:** Complete math support
**Operations:** 14
- Trigonometry: sin, cos, tan, asin, acos, atan, etc.
- Constants: pi, e

### Phase 6: Array Operations (4-6 weeks) 🔴 HIGH
**Impact:** Fundamental data structures
**Operations:** 18
**Note:** High complexity due to backend compatibility

### Phase 7: Specialized Operations (1-2 weeks) 🟢 LOW
**Impact:** Fill remaining gaps
**Operations:** 12
- Bitwise operations, misc enhancements

### Phase 8: Window/Analytic Functions (3-5 weeks) 🔴 CRITICAL
**Impact:** Essential for ranking, time series, sequential analysis
**Operations:** 17
- rank(), dense_rank(), row_number()
- lag(), lead(), nth_value()
- cumsum(), cummean(), cummin(), cummax()
- Window specification (.over() with PARTITION BY, ORDER BY, frames)

### Phase 9: ML/Statistical Metrics (4-7 weeks) 🟡 HIGH / 🟢 MEDIUM
**Impact:** Machine learning model evaluation and credit risk analytics
**Operations:** 12 (beyond Ibis-Polars parity)

**Phase 9A: Classification Metrics (1-2 weeks) 🟡 HIGH**
- precision(), recall(), f1_score(), accuracy()
- No dependencies (aggregations only)

**Phase 9B: Ranking Metrics (1-2 weeks) 🟡 HIGH**
- roc_auc(), gini(), log_loss()
- Requires Phase 8 (Window Functions)

**Phase 9C: Credit Risk Metrics (2-3 weeks) 🟢 MEDIUM**
- information_value(), weight_of_evidence(), psi(), marginal_iv()
- Optional, domain-specific

**Reference Documentation:**
- ML Research: `/docs/ML-Statistical-Functions-Research.md`
- User Implementation: `/docs/User-Metrics-Implementation-Analysis.md`
- Framework Analysis: `/docs/Framework-Architecture-Analysis.md`

---

## Unique mountainash-expressions Features

Features we have that Ibis-Polars does NOT:

1. **Ternary Logic System** - TRUE/FALSE/UNKNOWN three-valued logic
2. **XOR Parity** - Different semantics from exclusive XOR
3. **SQL LIKE Pattern** - Native SQL-style pattern matching
4. **Regex Full Match** - Stricter pattern validation
5. **Natural Language Temporal Helpers** - User-friendly time expressions

---

## Quick Links

### Internal Documentation
- [Project CLAUDE.md](../../CLAUDE.md) - Current architecture documentation
- [Backend Inconsistencies](../BACKEND_INCONSISTENCIES.md) - Known backend differences

### External References
- Ibis Documentation: https://ibis-project.org/
- Polars Documentation: https://pola-rs.github.io/polars/
- Ibis-Polars Compiler: `/home/nathanielramm/git/ibis/ibis/backends/polars/compiler.py`

---

## Using These Documents

### For Developers

**Starting a new phase?**
1. Read the relevant section in [Implementation-Roadmap.md](./Implementation-Roadmap.md)
2. Check detailed operations in [Ibis-Polars-Comparison.md](./Ibis-Polars-Comparison.md)
3. Follow the implementation checklist
4. Use [Quick-Gap-Reference.md](./Quick-Gap-Reference.md) for quick lookups

**Implementing a specific operation?**
1. Look up the operation in [Ibis-Polars-Comparison.md](./Ibis-Polars-Comparison.md)
2. Check backend compatibility notes
3. Reference Ibis implementation in compiler.py
4. Follow established patterns from existing code

### For Product/Project Management

**Planning work?**
1. Use [Implementation-Roadmap.md](./Implementation-Roadmap.md) for timeline estimates
2. Review priority matrix in [Quick-Gap-Reference.md](./Quick-Gap-Reference.md)
3. Consider dependencies between phases

**Reporting status?**
1. Use coverage metrics from [Quick-Gap-Reference.md](./Quick-Gap-Reference.md)
2. Reference phase completion from [Implementation-Roadmap.md](./Implementation-Roadmap.md)

### For Architecture Review

**Evaluating mountainash-expressions?**
1. Start with [Quick-Gap-Reference.md](./Quick-Gap-Reference.md) for overview
2. Review unique features section
3. Check detailed comparison for specific operation categories
4. Consider backend compatibility requirements

---

## Maintenance Schedule

### After Each Phase Completion
- [ ] Update coverage percentages
- [ ] Mark completed operations
- [ ] Update timelines based on actual effort
- [ ] Document any new findings

### Quarterly Reviews
- [ ] Re-evaluate priorities based on user feedback
- [ ] Assess backend compatibility landscape
- [ ] Update effort estimates
- [ ] Review and adjust roadmap

### Major Milestones
- [ ] 50% coverage reached
- [ ] 75% coverage reached
- [ ] 80% coverage reached (target)
- [ ] Feature parity achieved

---

## Contributing

When adding new operations or updating documentation:

1. **Update all three documents:**
   - Comparison: Add detailed operation info
   - Roadmap: Update implementation status
   - Quick Reference: Update summary tables

2. **Follow established patterns:**
   - Use consistent formatting
   - Include code examples
   - Document backend compatibility
   - Add to appropriate category

3. **Test thoroughly:**
   - Cross-backend tests
   - Edge cases
   - NULL handling
   - Document any backend-specific behavior

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-01-09 | Initial documentation created | Analysis of Ibis-Polars compiler |

---

## Contact & Questions

For questions about this documentation or the expansion roadmap:
- Review the [Quick-Gap-Reference.md](./Quick-Gap-Reference.md) FAQ section
- Check project CLAUDE.md for current architecture
- Consult detailed comparison for specific operations

---

**Last Updated:** 2025-01-09
**Next Review:** After Phase 1 completion
