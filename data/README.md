# Pipeline and Incident Dataset Information

This repository does not commit the raw 493 MB location dataset. Instead, the script `experiments/bsee_records.py` computes the external consistency checks directly from the official public source files, and `results/bsee_records.json` stores the computed summaries along with the cryptographic SHA-256 fingerprints of each input file.

## Data Source

The pipeline location and incident datasets are published by the National Energy Technology Laboratory (NETL) via the Energy Data eXchange (EDX):

- **Dataset**: "U.S. Offshore Pipeline and Reported Incident Datasets"
- **Permanent DOI**: [10.18141/2280823](https://doi.org/10.18141/2280823)
- **Data Article**: Pfander et al., *Data in Brief*, vol. 55, p. 110728, 2024 ([doi:10.1016/j.dib.2024.110728](https://doi.org/10.1016/j.dib.2024.110728))
- **URL**: <https://edx.netl.doe.gov/dataset/us-offshore-pipeline-and-reported-incident-datasets>

## Required Files

To run `experiments/bsee_records.py`, download the following four CSV files from the EDX submission:

1. `pipeline_incidents.csv`
2. `pipeline_locations.csv`
3. `pipeline_incidents_data_dictionary.csv`
4. `pipeline_location_data_dictionary.csv`

Place all four files in a local directory (e.g., `data/netl_pipelines/` or any external folder).

## Expected SHA-256 Hashes (Download of 29 Sep 2026)

| File | SHA-256 Checksum |
|---|---|
| `pipeline_incidents.csv` | `66d3f0f0681dc7a0529c09115cc0404a5d5cbd3e0912e4961665032aa79b35ea` |
| `pipeline_locations.csv` | `1f7b730651f0960727889321c16cb8337707f79bfe1c956e0a3f559e57851c59` |
| `pipeline_incidents_data_dictionary.csv` | `9a8f4b2ccba1cdd930a2a7c687b224ae2ce7399c36cdb685f84a393e0a0f1351` |
| `pipeline_location_data_dictionary.csv` | `ad6d47cb4d8305403c0248f561c4adea131111ae2ef8e97a61850769aabf8d7b` |

## Running Consistency Checks

```bash
python experiments/bsee_records.py --data path/to/netl_files
```

This updates `results/bsee_records.json` and prints the three external consistency checks:
1. **Pipe Size Context**: 24-inch diameter represents a large trunkline (only 1.5% of installed Gulf of Mexico segments are $\ge$ 24 in).
2. **Shock Rate Assessment**: Historical incident frequency is $\le 0.0051$ per segment-year; therefore $\lambda = 0.8$/yr in the degradation model remains an analytical assumption.
3. **Failure Cost Comparison**: The $5M modeled failure cost exceeds 91.7% of historical incident cleanup costs reported in the database.
