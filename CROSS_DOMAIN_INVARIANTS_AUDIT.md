# CROSS-DOMAIN INVARIANTS AUDIT

**Date:** 2026-01-09  
**Task:** Identify cross-problem invariants and ratio-dependent behavior  
**Scope:** Global system behavior independent of problem domain

---

## INVARIANT 1: SEVERITY MUST RESPECT TOTAL SIGNAL FLOOR

### WHY IT MUST HOLD:
A problem with very few total signals (e.g., 3 signals) should NEVER be classified as DRASTIC or SEVERE, regardless of their type ratio. The severity level should reflect the STRENGTH OF EVIDENCE, which requires a minimum volume of signals to be credible.

### CURRENT VIOLATION EXAMPLE:
```python
# Case 1: Only 3 total signals
signals = {'intensity_count': 2, 'complaint_count': 1, 'workaround_count': 0}
# Score: 2*3 + 1*2 + 0*1 = 8
# Result: SEVERE (passes score >= 8 threshold)

# Case 2: 4 total signals
signals = {'intensity_count': 0, 'complaint_count': 4, 'workaround_count': 0}
# Score: 0*3 + 4*2 + 0*1 = 8
# Result: MODERATE (SEVERE guardrail downgrades due to intensity=0)
```

**Issue:** A problem with only 3 signals can reach SEVERE, while one with 4 signals gets MODERATE. The weighted scoring allows sparse data to achieve high severity levels based purely on signal type ratio, not data quality.

### PROPOSED GUARD:
```python
def classify_problem_level(signals):
    # ... existing code ...
    
    # INVARIANT GUARD: Minimum total signals for each severity level
    total_signals = intensity_count + complaint_count + workaround_count
    
    # Enforce absolute minimums regardless of score
    if problem_level == "DRASTIC" and total_signals < 10:
        logger.info(
            f"DRASTIC invariant guard: total_signals={total_signals} < 10, "
            f"downgrading to SEVERE"
        )
        problem_level = "SEVERE"
    
    if problem_level == "SEVERE" and total_signals < 6:
        logger.info(
            f"SEVERE invariant guard: total_signals={total_signals} < 6, "
            f"downgrading to MODERATE"
        )
        problem_level = "MODERATE"
    
    if problem_level == "MODERATE" and total_signals < 3:
        logger.info(
            f"MODERATE invariant guard: total_signals={total_signals} < 3, "
            f"downgrading to LOW"
        )
        problem_level = "LOW"
    
    return problem_level
```

### RISK IF IGNORED:
- **False urgency:** Sparse data with favorable ratios triggers high severity alerts
- **Cross-domain inconsistency:** Same severity level represents vastly different evidence volumes
- **Undermined confidence:** High severity ratings based on 3-4 signals lack statistical credibility
- **Gaming risk:** Easy to manipulate severity by targeting specific signal types

---

## INVARIANT 2: MAXIMUM SEVERITY MUST HAVE INTENSITY FLOOR

### WHY IT MUST HOLD:
The DRASTIC severity level should represent IMMEDIATE, CRITICAL problems. Currently, it requires only `intensity_level == HIGH` (5+ intensity signals) but this can be achieved with relatively few signals if complaint/workaround counts are high. DRASTIC should require a MINIMUM intensity count to justify the urgency label.

### CURRENT VIOLATION EXAMPLE:
```python
# Current rule: DRASTIC requires intensity_level == HIGH (5+ intensity signals)
# But this can be satisfied with exactly 5 intensity signals

signals = {'intensity_count': 5, 'complaint_count': 10, 'workaround_count': 0}
# Score: 5*3 + 10*2 + 0 = 35 (>= 15)
# intensity_level: HIGH (5 >= 5)
# Result: DRASTIC

# vs. SEVERE with more total evidence:
signals = {'intensity_count': 4, 'complaint_count': 15, 'workaround_count': 5}
# Score: 4*3 + 15*2 + 5 = 47 (>= 15)
# intensity_level: MEDIUM (4 < 5)
# Result: SEVERE (downgraded from DRASTIC)
```

**Issue:** The first case (25 total signals) gets DRASTIC, while the second (24 total signals with more evidence) gets SEVERE, purely because intensity crossed a threshold by 1 signal.

### PROPOSED GUARD:
```python
def classify_problem_level(signals):
    # ... existing code ...
    
    # INVARIANT GUARD: DRASTIC requires substantial intensity evidence
    # Current: intensity_level == HIGH (5+ signals)
    # Enhanced: intensity_count >= 7 AND intensity_level == HIGH
    
    if problem_level == "DRASTIC":
        if intensity_count < 7:
            logger.info(
                f"DRASTIC intensity floor guard: intensity_count={intensity_count} < 7, "
                f"downgrading to SEVERE despite intensity_level={intensity_level}"
            )
            problem_level = "SEVERE"
    
    return problem_level
```

### RISK IF IGNORED:
- **Brittle boundaries:** Single signal difference (4 vs 5 intensity) causes large severity jump
- **Ratio gaming:** Can achieve DRASTIC by barely meeting intensity threshold + high other signals
- **Inconsistent urgency:** DRASTIC label applied to marginally urgent cases
- **Operational noise:** Too many DRASTIC alerts reduce response effectiveness

---

## INVARIANT 3: WORKAROUND CAP MUST BE ABSOLUTE, NOT CONDITIONAL

### WHY IT MUST HOLD:
The workaround cap (max 3 when intensity=0 AND complaints<=1) is RATIO-DEPENDENT. This means the same workaround count contributes differently to severity based on OTHER signal ratios, creating cross-domain inconsistency. Workaround contribution should depend only on workaround count itself, not on intensity/complaint ratios.

### CURRENT VIOLATION EXAMPLE:
```python
# Case 1: Workaround capped
signals = {'intensity_count': 0, 'complaint_count': 1, 'workaround_count': 10}
# Effective workaround: min(10, 3) = 3 (cap applies)
# Score: 0*3 + 1*2 + 3*1 = 5
# Result: MODERATE

# Case 2: No cap (intensity > 0)
signals = {'intensity_count': 1, 'complaint_count': 1, 'workaround_count': 10}
# Effective workaround: 10 (no cap)
# Score: 1*3 + 1*2 + 10*1 = 15
# Result: SEVERE

# Case 3: No cap (complaints > 1)
signals = {'intensity_count': 0, 'complaint_count': 2, 'workaround_count': 10}
# Effective workaround: 10 (no cap)
# Score: 0*3 + 2*2 + 10*1 = 14
# Result: MODERATE (SEVERE guardrail downgrades due to intensity=0)
```

**Issue:** Same workaround count (10) contributes 3, 10, or 10 to score depending on intensity/complaint ratios. This violates signal independence.

### PROPOSED GUARD:
```python
def classify_problem_level(signals):
    intensity_count = signals.get("intensity_count", 0)
    complaint_count = signals.get("complaint_count", 0)
    workaround_count = signals.get("workaround_count", 0)
    
    # INVARIANT GUARD: Workaround cap is ABSOLUTE, not conditional
    # Cap workarounds at reasonable maximum regardless of other signals
    MAX_WORKAROUND_CONTRIBUTION = 5
    
    effective_workaround = min(workaround_count, MAX_WORKAROUND_CONTRIBUTION)
    
    if effective_workaround < workaround_count:
        logger.info(
            f"Workaround absolute cap: {workaround_count} → {effective_workaround} "
            f"(unconditional maximum)"
        )
    
    # Calculate score with capped workaround
    score = (
        3 * intensity_count +
        2 * complaint_count +
        1 * effective_workaround
    )
    
    # ... rest of classification logic ...
```

**Alternative:** Remove workaround cap entirely and let all signals contribute equally based on their weight.

### RISK IF IGNORED:
- **Ratio dependency:** Workaround contribution varies based on intensity/complaint levels
- **Unpredictable scoring:** Same workaround count produces different severities across domains
- **Signal coupling:** Workaround signals become dependent on intensity/complaint signals
- **Analysis confusion:** Users cannot predict how workarounds affect severity

---

## INVARIANT 4: SEVERITY LEVELS MUST HAVE SCORE RANGES, NOT JUST MINIMUMS

### WHY IT MUST HOLD:
Current thresholds are minimums only:
- score >= 15: DRASTIC
- score >= 8: SEVERE
- score >= 4: MODERATE
- score < 4: LOW

This means a problem with score=32 gets the same DRASTIC label as one with score=15, despite 2x the evidence. This creates a CEILING EFFECT where severity cannot increase beyond DRASTIC regardless of signal strength.

### CURRENT VIOLATION EXAMPLE:
```python
# Case 1: Barely DRASTIC
signals = {'intensity_count': 5, 'complaint_count': 0, 'workaround_count': 0}
# Score: 5*3 + 0*2 + 0*1 = 15
# Result: DRASTIC

# Case 2: Extremely DRASTIC
signals = {'intensity_count': 10, 'complaint_count': 10, 'workaround_count': 10}
# Score: 10*3 + 10*2 + 10*1 = 60
# Result: DRASTIC (same label, 4x the score)
```

**Issue:** No way to distinguish between "barely urgent" and "extremely urgent" problems. All high-signal problems collapse into single DRASTIC bucket.

### PROPOSED GUARD:
```python
def classify_problem_level(signals):
    # ... calculate score ...
    
    # INVARIANT GUARD: Add score range maximums
    # This ensures severity reflects the FULL range of evidence strength
    
    if score >= 25:
        problem_level = "CRITICAL"  # New top tier
    elif score >= 15:
        problem_level = "DRASTIC"
    elif score >= 8:
        problem_level = "SEVERE"
    elif score >= 4:
        problem_level = "MODERATE"
    else:
        problem_level = "LOW"
    
    # Apply existing guardrails...
    # (intensity_level, intensity_count checks)
    
    return problem_level
```

**Note:** This adds a new severity level. Alternative is to add score ranges to existing levels for internal tracking.

### RISK IF IGNORED:
- **Loss of granularity:** Cannot distinguish between moderately and extremely urgent problems
- **Operational inefficiency:** All DRASTIC problems treated equally despite evidence differences
- **Score inflation meaningless:** Accumulating more signals beyond threshold provides no additional signal
- **Gaming immunity:** No penalty for under-reporting if you're already above threshold

---

## INVARIANT 5: TOTAL SIGNAL COUNT MUST BOUND MAXIMUM SEVERITY

### WHY IT MUST HOLD:
Even with perfect signal ratios, a problem with very few total signals should have a MAXIMUM achievable severity. This prevents ratio optimization from inflating severity with sparse data.

### CURRENT VIOLATION EXAMPLE:
```python
# Achievable with minimal data via ratio optimization:
signals = {'intensity_count': 5, 'complaint_count': 0, 'workaround_count': 0}
# Total: 5 signals
# Score: 15
# Result: DRASTIC

# More evidence but worse ratio:
signals = {'intensity_count': 4, 'complaint_count': 10, 'workaround_count': 10}
# Total: 24 signals
# Score: 42
# Result: SEVERE (downgraded due to intensity=4 < 5)
```

**Issue:** 5 signals can achieve DRASTIC, while 24 signals gets SEVERE. Total evidence volume is ignored in favor of type ratio.

### PROPOSED GUARD:
```python
def classify_problem_level(signals):
    # ... existing classification ...
    
    # INVARIANT GUARD: Total signal count bounds maximum severity
    total_signals = intensity_count + complaint_count + workaround_count
    
    # Define maximum achievable severity based on total evidence
    if total_signals < 5:
        max_severity = "LOW"
    elif total_signals < 10:
        max_severity = "MODERATE"
    elif total_signals < 20:
        max_severity = "SEVERE"
    else:
        max_severity = "DRASTIC"  # or CRITICAL if added
    
    # Enforce maximum
    severity_order = ["LOW", "MODERATE", "SEVERE", "DRASTIC"]
    problem_level_index = severity_order.index(problem_level)
    max_severity_index = severity_order.index(max_severity)
    
    if problem_level_index > max_severity_index:
        logger.info(
            f"Total signal ceiling: {total_signals} signals caps severity at {max_severity}, "
            f"downgrading from {problem_level}"
        )
        problem_level = max_severity
    
    return problem_level
```

### RISK IF IGNORED:
- **Sparse data bias:** Small samples with lucky ratios get disproportionate severity
- **Statistical invalidity:** High severity based on insufficient evidence volume
- **Ratio gaming:** Optimizing signal types more valuable than gathering more evidence
- **False urgency:** Alerts fire on thin data that happens to have good ratios

---

## SUMMARY: PROPOSED INVARIANT GUARDS

### Guards to Add (in order of application):

1. **Zero-signal check** (already exists) ✓
2. **Total signal floor for each severity level** (NEW)
   - DRASTIC requires >= 10 total signals
   - SEVERE requires >= 6 total signals
   - MODERATE requires >= 3 total signals
3. **Intensity absolute floor for DRASTIC** (NEW)
   - DRASTIC requires >= 7 intensity signals (not just level=HIGH)
4. **Workaround absolute cap** (ENHANCED)
   - Cap at 5 unconditionally (remove conditional cap)
5. **Total signal ceiling for maximum severity** (NEW)
   - < 5 total → max LOW
   - < 10 total → max MODERATE
   - < 20 total → max SEVERE
6. **Existing guardrails** (keep)
   - DRASTIC requires intensity_level == HIGH
   - SEVERE requires intensity_count >= 1

### Priority Order:
1. **HIGH PRIORITY:** Total signal floor (Invariant 1)
2. **HIGH PRIORITY:** Total signal ceiling (Invariant 5)
3. **MEDIUM PRIORITY:** Workaround absolute cap (Invariant 3)
4. **LOW PRIORITY:** Intensity floor for DRASTIC (Invariant 2)
5. **OPTIONAL:** Score range maximums (Invariant 4)

---

## RISK ASSESSMENT IF IGNORED

### Operational Risks:
- **Alert fatigue:** Sparse data triggers high-severity alerts
- **Resource misallocation:** DRASTIC alerts on weak evidence divert resources
- **Inconsistent response:** Same severity label represents different evidence strength

### System Risks:
- **Cross-domain variability:** Same total signals produce different severities based on domain
- **Ratio gaming:** Users can optimize signal types to inflate severity
- **Statistical invalidity:** High severity claims based on insufficient sample sizes
- **Unpredictable behavior:** Severity changes non-monotonically with evidence volume

### Business Risks:
- **Lost trust:** Users see severity labels that don't match their intuition
- **Missed opportunities:** Real urgent problems obscured by ratio-inflated noise
- **Decision errors:** Severity-based decisions made on insufficient evidence

---

## IMPLEMENTATION NOTES

### Testing Requirements:
- Validate all guards with boundary test cases
- Ensure guards apply in correct order
- Check that existing guardrails still work
- Verify cross-domain consistency improves

### Backward Compatibility:
- Most guards will LOWER severity (downgrade sparse data)
- Some existing SEVERE/DRASTIC classifications may become MODERATE
- This is DESIRABLE - reduces false urgency

### Logging:
- All guards should log when they apply
- Include before/after severity levels
- Log total signal counts for analysis

### Monitoring:
- Track guard activation frequency
- Monitor severity distribution changes
- Watch for patterns in which guards fire most often

---

**Audit Complete:** 2026-01-09  
**Recommendation:** Implement Invariants 1, 3, and 5 as minimum viable hardening
