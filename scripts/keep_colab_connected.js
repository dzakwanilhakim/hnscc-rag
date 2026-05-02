function keepAlive() {
    console.log("Keep-alive ping at " + new Date().toLocaleTimeString());
    document.querySelector("colab-toolbar-button#connect")?.click();
}
setInterval(keepAlive, 60000);