# Orbit ? live deployment copy

This copy is prepared for Streamlit Community Cloud. `main.py` is the entry point. The original backend modules and tests are included. The existing `data/*.json` records are intentionally not included; the app initializes empty data files on first run, so the existing student profile and password hash stay private.

## Publish a live link

1. Create a GitHub repository for this folder. Keep it private if you want the source code private.
2. Upload the files in this folder to the repository.
3. Sign in at https://share.streamlit.io and choose **Create app**. Select your repository, branch, and `main.py`.
4. After it launches, set **Who can view this app** to public if anyone with the URL should be able to open it. Streamlit assigns a `*.streamlit.app` URL.

The app's JSON and uploaded-image storage is local to the running host. Streamlit Community Cloud does not guarantee persistence for local files, so use this live link as a demo and avoid entering real student or sensitive data.
