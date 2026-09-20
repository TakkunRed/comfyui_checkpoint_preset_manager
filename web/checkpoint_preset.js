import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "Comfy.CheckpointPresetManager",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "CheckpointPresetNode") {
            
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;

                const memoWidget = this.widgets.find(w => w.name === "memo");
                if (memoWidget) {
                    memoWidget.type = "customtext";
                    // inputEl は生成が遅れることがあるため、できるまで短く再試行する
                    let tries = 0;
                    const styleMemo = () => {
                        if (memoWidget.inputEl) {
                            memoWidget.inputEl.style.height = "70px";
                            memoWidget.inputEl.style.fontFamily = "monospace";
                            memoWidget.inputEl.style.fontSize = "12px";
                            memoWidget.inputEl.style.marginTop = "4px";
                            memoWidget.inputEl.style.marginBottom = "0px";
                            memoWidget.inputEl.placeholder = "enter note...";
                        } else if (tries++ < 50) {
                            setTimeout(styleMemo, 20);
                        }
                    };
                    styleMemo();
                }

                const el = document.createElement("div");
                el.style.color = "#00FF00";
                el.style.backgroundColor = "black";
                el.style.padding = "8px";
                
                el.style.position = "relative";
                el.style.top = "-25px";
                el.style.margin = "0 auto"; 
                
                el.style.width = "calc(100% - 24px)";
                el.style.boxSizing = "border-box";
                el.style.borderRadius = "6px";
                el.style.fontFamily = "monospace";
                el.style.fontSize = "11px";
                el.style.lineHeight = "1.3";
                el.style.height = "106px"; 
                el.style.overflow = "hidden";
                el.style.whiteSpace = "pre-wrap";
                el.style.border = "1px solid #444";
                el.innerText = "Queue prompt to initialize...";

                this.addDOMWidget("STATUS_DISPLAY", "display", el);
                this.status_div = el;

                this.setSize([380, 560]); 
                return r;
            };

            const onExecuted = nodeType.prototype.onExecuted;
            nodeType.prototype.onExecuted = function (message) {
                onExecuted?.apply(this, arguments);
                if (message?.status_text && this.status_div) {
                    const txt = message.status_text[0];
                    this.status_div.innerText = txt;

                    if (txt.includes("(SAVED!)")) {
                        this.status_div.style.borderColor = "#00E5FF";
                        this.status_div.style.color = "#00E5FF";
                    } else if (txt.includes("SAVE SKIPPED") || txt.includes("NOT SAVED") || txt.includes("MODE: UI")) {
                        this.status_div.style.borderColor = "#FF9900";
                        this.status_div.style.color = "#FF9900";
                    } else {
                        this.status_div.style.borderColor = "#00FF00";
                        this.status_div.style.color = "#00FF00";
                    }
                }
            };
        }
    }
});