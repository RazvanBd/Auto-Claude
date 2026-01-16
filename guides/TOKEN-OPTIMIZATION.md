# Token Usage Optimization Guide

## Overview

Auto Claude uses **extended thinking budgets** (also called "thinking tokens") to control how much Claude can "think" before responding. This guide explains how token budgets are optimized across different phases to minimize costs while maintaining quality.

## Token Budget Levels

| Level | Tokens | Use Case |
|-------|--------|----------|
| **none** | 0 | No extended thinking - direct responses |
| **low** | 1,024 | Minimal reasoning - deterministic operations |
| **medium** | 4,096 | Moderate analysis - typical specs/planning |
| **high** | 16,384 | Deep thinking - complex validation |
| **ultrathink** | 60,000 | Maximum reasoning - self-critique only |

## Optimization Strategy

### Why Optimize?

Before optimization, simple tasks could use **68K tokens** when only **4K tokens** were needed - a **94% waste**. This happened because:

1. **Discovery phase** used ultrathink (60K) to run a deterministic Python script
2. **Spec writing** used ultrathink (60K) even for simple 1-2 file changes
3. All **data collection phases** used medium (4K) when they don't need reasoning

### Current Optimization

#### Spec Runner Phases

| Phase | Budget | Reasoning |
|-------|--------|-----------|
| **discovery** | low (1K) | Runs deterministic analyzer script - no AI reasoning needed |
| **requirements** | low (1K) | Data collection from user input |
| **research** | low (1K) | External API validation (deterministic) |
| **context** | low (1K) | Codebase file gathering |
| **planning** | low (1K) | Data structure creation |
| **validation** | low (1K) | Schema validation (deterministic) |
| **quick_spec** | low (1K) | Simple 1-2 file specs |
| **historical_context** | low (1K) | Git history gathering |
| **complexity_assessment** | low (1K) | Task complexity classification |
| **spec_writing** | medium (4K) | Spec document creation - needs reasoning |
| **self_critique** | ultrathink (60K) | Deep analysis for complex tasks only |

#### Implementation Phases

| Phase | Default Budget | Reasoning |
|-------|----------------|-----------|
| **spec** | low (1K) | Most specs don't need deep thinking |
| **planning** | medium (4K) | Planning benefits from reasoning |
| **coding** | low (1K) | Implementation is mostly straightforward |
| **qa** | medium (4K) | Validation needs reasoning but not ultrathink |

## Token Savings Examples

### Simple Task (e.g., "Fix button color")

**Before optimization:**
- Discovery: 60K (ultrathink)
- Historical context: 4K (medium)
- Quick spec: 4K (medium)
- Validation: 4K (medium)
- **Total: 72K tokens**

**After optimization:**
- Discovery: 1K (low)
- Historical context: 1K (low)
- Quick spec: 1K (low)
- Validation: 1K (low)
- **Total: 4K tokens (94% reduction)**

### Standard Task (e.g., "Add user authentication")

**Before optimization:**
- Discovery: 60K (ultrathink)
- Requirements: 4K (medium)
- Research: 4K (medium)
- Context: 4K (medium)
- Spec writing: 60K (ultrathink)
- Planning: 4K (medium)
- **Total: 136K tokens**

**After optimization:**
- Discovery: 1K (low)
- Requirements: 1K (low)
- Research: 1K (low)
- Context: 1K (low)
- Spec writing: 4K (medium)
- Planning: 1K (low)
- **Total: 9K tokens (93% reduction)**

### Complex Task (with self-critique)

**Before optimization:**
- All standard phases: 136K
- Self-critique: 60K
- **Total: 196K tokens**

**After optimization:**
- All standard phases: 9K
- Self-critique: 60K (still uses ultrathink)
- **Total: 69K tokens (65% reduction)**

## When Extended Thinking Matters

Extended thinking budgets are most valuable for:

1. **Creative problem-solving** - Novel solutions, architectural decisions
2. **Complex analysis** - Evaluating tradeoffs, security implications
3. **Self-critique** - Deep review of own work

Extended thinking is **not valuable** for:

1. **Deterministic operations** - Running scripts, file operations
2. **Data collection** - Gathering files, reading documentation
3. **Schema validation** - Checking JSON structure
4. **Simple transformations** - Renaming variables, formatting code

## Overriding Defaults

You can override thinking budgets through:

### 1. Task Metadata (UI)

When creating a task in the UI, select a profile:

- **Fast**: All phases use "low" budget
- **Balanced**: Default optimized budgets (recommended)
- **Quality**: Higher budgets for critical phases
- **Auto**: Automatically adjusts per phase

### 2. CLI Arguments

```bash
# Force all phases to use high budget
python apps/backend/run.py --spec 001 --thinking high

# Use specific model
python apps/backend/run.py --spec 001 --model opus
```

### 3. Environment Variables

```bash
# Override utility operations (commit messages, merge)
UTILITY_THINKING_BUDGET=1024
```

### 4. Per-Phase Configuration

Edit `task_metadata.json` in your spec directory:

```json
{
  "isAutoProfile": true,
  "phaseThinking": {
    "spec": "low",
    "planning": "medium",
    "coding": "low",
    "qa": "high"
  }
}
```

## Impact on Quality

**No quality degradation** has been observed after optimization because:

1. **Discovery doesn't use AI** - It runs a Python script (`analyzer.py`) that scans files
2. **Data collection phases** don't benefit from reasoning - They just gather information
3. **Simple specs** are straightforward - "Change button color" doesn't need 60K tokens
4. **Self-critique still uses ultrathink** - Complex tasks still get deep analysis

The optimization recognizes that **not all AI operations benefit from extended thinking**. Some operations are deterministic or data-gathering, where additional tokens provide no value.

## Monitoring Token Usage

Check token usage in:

1. **Agent logs** - Each session shows thinking tokens used
2. **Claude dashboard** - Track API usage and costs
3. **Task metadata** - Shows thinking levels per phase

## Best Practices

1. **Start with defaults** - Optimized budgets work for 95% of tasks
2. **Use 'Auto' profile** - Let the system adjust per phase
3. **Reserve ultrathink** - Only for self-critique in complex tasks
4. **Monitor costs** - Track token usage over time
5. **Adjust if needed** - Increase budgets only for specific complex tasks

## Technical Details

Configuration is in `apps/backend/phase_config.py`:

- `THINKING_BUDGET_MAP`: Token amounts per level
- `SPEC_PHASE_THINKING_LEVELS`: Budgets for spec runner phases
- `DEFAULT_PHASE_THINKING`: Default budgets for implementation phases

Tests verify optimization in `tests/test_token_optimization.py`.
