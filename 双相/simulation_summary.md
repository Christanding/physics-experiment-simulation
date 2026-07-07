# 第一层加噪声算法仿真结果

本次仿真只使用纯算法生成数据，不再和实验短采集 CSV 比较。噪声结构按 `相关文件/第一层仿真.pdf`：测量通道为目标信号、直流偏置、慢漂移、白噪声、带限 1/f 噪声、工频谐波和邻近频率干扰；参考通道为受噪参考、幅度起伏/局部掉幅、谐波、白噪声、工频泄漏、公共相噪和参考独立相位抖动。

仿真设置：频率 `1/2/5/10 kHz`，信号源档位 `0.1/1/3/5/10 Vpp`，理论输出峰值按 `信号源 Vpp / 20` 计算；每组采样 `T=6.0 s`，每周期 12 点。本版为强噪声压力测试：测量通道白噪声按 `e_n=2.00e-05 V/sqrt(Hz)` 和 `sigma=e_n sqrt(fs/2)` 标定，参考通道白噪声按 `e_n=2.50e-04 V/sqrt(Hz)` 标定，并叠加工频、慢漂移、1/f 噪声和邻近频率干扰。

## 总体结果

- 共完成 20 组加噪声仿真，全部生成 6 联图。
- 幅值绝对偏差：中位数 0.183%，最大 1.554%。
- 相对幅值不确定度：中位数 0.222%，最大 4.493%。
- 相位误差：中位数 0.411°，最大 2.875°。
- 最大幅值偏差出现在 1 kHz、0.1 Vpp：偏差 -1.554%。

## 恢复效果与不确定度

| 频率 | 信号源设置 | 理论输出峰值 | 恢复峰值 | 幅值偏差 | 幅值不确定度 | 相对不确定度 | 真实相位 | 恢复相位 | 相位不确定度 | 锁相 SNR | 6联图 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 kHz | 0.1 Vpp | 5.000 mV | 4.922 mV | -1.554% | 0.1983 mV | 4.0285% | 8.00° | 5.512° | 6.9523° | 15.97 dB | [simulation_1kHz_0p1Vpp_phi_8deg.png](six_panel/1kHz/simulation_1kHz_0p1Vpp_phi_8deg.png) |
| 1 kHz | 1 Vpp | 50.000 mV | 49.881 mV | -0.237% | 0.2607 mV | 0.5226% | 8.00° | 7.771° | 0.9984° | 33.12 dB | [simulation_1kHz_1Vpp_phi_8deg.png](six_panel/1kHz/simulation_1kHz_1Vpp_phi_8deg.png) |
| 1 kHz | 3 Vpp | 150.000 mV | 149.714 mV | -0.191% | 0.4076 mV | 0.2722% | 8.00° | 7.698° | 0.4485° | 40.14 dB | [simulation_1kHz_3Vpp_phi_8deg.png](six_panel/1kHz/simulation_1kHz_3Vpp_phi_8deg.png) |
| 1 kHz | 5 Vpp | 250.000 mV | 249.563 mV | -0.175% | 0.4113 mV | 0.1648% | 8.00° | 6.971° | 0.7215° | 36.30 dB | [simulation_1kHz_5Vpp_phi_8deg.png](six_panel/1kHz/simulation_1kHz_5Vpp_phi_8deg.png) |
| 1 kHz | 10 Vpp | 500.000 mV | 499.525 mV | -0.095% | 0.7461 mV | 0.1494% | 8.00° | 7.311° | 0.3461° | 42.50 dB | [simulation_1kHz_10Vpp_phi_8deg.png](six_panel/1kHz/simulation_1kHz_10Vpp_phi_8deg.png) |
| 2 kHz | 0.1 Vpp | 5.000 mV | 4.938 mV | -1.244% | 0.2218 mV | 4.4929% | 8.00° | 5.776° | 7.3086° | 15.41 dB | [simulation_2kHz_0p1Vpp_phi_8deg.png](six_panel/2kHz/simulation_2kHz_0p1Vpp_phi_8deg.png) |
| 2 kHz | 1 Vpp | 50.000 mV | 49.864 mV | -0.272% | 0.2120 mV | 0.4253% | 8.00° | 6.972° | 0.7426° | 35.53 dB | [simulation_2kHz_1Vpp_phi_8deg.png](six_panel/2kHz/simulation_2kHz_1Vpp_phi_8deg.png) |
| 2 kHz | 3 Vpp | 150.000 mV | 149.781 mV | -0.146% | 0.3352 mV | 0.2238% | 8.00° | 8.186° | 0.1807° | 46.37 dB | [simulation_2kHz_3Vpp_phi_8deg.png](six_panel/2kHz/simulation_2kHz_3Vpp_phi_8deg.png) |
| 2 kHz | 5 Vpp | 250.000 mV | 249.666 mV | -0.134% | 0.3814 mV | 0.1528% | 8.00° | 6.841° | 0.1549° | 48.22 dB | [simulation_2kHz_5Vpp_phi_8deg.png](six_panel/2kHz/simulation_2kHz_5Vpp_phi_8deg.png) |
| 2 kHz | 10 Vpp | 500.000 mV | 499.376 mV | -0.125% | 0.6924 mV | 0.1387% | 8.00° | 7.710° | 0.4215° | 40.99 dB | [simulation_2kHz_10Vpp_phi_8deg.png](six_panel/2kHz/simulation_2kHz_10Vpp_phi_8deg.png) |
| 5 kHz | 0.1 Vpp | 5.000 mV | 4.948 mV | -1.043% | 0.1953 mV | 3.9462% | 8.00° | 5.125° | 7.8333° | 15.15 dB | [simulation_5kHz_0p1Vpp_phi_8deg.png](six_panel/5kHz/simulation_5kHz_0p1Vpp_phi_8deg.png) |
| 5 kHz | 1 Vpp | 50.000 mV | 49.892 mV | -0.216% | 0.2291 mV | 0.4591% | 8.00° | 7.702° | 1.0390° | 33.01 dB | [simulation_5kHz_1Vpp_phi_8deg.png](six_panel/5kHz/simulation_5kHz_1Vpp_phi_8deg.png) |
| 5 kHz | 3 Vpp | 150.000 mV | 149.782 mV | -0.145% | 0.3311 mV | 0.2210% | 8.00° | 6.622° | 0.9591° | 34.11 dB | [simulation_5kHz_3Vpp_phi_8deg.png](six_panel/5kHz/simulation_5kHz_3Vpp_phi_8deg.png) |
| 5 kHz | 5 Vpp | 250.000 mV | 249.101 mV | -0.360% | 0.3564 mV | 0.1431% | 8.00° | 7.682° | 0.5400° | 38.97 dB | [simulation_5kHz_5Vpp_phi_8deg.png](six_panel/5kHz/simulation_5kHz_5Vpp_phi_8deg.png) |
| 5 kHz | 10 Vpp | 500.000 mV | 499.618 mV | -0.076% | 0.5973 mV | 0.1195% | 8.00° | 8.198° | 0.2416° | 45.71 dB | [simulation_5kHz_10Vpp_phi_8deg.png](six_panel/5kHz/simulation_5kHz_10Vpp_phi_8deg.png) |
| 10 kHz | 0.1 Vpp | 5.000 mV | 4.944 mV | -1.127% | 0.1686 mV | 3.4094% | 8.00° | 5.815° | 5.9688° | 15.40 dB | [simulation_10kHz_0p1Vpp_phi_8deg.png](six_panel/10kHz/simulation_10kHz_0p1Vpp_phi_8deg.png) |
| 10 kHz | 1 Vpp | 50.000 mV | 49.894 mV | -0.212% | 0.1964 mV | 0.3937% | 8.00° | 7.710° | 0.9362° | 31.32 dB | [simulation_10kHz_1Vpp_phi_8deg.png](six_panel/10kHz/simulation_10kHz_1Vpp_phi_8deg.png) |
| 10 kHz | 3 Vpp | 150.000 mV | 149.749 mV | -0.167% | 0.2659 mV | 0.1776% | 8.00° | 7.807° | 0.4368° | 38.07 dB | [simulation_10kHz_3Vpp_phi_8deg.png](six_panel/10kHz/simulation_10kHz_3Vpp_phi_8deg.png) |
| 10 kHz | 5 Vpp | 250.000 mV | 249.566 mV | -0.173% | 0.2311 mV | 0.0926% | 8.00° | 8.448° | 0.2032° | 44.95 dB | [simulation_10kHz_5Vpp_phi_8deg.png](six_panel/10kHz/simulation_10kHz_5Vpp_phi_8deg.png) |
| 10 kHz | 10 Vpp | 500.000 mV | 499.320 mV | -0.136% | 0.5107 mV | 0.1023% | 8.00° | 8.374° | 0.2853° | 41.53 dB | [simulation_10kHz_10Vpp_phi_8deg.png](six_panel/10kHz/simulation_10kHz_10Vpp_phi_8deg.png) |

## 相位扫描

下面固定 `1 kHz, 1 Vpp`，扫描 `0°/30°/60°/90°`。双相理论上应对未知相位不敏感，恢复峰值仍接近真实峰值。

| 相位 | 理论输出峰值 | 双相恢复峰值 | 幅值偏差 | 幅值不确定度 | 相对不确定度 | 恢复相位 | 相位误差 | 相位不确定度 | 6联图 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 0° | 50.000 mV | 49.971 mV | -0.057% | 0.1558 mV | 0.3117% | 0.392° | 0.392° | 0.3429° | [double_phase_sweep_1kHz_1Vpp_phi_0deg.png](six_panel/phase_sweep/1kHz/double_phase_sweep_1kHz_1Vpp_phi_0deg.png) |
| 30° | 50.000 mV | 49.769 mV | -0.461% | 0.4727 mV | 0.9498% | 29.124° | 0.876° | 0.5632° | [double_phase_sweep_1kHz_1Vpp_phi_30deg.png](six_panel/phase_sweep/1kHz/double_phase_sweep_1kHz_1Vpp_phi_30deg.png) |
| 60° | 50.000 mV | 49.782 mV | -0.435% | 0.6839 mV | 1.3738% | 60.037° | 0.037° | 0.6922° | [double_phase_sweep_1kHz_1Vpp_phi_60deg.png](six_panel/phase_sweep/1kHz/double_phase_sweep_1kHz_1Vpp_phi_60deg.png) |
| 90° | 50.000 mV | 49.694 mV | -0.612% | 0.6575 mV | 1.3230% | 89.674° | 0.326° | 0.7817° | [double_phase_sweep_1kHz_1Vpp_phi_90deg.png](six_panel/phase_sweep/1kHz/double_phase_sweep_1kHz_1Vpp_phi_90deg.png) |

## 6联图目录

- `1kHz`：`six_panel/1kHz/`
- `2kHz`：`six_panel/2kHz/`
- `5kHz`：`six_panel/5kHz/`
- `10kHz`：`six_panel/10kHz/`