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
    "savefig.dpi": 300,
})
import matplotlib.pyplot as plt


def 抽样绘制(ax, x: np.ndarray, y: np.ndarray, max_points: int = 5000, **kwargs) -> None:
    step = max(len(x) // max_points, 1)
    ax.plot(x[::step], y[::step], **kwargs)


def 按周期取样本数(total_len: int, fs: float, f0: float, cycles: float = 5.0) -> int:
    n = int(round(cycles * fs / f0))
    return max(2, min(total_len, n))


def 格式化时间窗(n: int, fs: float) -> str:
    duration = n / fs
    if duration < 1e-3:
        return f"{duration * 1e6:.1f} µs"
    if duration < 1.0:
        return f"{duration * 1e3:.2f} ms"
    return f"{duration:.2f} s"


def 格式化幅值(a_v: float) -> str:
    a_abs = abs(float(a_v))
    if a_abs >= 1.0:
        return f"{a_v:.3f} V"
    if a_abs >= 1e-3:
        return f"{a_v * 1e3:.3f} mV"
    return f"{a_v * 1e6:.3f} µV"


def 保存仿真六联图(cfg: Any, run: Mapping[str, Any], out_path: Path) -> None:
    t = np.asarray(run["t"], dtype=float)
    s = np.asarray(run["s"], dtype=float)
    s_dc = s - np.mean(s)
    t_sync = np.asarray(run["t_sync"], dtype=float)
    x_raw = np.asarray(run["x_raw"], dtype=float)
    y_raw = np.asarray(run["y_raw"], dtype=float)
    x_lp = np.asarray(run["x_lp"], dtype=float)
    y_lp = np.asarray(run["y_lp"], dtype=float)
    steady_mask = np.asarray(run["稳态掩码"], dtype=bool)
    valid_mask = np.asarray(run["有效掩码"], dtype=bool)

    phi_rec = float(run["phi_true_rec"]) if run["phi_true_rec"] is not None else float(run["phi_meas"] - run["theta_delay"])
    s_rec = float(run["a_rec"]) * np.cos(2.0 * np.pi * cfg.参考频率_f0 * t + phi_rec)

    n_show = 按周期取样本数(len(t), cfg.采样率_fs, cfg.参考频率_f0, cycles=5.0)
    window_label = 格式化时间窗(n_show, cfg.采样率_fs)

    fig, axes = plt.subplots(2, 3, figsize=(13.5, 7.8), constrained_layout=True, facecolor="white")
    ax = axes.ravel()

    ax[0].plot(t[:n_show] * 1000.0, s[:n_show], color="#0F4D92", linewidth=0.9)
    ax[0].set_title(f"原始测量通道波形（含直流偏置，前 {window_label}）", fontsize=11, fontweight="bold")
    ax[0].set_xlabel("时间 / ms")
    ax[0].set_ylabel("幅值 / V")
    ax[0].grid(True, alpha=0.3)

    抽样绘制(ax[1], t_sync * 1000.0, x_raw, color="#C8C8C8", linewidth=0.7, label="混频")
    抽样绘制(ax[1], t_sync * 1000.0, x_lp, color="#B64342", linewidth=1.3, label="低通")
    ax[1].set_title("X 通道：混频到低通", fontsize=11, fontweight="bold")
    ax[1].set_xlabel("时间 / ms")
    ax[1].set_ylabel("幅值 / V")
    ax[1].grid(True, alpha=0.3)
    ax[1].legend(loc="upper right", frameon=False)

    抽样绘制(ax[2], t_sync * 1000.0, y_raw, color="#C8C8C8", linewidth=0.7, label="混频")
    抽样绘制(ax[2], t_sync * 1000.0, y_lp, color="#0F4D92", linewidth=1.3, label="低通")
    ax[2].set_title("Y 通道：混频到低通", fontsize=11, fontweight="bold")
    ax[2].set_xlabel("时间 / ms")
    ax[2].set_ylabel("幅值 / V")
    ax[2].grid(True, alpha=0.3)
    ax[2].legend(loc="upper right", frameon=False)

    sig_fft = np.abs(np.fft.rfft(s - np.mean(s))) / max(len(s), 1)
    f_ax = np.fft.rfftfreq(len(s), d=1.0 / cfg.采样率_fs)
    max_f = min(max(5000.0, cfg.参考频率_f0 * 2.5), cfg.采样率_fs / 2.0)
    fft_mask = f_ax <= max_f
    抽样绘制(ax[3], f_ax[fft_mask], sig_fft[fft_mask], color="#0F4D92", linewidth=0.9)
    ax[3].axvline(cfg.参考频率_f0, color="#B64342", linestyle="--", linewidth=1.0, label="$f_0$")
    ax[3].set_title("信号频谱", fontsize=11, fontweight="bold")
    ax[3].set_xlabel("频率 / Hz")
    ax[3].set_ylabel("|FFT|")
    ax[3].grid(True, alpha=0.3)
    ax[3].legend(loc="upper right", frameon=False)

    ax[4].plot(t[:n_show] * 1000.0, s_dc[:n_show], color="#0F4D92", linewidth=0.8, label="原始去直流")
    ax[4].plot(t[:n_show] * 1000.0, s_rec[:n_show], color="#B64342", linewidth=1.2, label="锁相恢复基波")
    ax[4].set_title("去直流原始信号 vs 锁相恢复基波", fontsize=11, fontweight="bold")
    ax[4].set_xlabel("时间 / ms")
    ax[4].set_ylabel("幅值 / V")
    ax[4].grid(True, alpha=0.3)
    ax[4].legend(loc="upper right", frameon=False)

    抽样绘制(ax[5], t_sync * 1000.0, x_lp, color="#B64342", linewidth=1.1, label="X(t)")
    抽样绘制(ax[5], t_sync * 1000.0, y_lp, color="#0F4D92", linewidth=1.1, label="Y(t)")
    if np.any(steady_mask):
        ax[5].axvline(t_sync[int(np.argmax(steady_mask))] * 1000.0, color="#272727", linestyle="--", linewidth=1.0, label="稳态")
    if np.any(valid_mask):
        ax[5].axvline(t_sync[int(np.argmax(valid_mask))] * 1000.0, color="#767676", linestyle=":", linewidth=1.0, label="有效")
    ax[5].set_title(f"低通稳态：X={run['mu_x']:.3e}, Y={run['mu_y']:.3e} V", fontsize=11, fontweight="bold")
    ax[5].set_xlabel("时间 / ms")
    ax[5].set_ylabel("幅值 / V")
    ax[5].grid(True, alpha=0.3)
    ax[5].legend(loc="upper right", frameon=False)

    title_parts = [f"A={格式化幅值(float(run['a_rec']))}"]
    if "theoretical_peak_v" in run:
        theoretical_peak = float(run["theoretical_peak_v"])
        title_parts.append(f"理论输出峰值={格式化幅值(theoretical_peak)}")
        if theoretical_peak > 0:
            err_percent = 100.0 * (float(run["a_rec"]) / theoretical_peak - 1.0)
            title_parts.append(f"偏差={err_percent:+.2f}%")
    if "true_phase_deg" in run:
        title_parts.append(f"真实相位={float(run['true_phase_deg']):.2f}°")
    if run["phi_true_rec"] is None:
        title_parts.append("恢复相位无效")
    else:
        title_parts.append(f"恢复相位={np.degrees(float(run['phi_true_rec'])):.2f}°")
    title_parts.append(f"SNR={float(run['snr_vector_db']):.1f} dB")

    fig.suptitle("，".join(title_parts), fontsize=14, fontweight="bold")
    fig.savefig(out_path, dpi=int(run.get("figure_dpi", 300)), bbox_inches="tight")
    plt.close(fig)
