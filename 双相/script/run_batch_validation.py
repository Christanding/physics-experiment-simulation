from __future__ import annotations

import json
import math
import importlib.util
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np


def 加载锁相算法模块(py_path: str):
    """动态加载数字锁相算法模块。"""
    spec = importlib.util.spec_from_file_location("digital_lockin_module", py_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"无法加载模块：{py_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def 输入信号有效值(signal_array: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.asarray(signal_array, dtype=float) ** 2)))


def 计算原始输入SNR_dB(目标信号: np.ndarray, 总测量信号: np.ndarray) -> float:
    干扰 = np.asarray(总测量信号, dtype=float) - np.asarray(目标信号, dtype=float)
    sig_rms = 输入信号有效值(目标信号)
    noise_rms = 输入信号有效值(干扰)
    if noise_rms <= 0.0:
        return float("inf")
    return float(20.0 * math.log10(sig_rms / noise_rms))


def 运行单次场景(module, cfg) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, np.ndarray]]:
    """运行一次数字锁相仿真场景，返回：
    - run：主程序运行结果
    - result_cn：中文结果字典
    - components：仿真各组成分
    """
    t, s, r, components = module.生成锁相仿真数据(cfg)
    run = module.运行数字锁相(t, s, r, cfg)
    result_cn = module.生成中文结果字典(cfg, run)
    result_cn.setdefault("原始输入评估", {})
    result_cn["原始输入评估"]["输入SNR_dB"] = 计算原始输入SNR_dB(components["目标信号"], s)
    result_cn["原始输入评估"]["输入目标信号RMS_V"] = 输入信号有效值(components["目标信号"])
    result_cn["原始输入评估"]["输入总测量信号RMS_V"] = 输入信号有效值(s)
    result_cn["原始输入评估"]["输出SNR提升_dB"] = (
        float(run["snr_vector_db"]) - float(result_cn["原始输入评估"]["输入SNR_dB"])
        if np.isfinite(run["snr_vector_db"]) and np.isfinite(result_cn["原始输入评估"]["输入SNR_dB"])
        else None
    )
    return run, result_cn, components


if __name__ == "__main__":
    simulation_root = Path(__file__).resolve().parents[1]
    project_root = simulation_root.parents[1]
    模块路径 = str(project_root / "scripts" / "dm.py")
    输出目录 = simulation_root
    输出目录.mkdir(parents=True, exist_ok=True)

    module = 加载锁相算法模块(模块路径)

    # =============================
    # 一、保留原程序的“单场景原始部分”
    # =============================
    baseline_cfg = module.锁相仿真配置()
    baseline_run, baseline_result, _baseline_components = 运行单次场景(module, baseline_cfg)

    # =============================
    # 二、批量扫描验证
    # =============================
    扫描结果: Dict[str, Any] = {}

    # 1) 输入幅值扫描：100 mV → 10 mV → 1 mV → 100 µV
    amp_values = [1e-1, 1e-2, 1e-3, 1e-4]
    amp_true, amp_rec, amp_err = [], [], []
    for i, A in enumerate(amp_values):
        cfg = module.锁相仿真配置()
        cfg.随机种子 = baseline_cfg.随机种子 + 10 + i
        cfg.目标幅值_A = A
        run, _, _ = 运行单次场景(module, cfg)
        amp_true.append(float(A))
        amp_rec.append(float(run["a_rec"]))
        amp_err.append(abs(float(run["a_rec"]) - A) / A * 100.0)
    扫描结果["幅值扫描"] = {
        "真实幅值_V": amp_true,
        "恢复幅值_V": amp_rec,
        "幅值相对误差_percent": amp_err,
    }

    # 2) 噪声强度逐步增加
    noise_values = [1.0e-7, 2.0e-7, 4.0e-7, 8.0e-7, 1.6e-6]
    noise_snr_in, noise_snr_out, noise_amp_err = [], [], []
    for i, en in enumerate(noise_values):
        cfg = module.锁相仿真配置()
        cfg.随机种子 = baseline_cfg.随机种子 + 100 + i
        cfg.白噪声谱密度_en = en
        run, result_cn, _ = 运行单次场景(module, cfg)
        noise_snr_in.append(float(result_cn["原始输入评估"]["输入SNR_dB"]))
        noise_snr_out.append(float(run["snr_vector_db"]))
        noise_amp_err.append(float(result_cn["误差评估"]["幅值相对误差_percent"]))
    扫描结果["噪声扫描"] = {
        "白噪声谱密度_V_per_sqrtHz": noise_values,
        "输入SNR_dB": noise_snr_in,
        "输出SNR_vector_dB": noise_snr_out,
        "幅值相对误差_percent": noise_amp_err,
    }

    # 3) 积分时间 / 低通截止频率逐步变化
    T_values = [8.0, 12.0, 16.0, 24.0, 32.0]
    fc_values = [2.0, 1.5, 1.0, 0.75, 0.5]
    snr_gain_list, uA_list, uphi_list = [], [], []
    for i, (T, fc) in enumerate(zip(T_values, fc_values)):
        cfg = module.锁相仿真配置()
        cfg.随机种子 = baseline_cfg.随机种子 + 200 + i
        cfg.总时长_T = T
        cfg.解调低通截止频率 = fc
        # 积分时间增大时，第二级滑动平均窗口同步略增，体现“积分时间 / 低通截止频率逐步变化”
        cfg.第二级滑动平均窗口_s = min(0.40, max(0.10, 0.10 * math.sqrt(T / 8.0)))
        run, result_cn, _ = 运行单次场景(module, cfg)
        snr_gain_list.append(float(result_cn["原始输入评估"]["输出SNR提升_dB"]))
        uA_list.append(float(run["u_a"]))
        uphi_list.append(float(run["u_phi"]) if run["u_phi"] is not None else None)
    扫描结果["积分时间扫描"] = {
        "积分时间_s": T_values,
        "对应低通截止频率_Hz": fc_values,
        "SNR提升_dB": snr_gain_list,
        "u_A_V": uA_list,
        "u_phi_rad": uphi_list,
    }

    # 4) 相位差：0° 到 180°
    phase_deg_values = list(range(0, 181, 15))
    phase_rec_deg, phase_err_deg = [], []
    for i, deg in enumerate(phase_deg_values):
        cfg = module.锁相仿真配置()
        cfg.随机种子 = baseline_cfg.随机种子 + 300 + i
        cfg.目标相位_phi = math.radians(deg)
        run, _, _ = 运行单次场景(module, cfg)
        phi_rec = float(run["phi_true_rec"]) if run["phi_true_rec"] is not None else module.相位包裹到_pi(float(run["phi_meas"]) - float(run["theta_delay"]))
        err = abs(module.相位包裹到_pi(phi_rec - cfg.目标相位_phi))
        phase_rec_deg.append(math.degrees(phi_rec))
        phase_err_deg.append(math.degrees(err))
    扫描结果["相位扫描"] = {
        "输入相位_deg": phase_deg_values,
        "恢复相位_deg": phase_rec_deg,
        "相位误差_deg": phase_err_deg,
    }

    总结果 = {
        "说明": "基于数字锁相仿真主程序的批量扫描验证。该脚本只输出数值 JSON，不再生成非报告图。",
        "原单场景结果": baseline_result,
        "批量扫描结果": 扫描结果,
    }

    json_path = 输出目录 / "数字锁相批量扫描验证结果.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(总结果, f, ensure_ascii=False, indent=2)

    print("批量扫描验证完成。")
    print(f"JSON：{json_path}")
    print("原单场景恢复摘要：")
    print(f"  恢复幅值 = {baseline_run['a_rec']:.6e} V")
    print(f"  恢复相位 = {baseline_run['phi_true_rec'] if baseline_run['phi_true_rec'] is not None else '无效'}")
    print(f"  工程评估 SNR = {baseline_run['snr_vector_db']:.3f} dB")

