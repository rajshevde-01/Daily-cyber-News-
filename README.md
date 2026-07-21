# 🛡️ Automated Daily Cybersecurity News Committer

A fully automated, zero-maintenance system that fetches real-world cybersecurity news every day, writes detailed summaries, crafts actionable defense checklists, lists skill-building/career-improvement ideas, and commits them to your GitHub repository.

By running under your Git identity, this system automatically maintains your GitHub contribution graph ("green squares") daily.

<!-- CYBER_ALERT_START -->
> [!WARNING]
> **Latest Cybersecurity Alert (2026-07-21):**
> **[Critical Palo Alto VPN bug now exploited by Qilin ransomware gang](https://www.bleepingcomputer.com/news/security/critical-globalprotect-vpn-bug-now-exploited-in-ransomware-attacks/)** (Source: *BleepingComputer*)
>
> A detailed breakdown, including security engineering mitigation steps and career skill-building exercises, has been posted in [news/2026-07-21-news.md](news/2026-07-21-news.md). Check the [Threat Intel Dashboard](index.html) for interactive updates!
<!-- CYBER_ALERT_END -->

## 🚀 How It Works
1. **Fetch**: A Python script runs daily inside GitHub Actions. It scans top-tier cybersecurity RSS feeds (CISA Alerts, BleepingComputer, The Hacker News, Dark Reading) for authentic, live stories.
2. **Generate**: The script compiles the latest story. If you configure a Groq API key, it generates highly custom technical breakdowns and tailored cybersecurity career exercises. Otherwise, it falls back to built-in keyword-mapped templates (for Ransomware, Cloud, Credential/Phishing, CVEs, etc.) requiring zero API keys.
3. **Commit & Push**: GitHub Actions commits the generated markdown file to the `news/` folder using your name (`rajshevde-01`) and email (`rajshevde009@gmail.com`), updating your GitHub activity chart.

---

## ⚙️ Initial Setup

### 1. Initialize Git & Publish to GitHub
If this directory is not yet pushed to GitHub, run these commands in your terminal:
```bash
git init
git add .
git commit -m "Initial commit: Daily cybersecurity news automation"
git branch -M main
# Add your GitHub repository URL:
git remote add origin https://github.com/rajshevde-01/<your-repo-name>.git
git push -u origin main
```

### 2. Configure GitHub Permissions (Required)
By default, GitHub Actions workflows have read-only access to repositories. Since this workflow needs to commit news files, ensure your repository permissions allow it:
1. Go to your repository on GitHub.
2. Navigate to **Settings** > **Actions** > **General**.
3. Scroll down to **Workflow permissions**.
4. Select **Read and write permissions**.
5. Click **Save**.

### 3. Add Groq API Key (Optional but Recommended)
For high-quality, custom career-upgrade advice and technical checklists:
1. Go to your repository on GitHub.
2. Navigate to **Settings** > **Secrets and variables** > **Actions**.
3. Click **New repository secret**.
4. Set the **Name** to `GROQ_API_KEY`.
5. Set the **Value** to your Groq API Key (e.g. `gsk_...`).
6. Click **Add secret**.

*Note: If no API key is provided, the script automatically uses smart templates to ensure it always succeeds and updates your activity graph.*

---

## 🧪 Local Testing
You can run the generator locally to check the output before pushing:
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the script:
   ```bash
   python scripts/generate_daily_post.py
   ```
3. Check the `news/` folder for the newly generated daily update!
