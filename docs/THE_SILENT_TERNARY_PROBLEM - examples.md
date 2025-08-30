# The Silent Ternary Problem: Why Your Data Analysis is Secretly Broken


Consider this seemingly innocent query:
```sql
SELECT COUNT(*) FROM customers
WHERE age > 65;
```
 ==
```python
AGE_GT_65 = teb.gt('age', 65)
customers.filter( AGE_GT_65.is_true() );
```

Ternary Variant - allows easy keeping of missings, while being expressive of intent
```sql
SELECT COUNT(*) FROM customers
WHERE (age > 18 OR age IS NULL)
```
==
```python
AGE_GT_65 = teb.gt('age', 65)
customers.filter( AGE_GT_65.maybe_true() );
```



Consider the complexity this creates:
```sql
-- Simple filter becomes complex
WHERE (age > 18 OR age IS NULL)
  AND (income > 50000 OR income IS NULL)
  AND (status = 'active' OR status IS NULL)
```

```python
AGE_GT_65 =     teb.gt('age', 65)
INCOME_GT_50K = teb.gt('income', 50000)
STATUS_ACTIVE = teb.eq('status', 'active')

QUALIFYING_CUSTOMERS = teb.and(AGE_GT_65.maybe_true(),INCOME_GT_50K.maybe_true(),STATUS_ACTIVE.maybe_true())

customers.filter( QUALIFYING_CUSTOMERS );

```




```python
# Clear intent, no forgotten edge cases
customers.filter(age_condition.eval_is_true())      # Definite adults only
customers.filter(age_condition.eval_maybe_true())   # Adults + unknown ages
customers.filter(age_condition.eval_is_known())     # Exclude all uncertainty
customers.filter(age_condition.eval_is_unknown())   # Focus on data quality
```
