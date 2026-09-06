import re

with open('public/index.html', 'r') as f:
    html = f.read()

# Add service worker registration
sw_script = """
    // Web Push Service Worker
    let publicVapidKey = null;
    let swRegistration = null;

    async function initPush() {
        if ('serviceWorker' in navigator && 'PushManager' in window) {
            try {
                swRegistration = await navigator.serviceWorker.register('/service-worker.js');
                console.log('Service Worker registered');
                const res = await fetch('/api/push/vapidPublicKey');
                publicVapidKey = await res.text();
            } catch (error) {
                console.error('Service Worker Error', error);
            }
        } else {
            console.warn('Push messaging is not supported');
        }
    }
    
    function urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);
        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        return outputArray;
    }

    async function registerPush(destination) {
        if (!swRegistration || !publicVapidKey) {
            alert('Push not supported or initialized');
            return;
        }
        
        if (!destination) {
            alert('Please fill out the destination number first, then save, before registering for Push.');
            return;
        }

        try {
            const subscription = await swRegistration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: urlBase64ToUint8Array(publicVapidKey)
            });

            const res = await fetch('/api/push/subscribe', {
                method: 'POST',
                body: JSON.stringify({ destination, subscription }),
                headers: { 'Content-Type': 'application/json' }
            });

            if (res.ok) {
                alert('Device successfully registered for push notifications on this profile!');
            } else {
                alert('Failed to register device');
            }
        } catch (error) {
            console.error('Push registration error', error);
            if (Notification.permission === 'denied') {
                alert('Push Notifications are blocked by your browser settings.');
            } else {
                alert('Failed to subscribe: ' + error.message);
            }
        }
    }

    initPush();
"""
html = html.replace("    async function testAlert(destination) {", sw_script + "\n    async function testAlert(destination) {")

# Add checkboxes and push button to the profile HTML generator
old_form_row2 = """            <div class="form-row">
                <div class="form-group">
                    <label>Delivery Rate Threshold (%)</label>
                    <input type="number" step="0.1" id="rate_${index}" value="${p.delivery_rate_threshold_percent || 85}" required>
                </div>
                <div class="form-group">
                    <label>Pending Msgs Threshold</label>
                    <input type="number" id="pend_count_${index}" value="${p.pending_messages_threshold || 1000}" required>
                </div>
                <div class="form-group">
                    <label>Pending Duration (Secs)</label>
                    <input type="number" id="pend_dur_${index}" value="${p.pending_messages_duration_seconds || 60}" required>
                </div>
            </div>"""

new_form_row2 = """            <div class="form-row">
                <div class="form-group">
                    <label>Delivery Rate Threshold (%)</label>
                    <input type="number" step="0.1" id="rate_${index}" value="${p.delivery_rate_threshold_percent || 85}" required>
                </div>
                <div class="form-group">
                    <label>Pending Msgs Threshold</label>
                    <input type="number" id="pend_count_${index}" value="${p.pending_messages_threshold || 1000}" required>
                </div>
                <div class="form-group">
                    <label>Pending Duration (Secs)</label>
                    <input type="number" id="pend_dur_${index}" value="${p.pending_messages_duration_seconds || 60}" required>
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
                pending_messages_threshold: parseInt(document.getElementById(`pend_count_${i}`).value),
                pending_messages_duration_seconds: parseInt(document.getElementById(`pend_dur_${i}`).value)
            });"""

new_save_loop = """            const dest = document.getElementById(`dest_${i}`).value;
            if (!dest) continue;
            
            globalConfig.profiles.push({
                destination_number: dest,
                alert_cooldown_minutes: parseInt(document.getElementById(`cool_${i}`).value),
                delivery_rate_threshold_percent: parseFloat(document.getElementById(`rate_${i}`).value),
                pending_messages_threshold: parseInt(document.getElementById(`pend_count_${i}`).value),
                pending_messages_duration_seconds: parseInt(document.getElementById(`pend_dur_${i}`).value),
                enable_sms: document.getElementById(`sms_${i}`).checked,
                enable_push: document.getElementById(`push_${i}`).checked
            });"""

html = html.replace(old_save_loop, new_save_loop)

# One more fix: we need to default new profiles correctly
old_add_profile = """    function addProfile() {
        globalConfig.profiles.push({
            destination_number: "",
            delivery_rate_threshold_percent: 85,
            pending_messages_threshold: 1000,
            pending_messages_duration_seconds: 60,
            alert_cooldown_minutes: 15
        });
        renderProfiles();
    }"""
new_add_profile = """    function addProfile() {
        globalConfig.profiles.push({
            destination_number: "",
            delivery_rate_threshold_percent: 85,
            pending_messages_threshold: 1000,
            pending_messages_duration_seconds: 60,
            alert_cooldown_minutes: 15,
            enable_sms: true,
            enable_push: true
        });
        renderProfiles();
    }"""
html = html.replace(old_add_profile, new_add_profile)

with open('public/index.html', 'w') as f:
    f.write(html)
