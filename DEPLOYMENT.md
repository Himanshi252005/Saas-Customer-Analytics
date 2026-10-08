# Publish SaaS Pulse

## 1. Confirm the repository locally

From the project root:

```bash
python -m pip install -r requirements-dev.txt
python -m src.generate_data
python -m src.etl
python -m src.eda
python -m pytest -q
streamlit run app.py
```

Commit the included `data/` CSVs and `reports/` files. The cloud app reads the committed processed CSV, so its first launch does not need to run ETL or access an external database.

## 2. Push to your GitHub account

The target public repository is [Himanshi252005/Saas-Customer-Analytics](https://github.com/Himanshi252005/Saas-Customer-Analytics). From this directory, if you are publishing a fresh copy manually:

```bash
git init
git add .
git commit -m "Build SaaS churn and revenue analytics portfolio"
git branch -M main
git remote add origin https://github.com/Himanshi252005/Saas-Customer-Analytics.git
git push -u origin main
```

If GitHub asks you to sign in, use its normal browser or credential-manager flow; never place a password or token in this repository. If the repository has already been published, clone it and push your edits to its default branch instead of reinitializing it.

Suggested repository description: **Synthetic SaaS customer churn and revenue analytics with reproducible Python ETL, DuckDB SQL, tests, and an interactive Streamlit dashboard.**

## 3. Deploy on Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io/) and sign in with GitHub.
2. Connect or authorize access to the public repository. You need admin access to the repository.
3. Select **Create app**, choose the GitHub repository and `main` branch, and set the entrypoint file to **`app.py`**.
4. Choose a supported Python version compatible with `requirements.txt` (prefer Python 3.12 if offered), then deploy. The dependency file lives at the repository root.
5. Open the resulting `*.streamlit.app` URL. Check that all four tabs load, change a sidebar filter, and download the CSV. Copy the verified URL into the README and your GitHub repository's website field.

The app uses no secrets. It reads only committed local CSV and SQL files. Pushing updates to the connected branch causes Community Cloud to update the app.

If deployment fails, inspect the app's build or runtime logs. The usual checks are that `requirements.txt`, `app.py`, the `data/processed/` CSV, and `sql/` files were pushed, and that the configured Python version is supported by the dependencies.

Official references: [deploy an app](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy), [app dependencies](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies), [file organization](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/file-organization), [connect GitHub](https://docs.streamlit.io/deploy/streamlit-community-cloud/get-started/connect-your-github-account).
