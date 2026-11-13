# Materials and battery formulas

Read only when a calculation needs one of these. Write each as an expression for the
`calculate` tool. The constant `F` (Faraday, 96485 C/mol) is built in.

| Quantity | Formula | Example expression |
|---|---|---|
| Longest absorbed wavelength (nm) | 1239.84 / band gap (eV) | `1239.84/3.4` (GaN) |
| Photon energy (eV) | 1239.84 / wavelength (nm) | `1239.84/365` |
| Capacity retention (%) | remaining / initial × 100 | `412/487*100` |
| Average fade per cycle (%) | (100 − retention) / cycles | `(100-84.6)/500` |
| Fold change (how many times) | a / b | `2.4/1.1` |
| Percentage change (%) | (new − old) / old × 100 | `(2.4-1.9)/1.9*100` |
| Specific capacity (mAh/g) | capacity (mAh) / active mass (g) | `3.2/0.019` |
| Theoretical capacity (mAh/g) | n × F / (3.6 × M), M in g/mol | `1*F/(3.6*157.76)` (LiFePO4) |
| Energy (Wh) | capacity (Ah) × nominal voltage (V) | `2.5*3.7` |
| Current for a C-rate (A) | C-rate × capacity (Ah) | `0.5*2.5` |
| Pressure | 1 MPa = 10 bar ≈ 145 psi | `1*145.04` |

Report units explicitly and round the final answer to the precision of the inputs.
