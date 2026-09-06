import re

with open('public/index.html', 'r') as f:
    html = f.read()

# Add checkboxes and push button to the profile HTML generator
old_form_row2 = """            <div class="form-row">
                <div class="form-group">
                    <label>Delivery Rate Threshold (%)</label>
                    <input type="number" step="0.1" id="rate_${index}" value="${p.delivery_rate_threshold_percent || 85}" required>
                </div>
                <div class="form-group">
                    <label>Pending Msgs Threshold</label>
                    <input type="number" id="pend_${index}" value="${p.pending_messages_threshold || 1000}" required>
                </div>
                <div class="form-group">
                    <label>Pending Msgs Duration (Secs)</label>
                    <input type="number" id="dur_${index}" value="${p.pending_messages_duration_seconds || 60}" required>
                </div>
            </div>"""

new_form_row2 = """            <div class="form-row">
                <div class="form-group">
                    <label>Delivery Rate Threshold (%)</label>
                    <input type="number" step="0.1" id="rate_${index}" value="${p.delivery_rate_threshold_percent || 85}" required>
                </div>
                <div class="form-group">
                    <label>Pending Msgs Threshold</label>
                    <input type="number" id="pend_${index}" value="${p.pending_messages_threshold || 1000}" required>
                </div>
                <div class="form-group">
                    <label>Pending Msgs Duration (Secs)</label>
                    <input type="number" id="dur_${index}" value="${p.pending_messages_duration_seconds || 60}" required>
                </div>
            </div>
            
            <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #eee;">
                <strong>Channels for this Profile:</strong>
                <div style="display: flex; gap: 20px; margin-top: 10px; align-items: center;">
                    <label style="display: flex; align-items: center; gap: 5px; font-weight: normal; cursor: pointer;">
                        <input type="checkbox" id="sms_${index}" ${p.enable_sms !== false ? 'checked' : ''}> Send SMS
                    </label>
                    <label style="display: flex; align-items: center; gap: 5px; font-weight: normal; cursor: pointer;">
                        <input type="checkbox" id="push_${index}" ${p.enable_push !== false ? 'checked' : ''}> Send Web Push
                    </label>
                    <div style="flex: 1;"></div>
                    <button type="button" class="btn btn-secondary" onclick="registerPush(document.getElementById('dest_${index}').value)" style="background-color: #28a745;">📱 Register Device for Push</button>
                </div>
            </div>"""

html = html.replace(old_form_row2, new_form_row2)

# Update save logic to include enable_sms and enable_push
old_save_loop = """            const dest = document.getElementById(`dest_${i}`).value;
            if (!dest) continue;
            
            globalConfig.profiles.push({
                destination_number: dest,
                alert_cooldown_minutes: parseInt(document.getElementById(`cool_${i}`).value),
                delivery_rate_threshold_percent: parseFloat(document.getElementById(`rate_${i}`).value),
                pending_messages_threshold: parseInt(document.getElementById(`pend_${i}`).value),
                pending_messages_duration_seconds: parseInt(document.getElementById(`dur_${i}`).value),
                enable_sms: true,
                enable_push: true
            });"""

new_save_loop = """            const dest = document.getElementById(`dest_${i}`).value;
            if (!dest) continue;
            
            globalConfig.profiles.push({
                destination_number: dest,
                alert_cooldown_minutes: parseInt(document.getElementById(`cool_${i}`).value),
                delivery_rate_threshold_percent: parseFloat(document.getElementById(`rate_${i}`).value),
                pending_messages_threshold: parseInt(document.getElementById(`pend_${i}`).value),
                pending_messages_duration_seconds: parseInt(document.getElementById(`dur_${i}`).value),
                enable_sms: document.getElementById(`sms_${i}`).checked,
                enable_push: document.getElementById(`push_${i}`).checked
            });"""

html = html.replace(old_save_loop, new_save_loop)

# I also need to fix the case where old_save_loop didn't have enable_sms and enable_push yet because the previous patch might have missed it or added it. Wait, the previous patch missed it too because the regex didn't match!
# Let's match the ACTUAL current save loop:
old_save_loop_actual = """            const dest = document.getElementById(`dest_${i}`).value;
            if (!dest) continue;
            
            globalConfig.profiles.push({
                destination_number: dest,
                alert_cooldown_minutes: parseInt(document.getElementById(`cool_${i}`).value),
                delivery_rate_threshold_percent: parseFloat(document.getElementById(`rate_${i}`).value),
                pending_messages_threshold: parseInt(document.getElementById(`pend_${i}`).value),
                pending_messages_duration_seconds: parseInt(document.getElementById(`dur_${i}`).value),
            });"""

html = html.replace(old_save_loop_actual, new_save_loop)

# The previous patch missed the addProfile because I added a trailing comma in the regex and the actual file didn't have it or something?
# Actually the previous patch successfully replaced `addProfile()` because I can see `enable_sms: true` in the output above. But I didn't grep for addProfile.

with open('public/index.html', 'w') as f:
    f.write(html)
