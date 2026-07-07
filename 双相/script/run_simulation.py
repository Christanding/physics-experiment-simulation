from __future__ import annotations

import json
import sys
from pathlib import Path

SIMULATION_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = SIMULATION_ROOT.parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from dm import 生成中文结果字典, 生成锁相仿真数据, 打印中文摘要, 运行数字锁相, 锁相仿真配置
from simulation_plots import 保存仿真六联图


RESULTS_DIR = SIMULATION_ROOT


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    cfg = 锁相仿真配置(输出目录=str(RESULTS_DIR))
    t, s, r, _components = 生成锁相仿真数据(cfg)
    run = 运行数字锁相(t, s, r, cfg)
    result_json = 生成中文结果字典(cfg, run)

    json_path = RESULTS_DIR / "dm_simulation_result.json"
    fig_path = RESULTS_DIR / "dm_simulation_appendix_six_panel.png"

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(result_json, f, ensure_ascii=False, indent=2)

    保存仿真六联图(cfg, run, fig_path)
    打印中文摘要(cfg, result_json)

    print(f"JSON：{json_path}")
    print(f"附录六联图：{fig_path}")


if __name__ == "__main__":
    main()
