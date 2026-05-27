# A6 — Cost & Operational Overhead Tables

Both tables extracted from `discussion.tex` of the EMSE manuscript. Tokens
are model-specific BPE (Qwen3 tokenizer for Qwen models, Llama-3.1
tokenizer for Nemotron). Wall-clock duration measured on RunPod H100 SXM;
monetary cost at \$2.69 / GPU-hr. n = 868 samples per configuration.

> **Caveat on cost / duration**: `cost_usd = duration_hours × gpu_count × $2.69`,
> where `duration_hours` is the sum of CodeCarbon session durations attributed
> to each cell. Configurations executed across more sessions (e.g., due to pod
> restarts) accumulate more setup/idle overhead and so show larger
> duration/cost even at identical per-sample token counts. Close per-cell
> cost comparisons across designs at matched model + mode + prompting reflect
> this experimental-execution basis as well as intrinsic compute work. The
> supplementary CSV (`cost_analysis_870_bpe.csv`) now carries a `num_sessions`
> column so this can be inspected directly.

## Table 1 — Cost–performance summary by design × mode (8 cells)

Duration / energy / cost are totals across the 8 configs in each cell
(4 models × 2 prompting). Avg Tok./Sample is per-sample mean (input,
output). Total Tok. shown in millions.

| Design | Mode    | Dur. (h) | kWh   | Avg In | Avg Out | Tot. In (M) | Tot. Out (M) | Cost (\$) |
|--------|---------|---------:|------:|-------:|--------:|------------:|-------------:|----------:|
| NA     | Inst.   | 44.0     | 19.2  | 220    | 1,096   | 1.5         | 7.6          | 133       |
| NA     | Think   | 132.9    | 68.5  | 220    | 3,483   | 1.5         | 24.2         | 438       |
| SA     | Inst.   | 25.4     | 17.6  | 220    | 1,099   | 1.5         | 7.6          | 83        |
| SA     | Think   | 102.7    | 76.7  | 220    | 3,482   | 1.5         | 24.2         | 357       |
| DA     | Inst.   | 38.3     | 24.9  | 4,182  | 1,287   | 29.0        | 8.9          | 127       |
| DA     | Think   | 145.9    | 85.4  | 6,515  | 4,598   | 45.2        | 31.9         | 466       |
| MA     | Inst.   | 76.2     | 61.4  | 4,580  | 2,879   | 31.8        | 20.0         | 261       |
| MA     | Think   | 256.1    | 184.9 | 16,670 | 7,935   | 115.7       | 55.1         | 879       |
| **Total** |       | **821**  | **539** |       |         | **227.9**   | **179.5**    | **2,745** |

## Table 2 — Per-configuration cost breakdown (64 configs)

Mode: I = Instruct, T = Thinking.  Prom.: F = Few-shot, Z = Zero-shot.
Avg In/Out are per-sample averages; Tot. is total tokens in millions
(input + output combined).

| Design | Model      | Mode | Prom. | Dur. (h) | kWh  | Avg In | Avg Out | Tot. (M) | Cost (\$) |
|--------|------------|------|-------|---------:|-----:|-------:|--------:|---------:|----------:|
| NA     | Nano-8B    | I    | F     | 2.6      | 1.4  | 370    | 1,066   | 1.2      | 6.9       |
| NA     | Nano-8B    | I    | Z     | 1.6      | 0.8  | 71     | 602     | 0.6      | 4.2       |
| NA     | Nano-8B    | T    | F     | 3.3      | 1.8  | 370    | 1,523   | 1.6      | 9.0       |
| NA     | Nano-8B    | T    | Z     | 2.1      | 1.1  | 71     | 746     | 0.7      | 5.8       |
| NA     | Super-49B  | I    | F     | 2.6      | 3.1  | 370    | 582     | 0.8      | 14.1      |
| NA     | Super-49B  | I    | Z     | 2.9      | 3.4  | 71     | 656     | 0.6      | 15.8      |
| NA     | Super-49B  | T    | F     | 13.5     | 15.8 | 370    | 2,886   | 2.8      | 72.4      |
| NA     | Super-49B  | T    | Z     | 16.4     | 19.2 | 71     | 3,517   | 3.1      | 88.1      |
| NA     | 4B         | I    | F     | 3.8      | 1.4  | 370    | 1,311   | 1.5      | 10.3      |
| NA     | 4B         | I    | Z     | 5.0      | 1.8  | 69     | 1,491   | 1.4      | 13.4      |
| NA     | 4B         | T    | F     | 16.6     | 6.3  | 370    | 5,115   | 4.8      | 44.5      |
| NA     | 4B         | T    | Z     | 16.2     | 5.6  | 69     | 5,299   | 4.7      | 43.5      |
| NA     | 30B        | I    | F     | 12.1     | 3.4  | 370    | 1,429   | 1.6      | 32.6      |
| NA     | 30B        | I    | Z     | 13.4     | 3.8  | 69     | 1,631   | 1.5      | 36.1      |
| NA     | 30B        | T    | F     | 29.8     | 8.5  | 370    | 4,007   | 3.8      | 80.2      |
| NA     | 30B        | T    | Z     | 35.1     | 10.2 | 69     | 4,768   | 4.2      | 94.4      |
| SA     | Nano-8B    | I    | F     | 1.6      | 1.1  | 370    | 1,017   | 1.2      | 4.4       |
| SA     | Nano-8B    | I    | Z     | 1.4      | 1.1  | 71     | 789     | 0.7      | 3.8       |
| SA     | Nano-8B    | T    | F     | 2.4      | 2.0  | 370    | 1,497   | 1.6      | 6.5       |
| SA     | Nano-8B    | T    | Z     | 1.3      | 1.0  | 71     | 734     | 0.7      | 3.5       |
| SA     | Super-49B  | I    | F     | 2.5      | 3.5  | 370    | 576     | 0.8      | 13.6      |
| SA     | Super-49B  | I    | Z     | 2.9      | 4.0  | 71     | 654     | 0.6      | 15.4      |
| SA     | Super-49B  | T    | F     | 13.9     | 19.0 | 370    | 2,990   | 2.9      | 74.7      |
| SA     | Super-49B  | T    | Z     | 16.3     | 22.8 | 71     | 3,497   | 3.1      | 87.8      |
| SA     | 4B         | I    | F     | 2.3      | 1.5  | 370    | 1,226   | 1.4      | 6.3       |
| SA     | 4B         | I    | Z     | 1.8      | 1.4  | 69     | 1,678   | 1.5      | 4.8       |
| SA     | 4B         | T    | F     | 14.1     | 7.8  | 370    | 5,082   | 4.7      | 37.8      |
| SA     | 4B         | T    | Z     | 17.0     | 8.0  | 69     | 5,398   | 4.7      | 45.6      |
| SA     | 30B        | I    | F     | 6.9      | 2.7  | 370    | 1,503   | 1.6      | 18.6      |
| SA     | 30B        | I    | Z     | 5.9      | 2.3  | 69     | 1,351   | 1.2      | 15.9      |
| SA     | 30B        | T    | F     | 19.5     | 8.7  | 370    | 4,152   | 3.9      | 52.4      |
| SA     | 30B        | T    | Z     | 18.2     | 7.3  | 69     | 4,504   | 4.0      | 49.1      |
| DA     | Nano-8B    | I    | F     | 2.6      | 1.3  | 4,498  | 1,052   | 4.8      | 7.1       |
| DA     | Nano-8B    | I    | Z     | 6.8      | 3.5  | 4,093  | 1,211   | 4.6      | 18.2      |
| DA     | Nano-8B    | T    | F     | 5.4      | 2.7  | 4,782  | 1,391   | 5.4      | 14.6      |
| DA     | Nano-8B    | T    | Z     | 4.2      | 2.1  | 4,063  | 1,237   | 4.6      | 11.2      |
| DA     | Super-49B  | I    | F     | 4.5      | 6.1  | 4,491  | 1,272   | 5.0      | 24.2      |
| DA     | Super-49B  | I    | Z     | 4.5      | 6.1  | 3,845  | 1,415   | 4.6      | 24.1      |
| DA     | Super-49B  | T    | F     | 13.0     | 17.8 | 5,392  | 3,674   | 7.9      | 70.1      |
| DA     | Super-49B  | T    | Z     | 14.5     | 20.1 | 4,752  | 3,784   | 7.4      | 77.9      |
| DA     | 4B         | I    | F     | 2.6      | 1.2  | 4,243  | 1,136   | 4.7      | 6.9       |
| DA     | 4B         | I    | Z     | 3.5      | 2.0  | 3,495  | 871     | 3.8      | 9.3       |
| DA     | 4B         | T    | F     | 19.7     | 9.3  | 8,521  | 6,411   | 13.0     | 52.9      |
| DA     | 4B         | T    | Z     | 22.3     | 10.8 | 8,348  | 7,320   | 13.6     | 60.0      |
| DA     | 30B        | I    | F     | 8.1      | 2.6  | 4,953  | 2,132   | 6.1      | 21.7      |
| DA     | 30B        | I    | Z     | 5.8      | 2.1  | 3,839  | 1,205   | 4.4      | 15.5      |
| DA     | 30B        | T    | F     | 31.2     | 10.7 | 7,990  | 5,963   | 12.1     | 84.1      |
| DA     | 30B        | T    | Z     | 35.6     | 11.9 | 8,272  | 7,004   | 13.3     | 95.7      |
| MA     | Nano-8B    | I    | F     | 11.0     | 8.8  | 6,423  | 3,834   | 8.9      | 29.5      |
| MA     | Nano-8B    | I    | Z     | 18.3     | 14.4 | 7,942  | 6,292   | 12.3     | 49.1      |
| MA     | Nano-8B    | T    | F     | 23.6     | 17.5 | 11,313 | 6,306   | 15.3     | 63.4      |
| MA     | Nano-8B    | T    | Z     | 27.9     | 20.5 | 12,179 | 7,830   | 17.4     | 74.9      |
| MA     | Super-49B  | I    | F     | 9.6      | 13.0 | 4,041  | 2,200   | 5.4      | 51.7      |
| MA     | Super-49B  | I    | Z     | 11.1     | 15.1 | 3,790  | 2,646   | 5.6      | 59.8      |
| MA     | Super-49B  | T    | F     | 29.0     | 39.2 | 11,077 | 5,215   | 14.1     | 156.2     |
| MA     | Super-49B  | T    | Z     | 41.6     | 56.5 | 13,888 | 6,679   | 17.9     | 223.9     |
| MA     | 4B         | I    | F     | 3.4      | 1.6  | 2,866  | 1,347   | 3.7      | 9.3       |
| MA     | 4B         | I    | Z     | 5.4      | 2.7  | 4,715  | 2,704   | 6.4      | 14.5      |
| MA     | 4B         | T    | F     | 24.0     | 10.9 | 21,397 | 9,278   | 26.6     | 64.6      |
| MA     | 4B         | T    | Z     | 25.1     | 11.6 | 23,781 | 10,387  | 29.7     | 67.6      |
| MA     | 30B        | I    | F     | 7.8      | 2.6  | 2,593  | 1,607   | 3.6      | 21.0      |
| MA     | 30B        | I    | Z     | 9.6      | 3.1  | 4,272  | 2,400   | 5.8      | 25.8      |
| MA     | 30B        | T    | F     | 41.4     | 13.9 | 19,410 | 8,534   | 24.3     | 111.4     |
| MA     | 30B        | T    | Z     | 43.5     | 14.8 | 20,319 | 9,254   | 25.7     | 116.9     |
