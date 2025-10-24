from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
import io, os, json, zipfile, tempfile, pickle, matplotlib
matplotlib.use("Agg")  # headless plots
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
import toad
from toad.plot import bin_plot
import uvicorn  # Keep this import for running the app

app = FastAPI(title="Binning + WOE API", version="1.0")

# allow browser apps like Lovable to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"]
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/process")
async def process(
    data: UploadFile = File(...),
    target: str = Form(...),
    method: str = Form("chi"),
    min_samples_on: bool = Form(True),
    min_samples_value: float = Form(0.05),
    exclude: str = Form(""),
    test_size: float = Form(0.2),
    random_state: int = Form(42),
    plot_feature: str = Form("")
):
    # read CSV
    content = await data.read()
    df = pd.read_csv(io.BytesIO(content))

    if target not in df.columns:
        return JSONResponse(status_code=400, content={"error": f"target '{target}' not in columns"})

    # exclude list
    exclude_list = []
    if exclude.strip():
        try:
            exclude_list = json.loads(exclude)
            if not isinstance(exclude_list, list):
                raise ValueError
        except Exception:
            exclude_list = [c.strip() for c in exclude.split(",") if c.strip()]
    if target not in exclude_list:
        exclude_list.append(target)

    # split
    train, test = train_test_split(df, test_size=test_size, random_state=random_state)

    # set min_samples
    min_samples = min_samples_value if min_samples_on else None

    # fit combiner
    combiner = toad.transform.Combiner()
    combiner.fit(
        X=train,
        y=train[target],
        method=method,
        min_samples=min_samples,
        exclude=exclude_list
    )

    # transform train
    train_selected_bin = combiner.transform(train)

    # align test
    shared_cols = train_selected_bin.columns.tolist()
    test_aligned = test[[c for c in shared_cols if c in test.columns]].copy()
    for c in shared_cols:
        if c not in test_aligned.columns:
            test_aligned[c] = np.nan
    test_bin = combiner.transform(test_aligned)

    # plotting
    tmpdir = tempfile.mkdtemp()
    plot_files = []
    try:
        if plot_feature and plot_feature in train_selected_bin.columns:
            try:
                bin_plot(train_selected_bin, x=plot_feature, target=target)
                train_plot_path = os.path.join(tmpdir, f"bin_plot_train_{plot_feature}.png")
                plt.savefig(train_plot_path, bbox_inches="tight")
                plt.close()
                plot_files.append(train_plot_path)
            except Exception:
                pass
            try:
                bin_plot(test_bin, x=plot_feature, target=target)
                test_plot_path = os.path.join(tmpdir, f"bin_plot_test_{plot_feature}.png")
                plt.savefig(test_plot_path, bbox_inches="tight")
                plt.close()
                plot_files.append(test_plot_path)
            except Exception:
                pass

        # WOE transform
        woe = toad.transform.WOETransformer()
        train_woe = woe.fit_transform(
            X=train_selected_bin,
            y=train_selected_bin[target],
            exclude=exclude_list
        )
        test_woe = woe.transform(test_bin)

        # save CSVs
        out_train_bin = os.path.join(tmpdir, "train_selected_bin.csv")
        out_test_bin = os.path.join(tmpdir, "test_bin.csv")
        out_train_woe = os.path.join(tmpdir, "train_woe.csv")
        out_test_woe = os.path.join(tmpdir, "test_woe.csv")

        train_selected_bin.to_csv(out_train_bin, index=False)
        test_bin.to_csv(out_test_bin, index=False)
        train_woe.to_csv(out_train_woe, index=False)
        test_woe.to_csv(out_test_woe, index=False)

        # pickle artifacts
        combiner_path = os.path.join(tmpdir, "combiner.pkl")
        woe_path = os.path.join(tmpdir, "woe.pkl")
        with open(combiner_path, "wb") as f:
            pickle.dump(combiner, f)
        with open(woe_path, "wb") as f:
            pickle.dump(woe, f)

        # zip results
        zip_path = os.path.join(tmpdir, "outputs.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
            for fpath in [out_train_bin, out_test_bin, out_train_woe, out_test_woe, combiner_path, woe_path]:
                z.write(fpath, arcname=os.path.basename(fpath))
            for p in plot_files:
                z.write(p, arcname=os.path.basename(p))

        return FileResponse(zip_path, filename="outputs.zip", media_type="application/zip")
    finally:
        # Clean up temporary directory and files
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)

# Start Uvicorn when run as a module
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))  # Use Railway's PORT or fallback to 8000
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, log_level="info")
