// messaging.js 

// Scroll to the bottom of chat box on page load 
window.addEventListener('DOMContentLoaded', () =>{
    const chatBox = document.getElementById('chat-box');
    if (chatBox) {
        chatBox.scrollTop = chatBox.scrollHeight;
    }
});