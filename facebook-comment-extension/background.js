chrome.runtime.onInstalled.addListener(async () => {
    chrome.storage.local.set({ 
        bot_state: 'SCANNING', 
        groups_joined: 0, 
        feat_leads: true, 
        feat_groups: true 
    });
});

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "type_comment") {
    const tabId = sender.tab.id;
    const windowId = sender.tab.windowId;
    
    // 1. Bring the tab to the front so the debugger works perfectly
    chrome.tabs.update(tabId, { active: true }, () => {
        chrome.windows.update(windowId, { focused: true }, () => {
            
            // 2. Attach Debugger
            chrome.debugger.attach({ tabId: tabId }, "1.3", () => {
              if (chrome.runtime.lastError) {
                sendResponse({ success: false, error: chrome.runtime.lastError.message });
                return;
              }

              const clickParams = { type: "mousePressed", x: request.x, y: request.y, button: "left", clickCount: 1 };
              
              try {
                chrome.debugger.sendCommand({ tabId: tabId }, "Input.dispatchMouseEvent", clickParams, () => {
                  if (chrome.runtime.lastError) { throw new Error(chrome.runtime.lastError.message); }

                  setTimeout(() => {
                    const text = request.text;
                    let i = 0;

                    function typeChar() {
                      if (i < text.length) {
                        try {
                          chrome.debugger.sendCommand({ tabId: tabId }, "Input.dispatchKeyEvent", {
                            type: "char", text: text[i]
                          }, () => {
                            if (chrome.runtime.lastError) return; 
                            i++;
                            setTimeout(typeChar, Math.floor(Math.random() * 100) + 100); 
                          });
                        } catch(e) {}
                      } else {
                        try {
                          setTimeout(() => {
                            chrome.debugger.sendCommand({ tabId: tabId }, "Input.dispatchKeyEvent", {
                              type: "keyDown", key: "Enter", code: "Enter", windowsVirtualKeyCode: 13
                            }, () => {
                              setTimeout(() => {
                                chrome.debugger.detach({ tabId: tabId }, () => {
                                  sendResponse({ success: true });
                                });
                              }, 2000);
                            });
                          }, 2000);
                        } catch(e) { sendResponse({ success: false }); }
                      }
                    }
                    typeChar(); 
                  }, 1500); 
                });
              } catch (err) {
                chrome.debugger.detach({ tabId: tabId }, () => {
                  sendResponse({ success: false, error: err.message });
                });
              }
            });
            
        });
    });
    
    return true; 
  }
});