def generate_vulnerability_report(vulnerabilities):
    if not vulnerabilities:
        return "✅ No vulnerabilities found!"
    
    report = ["🚨 **Vulnerability Report** 🚨", ""]
    report.append(f"📊 Total vulnerabilities found: {len(vulnerabilities)}")
    report.append("----------------------------------")
    
    vuln_types = {}
    for vuln in vulnerabilities:
        vuln_types[vuln["type"]] = vuln_types.get(vuln["type"], 0) + 1
    
    report.append("📋 **Vulnerability Types:**")
    for vuln_type, count in vuln_types.items():
        report.append(f"- {vuln_type}: {count} instances")
    
    report.append("\n🔍 **Detailed Findings:**")
    for i, vuln in enumerate(vulnerabilities, 1):
        report.append(f"\n{i}. **{vuln['type']}**")
        report.append(f"   🔗 URL: {vuln['url']}")
        report.append(f"   📌 Parameter: `{vuln['param']}`")
        report.append(f"   💣 Payload: `{vuln['payload']}`")
        report.append(f"   📄 Evidence: `{vuln['evidence']}`")
    
    return "\n".join(report)