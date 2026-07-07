from __future__ import annotations

import math
from typing import Any

import numpy as np
from scipy import signal


def design_lowpass(order: int, cutoff_hz: float, fs_hz: float) -> tuple[np.ndarray, np.ndarray]:
    if not (0.0 < cutoff_hz < fs_hz / 2.0):
        raise ValueError(f"低通截止频率必须满足 0 < fc < fs/2，当前 fc={cutoff_hz}, fs={fs_hz}")
    return signal.butter(order, cutoff_hz, btype="low", fs=fs_hz)


def design_bandpass(order: int, low_hz: float, high_hz: float, fs_hz: float) -> np.ndarray:
    if not (0.0 < low_hz < high_hz < fs_hz / 2.0):
        raise ValueError(f"带通频率必须满足 0 < fl < fh < fs/2，当前 fl={low_hz}, fh={high_hz}, fs={fs_hz}")
    return signal.butter(order, [low_hz, high_hz], btype="bandpass", fs=fs_hz, output="sos")


def apply_reference_filter(x: np.ndarray, cfg: Any) -> np.ndarray:
    y = np.asarray(x, dtype=float)
    for f0 in cfg.陷波频率列表_Hz:
        if 0.0 < f0 < cfg.采样率_fs / 2.0:
            b_notch, a_notch = signal.iirnotch(w0=f0, Q=cfg.陷波品质因数_Q, fs=cfg.采样率_fs)
            y = signal.lfilter(b_notch, a_notch, y)
    bp_sos = design_bandpass(cfg.参考带通阶数, cfg.参考带通下截止频率, cfg.参考带通上截止频率, cfg.采样率_fs)
    return signal.sosfilt(bp_sos, y)


def reference_filter_phase_delay(cfg: Any) -> float:
    bp_sos = design_bandpass(cfg.参考带通阶数, cfg.参考带通下截止频率, cfg.参考带通上截止频率, cfg.采样率_fs)
    _, h_bp = signal.sosfreqz(bp_sos, worN=np.array([cfg.参考频率_f0], dtype=float), fs=cfg.采样率_fs)
    h_total = h_bp[0]
    for f0 in cfg.陷波频率列表_Hz:
        if 0.0 < f0 < cfg.采样率_fs / 2.0:
            b_notch, a_notch = signal.iirnotch(w0=f0, Q=cfg.陷波品质因数_Q, fs=cfg.采样率_fs)
            _, h_notch = signal.freqz(b_notch, a_notch, worN=np.array([cfg.参考频率_f0], dtype=float), fs=cfg.采样率_fs)
            h_total *= h_notch[0]
    return float(-np.angle(h_total))


def cascade_enbw_hz(filters: list[tuple[np.ndarray, np.ndarray]], fs_hz: float, wor_n: int = 16384) -> float:
    f_ref = None
    h_total = None
    for b, a in filters:
        f, h = signal.freqz(b, a, worN=wor_n, fs=fs_hz)
        if f_ref is None:
            f_ref = f
            h_total = h
        else:
            h_total = h_total * h
    if f_ref is None or h_total is None:
        raise ValueError("滤波器列表为空，无法计算 ENBW。")
    h2 = np.abs(h_total) ** 2
    h0 = float(h2[0])
    if h0 <= 0.0:
        raise ValueError("级联滤波器直流增益为 0，无法计算 ENBW。")
    return float(np.trapezoid(h2 / h0, f_ref))


def step_settle_time_s(b: np.ndarray, a: np.ndarray, fs_hz: float, tol: float = 0.007) -> float:
    n_test = max(int(fs_hz * 8), 20000)
    y = signal.lfilter(b, a, np.ones(n_test, dtype=float))
    y_final = float(y[-1])
    if abs(y_final) < 1e-15:
        return 0.0
    err = np.abs(y - y_final)
    bad = np.where(err > tol * abs(y_final))[0]
    idx = 0 if bad.size == 0 else min(int(bad[-1] + 1), n_test - 1)
    return idx / fs_hz


def robust_mean_std(x: np.ndarray, c: float = 1.5, n_iter: int = 6) -> tuple[float, float, np.ndarray]:
    x = np.asarray(x, dtype=float)
    if x.size == 0:
        raise ValueError("稳态样本为空，无法统计。")
    w = np.ones_like(x)
    mu = float(np.mean(x))
    for _ in range(max(n_iter, 1)):
        med = float(np.median(x))
        mad = float(np.median(np.abs(x - med)))
        scale = max(1.4826 * mad, 1e-18)
        resid = (x - mu) / scale
        w_new = np.ones_like(x)
        mask = np.abs(resid) > c
        w_new[mask] = c / np.maximum(np.abs(resid[mask]), 1e-18)
        mu_new = float(np.sum(w_new * x) / max(float(np.sum(w_new)), 1e-18))
        w = w_new
        if abs(mu_new - mu) <= 1e-15:
            mu = mu_new
            break
        mu = mu_new
    var = float(np.sum(w * (x - mu) ** 2) / max(float(np.sum(w)), 1e-18))
    return mu, math.sqrt(max(var, 0.0)), w


def run_single_phase_lockin(t: np.ndarray, s: np.ndarray, r: np.ndarray, cfg: Any) -> dict[str, Any]:
    t = np.asarray(t, dtype=float)
    s = np.asarray(s, dtype=float)
    r = np.asarray(r, dtype=float)
    s_dc = s - np.mean(s)
    r_dc = r - np.mean(r)

    r_f = apply_reference_filter(r_dc, cfg)
    theta_delay = reference_filter_phase_delay(cfg)
    r_analytic = signal.hilbert(r_f)
    edge_trim = int(round(cfg.希尔伯特附加裁剪周期数 * cfg.采样率_fs / cfg.参考频率_f0))
    start = edge_trim
    end = len(t) - edge_trim
    if end <= start + 100:
        raise ValueError("同步裁剪后剩余样本过少，请增大总时长 T 或减小裁剪量。")

    t_sync = t[start:end]
    s_sync = s_dc[start:end]
    r_analytic_sync = r_analytic[start:end]
    envelope = np.abs(r_analytic_sync)
    phase = np.unwrap(np.angle(r_analytic_sync))
    compensated_phase = phase + theta_delay
    ref_cos = np.cos(compensated_phase)
    x_raw = s_sync * ref_cos

    b_lp, a_lp = design_lowpass(cfg.解调低通阶数, cfg.解调低通截止频率, cfg.采样率_fs)
    x_lp1 = signal.lfilter(b_lp, a_lp, x_raw)
    win = max(int(round(cfg.第二级滑动平均窗口_s * cfg.采样率_fs)), 1)
    ma_kernel = np.ones(win, dtype=float) / win
    x_lp = signal.lfilter(ma_kernel, np.array([1.0]), x_lp1)

    settle_s = step_settle_time_s(b_lp, a_lp, cfg.采样率_fs) + (win - 1) / cfg.采样率_fs
    local_t = np.arange(len(x_lp), dtype=float) / cfg.采样率_fs
    steady_mask = local_t >= settle_s

    median_env = float(np.median(envelope))
    relative_env = envelope / max(median_env, cfg.包络安全阈值_epsilon)
    valid_mask = steady_mask & (relative_env >= cfg.低包络异常阈值_相对中位数)
    if np.count_nonzero(valid_mask) < 100:
        raise ValueError("稳态有效样本过少，无法可靠统计，请增大 T 或放宽设置。")

    x_steady = x_lp[valid_mask]
    mu_x, sigma_x, robust_w = robust_mean_std(x_steady, cfg.Huber阈值_c, cfg.鲁棒迭代次数)
    t_weighted = float(np.sum(robust_w) / cfg.采样率_fs)
    enbw_hz = cascade_enbw_hz([(b_lp, a_lp), (ma_kernel, np.array([1.0]))], cfg.采样率_fs)
    neff = max(float(2.0 * enbw_hz * t_weighted), 1.0)
    u_mu_x = sigma_x / math.sqrt(neff)

    a_projection = float(2.0 * mu_x)
    u_a_projection = float(2.0 * u_mu_x)
    snr_db = float("inf") if sigma_x <= 0.0 else float(20.0 * math.log10(abs(mu_x) / sigma_x))

    return {
        "t": t,
        "s": s,
        "r": r,
        "t_sync": t_sync,
        "s_sync": s_sync,
        "r_filtered": r_f,
        "ref_cos": ref_cos,
        "theta_delay": theta_delay,
        "ref_phase_raw": phase,
        "ref_phase_compensated": compensated_phase,
        "x_raw": x_raw,
        "x_lp": x_lp,
        "稳态掩码": steady_mask,
        "有效掩码": valid_mask,
        "mu_x": mu_x,
        "sigma_x": sigma_x,
        "a_projection": a_projection,
        "u_a_projection": u_a_projection,
        "enbw_hz": enbw_hz,
        "neff": neff,
        "t_weighted": t_weighted,
        "snr_db": snr_db,
        "reference_quality_mean": float(np.mean(np.clip(relative_env[valid_mask], 0.0, 1.0))),
        "steady_count": int(np.count_nonzero(steady_mask)),
        "effective_count": int(np.count_nonzero(valid_mask)),
        "dropped_count": int(np.count_nonzero(steady_mask) - np.count_nonzero(valid_mask)),
    }
