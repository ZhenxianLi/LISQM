# 心理声学指标开源实现索引（Psychoacoustic Metrics Index）

这是一个心理声学指标开源实现的索引，覆盖响度、尖锐度、粗糙度、波动强度、音调性、冲击性和心理声学烦恼度，
不限编程语言。每个实现都按它对应的标准版本或模型论文归类，数据每周自动刷新。

**网站：** <https://zhenxianli.github.io/psychoacoustic-metrics-index/>（英文）
**数据：** [`data/index.json`](data/index.json) · [`llms.txt`](llms.txt) · [`llms-full.txt`](llms-full.txt) · [数据格式](data/SCHEMA.md)
**English:** [README.md](README.md)

<!-- BEGIN GENERATED: stats -->
数据截至 2026-10-06：22 个方法，6 个项目，语言包括 C, MATLAB, Python。
<!-- END GENERATED: stats -->

## 为什么要做这个索引

心理声学指标的定义一直在变：ECMA-418-2 自 2020 年以来已经出了四版，ISO 532 的三个部分都在修订。两个都说自己实现了
"ECMA-418-2 粗糙度"的工具，可能对应不同版本，算出来的数也不一样；有的项目在主分支上做了重要修正，但很久才发版。

对每个已知的开源实现，这个索引记录：

- 它对应的**标准版本或模型论文**，以及要调用的函数；
- 项目自己说明的**验证方式**（标准附录数据、参考代码、与其它工具对照、只有自测，或没有说明）；
- **许可证**、最新**发版**、最近**提交**，以及项目是否声明使用了 **AI 辅助**；
- 每条信息的**来源**（README、文档、发版说明、包管理器元数据）。

本仓库不包含任何指标的实现代码。索引只记录各项目自己的说法，不运行代码；被收录不代表被推荐。

## 总览

每个方法的现行版本，以及实现了这一版本的项目（按语言分组）。网站上每个方法都有单独页面，列出完整的版本演变、函数名和验证说明。

<!-- BEGIN GENERATED: overview -->
| 类别 | 方法 | 现行版本 | 已有的开源实现（按语言） |
|---|---|---|---|
| 响度 | [Zwicker 响度（ISO 532-1）](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/loudness-zwicker.html) | ISO 532-1:2017 | Python: [MetaSona](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/metasona.html) (also C), [MoSQITo](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/mosqito.html), [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html), [pySQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/pysqat.html) · MATLAB: [SQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sqat.html) |
| 响度 | [Moore–Glasberg 稳态响度（ISO 532-2）](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/loudness-moore-glasberg.html) | ISO 532-2:2017 | Python: [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html) |
| 响度 | [Moore–Glasberg–Schlittenlacher 时变响度（ISO 532-3）](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/loudness-moore-glasberg-time-varying.html) | ISO 532-3:2023 | Python: [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html) |
| 响度 | [Sottek 听觉模型响度（ECMA-418-2）](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/loudness-ecma-418-2.html) | ECMA-418-2:2025 (4th ed.) | Python: [MetaSona](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/metasona.html) (also C), [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html), [pySQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/pysqat.html), [sottek-hearing-model](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sottek-hearing-model.html) · MATLAB: [SQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sqat.html) (unreleased) · earlier editions: [SQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sqat.html) (ECMA-418-2:2024 (3rd ed.)), [MoSQITo](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/mosqito.html) (ECMA-418-2:2022 (2nd ed.)) |
| 尖锐度 | [尖锐度（DIN 45692）](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/sharpness.html) | DIN 45692:2009 | Python: [MetaSona](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/metasona.html) (also C), [MoSQITo](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/mosqito.html), [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html), [pySQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/pysqat.html) · MATLAB: [SQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sqat.html) |
| 粗糙度 | [粗糙度（Daniel & Weber 模型）](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/roughness-daniel-weber.html) | Daniel & Weber (1997) | Python: [MetaSona](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/metasona.html) (also C), [MoSQITo](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/mosqito.html), [pySQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/pysqat.html) · MATLAB: [SQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sqat.html) |
| 粗糙度 | [Sottek 听觉模型粗糙度（ECMA-418-2）](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/roughness-ecma-418-2.html) | ECMA-418-2:2025 (4th ed.) | Python: [MetaSona](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/metasona.html) (also C), [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html), [pySQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/pysqat.html), [sottek-hearing-model](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sottek-hearing-model.html) · MATLAB: [SQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sqat.html) (unreleased) · earlier editions: [SQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sqat.html) (ECMA-418-2:2024 (3rd ed.)), [MoSQITo](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/mosqito.html) (ECMA-418-2:2022 (2nd ed.)) |
| 粗糙度 | [粗糙度（DIN 38455）](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/roughness-din-38455.html) | DIN 38455:2024 | none found |
| 波动强度 | [波动强度（Osses 模型）](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/fluctuation-strength-osses.html) | Osses et al. (2016) | Python: [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html), [pySQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/pysqat.html) · MATLAB: [SQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sqat.html) · earlier editions: [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html) (Fastl & Zwicker (2007)) |
| 波动强度 | [Sottek 听觉模型波动强度（ECMA-418-2）](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/fluctuation-strength-ecma-418-2.html) | ECMA-418-2:2025 (4th ed.) | Python: [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html), [sottek-hearing-model](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sottek-hearing-model.html) (unreleased) · MATLAB: [SQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sqat.html) (proposed) |
| 音调性 | [音调性（Aures 模型）](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonality-aures.html) | Aures (1985b) | Python: [MetaSona](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/metasona.html) (also C), [pySQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/pysqat.html), [MoSQITo](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/mosqito.html) (proposed) · MATLAB: [SQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sqat.html) |
| 音调性 | [Sottek 听觉模型音调性（ECMA-418-2）](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonality-ecma-418-2.html) | ECMA-418-2:2025 (4th ed.) | Python: [MetaSona](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/metasona.html) (also C), [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html), [pySQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/pysqat.html), [sottek-hearing-model](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sottek-hearing-model.html) · MATLAB: [SQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sqat.html) (unreleased) · earlier editions: [SQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sqat.html) (ECMA-418-2:2024 (3rd ed.)) |
| 音调性 | [音噪比与突出比（ECMA-418-1）](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tone-to-noise-prominence-ratio.html) | ECMA-418-1:2024 (3rd ed.) | Python: [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html) · earlier editions: [MoSQITo](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/mosqito.html) (ECMA-74:2019 (17th ed.)) |
| 音调性 | [音调成分与音调修正（DIN 45681）](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonality-din-45681.html) | DIN 45681:2005 | none found |
| 音调性 | [噪声中音调的可听度（ISO/TS 20065）](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonal-audibility-iso-20065.html) | ISO/TS 20065:2022 | none found · earlier editions: [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html) (ISO/PAS 20065:2016) |
| 音调性 | [环境噪声音调可听度（ISO 1996-2）](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonal-audibility-iso-1996-2.html) | ISO 1996-2:2017 | Python: [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html), [MoSQITo](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/mosqito.html) (proposed) · earlier editions: [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html) (ISO 1996-2:2007) |
| 音调性 | [风电机组音调可听度（IEC 61400-11）](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonal-audibility-iec-61400-11.html) | IEC 61400-11:2012+AMD1:2018 | Python: [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html) |
| 冲击性 | [冲击声显著性（ISO/PAS 1996-3）](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/impulsiveness.html) | ISO/PAS 1996-3:2022 | Python: [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html) · earlier editions: [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html) (NT ACOU 112) |
| 烦恼度 | [心理声学烦恼度](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/psychoacoustic-annoyance.html) | Widmann (1992), Zwicker & Fastl (1999), More (2010), and Di et al. (2016) | Python: [pySQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/pysqat.html), [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html) · MATLAB: [SQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sqat.html), [SQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sqat.html) (unreleased) |
| 相关指标 | [等响曲线（ISO 226）](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/equal-loudness-contours.html) | ISO 226:2023 | Python: [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html) · earlier editions: [MoSQITo](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/mosqito.html) (ISO 226:2003) |
| 相关指标 | [有效感觉噪声级（EPNL）](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/epnl.html) | ICAO Annex 16, Vol. I and 14 CFR Part 36 | Python: [pySQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/pysqat.html), [phonometry](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/phonometry.html) · MATLAB: [SQAT](https://zhenxianli.github.io/psychoacoustic-metrics-index/projects/sqat.html) |
| 相关指标 | [可察觉度](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/aural-detectability.html) | Fidell et al. (1974) | none found |
<!-- END GENERATED: overview -->

### 空白

以下方法的现行版本还没有找到可用的开源实现：

<!-- BEGIN GENERATED: gaps -->
- [粗糙度（DIN 38455）](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/roughness-din-38455.html)
- [音调成分与音调修正（DIN 45681）](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonality-din-45681.html)
- [噪声中音调的可听度（ISO/TS 20065）](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonal-audibility-iso-20065.html)
- [可察觉度](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/aural-detectability.html)
<!-- END GENERATED: gaps -->

### 各语言覆盖情况

每个方法在各语言中是否已有实现。

<!-- BEGIN GENERATED: coverage -->
| 方法 | Python | MATLAB/Octave | C/C++ | Rust | Julia | 其它 |
|---|---|---|---|---|---|---|
| [Zwicker 响度（ISO 532-1）](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/loudness-zwicker.html) | ● | ● | ● | — | — | — |
| [Moore–Glasberg 稳态响度（ISO 532-2）](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/loudness-moore-glasberg.html) | ● | — | — | — | — | — |
| [Moore–Glasberg–Schlittenlacher 时变响度（ISO 532-3）](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/loudness-moore-glasberg-time-varying.html) | ● | — | — | — | — | — |
| [Sottek 听觉模型响度（ECMA-418-2）](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/loudness-ecma-418-2.html) | ● | ○ | ● | — | — | — |
| [尖锐度（DIN 45692）](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/sharpness.html) | ● | ● | ● | — | — | — |
| [粗糙度（Daniel & Weber 模型）](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/roughness-daniel-weber.html) | ● | ● | ● | — | — | — |
| [Sottek 听觉模型粗糙度（ECMA-418-2）](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/roughness-ecma-418-2.html) | ● | ○ | ● | — | — | — |
| [粗糙度（DIN 38455）](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/roughness-din-38455.html) | — | — | — | — | — | — |
| [波动强度（Osses 模型）](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/fluctuation-strength-osses.html) | ● | ● | — | — | — | — |
| [Sottek 听觉模型波动强度（ECMA-418-2）](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/fluctuation-strength-ecma-418-2.html) | ● | ○ | — | — | — | — |
| [音调性（Aures 模型）](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonality-aures.html) | ● | ● | ● | — | — | — |
| [Sottek 听觉模型音调性（ECMA-418-2）](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonality-ecma-418-2.html) | ● | ○ | ● | — | — | — |
| [音噪比与突出比（ECMA-418-1）](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tone-to-noise-prominence-ratio.html) | ● | — | — | — | — | — |
| [音调成分与音调修正（DIN 45681）](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonality-din-45681.html) | — | — | — | — | — | — |
| [噪声中音调的可听度（ISO/TS 20065）](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonal-audibility-iso-20065.html) | ○ | — | — | — | — | — |
| [环境噪声音调可听度（ISO 1996-2）](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonal-audibility-iso-1996-2.html) | ● | — | — | — | — | — |
| [风电机组音调可听度（IEC 61400-11）](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/tonal-audibility-iec-61400-11.html) | ● | — | — | — | — | — |
| [冲击声显著性（ISO/PAS 1996-3）](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/impulsiveness.html) | ● | — | — | — | — | — |
| [心理声学烦恼度](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/psychoacoustic-annoyance.html) | ● | ● | — | — | — | — |
| [等响曲线（ISO 226）](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/equal-loudness-contours.html) | ● | — | — | — | — | — |
| [有效感觉噪声级（EPNL）](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/epnl.html) | ● | ● | — | — | — | — |
| [可察觉度](https://zhenxianli.github.io/psychoacoustic-metrics-index/metrics/aural-detectability.html) | — | — | — | — | — | — |

● 现行版本有可用实现；○ 只有未发布、待合并或旧版本的实现；— 没有找到。含绑定接口：带 Python 接口的 C 库也算 Python。
<!-- END GENERATED: coverage -->

## 项目

<!-- BEGIN GENERATED: projects -->
| 项目 | 语言 | 许可证 | 最新发布 | 最近提交 | 状态 |
|---|---|---|---|---|---|
| [MetaSona](https://github.com/huaaudio/metasona) | Python, C | GPL-3.0-only AND Apache-2.0 AND BSD-3-Clause AND MIT | 0.2.2 (2026-09) | 2026-09-25 | active |
| [MoSQITo](https://github.com/Eomys/MoSQITo) | Python | Apache-2.0 | 1.2.1 (2024-04) | 2024-04-22 | inactive since 2024-04 |
| [phonometry](https://github.com/jmrplens/phonometry) | Python | MIT | 3.3.0 (2026-07) | 2026-10-01 | active |
| [pySQAT](https://github.com/PALILA-TUDelft/pySQAT) | Python | none | no release | 2026-06-27 | active |
| [sottek-hearing-model](https://github.com/mlotinga/sottek-hearing-model) | Python | GPL-3.0-only | 0.1.14 (2026-03) | 2026-09-18 | active |
| [SQAT](https://github.com/ggrecow/SQAT) | MATLAB | GPL-3.0-or-later (main) / CC-BY-NC-4.0 (releases) | v1.3 (2025-04) | 2026-10-02 | active |
<!-- END GENERATED: projects -->

"状态"根据默认分支的最近一次提交计算：超过 365 天没有提交即标为 inactive。

## 维护方式

- **数据**：全部在 [`data/`](data/) 目录里。方法在 `metrics.yaml`，标准版本和模型论文在 `references.yaml`，
  每个项目一个文件放在 `projects/`。格式见 [`data/SCHEMA.md`](data/SCHEMA.md)。
- **生成**：[`scripts/build.py`](scripts/build.py) 校验数据，并生成网站、README 里的表格、`llms.txt`、
  `llms-full.txt` 和 `data/index.json`。
- **每周刷新**：GitHub Action 每周更新各仓库和软件包的元数据（最近提交、发版、PyPI 和 crates.io 版本），在 GitHub
  和包管理器里搜索新的候选项目，并检查 ISO 和 Ecma 是否发布了新版本。结果汇总到一个带 `weekly-review` 标签的
  issue 里，由人工确认后再修改数据。

## 使用数据

- [`data/index.json`](data/index.json)：整个索引（方法、版本、项目、实现）的 JSON。网站上也有同一份文件：
  <https://zhenxianli.github.io/psychoacoustic-metrics-index/index.json>。
- [`llms.txt`](llms.txt) 和 [`llms-full.txt`](llms-full.txt)：给大语言模型和其它工具读的纯文本摘要。网站的每个页面都有
  Markdown 版本（把 `.html` 换成 `.md`）。
- 更新的 Atom 订阅：<https://zhenxianli.github.io/psychoacoustic-metrics-index/feed.xml>。

本地生成网站：

```sh
pip install -r requirements.txt
python scripts/build.py          # 生成 site/，打开 site/index.html
python scripts/build.py --check  # 只校验数据
```

## 参与贡献

欢迎提交新项目、更正信息和标准动态。可以用[模板](https://github.com/ZhenxianLi/psychoacoustic-metrics-index/issues/new/choose)
开 issue，也可以提交 pull request，在 `data/projects/` 里新增或修改文件。详见 [CONTRIBUTING.md](CONTRIBUTING.md)
（英文）。欢迎项目作者核对自己的条目。

## 引用

如果这个索引对你的工作有帮助，请按 [CITATION.cff](CITATION.cff) 引用（GitHub 页面上有 "Cite this repository"
按钮），注明访问日期，并引用你实际使用的实现。

## 许可证

[MIT](LICENSE)，适用于数据、文字和代码。被收录的项目各有自己的许可证，见上面的表格。
