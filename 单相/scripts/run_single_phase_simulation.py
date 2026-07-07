from __future__ import annotations

import csv
import json
import math
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np

SIMULATION_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = SIMULATION_ROOT.parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from dm import 生成锁相仿真数据, 锁相仿真配置
from single_phase_lockin import run_single_phase_lockin
from single_phase_plots import save_single_phase_six_panel


OUT_DIR = SIMULATION_ROOT
DATA_DIR = OUT_DIR / "data"
FIG_DIR = OUT_DIR / "six_panel"

FREQUENCIES_HZ = [1_000.0, 2_000.0, 5_000.0, 10_000.0]
INPUT_VPP_LEVELS = [0.1, 1.0, 3.0, 5.0, 10.0]
SAMPLES_PER_CYCLE = 12
SIM_DURATION_S = 6.0
PHI_TRUE_RAD = math.radians(8.0)
PHASE_SWEEP_DEGREES = [0.0, 30.0, 60.0, 90.0]
BASE_SEED = 20260706
MEASUREMENT_WHITE_EN_V_PER_SQRT_HZ = 2.0e-5
REFERENCE_WHITE_EN_V_PER_SQRT_HZ = 2.5e-4


def safe_float(value: Any) -> float | None:
    if value is None:
        return None
    value = float(value)
    return value if math.isfinite(value) else None


def fmt_number(value: float | None, digits: int = 3) -> str:
    if value is None or not math.isfinite(float(value)):
        return "-"
    return f"{float(value):.{digits}f}"


def fmt_percent(value: float | None, digits: int = 3) -> str:
    if value is None or not math.isfinite(float(value)):
        return "-"
    return f"{float(value):+.{digits}f}%"


def frequency_label(f0_hz: float) -> str:
    return f"{f0_hz / 1000:g}kHz"


def amplitude_label(input_vpp: float) -> str:
    return f"{input_vpp:g}Vpp".replace(".", "p")


def make_config(f0_hz: float, input_vpp: float, seed: int, phase_rad: float = PHI_TRUE_RAD) -> 锁相仿真配置:
    cfg = 锁相仿真配置()
    cfg.参考频率_f0 = float(f0_hz)
    cfg.采样率_fs = float(f0_hz * SAMPLES_PER_CYCLE)
    cfg.总时长_T = SIM_DURATION_S
    cfg.目标幅值_A = float(input_vpp) / 20.0
    cfg.目标相位_phi = phase_rad
    cfg.随机种子 = seed
    cfg.输出目录 = str(OUT_DIR)

    cfg.一_f_低频截止_fL = 1.0 / cfg.总时长_T
    cfg.一_f_高频截止_fH = min(30.0, 0.45 * cfg.采样率_fs)
    cfg.白噪声谱密度_en = MEASUREMENT_WHITE_EN_V_PER_SQRT_HZ
    cfg.直流偏置_b0 = 2.0e-2
    cfg.漂移正弦幅值 = 2.0e-3
    cfg.漂移线性斜率 = 2.0e-4
    cfg.一_f_目标均方根 = 3.0e-4
    cfg.工频幅值_B1 = 1.2e-3
    cfg.工频幅值_B2 = 6.0e-4
    cfg.工频幅值_B3 = 3.0e-4
    cfg.邻近干扰幅值_C1 = 1.0e-3
    cfg.邻近干扰幅值_C2 = 8.0e-4

    cfg.参考局部掉幅中心1_s = 0.35 * cfg.总时长_T
    cfg.参考局部掉幅中心2_s = 0.72 * cfg.总时长_T
    cfg.参考局部掉幅宽度1_s = 0.015 * cfg.总时长_T
    cfg.参考局部掉幅宽度2_s = 0.018 * cfg.总时长_T

    cfg.参考带通下截止频率 = max(1.0, 0.70 * cfg.参考频率_f0)
    cfg.参考带通上截止频率 = min(0.45 * cfg.采样率_fs, 1.30 * cfg.参考频率_f0)
    cfg.陷波频率列表_Hz = tuple(f for f in (50.0, 100.0, 150.0) if f < 0.45 * cfg.采样率_fs)
    cfg.参考白噪声谱密度_en_r = REFERENCE_WHITE_EN_V_PER_SQRT_HZ
    cfg.参考工频幅值_RB1 = 1.0e-2
    cfg.参考工频幅值_RB2 = 5.0e-3
    cfg.参考相位平滑截止频率_Hz = 8.0
    cfg.解调低通阶数 = 2
    cfg.解调低通截止频率 = 1.0
    cfg.第二级滑动平均窗口_s = 0.10
    return cfg


def measurement_input_snr_db(components: dict[str, np.ndarray]) -> float:
    target = np.asarray(components["目标信号"], dtype=float)
    noise = (
        np.asarray(components["慢漂移"], dtype=float)
        + np.asarray(components["白噪声"], dtype=float)
        + np.asarray(components["带限一_f噪声"], dtype=float)
        + np.asarray(components["工频干扰"], dtype=float)
        + np.asarray(components["邻近频率干扰簇"], dtype=float)
    )
    signal_rms = float(np.sqrt(np.mean(target * target)))
    noise_rms = float(np.sqrt(np.mean(noise * noise)))
    if noise_rms <= 0.0:
        return float("inf")
    return float(20.0 * math.log10(signal_rms / noise_rms))


def run_case(f0_hz: float, input_vpp: float, case_index: int, phase_rad: float = PHI_TRUE_RAD, figure_root: Path | None = None, figure_prefix: str = "single_phase") -> dict[str, Any]:
    seed = BASE_SEED + case_index
    cfg = make_config(f0_hz, input_vpp, seed, phase_rad=phase_rad)
    t, s, r, components = 生成锁相仿真数据(cfg)
    run = run_single_phase_lockin(t, s, r, cfg)

    true_peak_v = cfg.目标幅值_A
    theoretical_projection_v = true_peak_v * math.cos(cfg.目标相位_phi)
    projection_error_percent = None
    if abs(theoretical_projection_v) >= 1e-12:
        projection_error_percent = 100.0 * (float(run["a_projection"]) / theoretical_projection_v - 1.0)
    run["true_peak_v"] = true_peak_v
    run["single_phase_theoretical_v"] = theoretical_projection_v
    run["figure_dpi"] = 220

    root = FIG_DIR if figure_root is None else figure_root
    freq_dir = root / frequency_label(f0_hz)
    freq_dir.mkdir(parents=True, exist_ok=True)
    phase_label = f"{math.degrees(phase_rad):g}deg".replace(".", "p")
    fig_path = freq_dir / f"{figure_prefix}_{frequency_label(f0_hz)}_{amplitude_label(input_vpp)}_phi_{phase_label}.png"
    save_single_phase_six_panel(cfg, run, fig_path)

    a_projection = float(run["a_projection"])
    u_a = float(run["u_a_projection"])
    return {
        "frequency_hz": f0_hz,
        "input_vpp_generator": input_vpp,
        "true_output_peak_mV": 1e3 * true_peak_v,
        "single_phase_theoretical_projection_mV": 1e3 * theoretical_projection_v,
        "recovered_single_phase_projection_mV": 1e3 * a_projection,
        "error_vs_true_peak_percent": 100.0 * (a_projection / true_peak_v - 1.0),
        "error_vs_single_phase_projection_percent": projection_error_percent,
        "u_A_mV": 1e3 * u_a,
        "relative_u_A_percent": 100.0 * u_a / abs(a_projection),
        "true_phase_deg": math.degrees(cfg.目标相位_phi),
        "reference_filter_phase_delay_deg": math.degrees(float(run["theta_delay"])),
        "input_snr_db": measurement_input_snr_db(components),
        "single_phase_snr_db": safe_float(run["snr_db"]),
        "enbw_hz": float(run["enbw_hz"]),
        "neff": float(run["neff"]),
        "effective_duration_s": float(run["t_weighted"]),
        "reference_quality_mean": float(run["reference_quality_mean"]),
        "steady_count": int(run["steady_count"]),
        "effective_count": int(run["effective_count"]),
        "figure": fig_path.relative_to(OUT_DIR).as_posix(),
        "seed": seed,
        "samples": cfg.点数_N,
        "sample_rate_hz": cfg.采样率_fs,
        "duration_s": cfg.总时长_T,
    }


def run_phase_sweep() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    sweep_root = FIG_DIR / "phase_sweep"
    for i, phase_deg in enumerate(PHASE_SWEEP_DEGREES):
        rows.append(run_case(
            f0_hz=1_000.0,
            input_vpp=1.0,
            case_index=100 + i,
            phase_rad=math.radians(phase_deg),
            figure_root=sweep_root,
            figure_prefix="single_phase_sweep",
        ))
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def config_snapshot() -> dict[str, Any]:
    cfg = make_config(FREQUENCIES_HZ[0], INPUT_VPP_LEVELS[0], BASE_SEED)
    return {
        "source_pdf": "相关文件/第一层仿真.pdf",
        "lockin_type": "single_phase",
        "single_phase_formula": "X = LPF{s(t) cos(theta_ref)}, A_single = 2X = A cos(phi) when reference is aligned",
        "frequencies_hz": FREQUENCIES_HZ,
        "input_vpp_levels": INPUT_VPP_LEVELS,
        "samples_per_cycle": SAMPLES_PER_CYCLE,
        "duration_s": SIM_DURATION_S,
        "true_phase_deg": math.degrees(PHI_TRUE_RAD),
        "phase_sweep_degrees": PHASE_SWEEP_DEGREES,
        "noise_model": {
            "measurement_channel": "A cos(2πf0t+phi+eta_phi) + b0 + d(t) + n_w + n_1/f + n_line + n_near",
            "reference_channel": "Ar(1+eps_a) cos(2πf0t+eta_phi+eps_phi,r) + harmonics + n_r,w + n_r,line",
        },
        "measurement_noise_parameters": {
            "white_noise_en_V_per_sqrtHz": cfg.白噪声谱密度_en,
            "white_noise_rms_V_at_1kHz_case": cfg.白噪声谱密度_en * math.sqrt(cfg.采样率_fs / 2.0),
            "white_noise_formula": "sigma_w = e_n * sqrt(fs / 2)",
            "dc_offset_b0_V": cfg.直流偏置_b0,
            "drift_sine_amp_V": cfg.漂移正弦幅值,
            "drift_linear_slope_V_per_s": cfg.漂移线性斜率,
            "one_over_f_rms_V": cfg.一_f_目标均方根,
            "line_harmonic_amplitudes_V": [cfg.工频幅值_B1, cfg.工频幅值_B2, cfg.工频幅值_B3],
            "near_frequency_amplitudes_V": [cfg.邻近干扰幅值_C1, cfg.邻近干扰幅值_C2],
            "near_frequency_offsets_Hz": [cfg.邻近干扰频偏_df1_Hz, cfg.邻近干扰频偏_df2_Hz],
        },
        "reference_noise_parameters": {
            "amplitude_ripple": cfg.参考幅度起伏正弦幅值,
            "dip_depths": [cfg.参考局部掉幅深度1, cfg.参考局部掉幅深度2],
            "harmonics_V": [cfg.参考谐波_H2, cfg.参考谐波_H3, cfg.参考谐波_H5],
            "white_noise_en_V_per_sqrtHz": cfg.参考白噪声谱密度_en_r,
            "white_noise_rms_V_at_1kHz_case": cfg.参考白噪声谱密度_en_r * math.sqrt(cfg.采样率_fs / 2.0),
            "white_noise_formula": "sigma_r,w = e_n,r * sqrt(fs / 2)",
            "line_leakage_V": [cfg.参考工频幅值_RB1, cfg.参考工频幅值_RB2],
            "common_phase_noise_rms_rad": cfg.公共相位噪声_RMS_rad,
            "reference_phase_jitter_rms_rad": cfg.参考独立相位抖动_RMS_rad,
        },
        "algorithm_switches": {
            "scene": asdict(cfg.场景项),
            "processing_note": "单相算法只使用同相 X 通道；不能恢复未知相位，只能恢复 A cos(phi) 投影。",
        },
    }


def write_summary_md(rows: list[dict[str, Any]], phase_rows: list[dict[str, Any]]) -> Path:
    abs_true_errors = [abs(float(row["error_vs_true_peak_percent"])) for row in rows]
    abs_projection_errors = [abs(float(row["error_vs_single_phase_projection_percent"])) for row in rows]
    rel_uncertainties = [float(row["relative_u_A_percent"]) for row in rows]
    worst_true = max(rows, key=lambda row: abs(float(row["error_vs_true_peak_percent"])))

    lines = [
        "# 单相锁相加噪声仿真结果",
        "",
        "本次仿真使用与双相仿真相同的受噪输入模型，噪声结构来自 `相关文件/第一层仿真.pdf`。区别是处理算法只保留同相 X 通道，不计算正交 Y 通道，因此单相锁相恢复的是 `A cos(phi)` 投影，而不是未知相位下的真实幅值 `A`。",
        "",
        f"仿真设置：频率 `1/2/5/10 kHz`，信号源档位 `0.1/1/3/5/10 Vpp`，真实相位 `{math.degrees(PHI_TRUE_RAD):.1f}°`，每组采样 `T={SIM_DURATION_S:.1f} s`，每周期 {SAMPLES_PER_CYCLE} 点。白噪声按 PDF 公式 `sigma=e_n sqrt(fs/2)` 标定。",
        "",
        "## 总体结果",
        "",
        f"- 共完成 {len(rows)} 组单相加噪声仿真，全部生成 6 联图。",
        f"- 相对真实峰值的幅值偏差：中位数 {np.median(abs_true_errors):.3f}%，最大 {max(abs_true_errors):.3f}%。",
        f"- 相对理论单相投影 `A cos(phi)` 的偏差：中位数 {np.median(abs_projection_errors):.3f}%，最大 {max(abs_projection_errors):.3f}%。",
        f"- 相对幅值不确定度：中位数 {np.median(rel_uncertainties):.3f}%，最大 {max(rel_uncertainties):.3f}%。",
        f"- 最大真幅偏差出现在 {worst_true['frequency_hz']/1000:g} kHz、{worst_true['input_vpp_generator']:g} Vpp：偏差 {worst_true['error_vs_true_peak_percent']:+.3f}%。",
        f"- 单相处理中已补偿参考前置滤波相位延迟；1 kHz 工况补偿量约为 {rows[0]['reference_filter_phase_delay_deg']:.2f}°。",
        "",
        "## 恢复效果与不确定度",
        "",
        "| 频率 | 信号源设置 | 真实峰值 | 理论单相投影 | 单相恢复值 | 相对真实峰值偏差 | 相对投影偏差 | 幅值不确定度 | 相对不确定度 | 输入 SNR | 单相 SNR | 6联图 |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        figure = row["figure"]
        lines.append(
            f"| {row['frequency_hz']/1000:g} kHz | {row['input_vpp_generator']:g} Vpp | "
            f"{row['true_output_peak_mV']:.3f} mV | {row['single_phase_theoretical_projection_mV']:.3f} mV | "
            f"{row['recovered_single_phase_projection_mV']:.3f} mV | {row['error_vs_true_peak_percent']:+.3f}% | "
            f"{row['error_vs_single_phase_projection_percent']:+.3f}% | {row['u_A_mV']:.4f} mV | "
            f"{row['relative_u_A_percent']:.4f}% | {fmt_number(row['input_snr_db'], 2)} dB | "
            f"{fmt_number(row['single_phase_snr_db'], 2)} dB | [{Path(figure).name}]({figure}) |"
        )

    lines.extend([
        "",
        "## 结论",
        "",
        "## 相位扫描",
        "",
        "下面固定 `1 kHz, 1 Vpp`，按照老师给出的相位示例扫描 `0°/30°/60°/90°`。单相理论值为 `A cos(phi)`。",
        "",
        "| 相位 | 真实峰值 | 理论单相投影 | 单相恢复值 | 相对真实峰值偏差 | 相对投影偏差 | 幅值不确定度 | 相对不确定度 | 6联图 |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ])
    for row in phase_rows:
        lines.append(
            f"| {row['true_phase_deg']:.0f}° | {row['true_output_peak_mV']:.3f} mV | "
            f"{row['single_phase_theoretical_projection_mV']:.3f} mV | "
            f"{row['recovered_single_phase_projection_mV']:.3f} mV | "
            f"{fmt_percent(row['error_vs_true_peak_percent'])} | "
            f"{fmt_percent(row['error_vs_single_phase_projection_percent'])} | "
            f"{row['u_A_mV']:.4f} mV | {row['relative_u_A_percent']:.4f}% | "
            f"[{Path(row['figure']).name}]({row['figure']}) |"
        )

    lines.extend([
        "",
        "## 结论",
        "",
        "单相锁相在参考相位严格对齐时可以恢复幅值；但当真实相位未知时，它恢复的是 `A cos(phi)`，会产生由相位引起的系统性低估。相位扫描显示：`phi=0°` 基本正确，`phi=30°` 约恢复为 `A cos30°`，`phi=60°` 约恢复一半，`phi=90°` 接近恢复不出来。双相锁相通过 `A=2 sqrt(X^2+Y^2)` 可以消除这类未知相位投影误差。",
        "",
        "## 6联图目录",
        "",
    ])
    for f0 in FREQUENCIES_HZ:
        label = frequency_label(f0)
        lines.append(f"- `{label}`：`six_panel/{label}/`")

    path = OUT_DIR / "single_phase_simulation_summary.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    case_index = 0
    for f0_hz in FREQUENCIES_HZ:
        for input_vpp in INPUT_VPP_LEVELS:
            rows.append(run_case(f0_hz, input_vpp, case_index))
            case_index += 1
    phase_rows = run_phase_sweep()

    csv_path = DATA_DIR / "single_phase_simulation_results.csv"
    phase_csv_path = DATA_DIR / "single_phase_phase_sweep_results.csv"
    config_path = OUT_DIR / "single_phase_simulation_config.json"
    summary_path = write_summary_md(rows, phase_rows)
    write_csv(csv_path, rows)
    write_csv(phase_csv_path, phase_rows)
    config_path.write_text(json.dumps(config_snapshot(), ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"单相锁相加噪声仿真完成：{len(rows)} 组")
    print(f"6联图目录：{FIG_DIR}")
    print(f"结果表：{csv_path}")
    print(f"相位扫描表：{phase_csv_path}")
    print(f"MD文档：{summary_path}")


if __name__ == "__main__":
    main()
