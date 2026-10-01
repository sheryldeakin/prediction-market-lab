Split conformal prediction sets: the previous month calibrates the threshold, the current month is scored. Coverage is how often the set contains the truth (should be at least the target); an empty set contains neither class and counts as a miss. Empty sets appear when the target is below about 50%. A single-class set is a call; a two-class set is an abstention.

| minute | target coverage | n | coverage | empty sets | single-class sets | two-class sets | accuracy when a call is made |
|---|---|---|---|---|---|---|---|
| 0 | 90% | 20352 | 90.9% | 0.0% | 21.2% | 78.8% | 56.86% |
| 0 | 80% | 20352 | 80.9% | 0.0% | 42.3% | 57.7% | 54.94% |
| 0 | 70% | 20352 | 70.7% | 0.0% | 63.6% | 36.4% | 53.88% |
| 0 | 60% | 20352 | 60.4% | 0.0% | 84.8% | 15.2% | 53.36% |
| 0 | 50% | 20352 | 49.8% | 5.8% | 94.2% | 0.0% | 52.84% |
| 0 | 40% | 20352 | 39.2% | 26.9% | 73.1% | 0.0% | 53.65% |
| 3 | 90% | 20352 | 90.2% | 0.0% | 41.2% | 58.8% | 76.10% |
| 3 | 80% | 20352 | 80.7% | 0.0% | 67.9% | 32.1% | 71.59% |
| 3 | 70% | 20352 | 70.5% | 0.0% | 91.4% | 8.6% | 67.69% |
| 3 | 60% | 20352 | 60.0% | 12.1% | 87.9% | 0.0% | 68.29% |
| 3 | 50% | 20352 | 49.6% | 30.3% | 69.7% | 0.0% | 71.19% |
| 3 | 40% | 20352 | 39.5% | 46.8% | 53.2% | 0.0% | 74.14% |
