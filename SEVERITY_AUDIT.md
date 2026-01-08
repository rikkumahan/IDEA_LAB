# SEVERITY CLASSIFICATION AUDIT - MANDATORY OUTPUT FORMAT

## CONTEXT

**Current Scoring Formula:**
```python
score = 3 * intensity_count + 2 * complaint_count + 1 * workaround_count

if score >= 15:
    problem_level = "DRASTIC"
elif score >= 8:
    problem_level = "SEVERE"
elif score >= 4:
    problem_level = "MODERATE"
else:
    problem_level = "LOW"
```

**Existing Guardrail:**
- DRASTIC requires intensity_level == HIGH (intensity_count >= 5)
- Otherwise downgrade DRASTIC → SEVERE

**Signal Normalization:**
- LOW: count in [0, 1]
- MEDIUM: count in [2, 4]
- HIGH: count >= 5

---

## ISSUE 1: Low Intensity With High Complaints Can Trigger SEVERE Classification

**WHY IT MATTERS:**
A problem with many complaints but zero/minimal intensity signals should not be classified as SEVERE. This could happen when users discuss a problem casually without urgency keywords. The system overestimates severity based on volume alone without considering actual problem urgency.

**CURRENT BEHAVIOR:**
```python
# Test case: intensity_count=0, complaint_count=4, workaround_count=0
signals = {'intensity_count': 0, 'complaint_count': 4, 'workaround_count': 0}
score = 3*0 + 2*4 + 1*0 = 8
problem_level = "SEVERE"  # ← OVERESTIMATION

# Context: Many people mention the problem, but nobody says it's urgent/critical
# Example: "I have this problem" repeated 4 times vs "This is a CRITICAL problem"
```

**PROPOSED FIX:**
Add guardrail: **SEVERE requires intensity_count >= 1**
- If score >= 8 but intensity_count == 0, downgrade to MODERATE

```python
# After DRASTIC guardrail, before returning:
if problem_level == "SEVERE" and signals["intensity_count"] == 0:
    logger.info(
        f"Applying SEVERE guardrail: intensity_count=0, "
        f"downgrading from SEVERE to MODERATE"
    )
    problem_level = "MODERATE"
```

**JUSTIFICATION:**
- **Deterministic**: Simple count check (intensity_count == 0)
- **Conservative**: Prevents false urgency from complaint volume alone
- **Concrete failure mode**: Protects against viral complaints without actual urgency
- **Risk mitigation**: High complaint volume ≠ high severity without intensity signals

**RISK LEVEL:** LOW
Simple threshold check with clear business logic. Minimal risk of false negatives.

---

## ISSUE 2: Workaround-Heavy Problems Can Inflate Score Without True Severity

**WHY IT MATTERS:**
A problem with many workaround signals but low complaints/intensity may represent a **solved** or **manageable** problem, not a severe one. The current formula can classify this as MODERATE/SEVERE when it should be LOW.

**CURRENT BEHAVIOR:**
```python
# Test case: intensity_count=0, complaint_count=1, workaround_count=6
signals = {'intensity_count': 0, 'complaint_count': 1, 'workaround_count': 6}
score = 3*0 + 2*1 + 1*6 = 8
problem_level = "SEVERE"  # ← OVERESTIMATION

# Context: One person complains, but 6 documents show workaround solutions
# This suggests the problem is manageable, not severe
```

**PROPOSED FIX:**
Add guardrail: **Cap workaround contribution when intensity/complaint are low**
- If intensity_count == 0 AND complaint_count <= 1, cap effective workaround_count at 3

```python
# Calculate effective workaround count with cap
effective_workaround = workaround_count
if signals["intensity_count"] == 0 and signals["complaint_count"] <= 1:
    effective_workaround = min(workaround_count, 3)
    if effective_workaround < workaround_count:
        logger.info(
            f"Applying workaround cap: intensity=0, complaints={signals['complaint_count']}, "
            f"capping workaround from {workaround_count} to {effective_workaround}"
        )

# Use effective count in score calculation
score = (
    3 * signals["intensity_count"] +
    2 * signals["complaint_count"] +
    1 * effective_workaround
)
```

**JUSTIFICATION:**
- **Deterministic**: Fixed threshold (intensity=0, complaints<=1) and cap (max=3)
- **Business logic**: Many workarounds suggest problem is solvable/manageable
- **Prevents inflation**: Workaround-only problems shouldn't reach SEVERE
- **Conservative**: Only applies when both intensity and complaints are minimal

**RISK LEVEL:** MEDIUM
Changes scoring behavior. However, capping at 3 still allows MODERATE classification (score=5), preventing complete dismissal of real problems.

---

## ISSUE 3: Score Exactly at Threshold Boundaries Can Be Unstable

**WHY IT MATTERS:**
When scores fall exactly on threshold boundaries (score=4, score=8, score=15), small variations in signal counts cause dramatic severity jumps. This creates instability in classification.

**CURRENT BEHAVIOR:**
```python
# Edge case 1: score = 8 exactly
signals1 = {'intensity_count': 1, 'complaint_count': 2, 'workaround_count': 1}
score1 = 3*1 + 2*2 + 1*1 = 8
problem_level1 = "SEVERE"  # ← At threshold

# Edge case 2: score = 7 (one less signal)
signals2 = {'intensity_count': 1, 'complaint_count': 2, 'workaround_count': 0}
score2 = 3*1 + 2*2 + 1*0 = 7
problem_level2 = "MODERATE"  # ← Just below threshold

# One workaround signal causes MODERATE → SEVERE jump
```

**PROPOSED FIX:**
**DO NOT implement hysteresis/fuzzy boundaries**
- Current sharp thresholds are intentional and deterministic
- Adding buffer zones would require arbitrary constants
- Classification instability at boundaries is acceptable trade-off for simplicity

**JUSTIFICATION:**
- **Sharp boundaries are a feature**: They provide clear decision points
- **Deterministic is priority**: Fuzzy logic would violate constraint
- **Real-world mitigation**: Multiple search results smooth out noise
- **Edge cases are rare**: Most problems don't land exactly on boundaries

**RISK LEVEL:** NONE (not an issue - working as designed)

---

## ISSUE 4: Zero Signals of All Types Should Always Be LOW

**WHY IT MATTERS:**
If all signal counts are zero, the problem should always be classified as LOW regardless of any logic. This is a sanity check to prevent bugs or edge cases from producing incorrect classifications.

**CURRENT BEHAVIOR:**
```python
# Test case: all zeros
signals = {'intensity_count': 0, 'complaint_count': 0, 'workaround_count': 0}
score = 3*0 + 2*0 + 1*0 = 0
problem_level = "LOW"  # ← CORRECT (but no explicit check)
```

Currently works correctly by default, but no explicit guardrail exists.

**PROPOSED FIX:**
Add explicit zero-signal check at the start:

```python
# Add at the beginning of classify_problem_level()
total_signals = (
    signals["intensity_count"] + 
    signals["complaint_count"] + 
    signals["workaround_count"]
)

if total_signals == 0:
    logger.info("Zero signals detected - returning LOW")
    return "LOW"
```

**JUSTIFICATION:**
- **Defensive programming**: Explicit check prevents future bugs
- **Deterministic**: Simple arithmetic check
- **Sanity check**: No signals = no problem
- **Early exit**: Avoids unnecessary computation

**RISK LEVEL:** LOW
Pure defensive programming with no behavior change for current logic.

---

## ISSUE 5: Extremely High Workaround Count Can Dominate Score

**WHY IT MATTERS:**
Due to unbounded workaround counts, a problem could reach SEVERE classification through workarounds alone, even with zero intensity. A score of 8 from workarounds alone requires workaround_count=8, but with cap from ISSUE 2 fix, maximum would be 3.

**CURRENT BEHAVIOR:**
```python
# Test case: extreme workaround dominance
signals = {'intensity_count': 0, 'complaint_count': 0, 'workaround_count': 15}
score = 3*0 + 2*0 + 1*15 = 15
problem_level = "DRASTIC"  # ← Would be downgraded to SEVERE by existing guardrail

# After existing DRASTIC guardrail (intensity_level != HIGH):
problem_level = "SEVERE"  # ← Still OVERESTIMATION for workarounds-only
```

**PROPOSED FIX:**
This is already addressed by **ISSUE 2 fix** (workaround cap).
- With ISSUE 2 cap in place: max workaround contribution when intensity=0 and complaints<=0 is 3
- New score: 3*0 + 2*0 + 1*3 = 3 → "LOW" (correct)

No additional fix needed.

**JUSTIFICATION:**
ISSUE 2 cap prevents this scenario by limiting workaround contribution when other signals are absent.

**RISK LEVEL:** NONE (resolved by ISSUE 2 fix)

---

## ISSUE 6: Single High-Intensity Signal With No Other Signals Can Trigger MODERATE

**WHY IT MATTERS:**
A single intensity keyword match (intensity_count=1) with no complaints or workarounds may be a false positive. Current behavior classifies this as MODERATE, which could be appropriate or overestimation depending on context.

**CURRENT BEHAVIOR:**
```python
# Test case: single intensity signal
signals = {'intensity_count': 1, 'complaint_count': 0, 'workaround_count': 0}
score = 3*1 + 2*0 + 1*0 = 3
problem_level = "LOW"  # ← Currently LOW

# Test case: intensity=2 (just above threshold)
signals = {'intensity_count': 2, 'complaint_count': 0, 'workaround_count': 0}
score = 3*2 + 2*0 + 1*0 = 6
problem_level = "MODERATE"  # ← Single intensity source, no corroboration
```

**PROPOSED FIX:**
**DO NOT add additional guardrail**
- Intensity keywords are high-weight (3x) for a reason (urgent, critical, blocking)
- Single intensity match at count=1 → score=3 → LOW (appropriate)
- Two intensity matches at count=2 → score=6 → MODERATE (reasonable)
- Intensity signals should carry weight even without complaints

**JUSTIFICATION:**
- **Intensity is high-priority**: Words like "critical", "blocking", "urgent" indicate severity
- **Current thresholds are reasonable**: Requires intensity_count >= 2 for MODERATE
- **No underestimation risk**: Critical problems should be flagged even with sparse data

**RISK LEVEL:** NONE (not an issue - working as designed)

---

## SUMMARY OF PROPOSED GUARDRAILS

### Guardrails to Implement:

1. ✅ **SEVERE requires intensity_count >= 1**
   - If score >= 8 but intensity_count == 0 → downgrade to MODERATE
   - Prevents false urgency from complaint volume alone

2. ✅ **Workaround cap when intensity/complaints are minimal**
   - If intensity_count == 0 AND complaint_count <= 1 → cap workaround at 3
   - Prevents workaround-only problems from inflating severity

3. ✅ **Zero-signal sanity check**
   - If all counts == 0 → return LOW immediately
   - Defensive programming to prevent edge cases

### Guardrails NOT to Implement:

4. ❌ **Threshold boundary smoothing** (ISSUE 3)
   - Sharp boundaries are intentional and deterministic
   - Fuzzy logic would violate constraints

5. ❌ **Single intensity downgrade** (ISSUE 6)
   - Current behavior is appropriate
   - Intensity signals should carry weight

### Implementation Order:

1. Zero-signal check (first, early exit)
2. Workaround cap calculation
3. Score calculation with capped workaround
4. Initial classification based on score
5. DRASTIC guardrail (existing)
6. SEVERE guardrail (new)
7. Return problem_level

---

## RISK ASSESSMENT

**Overall Risk Level:** LOW to MEDIUM

**Low Risk Components:**
- Zero-signal check (defensive programming, no behavior change)
- SEVERE intensity guardrail (prevents clear overestimation)

**Medium Risk Components:**
- Workaround cap (changes scoring behavior, but with clear business logic)

**Mitigation:**
- All guardrails are deterministic and rule-based
- Each guardrail prevents a concrete failure mode
- Comprehensive test coverage for all scenarios
- Conservative thresholds to minimize false negatives

---

## VALIDATION REQUIREMENTS

Each guardrail must be tested with:
1. ✅ Edge case where guardrail triggers (activation test)
2. ✅ Edge case where guardrail doesn't trigger (boundary test)
3. ✅ Integration with existing DRASTIC guardrail
4. ✅ Assertion checks to verify invariants
