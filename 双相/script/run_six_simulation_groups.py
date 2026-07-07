from __future__ import annotations

import csv
import json
import math
import statistics
import sys
from dataclasses import asdict, is_dataclass
from datetime import date
from pathlib import Path
from typing import Any, Dict, Iterable, List

import numpy as np

SIMULATION_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = SIMULATION_ROOT.parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from dm import 生成中文结果字典, 生成锁相仿真数据, 运行数字锁相, 锁相仿真配置


OUT_ROOT = SIMULATION_ROOT / "six_groups"
SOURCE_DIR = OUT_ROOT / "source_data"
RESULT_TABLE_TEX = OUT_ROOT / "six_group_result_tables.tex"

SEEDS_5 = [20260323, 20260324, 20260325, 20260326, 20260327]
SEEDS_3 = [20260323, 20260324, 20260325]

def mean(values: Iterable[float]) -> float:
    vals = [float(v) for v in values if v is not None and math.isfinite(float(v))]
    return float(statistics.fmean(vals)) if vals else float("nan")


def sd(values: Iterable[float]) -> float:
    vals = [float(v) for v in values if v is not None and math.isfinite(float(v))]
    return float(statistics.stdev(vals)) if len(vals) > 1 else 0.0


def sem(values: Iterable[float]) -> float:
    vals = [float(v) for v in values if v is not None and math.isfinite(float(v))]
    return sd(vals) / math.sqrt(len(vals)) if len(vals) > 1 else 0.0


def as_jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return as_jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    return value


def configure_reference_band(cfg: 锁相仿真配置, relative_half_width: float = 0.30) -> None:
    half = max(40.0, relative_half_width * cfg.参考频率_f0)
    cfg.参考带通下截止频率 = max(0.5, cfg.参考频率_f0 - half)
    cfg.参考带通上截止频率 = min(0.45 * cfg.采样率_fs, cfg.参考频率_f0 + half)


def configure_time_dependent_noise(cfg: 锁相仿真配置) -> None:
    cfg.一_f_低频截止_fL = 1.0 / max(cfg.总时长_T, 1e-9)
    if cfg.一_f_高频截止_fH <= cfg.一_f_低频截止_fL:
        cfg.一_f_目标均方根 = 0.0


def group_data_dir(group_dir: Path) -> Path:
    return group_dir / "data"


def write_group_outputs(group_dir: Path, rows: List[Dict[str, Any]], summary: List[Dict[str, Any]]) -> None:
    data_dir = group_data_dir(group_dir)
    write_csv(data_dir / "runs.csv", rows)
    write_csv(data_dir / "summary.csv", summary)
    write_json(data_dir / "summary.json", summary)


def base_config(seed: int, out_dir: Path) -> 锁相仿真配置:
    cfg = 锁相仿真配置(随机种子=seed, 输出目录=str(out_dir))
    configure_reference_band(cfg)
    configure_time_dependent_noise(cfg)
    return cfg


def input_snr_db(components: Dict[str, np.ndarray], measured: np.ndarray) -> float:
    target = np.asarray(components["目标信号"], dtype=float)
    noise = np.asarray(measured, dtype=float) - target
    sig_rms = float(np.sqrt(np.mean(target * target)))
    noise_rms = float(np.sqrt(np.mean(noise * noise)))
    return float("inf") if noise_rms <= 0 else float(20.0 * math.log10(sig_rms / noise_rms))


def run_case(group: str, label: str, seed: int, cfg: 锁相仿真配置, metadata: Dict[str, Any]) -> Dict[str, Any]:
    t, s, r, components = 生成锁相仿真数据(cfg)
    run = 运行数字锁相(t, s, r, cfg)
    result = 生成中文结果字典(cfg, run)
    phase_err = result["误差评估"]["相位误差_rad"]
    u_phi = result["误差评估"]["u_phi_rad"]
    nnear = result["nnear检测结果"]
    row = {
        "group": group,
        "label": label,
        "seed": seed,
        "fs_Hz": cfg.采样率_fs,
        "T_s": cfg.总时长_T,
        "f0_Hz": cfg.参考频率_f0,
        "A_true_V": cfg.目标幅值_A,
        "phi_true_rad": cfg.目标相位_phi,
        "lowpass_fc_Hz": cfg.解调低通截止频率,
        "noise_density_V_per_sqrtHz": cfg.白噪声谱密度_en,
        "near_df1_Hz": cfg.邻近干扰频偏_df1_Hz,
        "near_df2_Hz": cfg.邻近干扰频偏_df2_Hz,
        "A_rec_V": result["恢复结果"]["恢复幅值_A_rec_V"],
        "phi_rec_rad": result["恢复结果"]["恢复相位_phi_rec_rad"],
        "amp_abs_error_V": result["误差评估"]["幅值绝对误差_V"],
        "amp_error_percent": result["误差评估"]["幅值相对误差_percent"],
        "phase_error_rad": phase_err,
        "phase_error_deg": None if phase_err is None else math.degrees(float(phase_err)),
        "snr_vector_dB": result["误差评估"]["工程评估_SNR_vector_dB"],
        "input_snr_dB": input_snr_db(components, s),
        "snr_gain_dB": result["误差评估"]["工程评估_SNR_vector_dB"] - input_snr_db(components, s),
        "u_A_V": result["误差评估"]["u_A_V"],
        "u_phi_rad": u_phi,
        "u_phi_deg": None if u_phi is None else math.degrees(float(u_phi)),
        "ENBW_Hz": result["稳态统计"]["ENBW_Hz"],
        "Neff": result["稳态统计"]["Neff"],
        "phase_valid": result["相位有效性判据"]["相位是否有效"],
        "beat_detected": nnear["检测到显著拍频峰"],
        "beat_R": nnear["峰中位数比值_R"],
        "beat_freq_Hz": nnear["检测到的拍频频率_Hz"][0] if nnear["检测到的拍频频率_Hz"] else None,
        "processing_chain": nnear["最终处理链"],
    }
    row.update(metadata)
    return row


def summarize(rows: List[Dict[str, Any]], group: str, x_field: str, x_label_field: str = "label") -> List[Dict[str, Any]]:
    labels = []
    for row in rows:
        key = row[x_label_field]
        if key not in labels:
            labels.append(key)
    summary: List[Dict[str, Any]] = []
    for label in labels:
        subset = [r for r in rows if r[x_label_field] == label]
        first = subset[0]
        summary.append({
            "group": group,
            "label": label,
            "x_value": first.get(x_field),
            "n": len(subset),
            "amp_error_mean_percent": mean(r["amp_error_percent"] for r in subset),
            "amp_error_sd_percent": sd(r["amp_error_percent"] for r in subset),
            "phase_error_mean_deg": mean(r["phase_error_deg"] for r in subset),
            "phase_error_sd_deg": sd(r["phase_error_deg"] for r in subset),
            "snr_mean_dB": mean(r["snr_vector_dB"] for r in subset),
            "snr_sd_dB": sd(r["snr_vector_dB"] for r in subset),
            "snr_gain_mean_dB": mean(r["snr_gain_dB"] for r in subset),
            "u_A_mean_V": mean(r["u_A_V"] for r in subset),
            "u_A_sd_V": sd(r["u_A_V"] for r in subset),
            "u_phi_mean_deg": mean(r["u_phi_deg"] for r in subset),
            "u_phi_sd_deg": sd(r["u_phi_deg"] for r in subset),
            "phase_valid_rate": mean(1.0 if r["phase_valid"] else 0.0 for r in subset),
            "beat_detected_rate": mean(1.0 if r["beat_detected"] else 0.0 for r in subset),
            "A_rec_mean_V": mean(r["A_rec_V"] for r in subset),
            "A_rec_sd_V": sd(r["A_rec_V"] for r in subset),
            "A_true_V": first["A_true_V"],
            "f0_Hz": first["f0_Hz"],
            "fs_Hz": first["fs_Hz"],
            "T_s": first["T_s"],
            "lowpass_fc_Hz": first["lowpass_fc_Hz"],
        })
    return summary


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    keys: List[str] = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(as_jsonable(value), f, ensure_ascii=False, indent=2)


def run_group_baseline(all_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    group_dir = OUT_ROOT / "group_00_baseline"
    rows = []
    for seed in SEEDS_5:
        cfg = base_config(seed, group_dir)
        row = run_case("baseline", "baseline", seed, cfg, {"x_value": 0})
        rows.append(row)
        all_rows.append(row)
    summary = summarize(rows, "baseline", "x_value")
    write_group_outputs(group_dir, rows, summary)
    return summary


def run_group_frequency(all_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    group_dir = OUT_ROOT / "group_01_frequency_scan"
    rows = []
    for f0 in [137.0, 250.0, 500.0, 1_000.0, 1_500.0]:
        for seed in SEEDS_5:
            cfg = base_config(seed, group_dir)
            cfg.参考频率_f0 = f0
            cfg.采样率_fs = max(10_000.0, 12.0 * f0)
            cfg.总时长_T = 8.0
            cfg.一_f_低频截止_fL = 1.0 / cfg.总时长_T
            configure_reference_band(cfg)
            rows.append(run_case("frequency", f"{f0:g} Hz", seed, cfg, {"x_value": f0}))
            all_rows.append(rows[-1])
    summary = summarize(rows, "frequency", "x_value")
    write_group_outputs(group_dir, rows, summary)
    return summary


def run_group_mhz(all_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    group_dir = OUT_ROOT / "group_02_mhz_direct_sampling"
    rows = []
    for f0 in [0.5e6, 1e6, 2e6, 5e6]:
        for seed in SEEDS_3:
            cfg = base_config(seed, group_dir)
            cfg.参考频率_f0 = f0
            cfg.采样率_fs = 10.0 * f0
            cfg.总时长_T = 0.01
            cfg.解调低通截止频率 = 2_000.0
            cfg.第二级滑动平均窗口_s = 5e-5
            cfg.白噪声谱密度_en = 1.0e-8
            cfg.参考白噪声谱密度_en_r = 1.0e-8
            cfg.一_f_目标均方根 = 0.0
            cfg.场景项.启用参考幅度起伏 = False
            cfg.场景项.启用参考局部掉幅 = False
            cfg.场景项.启用参考谐波失真 = False
            cfg.场景项.启用参考工频泄漏 = False
            cfg.场景项.启用邻近频率干扰簇 = False
            cfg.处理项.启用参考前置净化 = False
            cfg.处理项.启用参考相位平滑 = False
            configure_reference_band(cfg)
            rows.append(run_case("mhz", f"{f0 / 1e6:g} MHz", seed, cfg, {"x_value": f0, "carrier_frequency_Hz": f0}))
            all_rows.append(rows[-1])
    summary = summarize(rows, "mhz", "x_value")
    write_group_outputs(group_dir, rows, summary)
    return summary


def run_group_amplitude(all_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    group_dir = OUT_ROOT / "group_03_amplitude_scan"
    rows = []
    for amp_uv in [100.0, 30.0, 10.0, 3.0, 1.0]:
        for seed in SEEDS_5:
            cfg = base_config(seed, group_dir)
            cfg.目标幅值_A = amp_uv * 1e-6
            rows.append(run_case("amplitude", f"{amp_uv:g} µV", seed, cfg, {"x_value": cfg.目标幅值_A}))
            all_rows.append(rows[-1])
    summary = summarize(rows, "amplitude", "x_value")
    write_group_outputs(group_dir, rows, summary)
    return summary


def run_group_noise(all_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    group_dir = OUT_ROOT / "group_04_noise_scan"
    rows = []
    for en in [1e-7, 2e-7, 4e-7, 8e-7, 1.6e-6]:
        for seed in SEEDS_5:
            cfg = base_config(seed, group_dir)
            cfg.白噪声谱密度_en = en
            rows.append(run_case("noise", f"{en:.1e}", seed, cfg, {"x_value": en}))
            all_rows.append(rows[-1])
    summary = summarize(rows, "noise", "x_value")
    write_group_outputs(group_dir, rows, summary)
    return summary


def run_group_integration(all_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    group_dir = OUT_ROOT / "group_05_integration_scan"
    rows = []
    for T, fc in [(8.0, 2.0), (12.0, 1.5), (16.0, 1.0), (24.0, 0.75), (32.0, 0.5)]:
        for seed in SEEDS_5:
            cfg = base_config(seed, group_dir)
            cfg.总时长_T = T
            cfg.解调低通截止频率 = fc
            cfg.第二级滑动平均窗口_s = min(0.40, max(0.10, 0.10 * math.sqrt(T / 8.0)))
            configure_time_dependent_noise(cfg)
            rows.append(run_case("integration", f"{T:g} s", seed, cfg, {"x_value": T}))
            all_rows.append(rows[-1])
    summary = summarize(rows, "integration", "x_value")
    write_group_outputs(group_dir, rows, summary)
    return summary


def run_group_adjacent(all_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    group_dir = OUT_ROOT / "group_06_adjacent_interference"
    rows = []
    for df in [5.0, 2.0, 1.0, 0.5]:
        for seed in SEEDS_5:
            cfg = base_config(seed, group_dir)
            cfg.邻近干扰频偏_df1_Hz = df
            cfg.邻近干扰频偏_df2_Hz = -df
            rows.append(run_case("adjacent", f"±{df:g} Hz", seed, cfg, {"x_value": df}))
            all_rows.append(rows[-1])
    summary = summarize(rows, "adjacent", "x_value")
    write_group_outputs(group_dir, rows, summary)
    return summary


def value_pm(row: Dict[str, Any], key: str, sd_key: str, digits: int = 3) -> str:
    return f"{row[key]:.{digits}g} ± {row[sd_key]:.{digits}g}"


def markdown_table(rows: List[Dict[str, Any]], columns: List[tuple[str, str]]) -> str:
    lines = ["|" + "|".join(title for title, _ in columns) + "|", "|" + "|".join("---" for _ in columns) + "|"]
    for row in rows:
        cells = []
        for _, key in columns:
            value = row.get(key, "")
            if isinstance(value, float):
                if not math.isfinite(value):
                    cells.append("-")
                    continue
                if abs(value) >= 1000 or (abs(value) < 0.01 and value != 0):
                    cells.append(f"{value:.3e}")
                else:
                    cells.append(f"{value:.3f}")
            else:
                cells.append(str(value).replace("µV", "$\\mu$V"))
        lines.append("|" + "|".join(cells) + "|")
    return "\n".join(lines)


def precision_row(row: Dict[str, Any], scene: str) -> Dict[str, Any]:
    out = dict(row)
    out["scene"] = scene
    out["A_true_uV"] = out["A_true_V"] * 1e6
    out["A_rec_mean_uV"] = out["A_rec_mean_V"] * 1e6
    out["A_rec_sd_uV"] = out["A_rec_sd_V"] * 1e6
    out["u_A_mean_uV"] = out["u_A_mean_V"] * 1e6
    out["u_A_relative_percent"] = out["u_A_mean_V"] / out["A_true_V"] * 100.0 if out["A_true_V"] > 0 else float("nan")
    return out


def latex_escape(text: str) -> str:
    return (
        str(text)
        .replace("\\", r"\textbackslash{}")
        .replace("&", r"\&")
        .replace("%", r"\%")
        .replace("_", r"\_")
        .replace("#", r"\#")
        .replace("µ", r"\ensuremath{\mu}")
    )


def format_frequency_hz(value: float) -> str:
    if abs(value) >= 1e6:
        return f"{value / 1e6:g} MHz"
    if abs(value) >= 1e3:
        return f"{value / 1e3:g} kHz"
    return f"{value:g} Hz"


def format_duration_s(value: float) -> str:
    if value < 1:
        return f"{value * 1e3:g} ms"
    return f"{value:g} s"


def format_optional(value: Any, digits: int = 2) -> str:
    if value is None:
        return "--"
    number = float(value)
    if math.isnan(number):
        return "--"
    return f"{number:.{digits}f}"


def latex_label(row: Dict[str, Any]) -> str:
    label = str(row["label"])
    if row["group"] == "adjacent":
        return "$\\pm$" + latex_escape(label.replace("±", "").strip())
    return latex_escape(label)


def table_sort_key(row: Dict[str, Any]) -> tuple[int, float]:
    group_order = {
        "baseline": 0,
        "frequency": 1,
        "mhz": 2,
        "amplitude": 3,
        "noise": 4,
        "integration": 5,
        "adjacent": 6,
    }
    x_value = float(row.get("x_value", 0.0))
    return group_order.get(str(row["group"]), 99), x_value


def write_result_table_tex(all_summary: List[Dict[str, Any]]) -> None:
    group_names = {
        "baseline": "基准组",
        "frequency": "频率扫描",
        "mhz": "兆赫直采",
        "amplitude": "幅值扫描",
        "noise": "噪声扫描",
        "integration": "积分时间",
        "adjacent": "邻频干扰",
    }

    body_lines = []
    for row in sorted(all_summary, key=table_sort_key):
        phase_error = format_optional(row["phase_error_mean_deg"])
        phase_sd = format_optional(row["phase_error_sd_deg"])
        phase_cell = "--" if phase_error == "--" else f"{phase_error} $\\pm$ {phase_sd}"
        u_phi = format_optional(row["u_phi_mean_deg"])
        cells = [
            group_names.get(str(row["group"]), str(row["group"])),
            latex_label(row),
            f"{int(row['n'])}",
            format_frequency_hz(float(row["f0_Hz"])),
            format_frequency_hz(float(row["fs_Hz"])),
            format_duration_s(float(row["T_s"])),
            f"{float(row['A_true_V']) * 1e6:.3f}",
            f"{float(row['A_rec_mean_V']) * 1e6:.3f} $\\pm$ {float(row['A_rec_sd_V']) * 1e6:.3f}",
            f"{float(row['amp_error_mean_percent']):.2f} $\\pm$ {float(row['amp_error_sd_percent']):.2f}",
            phase_cell,
            f"{float(row['u_A_mean_V']) * 1e6:.3f}",
            u_phi,
            f"{float(row['snr_gain_mean_dB']):.2f}",
            f"{float(row['phase_valid_rate']) * 100:.0f}",
        ]
        body_lines.append(" & ".join(cells) + r" \\")

    text = r"""\documentclass[UTF8,zihao=-4]{ctexart}
\usepackage[a4paper,margin=1.35cm]{geometry}
\usepackage{fontspec}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{array}
\usepackage{pdflscape}
\usepackage{caption}
\usepackage{xcolor}
\usepackage{amsmath}
\setmainfont{Times New Roman}
\setCJKmainfont{SimSun}
\captionsetup{font=small,labelfont=bf}
\renewcommand{\arraystretch}{1.16}
\setlength{\tabcolsep}{3.2pt}
\definecolor{headgray}{RGB}{235,239,244}

\begin{document}
\begin{center}
{\heiti\zihao{3} 六组仿真运行结果汇总表}\par
\vspace{0.35em}
{\small 数据来源：\texttt{results/six\_groups/source\_data/all\_summary.csv}；表中 ``$\pm$'' 表示重复仿真的标准差。}
\end{center}

\begin{landscape}
\small
\begin{longtable}{>{\centering\arraybackslash}p{1.35cm} >{\centering\arraybackslash}p{1.45cm} r >{\centering\arraybackslash}p{1.35cm} >{\centering\arraybackslash}p{1.35cm} >{\centering\arraybackslash}p{1.10cm} r >{\centering\arraybackslash}p{2.15cm} >{\centering\arraybackslash}p{2.05cm} >{\centering\arraybackslash}p{2.05cm} r r r r}
\caption{六组仿真的恢复精度、不确定度与信噪比增益。}\label{tab:six-group-results}\\
\toprule
组别 & 参数 & $n$ & $f_0$ & $f_s$ & $T$ & $A_{\mathrm{true}}$ / $\mu\mathrm{V}$ & $A_{\mathrm{rec}}$ / $\mu\mathrm{V}$ & $e_A$ / \% & $e_\phi$ / $^{\circ}$ & $u_A$ / $\mu\mathrm{V}$ & $u_\phi$ / $^{\circ}$ & $G_{\mathrm{SNR}}$ / dB & 相位有效率 / \% \\
\midrule
\endfirsthead
\toprule
组别 & 参数 & $n$ & $f_0$ & $f_s$ & $T$ & $A_{\mathrm{true}}$ / $\mu\mathrm{V}$ & $A_{\mathrm{rec}}$ / $\mu\mathrm{V}$ & $e_A$ / \% & $e_\phi$ / $^{\circ}$ & $u_A$ / $\mu\mathrm{V}$ & $u_\phi$ / $^{\circ}$ & $G_{\mathrm{SNR}}$ / dB & 相位有效率 / \% \\
\midrule
\endhead
\midrule
\multicolumn{14}{r}{续下页}\\
\endfoot
\bottomrule
\endlastfoot
""" + "\n".join(body_lines) + r"""
\end{longtable}
\end{landscape}

\vspace{0.3em}
\noindent\textbf{符号说明：}
$A_{\mathrm{true}}$ 为仿真设定真实幅值，$A_{\mathrm{rec}}$ 为算法恢复幅值，$e_A$ 为幅值相对误差，$e_\phi$ 为相位误差，$u_A$ 和 $u_\phi$ 分别为幅值与相位不确定度，$G_{\mathrm{SNR}}$ 为锁相处理后的信噪比增益。相位误差为 ``--'' 表示该工况相位结果不可靠或无有效统计值。

\end{document}
"""
    RESULT_TABLE_TEX.write_text(text, encoding="utf-8")


def write_report(summaries: Dict[str, List[Dict[str, Any]]]) -> None:
    report = OUT_ROOT / "six_group_simulation_report.md"
    baseline = summaries["baseline"][0]
    freq_worst = max(summaries["frequency"], key=lambda r: r["amp_error_mean_percent"])
    mhz_worst = max(summaries["mhz"], key=lambda r: r["amp_error_mean_percent"])
    noise_worst = max(summaries["noise"], key=lambda r: r["amp_error_mean_percent"])
    integration_best = min(summaries["integration"], key=lambda r: r["u_A_mean_V"])
    adj_worst = max(summaries["adjacent"], key=lambda r: r["amp_error_mean_percent"])
    amp_3uv = next(r for r in summaries["amplitude"] if r["label"] == "3 µV")
    amp_1uv = next(r for r in summaries["amplitude"] if r["label"] == "1 µV")
    precision_rows = [
        precision_row(baseline, r"基准 $10\,\mu$V"),
        precision_row(freq_worst, f"频率最难点 {freq_worst['label']}"),
        precision_row(mhz_worst, f"MHz 最难点 {mhz_worst['label']}"),
        precision_row(amp_3uv, r"低幅值 $3\,\mu$V"),
        precision_row(amp_1uv, r"极限幅值 $1\,\mu$V"),
        precision_row(noise_worst, f"最强噪声 {noise_worst['label']}"),
        precision_row(integration_best, f"最低不确定度 {integration_best['label']}"),
    ]
    precision_table = markdown_table(precision_rows, [
        ("场景", "scene"),
        ("真值 ($\\mu$V)", "A_true_uV"),
        ("恢复均值 ($\\mu$V)", "A_rec_mean_uV"),
        ("重复性 SD ($\\mu$V)", "A_rec_sd_uV"),
        ("幅值误差 (%)", "amp_error_mean_percent"),
        ("$u_A$ ($\\mu$V)", "u_A_mean_uV"),
        ("相对 $u_A$ (%)", "u_A_relative_percent"),
        ("相位误差 (°)", "phase_error_mean_deg"),
        ("$u_\\phi$ (°)", "u_phi_mean_deg"),
        ("SNR 提升 (dB)", "snr_gain_mean_dB"),
    ])

    text = f"""# 六组数字锁相仿真结果报告

生成时间：{date.today().isoformat()}  
仿真入口：`results/noisy_algorithm_simulation/script/run_six_simulation_groups.py`  
输出目录：`results/six_groups`

## 核心结论

在当前仿真模型下，数字锁相算法可以在受噪参考、漂移、工频、相位噪声和邻近频率干扰存在时恢复微弱信号。基准场景的平均幅值误差为 {baseline['amp_error_mean_percent']:.3f}% ，平均相位误差为 {baseline['phase_error_mean_deg']:.3f}°。最主要的限制来自强白噪声和邻频干扰接近锁相等效带宽时的拍频残留；延长积分时间可以显著降低幅值不确定度。

本脚本只生成六组仿真的数据表和文字报告；当前加噪声 6 联图由本仿真文件夹内的 `script/simulation_plots.py` 生成。

## 恢复效果、测量精度与不确定度

这里把三个概念分开看：恢复效果看恢复值与真值的偏差；重复性看 5 个随机种子的恢复值标准差；不确定度看算法由稳态正交分量统计给出的标准不确定度 \(u_A\) 和 \(u_\phi\)。基准 \(10\,\mu\mathrm{{V}}\) 场景下，恢复幅值为 \({baseline['A_rec_mean_V'] * 1e6:.3f}\,\mu\mathrm{{V}}\)，幅值误差 {baseline['amp_error_mean_percent']:.3f}%，标准不确定度 \(u_A={baseline['u_A_mean_V'] * 1e6:.3f}\,\mu\mathrm{{V}}\)，相对标准不确定度约 {baseline['u_A_mean_V'] / baseline['A_true_V'] * 100.0:.2f}%，输出 SNR 提升约 {baseline['snr_gain_mean_dB']:.1f} dB。

{precision_table}

从表中可以看出：\(3\,\mu\mathrm{{V}}\) 仍能恢复，但相对不确定度已经明显升高；\(1\,\mu\mathrm{{V}}\) 时幅值误差超过 10%，且相位有效性不足，适合作为当前仿真条件下的接近下限点。积分时间组中最低 \(u_A\) 出现在 {integration_best['label']}，约为 {integration_best['u_A_mean_V'] * 1e9:.1f} nV。

## 参数选择原则

本报告基于当前 `scripts/dm.py` 算法主链重新生成六组仿真。六组仿真围绕后续实验最需要回答的问题来选：频率能否变化、MHz 要求如何处理、幅值下限在哪里、噪声会怎样影响结果、积分时间是否能降低不确定度、邻近频率干扰是否会造成拍频误差。

| 组别 | 扫描参数 | 固定关键参数 | 选择理由 |
|---|---:|---:|---|
| 0 基准 | 不扫描 | \(f_0=137\,\mathrm{{Hz}}, A=10\,\mu\mathrm{{V}}, f_s=10\,\mathrm{{kHz}}, T=16\,\mathrm{{s}}\) | 给所有结果一个对照点 |
| 1 完整链频率扫描 | \(137,250,500,1000,1500\,\mathrm{{Hz}}\) | \(T=8\,\mathrm{{s}}\)，参考净化、相位平滑、鲁棒统计均开启 | 验证完整算法链在低频到低 kHz 的稳定性 |
| 2 MHz 检查 | \(0.5,1,2,5\,\mathrm{{MHz}}\) | \(f_s=10f_0, T=10\,\mathrm{{ms}}\)，弱扰动短窗 | 回应老师提出的 MHz 频率要求，验证高速同频解调可行性 |
| 3 幅值扫描 | \(1,3,10,30,100\,\mu\mathrm{{V}}\) | \(f_0=137\,\mathrm{{Hz}}, f_s=10\,\mathrm{{kHz}}, T=16\,\mathrm{{s}}\) | 看线性恢复和弱信号下限 |
| 4 噪声扫描 | \(e_n=1,2,4,8,16\\times10^{{-7}}\,\mathrm{{V}}/\sqrt{{\mathrm{{Hz}}}}\) | \(A=10\,\mu\mathrm{{V}}\) | 看抗噪能力和失效趋势 |
| 5 积分/带宽扫描 | \(T=8\sim32\,\mathrm{{s}}, f_c=2\sim0.5\,\mathrm{{Hz}}\) | \(f_0=137\,\mathrm{{Hz}}\) | 验证更长积分是否降低 \(u_A\) |
| 6 邻频干扰扫描 | \(\lvert\Delta f\\rvert=5,2,1,0.5\,\mathrm{{Hz}}\) | 邻频幅值保持默认 | 检查拍频干扰和自动剥离链 |

## 图件与数据

- 全部单次运行数据：`source_data/all_runs.csv`
- 全部分组统计数据：`source_data/all_summary.csv`
- 每组子目录均包含 `data/runs.csv`、`data/summary.csv` 和 `data/summary.json`。

## 第 0 组：基准场景

基准场景用于后续对照：\(f_0=137\,\mathrm{{Hz}}\)，\(A=10\,\mu\mathrm{{V}}\)，\(f_s=10\,\mathrm{{kHz}}\)，\(T=16\,\mathrm{{s}}\)，解调低通 \(f_c=1\,\mathrm{{Hz}}\)。5 个随机种子下相位均有效。

{markdown_table(summaries['baseline'], [
    ('场景', 'label'),
    ('幅值误差均值 (%)', 'amp_error_mean_percent'),
    ('相位误差均值 (°)', 'phase_error_mean_deg'),
    ('输出 SNR (dB)', 'snr_mean_dB'),
    ('u_A (V)', 'u_A_mean_V'),
])}

## 第 1 组：频率扫描

目的：确认算法不是只对 \(137\,\mathrm{{Hz}}\) 有效。扫描 \(137\,\mathrm{{Hz}}\) 到 \(1.5\,\mathrm{{kHz}}\)，采样率随频率提高，参考带通按中心频率自动调整。这里保留完整处理链，不关闭参考净化、不关闭相位平滑。最大平均幅值误差出现在 {freq_worst['label']}，为 {freq_worst['amp_error_mean_percent']:.3f}%。

{markdown_table(summaries['frequency'], [
    ('f0', 'label'),
    ('幅值误差均值 (%)', 'amp_error_mean_percent'),
    ('幅值误差 SD (%)', 'amp_error_sd_percent'),
    ('相位误差均值 (°)', 'phase_error_mean_deg'),
    ('输出 SNR (dB)', 'snr_mean_dB'),
])}

## 第 2 组：MHz 直接高频采样检查

目的：回应 MHz 频率要求，验证在短时窗高速采样条件下的高频载波恢复。该组只作为工程可行性检查：关闭参考前置净化和强参考扰动，聚焦“高频同频参考 + 数字双相解调”的可行性。实际实验若不具备高速 ADC，更推荐用模拟前端先下变频，再进入当前数字锁相链路。

{markdown_table(summaries['mhz'], [
    ('载波', 'label'),
    ('采样率 (Hz)', 'fs_Hz'),
    ('采样时长 (s)', 'T_s'),
    ('幅值误差均值 (%)', 'amp_error_mean_percent'),
    ('相位误差均值 (°)', 'phase_error_mean_deg'),
])}

## 第 3 组：幅值扫描

目的：验证线性范围和微弱信号下限。\(1\sim100\,\mu\mathrm{{V}}\) 范围内恢复幅值整体保持单调线性。

{markdown_table(summaries['amplitude'], [
    ('真值幅值', 'label'),
    ('恢复幅值均值 (V)', 'A_rec_mean_V'),
    ('幅值误差均值 (%)', 'amp_error_mean_percent'),
    ('相位有效率', 'phase_valid_rate'),
])}

## 第 4 组：噪声强度扫描

目的：测试不同白噪声谱密度下的抗噪性能。最高噪声点的平均幅值误差为 {noise_worst['amp_error_mean_percent']:.3f}% ，说明极强噪声会成为当前恢复精度的主要压力源。

{markdown_table(summaries['noise'], [
    ('噪声谱密度', 'label'),
    ('幅值误差均值 (%)', 'amp_error_mean_percent'),
    ('输出 SNR (dB)', 'snr_mean_dB'),
    ('SNR 提升 (dB)', 'snr_gain_mean_dB'),
])}

## 第 5 组：积分时间 / 低通带宽扫描

目的：验证积分时间越长、低通越窄，不确定度越低。当前最小 \(u_A\) 出现在 {integration_best['label']}，平均 \(u_A={integration_best['u_A_mean_V']:.3e}\\,V\)。

{markdown_table(summaries['integration'], [
    ('积分时间', 'label'),
    ('低通 fc (Hz)', 'lowpass_fc_Hz'),
    ('u_A 均值 (V)', 'u_A_mean_V'),
    ('u_phi 均值 (°)', 'u_phi_mean_deg'),
    ('SNR 提升 (dB)', 'snr_gain_mean_dB'),
])}

## 第 6 组：邻近频率干扰扫描

目的：测试靠近参考频率的干扰是否会形成低频拍频并影响恢复。最难点为 {adj_worst['label']}，平均幅值误差为 {adj_worst['amp_error_mean_percent']:.3f}%。拍频检测率用于判断回归剥离链是否被触发。

{markdown_table(summaries['adjacent'], [
    ('邻频偏移', 'label'),
    ('幅值误差均值 (%)', 'amp_error_mean_percent'),
    ('相位误差均值 (°)', 'phase_error_mean_deg'),
    ('拍频检测率', 'beat_detected_rate'),
    ('输出 SNR (dB)', 'snr_mean_dB'),
])}

## 后续实验建议

1. 真实示波器实验优先复现第 0、3、4、5 组：它们最容易和实验装置参数对应。
2. 频率扫描不要贴近 50 Hz、100 Hz、150 Hz 工频及其谐波，避免把工频陷波影响误判为锁相算法问题。
3. MHz 演示应提前确认采样率。如果没有高速 ADC，应采用模拟下变频或锁相前端输出基带，再交给当前数字处理链。
4. 报告主图建议使用总览图，答辩备用图使用各组子图。
"""
    report.write_text(text, encoding="utf-8")


def main() -> None:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)

    all_rows: List[Dict[str, Any]] = []
    summaries: Dict[str, List[Dict[str, Any]]] = {}

    print("Running baseline...")
    summaries["baseline"] = run_group_baseline(all_rows)
    print("Running frequency scan...")
    summaries["frequency"] = run_group_frequency(all_rows)
    print("Running MHz direct-sampling check...")
    summaries["mhz"] = run_group_mhz(all_rows)
    print("Running amplitude scan...")
    summaries["amplitude"] = run_group_amplitude(all_rows)
    print("Running noise scan...")
    summaries["noise"] = run_group_noise(all_rows)
    print("Running integration scan...")
    summaries["integration"] = run_group_integration(all_rows)
    print("Running adjacent-frequency scan...")
    summaries["adjacent"] = run_group_adjacent(all_rows)

    all_summary = [row for group_rows in summaries.values() for row in group_rows]
    write_csv(SOURCE_DIR / "all_runs.csv", all_rows)
    write_csv(SOURCE_DIR / "all_summary.csv", all_summary)
    write_json(SOURCE_DIR / "all_summary.json", all_summary)
    write_result_table_tex(all_summary)
    write_report(summaries)

    print(f"Done. Report: {OUT_ROOT / 'six_group_simulation_report.md'}")


if __name__ == "__main__":
    main()
