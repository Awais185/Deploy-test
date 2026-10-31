function loadStats() {
  chrome.storage.local.get(['feat_leads', 'feat_groups', 'scanned', 'generated', 'posted', 'groups_joined'], (data) => {
    document.getElementById('toggle_leads').checked = data.feat_leads !== false;
    document.getElementById('toggle_groups').checked = data.feat_groups !== false;
    
    document.getElementById('scanned').textContent = data.scanned || 0;
    document.getElementById('generated').textContent = data.generated || 0;
    document.getElementById('posted').textContent = data.posted || 0;
    document.getElementById('groups_joined').textContent = data.groups_joined || 0;
  });
}

document.addEventListener('DOMContentLoaded', () => {
  loadStats();
  setInterval(loadStats, 2000);

  // Handle Leads Toggle
  document.getElementById('toggle_leads').addEventListener('change', (e) => {
    chrome.storage.local.set({ feat_leads: e.target.checked });
  });

  // Handle Groups Toggle
  document.getElementById('toggle_groups').addEventListener('change', (e) => {
    const isChecked = e.target.checked;
    chrome.storage.local.set({ feat_groups: isChecked });

    // If turning OFF group joiner, immediately switch to SCANNING
    if (!isChecked) {
        chrome.storage.local.get(['feat_leads'], (data) => {
            if (data.feat_leads !== false) {
                chrome.storage.local.set({ bot_state: 'SCANNING' });
                // Force the active Facebook tab to go to the feed
                chrome.tabs.query({ url: "*://*.facebook.com/*" }, (tabs) => {
                    if (tabs.length > 0) {
                        chrome.tabs.update(tabs[0].id, { url: "https://www.facebook.com/groups/feed/" });
                    }
                });
            }
        });
    }
  });
});