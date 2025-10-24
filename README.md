# Binning + WOE API

## Run locally
python -m venv .venv && . .venv/Scripts/activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload

Open http://127.0.0.1:8000/docs to test.

## Deploy
- Railway: New Project → Deploy from GitHub. Use Procfile.
- Render: New Web Service → Autodetects Dockerfile.

## Use
POST /process (multipart/form-data)
- data: CSV file
- target: label column
- method: dt|chi|quantile|step|kmeans
- min_samples_on: true|false
- min_samples_value: 0.05
- exclude: JSON array or comma list
- test_size: 0.2
- random_state: 42
- plot_feature: column for bin_plot

Returns: outputs.zip with binned/WOE CSVs, plots, and pickled transformers.
# toad
