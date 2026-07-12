from pathlib import Path
import json
import sys

source = Path("src/components/ChartAdapter/KLineChartsImpl.tsx").read_text()
checks = {
    "main_on_candle_pane": 'chart.createIndicator(mainIndicator, true, { id: "candle_pane" })' in source,
    "main_removed_by_name": 'chart.removeIndicator("candle_pane", activeMainIndicator.current)' in source,
    "imperative_theme_restores_indicators": "initializeChart(newTheme, true)" in source,
    "chart_data_survives_rebuild": "currentData.current" in source and "chart.applyNewData(currentData.current)" in source,
    "duplicate_theme_rebuild_removed": "// 切换主题（需销毁重建）" not in source,
    "unmount_disposes_current_instance": (
        "const currentChart = chartInstance.current" in source
        and "dispose(currentChart)" in source
        and "chartInstance.current = null" in source
    ),
}
print(json.dumps(checks, ensure_ascii=False, indent=2))
sys.exit(0 if all(checks.values()) else 1)
