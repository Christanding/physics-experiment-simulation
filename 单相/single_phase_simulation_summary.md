# 单相锁相加噪声仿真结果

本次仿真使用与双相仿真相同的受噪输入模型，噪声结构来自 `相关文件/第一层仿真.pdf`。区别是处理算法只保留同相 X 通道，不计算正交 Y 通道，因此单相锁相恢复的是 `A cos(phi)` 投影，而不是未知相位下的真实幅值 `A`。

仿真设置：频率 `1/2/5/10 kHz`，信号源档位 `0.1/1/3/5/10 Vpp`，真实相位 `8.0°`，每组采样 `T=6.0 s`，每周期 12 点。白噪声按 PDF 公式 `sigma=e_n sqrt(fs/2)` 标定。

## 总体结果

- 共完成 20 组单相加噪声仿真，全部生成 6 联图。
- 相对真实峰值的幅值偏差：中位数 1.024%，最大 1.273%。
- 相对理论单相投影 `A cos(phi)` 的偏差：中位数 0.051%，最大 0.303%。
- 相对幅值不确定度：中位数 0.134%，最大 3.948%。
- 最大真幅偏差出现在 5 kHz、0.1 Vpp：偏差 -1.273%。
- 单相处理中已补偿参考前置滤波相位延迟；1 kHz 工况补偿量约为 19.89°。

## 恢复效果与不确定度

| 频率 | 信号源设置 | 真实峰值 | 理论单相投影 | 单相恢复值 | 相对真实峰值偏差 | 相对投影偏差 | 幅值不确定度 | 相对不确定度 | 输入 SNR | 单相 SNR | 6联图 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 kHz | 0.1 Vpp | 5.000 mV | 4.951 mV | 4.942 mV | -1.152% | -0.180% | 0.1951 mV | 3.9479% | 3.18 dB | 17.94 dB | [single_phase_1kHz_0p1Vpp_phi_8deg.png](six_panel/1kHz/single_phase_1kHz_0p1Vpp_phi_8deg.png) |
| 1 kHz | 1 Vpp | 50.000 mV | 49.513 mV | 49.486 mV | -1.027% | -0.055% | 0.1930 mV | 0.3901% | 23.10 dB | 38.03 dB | [single_phase_1kHz_1Vpp_phi_8deg.png](six_panel/1kHz/single_phase_1kHz_1Vpp_phi_8deg.png) |
| 1 kHz | 3 Vpp | 150.000 mV | 148.540 mV | 148.434 mV | -1.044% | -0.071% | 0.1916 mV | 0.1291% | 32.76 dB | 47.65 dB | [single_phase_1kHz_3Vpp_phi_8deg.png](six_panel/1kHz/single_phase_1kHz_3Vpp_phi_8deg.png) |
| 1 kHz | 5 Vpp | 250.000 mV | 247.567 mV | 247.461 mV | -1.015% | -0.043% | 0.2146 mV | 0.0867% | 37.22 dB | 51.24 dB | [single_phase_1kHz_5Vpp_phi_8deg.png](six_panel/1kHz/single_phase_1kHz_5Vpp_phi_8deg.png) |
| 1 kHz | 10 Vpp | 500.000 mV | 495.134 mV | 495.219 mV | -0.956% | +0.017% | 0.3192 mV | 0.0645% | 43.13 dB | 53.93 dB | [single_phase_1kHz_10Vpp_phi_8deg.png](six_panel/1kHz/single_phase_1kHz_10Vpp_phi_8deg.png) |
| 2 kHz | 0.1 Vpp | 5.000 mV | 4.951 mV | 4.939 mV | -1.223% | -0.252% | 0.1950 mV | 3.9476% | 1.59 dB | 17.91 dB | [single_phase_2kHz_0p1Vpp_phi_8deg.png](six_panel/2kHz/single_phase_2kHz_0p1Vpp_phi_8deg.png) |
| 2 kHz | 1 Vpp | 50.000 mV | 49.513 mV | 49.512 mV | -0.977% | -0.004% | 0.1970 mV | 0.3979% | 21.74 dB | 37.87 dB | [single_phase_2kHz_1Vpp_phi_8deg.png](six_panel/2kHz/single_phase_2kHz_1Vpp_phi_8deg.png) |
| 2 kHz | 3 Vpp | 150.000 mV | 148.540 mV | 148.408 mV | -1.061% | -0.089% | 0.2281 mV | 0.1537% | 31.13 dB | 46.17 dB | [single_phase_2kHz_3Vpp_phi_8deg.png](six_panel/2kHz/single_phase_2kHz_3Vpp_phi_8deg.png) |
| 2 kHz | 5 Vpp | 250.000 mV | 247.567 mV | 247.551 mV | -0.980% | -0.006% | 0.2600 mV | 0.1050% | 35.69 dB | 49.51 dB | [single_phase_2kHz_5Vpp_phi_8deg.png](six_panel/2kHz/single_phase_2kHz_5Vpp_phi_8deg.png) |
| 2 kHz | 10 Vpp | 500.000 mV | 495.134 mV | 494.929 mV | -1.014% | -0.041% | 0.2815 mV | 0.0569% | 41.72 dB | 54.90 dB | [single_phase_2kHz_10Vpp_phi_8deg.png](six_panel/2kHz/single_phase_2kHz_10Vpp_phi_8deg.png) |
| 5 kHz | 0.1 Vpp | 5.000 mV | 4.951 mV | 4.936 mV | -1.273% | -0.303% | 0.1940 mV | 3.9294% | -1.04 dB | 18.09 dB | [single_phase_5kHz_0p1Vpp_phi_8deg.png](six_panel/5kHz/single_phase_5kHz_0p1Vpp_phi_8deg.png) |
| 5 kHz | 1 Vpp | 50.000 mV | 49.513 mV | 49.469 mV | -1.061% | -0.089% | 0.2025 mV | 0.4094% | 18.97 dB | 37.73 dB | [single_phase_5kHz_1Vpp_phi_8deg.png](six_panel/5kHz/single_phase_5kHz_1Vpp_phi_8deg.png) |
| 5 kHz | 3 Vpp | 150.000 mV | 148.540 mV | 148.469 mV | -1.021% | -0.048% | 0.2056 mV | 0.1385% | 28.58 dB | 47.15 dB | [single_phase_5kHz_3Vpp_phi_8deg.png](six_panel/5kHz/single_phase_5kHz_3Vpp_phi_8deg.png) |
| 5 kHz | 5 Vpp | 250.000 mV | 247.567 mV | 247.326 mV | -1.070% | -0.097% | 0.2155 mV | 0.0871% | 33.03 dB | 51.47 dB | [single_phase_5kHz_5Vpp_phi_8deg.png](six_panel/5kHz/single_phase_5kHz_5Vpp_phi_8deg.png) |
| 5 kHz | 10 Vpp | 500.000 mV | 495.134 mV | 494.755 mV | -1.049% | -0.077% | 0.4042 mV | 0.0817% | 39.02 dB | 51.90 dB | [single_phase_5kHz_10Vpp_phi_8deg.png](six_panel/5kHz/single_phase_5kHz_10Vpp_phi_8deg.png) |
| 10 kHz | 0.1 Vpp | 5.000 mV | 4.951 mV | 4.953 mV | -0.945% | +0.029% | 0.1485 mV | 2.9989% | -3.45 dB | 18.02 dB | [single_phase_10kHz_0p1Vpp_phi_8deg.png](six_panel/10kHz/single_phase_10kHz_0p1Vpp_phi_8deg.png) |
| 10 kHz | 1 Vpp | 50.000 mV | 49.513 mV | 49.494 mV | -1.013% | -0.040% | 0.1434 mV | 0.2898% | 16.59 dB | 38.30 dB | [single_phase_10kHz_1Vpp_phi_8deg.png](six_panel/10kHz/single_phase_10kHz_1Vpp_phi_8deg.png) |
| 10 kHz | 3 Vpp | 150.000 mV | 148.540 mV | 148.510 mV | -0.993% | -0.020% | 0.1627 mV | 0.1096% | 26.08 dB | 46.91 dB | [single_phase_10kHz_3Vpp_phi_8deg.png](six_panel/10kHz/single_phase_10kHz_3Vpp_phi_8deg.png) |
| 10 kHz | 5 Vpp | 250.000 mV | 247.567 mV | 247.464 mV | -1.014% | -0.041% | 0.1612 mV | 0.0652% | 30.53 dB | 51.38 dB | [single_phase_10kHz_5Vpp_phi_8deg.png](six_panel/10kHz/single_phase_10kHz_5Vpp_phi_8deg.png) |
| 10 kHz | 10 Vpp | 500.000 mV | 495.134 mV | 494.667 mV | -1.067% | -0.094% | 0.2699 mV | 0.0546% | 36.53 dB | 52.94 dB | [single_phase_10kHz_10Vpp_phi_8deg.png](six_panel/10kHz/single_phase_10kHz_10Vpp_phi_8deg.png) |

## 结论

## 相位扫描

下面固定 `1 kHz, 1 Vpp`，按照老师给出的相位示例扫描 `0°/30°/60°/90°`。单相理论值为 `A cos(phi)`。

| 相位 | 真实峰值 | 理论单相投影 | 单相恢复值 | 相对真实峰值偏差 | 相对投影偏差 | 幅值不确定度 | 相对不确定度 | 6联图 |
|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 0° | 50.000 mV | 50.000 mV | 49.991 mV | -0.018% | -0.018% | 0.2025 mV | 0.4050% | [single_phase_sweep_1kHz_1Vpp_phi_0deg.png](six_panel/phase_sweep/1kHz/single_phase_sweep_1kHz_1Vpp_phi_0deg.png) |
| 30° | 50.000 mV | 43.301 mV | 43.279 mV | -13.442% | -0.051% | 0.2432 mV | 0.5620% | [single_phase_sweep_1kHz_1Vpp_phi_30deg.png](six_panel/phase_sweep/1kHz/single_phase_sweep_1kHz_1Vpp_phi_30deg.png) |
| 60° | 50.000 mV | 25.000 mV | 24.887 mV | -50.226% | -0.451% | 0.1683 mV | 0.6764% | [single_phase_sweep_1kHz_1Vpp_phi_60deg.png](six_panel/phase_sweep/1kHz/single_phase_sweep_1kHz_1Vpp_phi_60deg.png) |
| 90° | 50.000 mV | 0.000 mV | 0.025 mV | -99.951% | - | 0.2231 mV | 902.8903% | [single_phase_sweep_1kHz_1Vpp_phi_90deg.png](six_panel/phase_sweep/1kHz/single_phase_sweep_1kHz_1Vpp_phi_90deg.png) |

## 结论

单相锁相在参考相位严格对齐时可以恢复幅值；但当真实相位未知时，它恢复的是 `A cos(phi)`，会产生由相位引起的系统性低估。相位扫描显示：`phi=0°` 基本正确，`phi=30°` 约恢复为 `A cos30°`，`phi=60°` 约恢复一半，`phi=90°` 接近恢复不出来。双相锁相通过 `A=2 sqrt(X^2+Y^2)` 可以消除这类未知相位投影误差。

## 6联图目录

- `1kHz`：`six_panel/1kHz/`
- `2kHz`：`six_panel/2kHz/`
- `5kHz`：`six_panel/5kHz/`
- `10kHz`：`six_panel/10kHz/`