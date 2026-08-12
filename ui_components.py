import streamlit as st

def inject_custom_css():
    """Injects custom CSS for a premium, glassmorphism UI design."""
    css = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

        :root {
            --primary-gradient: linear-gradient(135deg, #6366F1, #A855F7);
            --card-bg: rgba(30, 41, 59, 0.6);
            --card-border: rgba(255, 255, 255, 0.1);
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent-green: #10b981;
            --accent-amber: #f59e0b;
            --accent-red: #ef4444;
            --accent-blue: #3b82f6;
        }

        /* Global Font Settings */
        html, body, [class*="css"]  {
            font-family: 'Inter', sans-serif;
            color: var(--text-main);
        }

        h1, h2, h3, h4, h5, h6 {
            font-weight: 600;
        }

        /* Glassmorphism Cards */
        .glass-card {
            background: var(--card-bg);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 24px;
            transition: all 0.3s ease;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        }

        .glass-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
            border-color: rgba(255, 255, 255, 0.2);
        }

        /* Gradients */
        .gradient-text {
            background: var(--primary-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            display: inline-block;
        }

        /* Badges */
        .badge {
            display: inline-flex;
            align-items: center;
            padding: 4px 12px;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .badge-active { background-color: rgba(16, 185, 129, 0.1); color: var(--accent-green); border: 1px solid rgba(16, 185, 129, 0.2); }
        .badge-inactive { background-color: rgba(245, 158, 11, 0.1); color: var(--accent-amber); border: 1px solid rgba(245, 158, 11, 0.2); }
        .badge-revoked { background-color: rgba(239, 68, 68, 0.1); color: var(--accent-red); border: 1px solid rgba(239, 68, 68, 0.2); }
        .badge-gray { background-color: rgba(148, 163, 184, 0.1); color: var(--text-muted); border: 1px solid rgba(148, 163, 184, 0.2); }
        
        .badge-oos {
            background-color: rgba(239, 68, 68, 0.1);
            color: var(--accent-red);
            border: 1px solid rgba(239, 68, 68, 0.2);
            animation: pulse-red 2s infinite;
        }

        @keyframes pulse-red {
            0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); }
            70% { box-shadow: 0 0 0 6px rgba(239, 68, 68, 0); }
            100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
        }

        /* Metrics */
        .metric-container {
            text-align: center;
            padding: 16px;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 12px;
            border: 1px solid var(--card-border);
        }
        
        .metric-label {
            font-size: 0.875rem;
            color: var(--text-muted);
            margin-bottom: 4px;
        }

        .metric-value {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--text-main);
            font-family: 'JetBrains Mono', monospace;
        }

        /* Chips / Tags */
        .chip {
            display: inline-block;
            padding: 4px 12px;
            margin: 4px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--card-border);
            border-radius: 6px;
            font-size: 0.875rem;
            color: var(--text-main);
        }

        /* Tables/Grid Layouts for info */
        .info-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
        }
        
        .info-label {
            color: var(--text-muted);
            font-size: 0.875rem;
            margin-bottom: 2px;
        }

        .info-value {
            font-size: 1rem;
            font-weight: 500;
        }

        /* Loading Spinner */
        .spinner-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 40px;
        }

        .lds-ellipsis {
            display: inline-block;
            position: relative;
            width: 80px;
            height: 80px;
        }
        .lds-ellipsis div {
            position: absolute;
            top: 33px;
            width: 13px;
            height: 13px;
            border-radius: 50%;
            background: #a855f7;
            animation-timing-function: cubic-bezier(0, 1, 1, 0);
        }
        .lds-ellipsis div:nth-child(1) { left: 8px; animation: lds-ellipsis1 0.6s infinite; }
        .lds-ellipsis div:nth-child(2) { left: 8px; animation: lds-ellipsis2 0.6s infinite; }
        .lds-ellipsis div:nth-child(3) { left: 32px; animation: lds-ellipsis2 0.6s infinite; }
        .lds-ellipsis div:nth-child(4) { left: 56px; animation: lds-ellipsis3 0.6s infinite; }

        @keyframes lds-ellipsis1 {
            0% { transform: scale(0); }
            100% { transform: scale(1); }
        }
        @keyframes lds-ellipsis3 {
            0% { transform: scale(1); }
            100% { transform: scale(0); }
        }
        @keyframes lds-ellipsis2 {
            0% { transform: translate(0, 0); }
            100% { transform: translate(24px, 0); }
        }

        /* Messages / Alerts */
        .msg-card {
            padding: 16px;
            border-radius: 12px;
            margin-bottom: 16px;
            border-left: 4px solid;
            display: flex;
            flex-direction: column;
        }
        .msg-error { background: rgba(239, 68, 68, 0.1); border-left-color: var(--accent-red); color: #fca5a5; }
        .msg-warning { background: rgba(245, 158, 11, 0.1); border-left-color: var(--accent-amber); color: #fcd34d; }
        .msg-info { background: rgba(59, 130, 246, 0.1); border-left-color: var(--accent-blue); color: #93c5fd; }
        .msg-title { font-weight: 600; margin-bottom: 4px; font-size: 1.05rem; }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def render_header():
    """Renders the main app header."""
    html = """
    <div style="text-align: center; padding-bottom: 2rem;">
        <h1 class="gradient-text" style="font-size: 3rem; margin-bottom: 0.5rem;">MC Lookup Pro</h1>
        <p style="color: var(--text-muted); font-size: 1.1rem;">Advanced Carrier Identity & Safety Intelligence</p>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_status_badge(status: str) -> str:
    """Returns HTML for a status badge based on text."""
    if not status:
        return '<span class="badge badge-gray">UNKNOWN</span>'
        
    s = str(status).upper().strip()
    if s in ['ACTIVE', 'AUTHORIZED', 'SATISFACTORY']:
        cls = 'badge-active'
    elif s in ['INACTIVE', 'NOT AUTHORIZED', 'CONDITIONAL']:
        cls = 'badge-inactive'
    elif s in ['REVOKED', 'UNSATISFACTORY']:
        cls = 'badge-revoked'
    elif s == 'OUT OF SERVICE':
        cls = 'badge-oos'
    else:
        cls = 'badge-gray'
        
    return f'<span class="badge {cls}">{s}</span>'

def render_fmcsa_summary(data: dict):
    """Quick summary from the FMCSA primary endpoint."""
    if not data:
        return
        
    name = data.get('legal_name', 'Unknown')
    dba = data.get('dba_name', '')
    dot = data.get('dot_number', 'N/A')
    mc = data.get('mc_number', data.get('docket_number', 'N/A'))
    status = data.get('status', 'Unknown')
    
    html = f"""
    <div class="glass-card">
        <h3 style="margin-top:0; color: var(--text-muted); font-size:0.875rem; text-transform:uppercase;">Quick Summary</h3>
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 16px;">
            <div>
                <h2 style="margin:0; font-size: 1.5rem;">{name}</h2>
                {f'<div style="color: var(--text-muted); margin-bottom: 8px;">DBA: {dba}</div>' if dba else ''}
                <div style="display:flex; gap: 16px; margin-top:8px;">
                    <div><span class="info-label">USDOT:</span> <span class="info-value" style="font-family:'JetBrains Mono',monospace">{dot}</span></div>
                    <div><span class="info-label">MC:</span> <span class="info-value" style="font-family:'JetBrains Mono',monospace">{mc}</span></div>
                </div>
            </div>
            <div>
                {render_status_badge(status)}
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_company_card(data: dict):
    """Detailed company identity card."""
    if not data:
        return

    name = data.get('legal_name', data.get('legalName', 'Unknown'))
    dba = data.get('dba_name', data.get('dbaName', ''))
    dot = data.get('dot_number', data.get('dotNumber', 'N/A'))
    mc = data.get('mc_number', data.get('mcNumber', 'N/A'))
    ent_type = data.get('entity_type', data.get('entityType', 'Unknown'))
    op_class = data.get('operation_classification', data.get('operatingClassification', 'Unknown'))
    status = data.get('operating_status', data.get('status', 'Unknown'))

    html = f"""
    <div class="glass-card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
            <h2 style="margin: 0;">{name}</h2>
            {render_status_badge(status)}
        </div>
        {f'<div style="color: var(--text-muted); margin-bottom: 16px; font-size: 1.1rem;">DBA: {dba}</div>' if dba else ''}
        
        <div class="info-grid">
            <div>
                <div class="info-label">USDOT Number</div>
                <div class="info-value" style="font-family:'JetBrains Mono',monospace">{dot}</div>
            </div>
            <div>
                <div class="info-label">MC/FF Number</div>
                <div class="info-value" style="font-family:'JetBrains Mono',monospace">{mc}</div>
            </div>
            <div>
                <div class="info-label">Entity Type</div>
                <div class="info-value">{ent_type}</div>
            </div>
            <div>
                <div class="info-label">Operating Classification</div>
                <div class="info-value">{op_class}</div>
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_contact_section(data: dict):
    """Contact information section."""
    if not data:
        return

    phy_addr = data.get('physical_address', data.get('physicalAddress', 'N/A'))
    mail_addr = data.get('mailing_address', data.get('mailingAddress', ''))
    phone = data.get('phone', 'N/A')
    email = data.get('email', 'N/A')

    html = f"""
    <div class="glass-card">
        <h3 style="margin-top:0; margin-bottom:16px;">Contact Information</h3>
        <div class="info-grid">
            <div>
                <div class="info-label">📍 Physical Address</div>
                <div class="info-value">{phy_addr}</div>
                {f'<div class="info-label" style="margin-top:12px;">📮 Mailing Address</div><div class="info-value">{mail_addr}</div>' if mail_addr and mail_addr != phy_addr else ''}
            </div>
            <div>
                <div class="info-label">📞 Phone</div>
                <div class="info-value">{phone}</div>
                <div class="info-label" style="margin-top:12px;">✉️ Email</div>
                <div class="info-value">{email}</div>
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_operations_section(data: dict):
    """Operations metrics and cargo types."""
    if not data:
        return
        
    power_units = data.get('power_units', data.get('powerUnits', '0'))
    drivers = data.get('drivers', '0')
    cargo = data.get('cargo_types', data.get('cargoTypes', []))

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">Power Units</div>
            <div class="metric-value">{power_units}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">Drivers</div>
            <div class="metric-value">{drivers}</div>
        </div>
        """, unsafe_allow_html=True)

    if cargo:
        cargo_html = "".join([f'<span class="chip">{c}</span>' for c in cargo])
        st.markdown(f"""
        <div class="glass-card" style="margin-top: 16px;">
            <h3 style="margin-top:0; font-size:1rem; margin-bottom:12px;">Cargo Authorized</h3>
            <div>{cargo_html}</div>
        </div>
        """, unsafe_allow_html=True)

def render_safety_section(data: dict):
    """Safety and inspection metrics."""
    if not data:
        return

    rating = data.get('safety_rating', data.get('safetyRating', 'None'))
    inspections = data.get('total_inspections', data.get('totalInspections', '0'))
    veh_oos = data.get('vehicle_oos_pct', data.get('vehicleOosRate', '0%'))
    drv_oos = data.get('driver_oos_pct', data.get('driverOosRate', '0%'))
    crashes = data.get('total_crashes', data.get('totalCrashes', '0'))
    fatal = data.get('fatal_crashes', data.get('fatalCrashes', '0'))

    html = f"""
    <div class="glass-card">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
            <h3 style="margin:0;">Safety Rating</h3>
            {render_status_badge(rating)}
        </div>
        
        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 12px; margin-bottom: 20px;">
            <div class="metric-container">
                <div class="metric-label">Total Inspections</div>
                <div class="metric-value">{inspections}</div>
            </div>
            <div class="metric-container">
                <div class="metric-label">Vehicle OOS</div>
                <div class="metric-value">{veh_oos}</div>
            </div>
            <div class="metric-container">
                <div class="metric-label">Driver OOS</div>
                <div class="metric-value">{drv_oos}</div>
            </div>
        </div>

        <div style="display:flex; gap:20px;">
            <div>
                <span class="info-label">Total Crashes:</span>
                <span class="info-value">{crashes}</span>
            </div>
            <div>
                <span class="info-label" style="color:var(--accent-red)">Fatal Crashes:</span>
                <span class="info-value">{fatal}</span>
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_insurance_section(data: dict):
    """Insurance and authority status."""
    if not data:
        return

    bipd_req = data.get('bipd_required', data.get('bipdRequired', '$0'))
    bipd_file = data.get('bipd_on_file', data.get('bipdOnFile', '$0'))
    cargo_req = data.get('cargo_required', data.get('cargoRequired', 'No'))
    cargo_file = data.get('cargo_on_file', data.get('cargoOnFile', 'No'))
    bond_req = data.get('bond_required', data.get('bondRequired', 'No'))
    bond_file = data.get('bond_on_file', data.get('bondOnFile', 'No'))

    html = f"""
    <div class="glass-card">
        <h3 style="margin-top:0; margin-bottom:20px;">Insurance Coverage</h3>
        <table style="width:100%; border-collapse: collapse; margin-bottom: 24px; text-align: left;">
            <thead>
                <tr style="border-bottom: 1px solid var(--card-border);">
                    <th style="padding: 8px 4px; color:var(--text-muted); font-weight:500;">Type</th>
                    <th style="padding: 8px 4px; color:var(--text-muted); font-weight:500;">Required</th>
                    <th style="padding: 8px 4px; color:var(--text-muted); font-weight:500;">On File</th>
                </tr>
            </thead>
            <tbody>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                    <td style="padding: 12px 4px;">BIPD</td>
                    <td style="padding: 12px 4px;">{bipd_req}</td>
                    <td style="padding: 12px 4px;">{bipd_file}</td>
                </tr>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                    <td style="padding: 12px 4px;">Cargo</td>
                    <td style="padding: 12px 4px;">{cargo_req}</td>
                    <td style="padding: 12px 4px;">{cargo_file}</td>
                </tr>
                <tr>
                    <td style="padding: 12px 4px;">Bond</td>
                    <td style="padding: 12px 4px;">{bond_req}</td>
                    <td style="padding: 12px 4px;">{bond_file}</td>
                </tr>
            </tbody>
        </table>

    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_authority_section(data: dict):
    """Operating authority status section."""
    if not data:
        return

    common = data.get('common_authority', data.get('commonAuthority', 'N/A'))
    contract = data.get('contract_authority', data.get('contractAuthority', 'N/A'))
    broker = data.get('broker_authority', data.get('brokerAuthority', 'N/A'))

    html = f"""
    <div class="glass-card">
        <h3 style="margin-top:0; margin-bottom:20px;">Operating Authority</h3>
        <div style="display:flex; flex-direction:column; gap: 16px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span class="info-label">Common Authority</span>
                {render_status_badge(common)}
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span class="info-label">Contract Authority</span>
                {render_status_badge(contract)}
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span class="info-label">Broker Authority</span>
                {render_status_badge(broker)}
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_error_card(title: str, message: str, error_type: str = 'error'):
    """Styled error/warning message."""
    cls = f"msg-{error_type}" if error_type in ['error', 'warning', 'info'] else 'msg-error'
    
    html = f"""
    <div class="msg-card {cls}">
        <div class="msg-title">{title}</div>
        <div style="font-size: 0.9rem;">{message}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_loading_animation(message: str = 'Fetching carrier data...'):
    """Custom loading spinner."""
    html = f"""
    <div class="spinner-container">
        <div class="lds-ellipsis"><div></div><div></div><div></div><div></div></div>
        <div style="color: var(--text-muted); margin-top: 16px; font-weight: 500;">{message}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
