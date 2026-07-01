# Implementation Pattern

Extracted from `/Users/charles/.hermes/skills/software-development/browser-harness-integration/SKILL.md` on 2026-07-01T08:55:33.664327+00:00 by generic core-body debt remediation. Root SKILL.md keeps a progressive-loading pointer; content is preserved here.

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
