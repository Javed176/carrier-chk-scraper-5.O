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
def render_fmcsa_summary(data: dict):
    """
    Renders a summary card of FMCSA registration details.

    Accepts either:
    - A flat dict as returned by fmcsa_client.resolve_mc_to_usdot()
      (keys: dot_number, legal_name, dba_name, docket_number, physical_address, phone, status, etc.)
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
