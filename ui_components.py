import streamlit as st

def inject_custom_css():
    """Injects custom CSS for iOS 3D Glassmorphism theme with tactile 3D lighting buttons."""
    css = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

        :root {
            --primary-gradient: linear-gradient(135deg, #6366F1 0%, #8B5CF6 50%, #D946EF 100%);
            --glass-bg: rgba(15, 23, 42, 0.65);
            --glass-card-bg: rgba(30, 41, 59, 0.55);
            --glass-border: rgba(255, 255, 255, 0.15);
            --glass-highlight: rgba(255, 255, 255, 0.25);
            --text-main: #F8FAFC;
            --text-muted: #94A3B8;
            --accent-green: #10B981;
            --accent-amber: #F59E0B;
            --accent-red: #EF4444;
            --accent-indigo: #6366F1;
            --accent-purple: #A855F7;
        }

        /* Global Typography & Background */
        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            color: var(--text-main);
        }

        /* iOS Glassmorphism Card Container */
        .glass-card {
            background: var(--glass-card-bg);
            backdrop-filter: blur(20px) saturate(180%);
            -webkit-backdrop-filter: blur(20px) saturate(180%);
            border: 1px solid var(--glass-border);
            border-top: 1px solid var(--glass-highlight);
            border-radius: 20px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.15);
            transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
        }

        .glass-card:hover {
            transform: translateY(-3px) scale(1.005);
            border-color: rgba(255, 255, 255, 0.3);
            box-shadow: 0 30px 60px rgba(99, 102, 241, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.3);
        }

        /* iOS Header Text Gradient */
        .gradient-text {
            background: var(--primary-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-weight: 800;
            letter-spacing: -0.02em;
        }

        /* 3D Tactile Animated Buttons */
        .stButton > button {
            background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 50%, #D946EF 100%) !important;
            border: 1px solid rgba(255, 255, 255, 0.3) !important;
            border-top: 1px solid rgba(255, 255, 255, 0.5) !important;
            border-radius: 14px !important;
            color: #FFFFFF !important;
            font-weight: 700 !important;
            font-size: 0.95rem !important;
            letter-spacing: 0.02em !important;
            padding: 12px 24px !important;
            box-shadow: 0 10px 25px -5px rgba(99, 102, 241, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.4) !important;
            transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
            position: relative !important;
            overflow: hidden !important;
            cursor: pointer !important;
        }

        .stButton > button:hover {
            transform: translateY(-4px) scale(1.02) !important;
            box-shadow: 0 18px 35px -5px rgba(139, 92, 246, 0.65), 0 0 25px rgba(217, 70, 239, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.6) !important;
            border-color: rgba(255, 255, 255, 0.6) !important;
        }

        .stButton > button:active {
            transform: translateY(2px) scale(0.98) !important;
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3), inset 0 2px 4px rgba(0, 0, 0, 0.3) !important;
        }

        /* Secondary/Stop Button Styling */
        div[data-testid="stButton"] > button[kind="secondary"] {
            background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%) !important;
            box-shadow: 0 10px 25px -5px rgba(239, 68, 68, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.4) !important;
        }
        div[data-testid="stButton"] > button[kind="secondary"]:hover {
            box-shadow: 0 18px 35px -5px rgba(239, 68, 68, 0.7), 0 0 25px rgba(239, 68, 68, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.6) !important;
        }

        /* Status Badges */
        .badge {
            display: inline-flex;
            align-items: center;
            padding: 6px 14px;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            backdrop-filter: blur(10px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }

        .badge-active { background-color: rgba(16, 185, 129, 0.15); color: #34D399; border: 1px solid rgba(16, 185, 129, 0.4); }
        .badge-inactive { background-color: rgba(245, 158, 11, 0.15); color: #FBBF24; border: 1px solid rgba(245, 158, 11, 0.4); }
        .badge-revoked { background-color: rgba(239, 68, 68, 0.15); color: #F87171; border: 1px solid rgba(239, 68, 68, 0.4); }
        .badge-gray { background-color: rgba(148, 163, 184, 0.15); color: #CBD5E1; border: 1px solid rgba(148, 163, 184, 0.4); }
        
        .badge-oos {
            background-color: rgba(239, 68, 68, 0.2);
            color: #F87171;
            border: 1px solid rgba(239, 68, 68, 0.5);
            animation: pulse-red 1.8s infinite;
        }

        @keyframes pulse-red {
            0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.5); }
            70% { box-shadow: 0 0 0 8px rgba(239, 68, 68, 0); }
            100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
        }

        /* 3D Glass Data Table */
        .glass-table-container {
            border-radius: 16px;
            overflow: hidden;
            border: 1px solid var(--glass-border);
            border-top: 1px solid var(--glass-highlight);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
            margin-bottom: 24px;
            background: var(--glass-card-bg);
            backdrop-filter: blur(20px);
        }

        .glass-table {
            width: 100%;
            border-collapse: collapse;
            text-align: left;
            font-size: 0.875rem;
        }

        .glass-table th {
            background: rgba(15, 23, 42, 0.85);
            padding: 16px;
            color: #818CF8;
            font-weight: 700;
            font-size: 0.75rem;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            border-bottom: 2px solid var(--glass-border);
        }

        .glass-table td {
            padding: 16px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
            transition: background 0.2s ease;
        }

        .glass-table tr:hover td {
            background: rgba(255, 255, 255, 0.05);
        }

        /* Metric Cards */
        .metric-container {
            text-align: center;
            padding: 18px;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 14px;
            border: 1px solid var(--glass-border);
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.1);
        }
        
        .metric-label { font-size: 0.8rem; color: var(--text-muted); margin-bottom: 4px; font-weight: 500; }
        .metric-value { font-size: 1.6rem; font-weight: 800; color: var(--text-main); font-family: 'JetBrains Mono', monospace; }

        /* Chips */
        .chip {
            display: inline-block;
            padding: 6px 14px;
            margin: 4px;
            background: rgba(99, 102, 241, 0.1);
            border: 1px solid rgba(99, 102, 241, 0.3);
            border-radius: 8px;
            font-size: 0.85rem;
            color: #C7D2FE;
            font-weight: 500;
        }

        .info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
        .info-label { color: var(--text-muted); font-size: 0.85rem; margin-bottom: 2px; }
        .info-value { font-size: 1rem; font-weight: 500; }

        .msg-card {
            padding: 16px;
            border-radius: 14px;
            margin-bottom: 16px;
            border-left: 4px solid;
        }
        .msg-error { background: rgba(239, 68, 68, 0.15); border-left-color: var(--accent-red); color: #FCA5A5; }
        .msg-warning { background: rgba(245, 158, 11, 0.15); border-left-color: var(--accent-amber); color: #FCD34D; }
        .msg-info { background: rgba(99, 102, 241, 0.15); border-left-color: var(--accent-indigo); color: #C7D2FE; }
        .msg-title { font-weight: 700; margin-bottom: 4px; font-size: 1rem; }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def render_header():
    """Renders the iOS glassmorphism app header."""
    html = """
    <div style="text-align: center; padding: 1.5rem 0 2rem 0;">
        <h1 class="gradient-text" style="font-size: 3.2rem; margin-bottom: 0.4rem;">MC Carrier Intelligence</h1>
        <p style="color: #94A3B8; font-size: 1.15rem; font-weight: 400;">Live Carrier & MOTUS Verification Engine</p>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_status_badge(status: str) -> str:
    """Returns HTML for an iOS glass pill badge."""
    if not status:
        return '<span class="badge badge-gray">UNKNOWN</span>'
        
    s = str(status).upper().strip()
    if s in ['ACTIVE', 'AUTHORIZED', 'SATISFACTORY', 'Y']:
        cls = 'badge-active'
        s_text = 'AUTHORIZED' if s == 'Y' else s
    elif s in ['INACTIVE', 'NOT AUTHORIZED', 'N']:
        # Red for inactive / not authorized
        cls = 'badge-revoked'
        s_text = 'NOT AUTHORIZED' if s == 'N' else s
    elif s in ['CONDITIONAL']:
        cls = 'badge-inactive'
        s_text = s
    elif s in ['REVOKED', 'UNSATISFACTORY']:
        cls = 'badge-revoked'
        s_text = s
    elif s == 'OUT OF SERVICE':
        cls = 'badge-oos'
        s_text = s
    else:
        cls = 'badge-gray'
        s_text = s
        
    return f'<span class="badge {cls}">{s_text}</span>'

def render_history_table(history_list: list):
    """Renders all searched carriers in a clean 3D glass data table with exactly 5 columns."""
    if not history_list:
        return

    rows_html = ""
    for item in reversed(history_list):
        comp = item.get('company', {})
        contact = item.get('contact', {})
        
        mc = comp.get('mc_number', 'N/A')
        if not mc or mc == 'None' or mc == 'N/A':
            mc = item.get('searched_mc', 'N/A')
        if mc != 'N/A' and not str(mc).upper().startswith('MC'):
            mc = f"MC-{mc}"
            
        name = comp.get('legal_name', 'Unknown Carrier')
        dba = comp.get('dba_name', '')
        name_display = f"<strong>{name}</strong>"
        if dba:
            name_display += f"<br/><span style='color:#94A3B8; font-size:0.8rem;'>DBA: {dba}</span>"
            
        status = comp.get('operating_status', 'UNKNOWN')
        email = contact.get('email', 'N/A')
        location = contact.get('physical_address', 'N/A')

        badge_html = render_status_badge(status)
        
        rows_html += f"""
        <tr>
            <td style="font-family: 'JetBrains Mono', monospace; font-weight: 700; color: #A5B4FC;">{mc}</td>
            <td>{name_display}</td>
            <td>{badge_html}</td>
            <td>{email}</td>
            <td>{location}</td>
        </tr>
        """

    html = f"""
    <div class="glass-table-container">
        <table class="glass-table">
            <thead>
                <tr>
                    <th>MC NUMBER</th>
                    <th>CARRIER / BROKER NAME</th>
                    <th>OPERATING STATUS</th>
                    <th>EMAIL ADDRESS</th>
                    <th>LOCATION</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_company_card(data: dict):
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
            <h2 style="margin: 0; font-size: 1.6rem;">{name}</h2>
            {render_status_badge(status)}
        </div>
        {f'<div style="color: var(--text-muted); margin-bottom: 16px; font-size: 1.05rem;">DBA: {dba}</div>' if dba else ''}
        
        <div class="info-grid">
            <div>
                <div class="info-label">USDOT Number</div>
                <div class="info-value" style="font-family:\'JetBrains Mono\',monospace; font-weight:600;">{dot}</div>
            </div>
            <div>
                <div class="info-label">MC/FF Number</div>
                <div class="info-value" style="font-family:\'JetBrains Mono\',monospace; font-weight:600;">{mc}</div>
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
        <table style="width:100%; border-collapse: collapse; text-align: left;">
            <thead>
                <tr style="border-bottom: 1px solid var(--glass-border);">
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
    cls = f"msg-{error_type}" if error_type in ['error', 'warning', 'info'] else 'msg-error'
    html = f"""
    <div class="msg-card {cls}">
        <div class="msg-title">{title}</div>
        <div style="font-size: 0.9rem;">{message}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_fmcsa_summary(data: dict):
    """
    Renders a summary card of FMCSA registration details.

    Accepts either:
    - A flat dict as returned by fmcsa_client.resolve_mc_to_usdot()
    - A merged profile dict that contains 'company' and 'contact' sub-dicts.
    """
    if not data:
        return

    # If data has a 'company' sub-dict, we are dealing with merged profile data.
    if 'company' in data:
        comp = data.get('company', {})
        contact = data.get('contact', {})
        legal_name = comp.get('legal_name', comp.get('legalName', 'Unknown'))
        dba_name = comp.get('dba_name', comp.get('dbaName', ''))
        dot_number = comp.get('dot_number', comp.get('dotNumber', 'N/A'))
        mc_number = comp.get('mc_number', comp.get('mcNumber', data.get('searched_mc', 'N/A')))
        status = comp.get('operating_status', comp.get('status', 'Unknown'))
        physical_address = contact.get('physical_address', contact.get('physicalAddress', 'N/A'))
        phone = contact.get('phone', 'N/A')
        email = contact.get('email', 'N/A')
    else:
        # Flat FMCSA data.
        legal_name = data.get('legal_name', 'Unknown')
        dba_name = data.get('dba_name', '')
        dot_number = data.get('dot_number', 'N/A')
        mc_number = data.get('docket_number', data.get('searched_mc', 'N/A'))
        status = data.get('status', 'Unknown')
        physical_address = data.get('physical_address', 'N/A')
        phone = data.get('phone', 'N/A')
        email = data.get('email', 'N/A')

    # Build the HTML card.
    html = f"""
    <div class="glass-card">
        <h3 style="margin-top:0; margin-bottom:16px;">📋 FMCSA Registration Summary</h3>
        <div class="info-grid">
            <div>
                <div class="info-label">Legal Name</div>
                <div class="info-value">{legal_name}</div>
                {f'<div class="info-label" style="margin-top:12px;">DBA Name</div><div class="info-value">{dba_name}</div>' if dba_name else ''}
            </div>
            <div>
                <div class="info-label">USDOT Number</div>
                <div class="info-value" style="font-family:'JetBrains Mono',monospace; font-weight:600;">{dot_number}</div>
                <div class="info-label" style="margin-top:12px;">MC/FF Number</div>
                <div class="info-value" style="font-family:'JetBrains Mono',monospace; font-weight:600;">{mc_number}</div>
            </div>
        </div>
        <div style="display:flex; justify-content:space-between; align-items:center; margin-top:20px;">
            <span class="info-label">Operating Status</span>
            {render_status_badge(status)}
        </div>
        <div class="info-grid" style="margin-top:20px;">
            <div>
                <div class="info-label">📍 Physical Address</div>
                <div class="info-value">{physical_address}</div>
            </div>
            <div>
                <div class="info-label">📞 Phone</div>
                <div class="info-value">{phone}</div>
                {f'<div class="info-label" style="margin-top:12px;">✉️ Email</div><div class="info-value">{email}</div>' if email and email != 'N/A' else ''}
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
