from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any, Mapping

import numpy as np

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "matplotlib"))
import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams.update({
    "font.family": ["Times New Roman", "SimSun"],
    "font.serif": ["Times New Roman", "SimSun"],
    "font.sans-serif": ["Times New Roman", "SimSun"],
    "mathtext.fontset": "custom",
    "mathtext.rm": "Times New Roman",
    "mathtext.it": "Times New Roman:italic",
    "mathtext.bf": "Times New Roman:bold",
    "axes.unicode_minus": False,
    "axes.linewidth": 0.8,
    "xtick.direction": "out",
    "ytick.direction": "out",
    "figure.dpi": 160,
    "savefig.dpi": 220,
})
import matplotlib.pyplot as plt


def sampled_plot(ax, x: np.ndarray, y: np.ndarray, max_points: int = 2500, **kwargs) -> None:
    step = max(len(x) // max_points, 1)
    ax.plot(x[::step], y[::step], **kwargs)


def show_samples(total_len: int, fs_hz: float, f0_hz: float, cycles: float = 5.0) -> int:
    return max(2, min(total_len, int(round(cycles * fs_hz / f0_hz))))


def format_duration(n: int, fs_hz: float) -> str:
    duration = n / fs_hz
    if duration < 1e-3:
        return f"{duration * 1e6:.1f} µs"
    if duration < 1.0:
        return f"{duration * 1e3:.2f} ms"
    return f"{duration:.2f} s"


def format_amp(value_v: float) -> str:
    value_abs = abs(float(value_v))
    if value_abs >= 1.0:
        return f"{value_v:.3f} V"
    if value_abs >= 1e-3:
        return f"{value_v * 1e3:.3f} mV"
    return f"{value_v * 1e6:.3f} µV"


def save_single_phase_six_panel(cfg: Any, run: Mapping[str, Any], out_path: Path) -> None:
    t = np.asarray(run["t"], dtype=float)
    s = np.asarray(run["s"], dtype=float)
    s_dc = s - np.mean(s)
    t_sync = np.asarray(run["t_sync"], dtype=float)
    x_raw = np.asarray(run["x_raw"], dtype=float)
    x_lp = np.asarray(run["x_lp"], dtype=float)
    ref_cos = np.asarray(run["ref_cos"], dtype=float)
    steady_mask = np.asarray(run["稳态掩码"], dtype=bool)
    valid_mask = np.asarray(run["有效掩码"], dtype=bool)

    n_show = show_samples(len(t), cfg.采样率_fs, cfg.参考频率_f0)
    n_sync_show = show_samples(len(t_sync), cfg.采样率_fs, cfg.参考频率_f0)
    window_label = format_duration(n_show, cfg.采样率_fs)
    a_proj = float(run["a_projection"])
    s_rec = a_proj * np.cos(2.0 * np.pi * cfg.参考频率_f0 * t)

    fig, axes = plt.subplots(2, 3, figsize=(13.5, 7.8), constrained_layout=True, facecolor="white")
    ax = axes.ravel()

    ax[0].plot(t[:n_show] * 1000.0, s[:n_show], color="#0F4D92", marker="o", markersize=2.0, linewidth=0.8)
    ax[0].set_title(f"原始测量通道波形（含噪声，前 {window_label}）", fontsize=11, fontweight="bold")
    ax[0].set_xlabel("时间 / ms")
    ax[0].set_ylabel("幅值 / V")
    ax[0].grid(True, alpha=0.3)

    ax[1].plot(t_sync[:n_sync_show] * 1000.0, ref_cos[:n_sync_show], color="#1F7A4D", linewidth=1.0)
    ax[1].set_title("单相参考：cos 通道", fontsize=11, fontweight="bold")
    ax[1].set_xlabel("时间 / ms")
    ax[1].set_ylabel("归一化参考")
    ax[1].grid(True, alpha=0.3)

    sampled_plot(ax[2], t_sync * 1000.0, x_raw, color="#C8C8C8", linewidth=0.7, label="混频")
    sampled_plot(ax[2], t_sync * 1000.0, x_lp, color="#B64342", linewidth=1.3, label="低通")
    ax[2].set_title("单相 X 通道：混频到低通", fontsize=11, fontweight="bold")
    ax[2].set_xlabel("时间 / ms")
    ax[2].set_ylabel("幅值 / V")
    ax[2].grid(True, alpha=0.3)
    ax[2].legend(loc="upper right", frameon=False)

    sig_fft = np.abs(np.fft.rfft(s - np.mean(s))) / max(len(s), 1)
    f_ax = np.fft.rfftfreq(len(s), d=1.0 / cfg.采样率_fs)
    max_f = min(max(5000.0, cfg.参考频率_f0 * 2.5), cfg.采样率_fs / 2.0)
    fft_mask = f_ax <= max_f
    sampled_plot(ax[3], f_ax[fft_mask], sig_fft[fft_mask], color="#0F4D92", linewidth=0.9)
    ax[3].axvline(cfg.参考频率_f0, color="#B64342", linestyle="--", linewidth=1.0, label="$f_0$")
    ax[3].set_title("信号频谱", fontsize=11, fontweight="bold")
    ax[3].set_xlabel("频率 / Hz")
    ax[3].set_ylabel("|FFT|")
    ax[3].grid(True, alpha=0.3)
    ax[3].legend(loc="upper right", frameon=False)

    ax[4].plot(t[:n_show] * 1000.0, s_dc[:n_show], color="#0F4D92", marker="o", markersize=2.0, linewidth=0.8, label="原始去直流")
    ax[4].plot(t[:n_show] * 1000.0, s_rec[:n_show], color="#B64342", linewidth=1.2, label="单相恢复投影")
    ax[4].set_title("去直流原始信号 vs 单相恢复投影", fontsize=11, fontweight="bold")
    ax[4].set_xlabel("时间 / ms")
    ax[4].set_ylabel("幅值 / V")
    ax[4].grid(True, alpha=0.3)
    ax[4].legend(loc="upper right", frameon=False)

    sampled_plot(ax[5], t_sync * 1000.0, x_lp, color="#B64342", linewidth=1.1, label="X(t)")
    if np.any(steady_mask):
        ax[5].axvline(t_sync[int(np.argmax(steady_mask))] * 1000.0, color="#272727", linestyle="--", linewidth=1.0, label="稳态")
    if np.any(valid_mask):
        ax[5].axvline(t_sync[int(np.argmax(valid_mask))] * 1000.0, color="#767676", linestyle=":", linewidth=1.0, label="有效")
    ax[5].set_title(f"低通稳态：X={run['mu_x']:.3e} V", fontsize=11, fontweight="bold")
    ax[5].set_xlabel("时间 / ms")
    ax[5].set_ylabel("幅值 / V")
    ax[5].grid(True, alpha=0.3)
    ax[5].legend(loc="upper right", frameon=False)

    true_peak = float(run["true_peak_v"])
    true_projection = float(run["single_phase_theoretical_v"])
    err_true = 100.0 * (a_proj / true_peak - 1.0)
    err_proj = 100.0 * (a_proj / true_projection - 1.0)
    title = (
        f"单相A={format_amp(a_proj)}，理论输出峰值={format_amp(true_peak)}，"
        f"理论单相投影={format_amp(true_projection)}，真幅偏差={err_true:+.2f}%，"
        f"投影偏差={err_proj:+.2f}%，真实相位={np.degrees(cfg.目标相位_phi):.2f}°"
    )
    fig.suptitle(title, fontsize=13, fontweight="bold")
    fig.savefig(out_path, dpi=int(run.get("figure_dpi", 220)), bbox_inches="tight")
    plt.close(fig)
