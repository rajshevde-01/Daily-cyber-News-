import os
import sys
import re
import datetime
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

def get_template_post(article: dict) -> str:
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
    elif any(k in content_lower for k in ["cve", "vulnerability", "zero-day", "flaw", "exploit", "patch"]):
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
    
    post_content = f"""# 🚨 {title}

**Source**: {source}
**Link**: {link}
**Date**: {date_str}
**Category**: {category}

## 📰 Summary of the Threat
{summary}

This vulnerability or active incident represents a significant risk vector. Organizations must review their exposure and verify that mitigating controls are functional.

## 🛠️ Actionable Defense & Mitigation Checklist
{defense_str}

## 🧠 Career & Skills Upgrade (How to do better in the Security Field)
{career_advice}

---
*Disclaimer: This post was automatically generated to track daily security events and share defensive insights.*
"""
    return post_content

def call_groq_llm(article: dict) -> str:
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

def main():
    article = fetch_latest_news()
    if not article:
        sys.exit(1)
        
    # Try LLM generation first
    post_content = call_groq_llm(article)
    
    # Fall back to template-based generation if LLM failed/disabled
    if not post_content:
        print("[INFO] Generating post using template fallback...")
        post_content = get_template_post(article)
        
    # Save the output file
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    os.makedirs("news", exist_ok=True)
    filename = f"news/{today_str}-news.md"
    
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(post_content)
        print(f"[SUCCESS] News post written to: {filename}")
    except Exception as e:
        print(f"[ERROR] Failed to write news file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
