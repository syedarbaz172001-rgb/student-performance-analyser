# Student Performance Analyser

Student Performance Analyser helps teachers understand class performance through clear score, attendance, and grade insights. It includes a Python desktop dashboard and an installable, cross-platform mobile web app.

## Run

From this folder, run:

```powershell
python student_performance_app.py
```

The app opens with the sample dataset at `data/students.csv` when that file is present. Use **Open CSV** to load another dataset, **Add student** to enter a record, **Save CSV** to keep your data, or **Export report** to save a text summary. The app can also start with no sample data, which is suitable for a public download.

## Mobile app

The `mobile_app` folder contains the Student Performance Analyser Progressive Web App (PWA) for Android and iPhone, with a responsive dashboard, a book-and-growth-chart logo, and a guided start screen. It starts without bundled student records; users can add records manually or download a CSV template to fill in and import. Imported and manually entered data is saved in that browser's local storage and is not uploaded to a shared database. To preview it from this folder, start Python's local web server:

```powershell
python -m http.server 8000
```

Open `http://localhost:8000/mobile_app/` on the computer, or use the computer's local network address on a phone connected to the same Wi-Fi. The mobile app supports student search, class filtering, CSV import, manual student entry, charts, and report export. Data stays in the user's browser; the site has no shared database. The desktop app's data stays in memory until the user saves it with **Save CSV**.

For home-screen installation and offline support, serve the app from an HTTPS address. On Android, use the browser's **Install app** option. On iPhone, open the app in Safari, tap **Share**, then **Add to Home Screen**.

CSV files must include these columns: `Student ID`, `Name`, `Gender`, `Class`, `Maths`, `Science`, `English`, `History`, `Attendance`, and `AssignmentScore`. Scores and attendance must be numbers from 0 to 100.

## Publish for everyone

To make the web app public, publish the contents of `mobile_app` to any HTTPS static-site host. No server or database is required for visitor-entered data. The GitHub Actions workflows in `.github/workflows` can publish it to GitHub Pages and create a Windows desktop download when a `v*` tag is pushed. For GitHub Pages, enable **Settings → Pages → Build and deployment → GitHub Actions**, then push to the `main` branch. The website URL appears in the Pages settings and deployment workflow. To create a desktop release, push a version tag such as `v1.0.0`; the generated release will contain `StudentPerformanceAnalyser.exe`.

Do not publish real student records. `.gitignore` excludes CSV files under `data/` and generated reports; the public mobile site starts empty, and the desktop release is built without bundling the local dataset. Each website visitor's imported or manually entered records remain in that visitor's browser and are not sent to a shared database.
