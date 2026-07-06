import os
import sys
import re
import datetime
import json
import feedparser
import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Fix console encoding for Windows to handle Unicode icons correctly
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Configured RSS feeds for authentic cybersecurity news
RSS_FEEDS = [
    {"url": "https://www.bleepingcomputer.com/feed/", "name": "BleepingComputer"},
    {"url": "https://feeds.feedburner.com/TheHackersNews", "name": "The Hacker News"},
    {"url": "https://www.darkreading.com/rss.xml", "name": "Dark Reading"},
    {"url": "https://www.cisa.gov/uscert/ncas/current-activity.xml", "name": "CISA Alert/Activity"}
]

def clean_html(text: str) -> str:
    """Removes HTML tags and cleans up whitespace."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def search_github_poc(cve_id: str) -> list:
    """Searches GitHub for public PoC repositories of a specific CVE."""
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"
        
    url = f"https://api.github.com/search/repositories?q={cve_id}&sort=stars&order=desc"
    pocs = []
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            items = response.json().get("items", [])
            for item in items[:2]: # Get top 2
                pocs.append({
                    "name": item.get("full_name"),
                    "url": item.get("html_url"),
                    "description": item.get("description") or "No description provided.",
                    "stars": item.get("stargazers_count")
                })
            print(f"[SUCCESS] Found {len(pocs)} public PoCs for {cve_id} on GitHub")
        else:
            print(f"[WARN] GitHub search status code: {response.status_code}")
    except Exception as e:
        print(f"[WARN] Error searching GitHub for PoCs: {e}")
    return pocs

def fetch_latest_news() -> dict:
    """Fetches the latest article across all configured RSS feeds."""
    all_articles = []
    print("[INFO] Fetching news from RSS feeds...")
    
    for feed_info in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_info["url"])
            for entry in feed.entries[:5]: # look at recent 5 entries
                title = entry.get("title", "").strip()
                link = entry.get("link", "").strip()
                summary = clean_html(entry.get("summary", entry.get("description", "")))
                
                # Truncate summary if too long
                if len(summary) > 400:
                    summary = summary[:400] + "..."
                
                if title and link:
                    all_articles.append({
                        "title": title,
                        "link": link,
                        "summary": summary,
                        "source": feed_info["name"]
                    })
        except Exception as e:
            print(f"[WARN] Failed to fetch {feed_info['name']}: {e}")
            
    if not all_articles:
        print("[ERROR] No articles could be fetched.")
        return None
        
    # Default to the very first article fetched (latest)
    print(f"[SUCCESS] Fetched {len(all_articles)} articles.")
    return all_articles[0]

def get_template_post(article: dict, cve_id: str = None, pocs: list = None) -> str:
    """Fallback generator using static templates based on article contents."""
    title = article["title"]
    summary = article["summary"]
    link = article["link"]
    source = article["source"]
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    
    content_lower = (title + " " + summary).lower()
    
    # Choose defense & career advice templates based on keywords
    if any(k in content_lower for k in ["ransomware", "ransom", "extortion", "encrypt"]):
        category = "Ransomware & Malware Defense"
        defense_steps = [
            "Disable exposed remote access endpoints (like RDP) or secure them behind a strict Zero-Trust VPN/boundary.",
            "Enforce Multi-Factor Authentication (MFA) across all administrative and user portals without exceptions.",
            "Establish an offline, immutable backup infrastructure and verify restoration workflows weekly.",
            "Deploy Endpoint Detection and Response (EDR) agents to actively monitor and block unauthorized volume shadow copy deletion or mass file encryption."
        ]
        career_advice = (
            "**Skills to Practice:** Study ransomware loaders and practice writing YARA rules to detect common tools like Cobalt Strike or Silver. "
            "Learn to analyze Windows Event Logs for Event ID 1102 (audit log cleared) or Event ID 4624 (successful login type 10 for RDP).\n\n"
            "**Labs to Build:** Set up a virtualized Active Directory forest in a closed sandbox. Use tools like PingCastle or BloodHound to audit it, "
            "identify misconfigurations, and learn how ransomware groups perform internal reconnaissance and privilege escalation."
        )
    elif any(k in content_lower for k in ["cve", "vulnerability", "zero-day", "flaw", "exploit", "patch"]) or cve_id:
        category = "Vulnerability Management & Exploitation"
        defense_steps = [
            "Perform an asset discovery scan to map out all servers running the affected software version.",
            "Apply the official vendor patch immediately. If a patch is unavailable, restrict inbound network access to the affected service.",
            "Apply virtual patching signatures on your Web Application Firewall (WAF) or IPS/IDS systems.",
            "Search centralized logs (SIEM) for exploit payload signatures or anomalous connection requests targeted at the service path."
        ]
        career_advice = (
            "**Skills to Practice:** Learn to write basic Proof of Concept (PoC) exploit scripts in Python to understand vulnerability mechanics "
            "at the packet/HTTP request level. Study security advisories from CISA, CVE, and NIST.\n\n"
            "**Labs to Build:** Set up a Docker container running a legacy, vulnerable version of software. Run vulnerability scanners "
            "like Nuclei or OpenVAS against it to see how they detect the flaw, and use Wireshark to capture and analyze the exploit traffic."
        )
    elif any(k in content_lower for k in ["phish", "social engineer", "credential", "email", "spoof"]):
        category = "Social Engineering & Identity Security"
        defense_steps = [
            "Enforce FIDO2/WebAuthn-based hardware security keys to immunize your organization against adversary-in-the-middle (AiTM) phishing.",
            "Enable strict email authentication records, including SPF, DKIM, and DMARC (with 'reject' policy) to prevent domain spoofing.",
            "Deploy modern email security gateways (SEGs) with link-rewriting and attachment sandboxing features.",
            "Train employees to verify high-risk out-of-band requests (like wiring funds or changing MFA devices) via trusted secondary channels."
        ]
        career_advice = (
            "**Skills to Practice:** Master parsing raw MIME email headers. Practice identifying email routing paths, SPF/DKIM alignment failures, "
            "and analyzing obfuscated links or macro-enabled attachments in a safe, isolated analysis environment.\n\n"
            "**Labs to Build:** Set up a private virtual lab and deploy open-source phishing simulation frameworks like GoPhish. "
            "Additionally, study how tools like Evilginx capture session tokens to understand how to design compensating session-revocation controls."
        )
    elif any(k in content_lower for k in ["cloud", "aws", "azure", "gcp", "s3", "kubernetes", "k8s"]):
        category = "Cloud & Infrastructure Security"
        defense_steps = [
            "Audit all cloud storage buckets and databases to ensure public access is explicitly blocked unless strictly required.",
            "Enforce the Principle of Least Privilege (PoLP) on IAM policies, removing wildcard ('*') permissions.",
            "Enable cloud provider control plane logs (e.g., AWS CloudTrail) and ingest them into a SIEM for anomaly detection.",
            "Scan infrastructure-as-code (IaC) templates (Terraform, CloudFormation) for misconfigurations before deployment."
        ]
        career_advice = (
            "**Skills to Practice:** Get hands-on experience with cloud security posture management (CSPM) concepts. Learn to query cloud configuration "
            "metadata using APIs/CLIs, and study the top threat vectors in the OWASP Kubernetes Top 10.\n\n"
            "**Labs to Build:** Set up a free-tier AWS or Azure account. Build a simple deployment containing an intentionally misconfigured IAM policy. "
            "Use open-source auditing tools like Pacu, Prowler, or Scout Suite to scan and discover the flaws, then practice remediating them."
        )
    else:
        category = "General Cyber Security & Hardening"
        defense_steps = [
            "Implement network segmentation to separate critical internal business databases from general user zones.",
            "Ensure centralized logging is active for all endpoint, firewall, and authentication events.",
            "Establish a regular patch schedule for all operating systems, hypervisors, and core applications.",
            "Maintain a documented Incident Response plan and run bi-annual tabletop simulations with key stakeholders."
        ]
        career_advice = (
            "**Skills to Practice:** Learn to read and parse raw system logs using basic command-line tools like grep, awk, sed, and jq. "
            "Familiarize yourself with the MITRE ATT&CK framework to map real-world adversary techniques to enterprise log sources.\n\n"
            "**Labs to Build:** Install Wazuh (open-source HIDS/SIEM) or an Elastic Stack on a local virtual machine. "
            "Configure it to ingest logs from your main desktop, trigger a test alert, and write a detection rule to catch it."
        )
        
    defense_str = "\n".join([f"- [ ] **Step {i+1}**: {step}" for i, step in enumerate(defense_steps)])
    
    poc_section = ""
    if cve_id and pocs:
        poc_list = "\n".join([f"- **[{p['name']}]({p['url']})** (⭐ {p['stars']}): {p['description']}" for p in pocs])
        poc_section = f"""

## 🎯 Public Exploit PoC Alert
We detected active public Proof-of-Concept exploits for **{cve_id}** on GitHub:
{poc_list}"""
    
    post_content = f"""# 🚨 {title}

**Source**: {source}
**Link**: {link}
**Date**: {date_str}
**Category**: {category}

## 📰 Summary of the Threat
{summary}

This vulnerability or active incident represents a significant risk vector. Organizations must review their exposure and verify that mitigating controls are functional.{poc_section}

## 🛠️ Actionable Defense & Mitigation Checklist
{defense_str}

## 🧠 Career & Skills Upgrade (How to do better in the Security Field)
{career_advice}

---
*Disclaimer: This post was automatically generated to track daily security events and share defensive insights.*
"""
    return post_content

def call_groq_llm(article: dict, cve_id: str = None, pocs: list = None) -> str:
    """Uses Groq API to generate a highly detailed and custom cybersecurity news/career post."""
    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key:
        print("[INFO] GROQ_API_KEY not found. Falling back to template mode.")
        return None
        
    try:
        from groq import Groq
    except ImportError:
        print("[WARN] groq library not installed. Falling back to template mode.")
        return None
        
    title = article["title"]
    summary = article["summary"]
    link = article["link"]
    source = article["source"]
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    
    prompt = f"""You are a Lead Cybersecurity Architect and expert technical writer.
Analyze this cybersecurity news story:
Title: {title}
Source: {source}
Link: {link}
Summary: {summary}

Generate a detailed, markdown-formatted daily report. The report MUST follow this exact structure:

# 🚨 {title}
**Source**: {source}
**Link**: {link}
**Date**: {date_str}

## 📰 Summary of the Threat
Provide a deep, 2-3 paragraph summary explaining what the threat is, who is targeted, and the technical mechanism of the vulnerability or attack. Keep the tone professional, technical, and direct.
"""

    if cve_id and pocs:
        poc_list_str = "\n".join([f"- {p['name']} ({p['url']}) with {p['stars']} stars. Description: {p['description']}" for p in pocs])
        prompt += f"""
CRITICAL CVE INFO:
We detected {cve_id} in this story. The following public PoC exploits are available on GitHub:
{poc_list_str}

You MUST include a dedicated '## 🎯 Public Exploit PoC Alert' section in your response right below the summary, listing these repositories and warning readers about active exploit tools.
"""

    prompt += """
## 🛠️ Actionable Defense & Mitigation Checklist
Provide 3-5 highly technical, concrete, and specific steps that security teams, developers, or system administrators can take to defend against or remediate this specific threat. Do not use generic advice like "be vigilant". Use specific controls, configuration actions, or auditing methods.

## 🧠 Career & Skills Upgrade (How to do better in the Security Field)
Provide concrete skill-building exercises and home lab projects that a security professional (e.g. SOC analyst, pentester, security engineer) can do to master the concepts behind this threat. Give step-by-step guidance on what tools to practice or what to build in a home lab.

Do not include any chat preamble, closing remarks, or metadata blocks. Return ONLY the markdown content.
"""
    try:
        print("[INFO] Requesting AI-enriched content from Groq (Llama-3.3-70b-versatile)...")
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[WARN] Groq API call failed: {e}. Falling back to template mode.")
        return None

def update_readme_with_alert(article: dict, date_str: str):
    """Updates the repository README.md between marker comments with latest news info."""
    readme_path = "README.md"
    if not os.path.exists(readme_path):
        print("[WARN] README.md not found. Skipping auto-update.")
        return
        
    try:
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        start_marker = "<!-- CYBER_ALERT_START -->"
        end_marker = "<!-- CYBER_ALERT_END -->"
        
        start_idx = content.find(start_marker)
        end_idx = content.find(end_marker)
        
        if start_idx == -1 or end_idx == -1:
            print("[INFO] Cyber Alert markers not found in README.md. Skipping auto-update.")
            return
            
        # Format the alert markdown
        alert_content = f"""{start_marker}
> [!WARNING]
> **Latest Cybersecurity Alert ({date_str}):**
> **[{article['title']}]({article['link']})** (Source: *{article['source']}*)
>
> A detailed breakdown, including security engineering mitigation steps and career skill-building exercises, has been posted in [news/{date_str}-news.md](news/{date_str}-news.md). Check the [Threat Intel Dashboard](index.html) for interactive updates!
{end_marker}"""
          
        new_content = content[:start_idx] + alert_content + content[end_idx + len(end_marker):]
        
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("[SUCCESS] Successfully updated README.md with latest alert.")
    except Exception as e:
        print(f"[ERROR] Failed to update README.md: {e}")

def update_news_json(article: dict, post_content: str, date_str: str, pocs: list):
    """Updates news_data.json with the latest entry, keeping up to 15 entries."""
    json_path = "news_data.json"
    entries = []
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                entries = json.load(f)
        except Exception:
            entries = []
            
    # Extract Category if present in post_content
    category = "General Cyber Security"
    cat_match = re.search(r"\*\*Category\*\*:\s*([^\n]+)", post_content)
    if cat_match:
        category = cat_match.group(1).strip()
    
    # Create new entry
    new_entry = {
        "title": article["title"],
        "source": article["source"],
        "link": article["link"],
        "date": date_str,
        "category": category,
        "content": post_content,
        "pocs": pocs
    }
    
    # Avoid duplicates by date
    entries = [e for e in entries if e["date"] != date_str]
    entries.insert(0, new_entry)
    
    # Keep up to 15 entries
    entries = entries[:15]
    
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2, ensure_ascii=False)
        print(f"[SUCCESS] Updated news_data.json with {len(entries)} entries")
    except Exception as e:
        print(f"[ERROR] Failed to write news_data.json: {e}")

def clean_for_linkedin(text: str) -> str:
    """Removes standard markdown symbols to make it readable on LinkedIn."""
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1 (\2)", text)
    text = re.sub(r"^#+\s+(.*?)$", r"\1", text, flags=re.MULTILINE)
    text = text.replace("`", "")
    return text.strip()

def post_to_linkedin(article: dict, category: str):
    """Publishes a summary of the cybersecurity threat to LinkedIn, directing users to the dashboard."""
    token = os.environ.get("LINKEDIN_ACCESS_TOKEN", "").strip()
    person_urn = os.environ.get("LINKEDIN_PERSON_URN", "").strip()
    
    if not token or not person_urn:
        print("[INFO] LinkedIn credentials (LINKEDIN_ACCESS_TOKEN or LINKEDIN_PERSON_URN) not found. Skipping LinkedIn cross-post.")
        return
        
    print("[INFO] Publishing alert update to LinkedIn...")
    title = article["title"]
    summary = article["summary"]
    source = article["source"]
    
    linkedin_text = f"""🚨 LATEST CYBERSECURITY ALERT: {title}

Category: {category}
Source: {source}

📰 Quick Brief:
{clean_for_linkedin(summary)}

🛡️ Practical mitigations, CVE details, and hands-on skill-building labs to master this threat are available on my Threat Intel Dashboard:
🔗 https://rajshevde-01.github.io/Daily-cyber-News-/

#Cybersecurity #ThreatIntel #SecurityEngineering #ActiveDefense"""

    url = "https://api.linkedin.com/rest/posts"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "LinkedIn-Version": "202601",
        "X-Restli-Protocol-Version": "2.0.0",
    }
    
    payload = {
        "author": person_urn,
        "commentary": linkedin_text,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        if response.status_code == 201:
            post_id = response.headers.get("x-restli-id", "unknown")
            print(f"[SUCCESS] Post successfully published to LinkedIn! ID: {post_id}")
        else:
            print(f"[WARN] Failed to post to LinkedIn. Status: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"[WARN] Error publishing to LinkedIn: {e}")

def main():
    article = fetch_latest_news()
    if not article:
        sys.exit(1)
        
    title = article["title"]
    summary = article["summary"]
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    
    # Check for CVE
    cves = re.findall(r"CVE-\d{4}-\d{4,}", title + " " + summary)
    pocs = []
    cve_id = None
    if cves:
        cve_id = list(set(cves))[0] # unique CVE
        print(f"[INFO] Detected CVE: {cve_id}. Searching GitHub for public PoC exploits...")
        pocs = search_github_poc(cve_id)
        
    # Try LLM generation first
    post_content = call_groq_llm(article, cve_id, pocs)
    
    # Fall back to template-based generation if LLM failed/disabled
    if not post_content:
        print("[INFO] Generating post using template fallback...")
        post_content = get_template_post(article, cve_id, pocs)
        
    # Save the output file
    os.makedirs("news", exist_ok=True)
    filename = f"news/{date_str}-news.md"
    
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(post_content)
        print(f"[SUCCESS] News post written to: {filename}")
    except Exception as e:
        print(f"[ERROR] Failed to write news file: {e}")
        sys.exit(1)
        
    # Update local README.md alert section
    update_readme_with_alert(article, date_str)
    
    # Update news_data.json
    update_news_json(article, post_content, date_str, pocs)
    
    # Cross-post to LinkedIn
    category = "General Cyber Security"
    cat_match = re.search(r"\*\*Category\*\*:\s*([^\n]+)", post_content)
    if cat_match:
        category = cat_match.group(1).strip()
    post_to_linkedin(article, category)

if __name__ == "__main__":
    main()
