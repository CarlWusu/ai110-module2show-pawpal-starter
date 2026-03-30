# PawPal+ (Module 2 Project)

**PawPal+** is a Streamlit app that helps a busy pet owner plan, prioritise, and track daily care tasks across multiple pets.

## Features

- **Owner & pet setup** — Enter your name, daily time budget, and one or more pets (name, species, age, breed).
- **Task management** — Add care tasks with title, duration, priority (high / medium / low), type, frequency, optional start time, and description. Assign each task to a specific pet.
- **Priority-based scheduling** — Tasks are sorted high → medium → low, then selected greedily to fit within the owner's available time. Tasks that don't fit are listed as skipped with an explanation.
- **Sort by time** — The schedule and task table are displayed in chronological order by `start_time` (HH:MM). Tasks without a time appear last.
- **Filter by pet or status** — The task table can be filtered by pet name and/or completion status (pending / complete) using dropdown controls.
- **Recurring tasks** — Marking a `daily` or `weekly` task complete automatically advances its `next_due` date (tomorrow or +7 days). The scheduler suppresses that task until it is due again.
- **Conflict detection** — If two scheduled tasks have overlapping time windows, a warning banner appears above the plan with a detailed breakdown of each conflict. The schedule is not blocked — the owner decides how to resolve it.
- **Completion tracking** — Mark tasks done from a dropdown; a progress bar and summary show how many of the day's tasks are complete. Recurring tasks display their next due date on completion.
- **Plan reasoning** — An expandable "How was this plan built?" section explains exactly why each task was included or skipped.
- **Reset day** — One button clears all completion statuses and the current plan so a fresh day can begin.

## 📸 Demo

<a href="/course_images/ai110/pawpal_screenshot.png" target="_blank">
  <img src='/course_images/ai110/pawpal_screenshot.png' title='PawPal App' width='' alt='PawPal App' class='center-block' />
</a>

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Smarter Scheduling

Beyond basic priority ordering, PawPal+ includes four algorithmic improvements:

**Sort by time** — `Scheduler.sort_by_time(tasks)` orders any task list by `start_time` (HH:MM), placing tasks with no time assigned at the end. Useful for displaying the day in chronological order.

**Filter by pet or status** — `Scheduler.filter_tasks(pet_name, status)` returns tasks matching a specific pet and/or completion status (`"pending"` / `"complete"`). Both parameters are optional and can be combined.

**Recurring tasks** — When `mark_task_complete()` is called on a `"daily"` or `"weekly"` task, a `next_due` date is set automatically (today + 1 day or today + 7 days). The scheduler excludes tasks whose `next_due` is in the future, so completed recurring tasks reappear only when they are actually due again.

**Conflict detection** — `Scheduler.detect_conflicts(tasks)` checks whether any two timed tasks overlap (`[start, start + duration)` window comparison). It returns a list of human-readable warning strings rather than crashing, so the owner can decide how to resolve each conflict.

## Testing PawPal+

Run the full test suite from the project root:

```bash
python -m pytest
```

Or with verbose output to see each test name:

```bash
python -m pytest -v
```

### What the tests cover

| Area | Tests |
|---|---|
| **Task completion** | `mark_complete()` flips status; `reset()` clears it |
| **Recurring tasks** | Daily tasks set `next_due` to tomorrow; weekly to +7 days; as-needed gets no date |
| **Recurrence gating** | Completed recurring tasks are excluded from today's schedule until due again |
| **Sorting** | Tasks sort chronologically by `start_time`; no-time tasks go last; empty list is safe |
| **Filtering** | Filter by pet name, completion status, or both; unknown pet returns empty list |
| **Conflict detection** | Overlapping windows flagged; sequential tasks clean; same start time flagged; single task safe |
| **Scheduling** | Time budget respected; priority ordering correct; tasks that don't fit land in skipped |
| **Edge cases** | Pet with no tasks, zero time budget, removing nonexistent task, invalid priority/frequency/time format |
| **Validation** | `ValueError` raised immediately on bad priority, frequency, or `start_time` |

**Confidence level: ★★★★☆**

The scheduler's core behaviors — priority ordering, time budgeting, recurring task suppression, and conflict detection — are all covered by explicit tests, including their key edge cases. The one gap is integration testing of the Streamlit UI layer (`app.py`), which currently has no automated tests. End-to-end UI behavior requires manual verification.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
