---
name: browser-harness-integration
description: Integrate comprehensive browser-based verification into automated task pipelines - combines dogfood testing, visual regression, and UIMax audit with project-type detection and viewport-specific testing
version: 1.0.0
metadata:
  hermes:
    tags: [qa, browser, testing, automation, verification, pipeline]
    related_skills: [dogfood, visual-regression, uimax-audit]
---

# Browser Harness Integration

> Integrate comprehensive browser-based verification into automated task pipelines. Combines dogfood testing, visual regression, and UIMax audit with intelligent project detection.

## When to Use

- Adding automated QA verification to task execution pipelines
- Need to verify frontend projects after code changes
- Want comprehensive testing (functional, visual, quality scoring)
- Need project-type detection for Vue, React, mobile vs desktop
- Integrating browser verification into existing automation workflows

## Core Workflow

```
Task Execution Complete
    ↓
Build Verification Passes
    ↓
Start Dev Server
    ↓
┌─────────────────────────────────────┐
│ 1. Dogfood Testing (per page)       │
│    - Page screenshot                │
│    - Console error check            │
│    - Interactive element testing    │
│    - Issue collection               │
├─────────────────────────────────────┤
│ 2. Visual Regression Check          │
│    - Current vs baseline screenshot │
│    - AI difference analysis         │
│    - Regression detection           │
├─────────────────────────────────────┤
│ 3. UIMax Audit                      │
│    - 6-dimension scoring (A-F)      │
│    - Issue categorization           │
│    - Optimization suggestions       │
└─────────────────────────────────────┘
    ↓
Generate Verification Report
    ↓
Stop Dev Server
```

## Implementation Pattern

### 1. Project Type Detection

```python
def _get_project_pages(project_path: str) -> List[Dict[str, str]]:
    """
    Determine which pages to test based on project type.
    
    Returns:
        List of page configs: [{"path": "/", "name": "home", "viewport": "desktop"}, ...]
    """
    pkg_json = Path(project_path) / "package.json"
    if pkg_json.is_file():
        pkg = json.loads(pkg_json.read_text())
        deps = pkg.get("dependencies", {})
        dev_deps = pkg.get("devDependencies", {})
        all_deps = {**deps, **dev_deps}
        
        # Vue 2 + Element UI (desktop)
        if "vue" in all_deps and "element-ui" in all_deps:
            return [
                {"path": "/", "name": "home", "viewport": "desktop"},
                {"path": "/login", "name": "login", "viewport": "desktop"},
                {"path": "/dashboard", "name": "dashboard", "viewport": "desktop"},
            ]
        
        # Vue 2 + Vant (mobile)
        if "vue" in all_deps and "vant" in all_deps:
            return [
                {"path": "/", "name": "home", "viewport": "mobile"},
                {"path": "/login", "name": "login", "viewport": "mobile"},
                {"path": "/market", "name": "market", "viewport": "mobile"},
            ]
        
        # React + Ant Design
        if "react" in all_deps and "antd" in all_deps:
            return [
                {"path": "/", "name": "home", "viewport": "desktop"},
                {"path": "/login", "name": "login", "viewport": "desktop"},
                {"path": "/dashboard", "name": "dashboard", "viewport": "desktop"},
            ]
    
    # Default
    return [{"path": "/", "name": "home", "viewport": "desktop"}]
```

### 2. Viewport-Specific Testing

```python
def run_dogfood_test(url: str, page_name: str, output_dir: str, viewport: str = "desktop") -> Dict[str, Any]:
    """
    Run dogfood-style exploratory testing with viewport-specific instructions.
    """
    if viewport == "mobile":
        viewport_instruction = """
### Mobile Viewport Testing (375px width):
1. Test touch interactions (tap, swipe)
2. Check mobile navigation (hamburger menu, bottom nav)
3. Verify responsive layout at 375px width
4. Test mobile-specific features (pull-to-refresh, etc.)
5. Check for horizontal scrolling issues
6. Verify touch targets are large enough (44px minimum)
"""
    else:
        viewport_instruction = """
### Desktop Viewport Testing (1280px width):
1. Test mouse interactions (hover, click)
2. Check desktop navigation (sidebar, header)
3. Verify responsive layout at 1280px width
4. Test keyboard navigation
5. Check for proper spacing and alignment
6. Verify all interactive elements are accessible
"""
    
    # Build prompt with viewport-specific instructions
    prompt = f"""## Browser QA Testing Task

Test the web page at: {url}
Viewport: {viewport} ({'375px' if viewport == 'mobile' else '1280px'} width)

### Instructions:
1. Navigate to the URL
2. Take a screenshot for visual assessment
3. Check console for JavaScript errors
4. Test all interactive elements (buttons, forms, links)
5. Check for visual issues (layout, spacing, colors)
6. Test responsive behavior (scroll, zoom)
7. Report any issues found
{viewport_instruction}
"""
```

### 3. Integration with Existing Pipeline

```python
# In executor.py - after build verification
harness_result = browser_harness.verify_with_browser_harness(envelope, dry_run=False)
if harness_result.get("success"):
    print(f"  [HARNESS OK] Grade: {harness_result.get('overall_grade')}")
    db.append_trace(eid, {
        "event": "browser_harness_passed",
        "grade": harness_result.get("overall_grade"),
        "report_path": harness_result.get("report_path"),
        "issues": harness_result.get("total_issues", 0)
    })
else:
    print(f"  [HARNESS FAIL] Grade: {harness_result.get('overall_grade')}")
    db.append_trace(eid, {
        "event": "browser_harness_failed",
        "grade": harness_result.get("overall_grade"),
        "report_path": harness_result.get("report_path"),
        "issues": harness_result.get("total_issues", 0),
        "critical": harness_result.get("critical_issues", 0),
        "high": harness_result.get("high_issues", 0)
    })
    
    # Handle issues based on severity
    critical_issues = harness_result.get("critical_issues", 0)
    high_issues = harness_result.get("high_issues", 0)
    
    if critical_issues > 0:
        notify.notify_task_failed(
            summary, 
            project_id, 
            f"Browser harness found {critical_issues} critical issues"
        )
    elif high_issues > 0:
        # High severity issues notify but don't fail the task
        notify.notify_task_completed(summary, project_id, files_changed)
        print(f"  [HARNESS WARNING] {high_issues} high issues found")
```

## Configuration

### Environment Variables

```bash
# Browser harness timeout (default: 300 seconds)
export ARC_BROWSER_HARNESS_TIMEOUT=300

# Hermes command path (default: "hermes")
export ARC_HERMES_CMD=hermes

# Screenshots directory (default: ~/.arc-dispatch/screenshots)
export ARC_SCREENSHOT_DIR=~/.arc-dispatch/screenshots

# Reports directory (default: ~/.arc-dispatch/reports)
export ARC_REPORT_DIR=~/.arc-dispatch/reports
```

### Manual Testing

```bash
# Test a single project
python3 browser_harness.py --project-path /path/to/project --project-id web_ui

# Dry run
python3 browser_harness.py --project-path /path/to/project --dry-run

# Test with specific viewport
python3 browser_harness.py --project-path /path/to/project --viewport mobile
```

## Report Structure

Reports are generated in `~/.arc-dispatch/reports/{project-id}-{timestamp}/verification-report.md`:

```markdown
# Browser Harness Verification Report

## Executive Summary
- **Project**: web_ui
- **Task**: Fix login page styling
- **Overall Grade**: B
- **Total Issues**: 3
  - Critical: 0
  - High: 1
  - Medium: 2
  - Low: 0

## Test Results

### Dogfood Testing (Exploratory QA)
| Page | Success | Issues | Console Errors | Screenshot |
|------|---------|--------|----------------|------------|
| home | ✅ | 1 | 0 | [View](screenshots/home-desktop-screenshot.png) |
| login | ✅ | 2 | 1 | [View](screenshots/login-desktop-screenshot.png) |

### Visual Regression
| Page | Regression | Severity | Differences |
|------|------------|----------|-------------|
| home | ✅ | none | 0 |
| login | ⚠️ | low | 1 |

### UIMax Audit
| Page | Visual | Responsive | A11y | Code | Interaction | Console |
|------|--------|------------|------|------|-------------|---------|
| home | A | B | C | A | B | A |
| login | B | B | B | A | B | B |
```

## Pitfalls

1. **Dev server startup**: Always verify server is ready before testing. Use health checks.
2. **Timeout handling**: Browser tests can be slow. Set appropriate timeouts.
3. **False positives**: Dynamic content (timestamps, random IDs) can cause visual regression false positives.
4. **Mobile viewport**: Browser tools don't support direct viewport setting. Use CSS media query checks instead.
5. **Project detection**: Some projects may have unusual dependency structures. Provide fallbacks.

## Key Learnings

1. **Project-specific detection**: Vue+Element UI (desktop), Vue+Vant (mobile), React+Ant Design (desktop) each need different test approaches.
2. **Viewport-specific instructions**: Mobile and desktop have different interaction patterns and accessibility requirements.
3. **Severity-based notifications**: Critical issues should fail tasks, high issues should warn but not fail.
4. **Fallback mechanisms**: Always have a fallback (e.g., simple screenshot) if browser_harness is unavailable.
5. **Integration points**: Browser verification should run after build verification but before task completion.

## Integration with Other Skills

- **dogfood**: Core testing methodology for exploratory QA
- **visual-regression**: Screenshot comparison for detecting UI changes
- **uimax-audit**: Quality scoring across 6 dimensions
- **systematic-debugging**: When browser tests fail unexpectedly
- **requesting-code-review**: Can trigger browser verification as part of code review