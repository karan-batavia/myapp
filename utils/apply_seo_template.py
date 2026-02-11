import os
import sys

PRERENDER_LOADING_SCREEN = '''
      <div id="dgp-prerender" style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:800px;margin:0 auto;padding:40px 20px;color:#1a1a2e;text-align:center;">
        <div style="margin-bottom:32px;">
          <div style="display:inline-flex;align-items:center;justify-content:center;width:64px;height:64px;background:linear-gradient(135deg,#1a1a2e,#16213e);border-radius:16px;margin-bottom:16px;">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
          </div>
          <h1 style="font-size:28px;font-weight:700;margin:0 0 8px;color:#1a1a2e;">DataGuardian Pro</h1>
          <p style="font-size:16px;color:#64748b;margin:0;">Enterprise Privacy &amp; GDPR Compliance Platform</p>
        </div>
        <div style="margin-bottom:32px;">
          <div style="width:48px;height:48px;border:3px solid #e2e8f0;border-top-color:#1a1a2e;border-radius:50%;margin:0 auto;animation:dgp-spin 0.8s linear infinite;"></div>
          <p style="margin-top:16px;color:#64748b;font-size:14px;">Loading secure environment...</p>
        </div>
        <div style="display:flex;flex-wrap:wrap;justify-content:center;gap:12px;margin-bottom:32px;">
          <span style="background:#f0fdf4;color:#166534;padding:6px 14px;border-radius:20px;font-size:13px;font-weight:500;">GDPR 99 Articles</span>
          <span style="background:#eff6ff;color:#1e40af;padding:6px 14px;border-radius:20px;font-size:13px;font-weight:500;">EU AI Act 113 Articles</span>
          <span style="background:#fef3c7;color:#92400e;padding:6px 14px;border-radius:20px;font-size:13px;font-weight:500;">UAVG 51 Articles</span>
          <span style="background:#f0f9ff;color:#0c4a6e;padding:6px 14px;border-radius:20px;font-size:13px;font-weight:500;">18 AI Scanners</span>
        </div>
        <p style="font-size:13px;color:#94a3b8;margin:0;">Trusted by Dutch &amp; European enterprises &bull; dataguardianpro.nl</p>
      </div>
      <style>@keyframes dgp-spin{to{transform:rotate(360deg)}}</style>
'''

def apply_seo_template():
    try:
        import streamlit
        streamlit_path = list(streamlit.__path__)[0]
        index_path = os.path.join(streamlit_path, 'static', 'index.html')

        if not os.path.exists(index_path):
            return

        with open(index_path, 'r') as f:
            content = f.read()

        if 'dgp-prerender' in content:
            return

        content = content.replace(
            '<title>Streamlit</title>',
            '<title>DataGuardian Pro | Enterprise Privacy & GDPR Compliance Platform</title>\n'
            '\n'
            '    <meta name="description" content="DataGuardian Pro - Enterprise privacy compliance platform for GDPR, EU AI Act 2025 & UAVG. 18 AI-powered scanners for PII detection, data sovereignty, deepfake analysis and more. Trusted by Dutch & European enterprises. Be audit-ready in minutes." />\n'
            '    <meta name="keywords" content="GDPR compliance, EU AI Act 2025, privacy scanner, PII detection, data sovereignty, UAVG, Netherlands compliance, enterprise privacy, data protection, DPIA, deepfake detection, BSN detection, Schrems II" />\n'
            '    <meta name="author" content="DataGuardian Pro B.V." />\n'
            '    <meta name="robots" content="index, follow" />\n'
            '    <link rel="canonical" href="https://dataguardianpro.nl" />\n'
            '\n'
            '    <meta property="og:type" content="website" />\n'
            '    <meta property="og:url" content="https://dataguardianpro.nl" />\n'
            '    <meta property="og:title" content="DataGuardian Pro | Enterprise Privacy & GDPR Compliance Platform" />\n'
            '    <meta property="og:description" content="Achieve 100% EU compliance with 18 AI-powered privacy scanners. GDPR, EU AI Act 2025 & UAVG ready. Be audit-ready in minutes, not months." />\n'
            '    <meta property="og:site_name" content="DataGuardian Pro" />\n'
            '    <meta property="og:locale" content="nl_NL" />\n'
            '    <meta property="og:locale:alternate" content="en_US" />\n'
            '\n'
            '    <meta name="twitter:card" content="summary_large_image" />\n'
            '    <meta name="twitter:title" content="DataGuardian Pro | Enterprise Privacy & GDPR Compliance" />\n'
            '    <meta name="twitter:description" content="18 AI-powered privacy scanners for GDPR, EU AI Act 2025 & UAVG compliance. Trusted by Dutch & European enterprises." />\n'
            '\n'
            '    <script type="application/ld+json">\n'
            '    {\n'
            '      "@context": "https://schema.org",\n'
            '      "@type": "SoftwareApplication",\n'
            '      "name": "DataGuardian Pro",\n'
            '      "url": "https://dataguardianpro.nl",\n'
            '      "description": "Enterprise privacy compliance platform with 18 AI-powered scanners for GDPR, EU AI Act 2025 and UAVG compliance.",\n'
            '      "applicationCategory": "BusinessApplication",\n'
            '      "operatingSystem": "Web",\n'
            '      "offers": {\n'
            '        "@type": "Offer",\n'
            '        "price": "29.99",\n'
            '        "priceCurrency": "EUR"\n'
            '      },\n'
            '      "author": {\n'
            '        "@type": "Organization",\n'
            '        "name": "DataGuardian Pro B.V.",\n'
            '        "url": "https://dataguardianpro.nl",\n'
            '        "address": {\n'
            '          "@type": "PostalAddress",\n'
            '          "addressLocality": "Haarlem",\n'
            '          "addressCountry": "NL"\n'
            '        }\n'
            '      }\n'
            '    }\n'
            '    </script>'
        )

        if '<style id="dgp-preload">' not in content:
            content = content.replace(
                '</head>',
                '    <style id="dgp-preload">\n'
                '      [data-testid="collapsedControl"] span,\n'
                '      [data-testid="stSidebarCollapseButton"] span,\n'
                '      [data-testid="stSidebarCollapsedControl"] span,\n'
                '      button[kind="headerNoPadding"] span,\n'
                '      .stAppDeployButton span,\n'
                '      [data-testid="baseButton-headerNoPadding"] span {\n'
                '        font-size: 0 !important;\n'
                '        color: transparent !important;\n'
                '        overflow: hidden !important;\n'
                '        width: 0 !important;\n'
                '        display: inline-block !important;\n'
                '      }\n'
                '    </style>\n'
                '    </head>'
            )

        content = content.replace(
            '<noscript>You need to enable JavaScript to run this app.</noscript>',
            '<noscript>\n'
            '      <h1>DataGuardian Pro - Enterprise Privacy & GDPR Compliance Platform</h1>\n'
            '      <p>DataGuardian Pro helps organizations achieve 100% EU compliance with 18 AI-powered privacy scanners covering GDPR (99 articles), EU AI Act 2025 (113 articles), and Dutch UAVG (51 articles).</p>\n'
            '      <p>Features include PII detection, data sovereignty scanning for AWS/Azure/GCP, deepfake detection, DPIA assessments, and enterprise connectors for Microsoft 365 and Google Workspace.</p>\n'
            '      <p>Trusted by Dutch and European enterprises. Be audit-ready in minutes, not months.</p>\n'
            '      <p>Contact us: <a href="mailto:info@dataguardianpro.nl">info@dataguardianpro.nl</a> | Visit: <a href="https://dataguardianpro.nl">dataguardianpro.nl</a></p>\n'
            '    </noscript>'
        )

        content = content.replace(
            '<div id="root"></div>',
            '<div id="root">' + PRERENDER_LOADING_SCREEN + '</div>'
        )

        with open(index_path, 'w') as f:
            f.write(content)

        print("SEO template with pre-render loading screen applied successfully", file=sys.stderr)

    except Exception as e:
        print(f"SEO template application skipped: {e}", file=sys.stderr)

if __name__ == '__main__':
    apply_seo_template()
