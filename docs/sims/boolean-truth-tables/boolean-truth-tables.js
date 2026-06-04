// Boolean Operation Truth Tables (AND, OR, NOT, XOR) with Three-Valued Logic
// CANVAS_HEIGHT: 500
let activeTab = 'AND';
let threeValued = false;
let highlightR = -1;
let highlightC = -1;
const tabs = ['AND', 'OR', 'NOT', 'XOR'];
let canvasW, canvasH;

function setup() {
    const main = document.querySelector('main');
    canvasW = main.offsetWidth || 600;
    canvasH = 500;
    let cnv = createCanvas(canvasW, canvasH);
    cnv.parent(main);
}

function draw() {
    background('#f0f8ff');

    // Title
    fill(0);
    noStroke();
    textSize(18);
    textAlign(CENTER, TOP);
    text('Boolean Truth Tables', canvasW / 2, 10);

    // Tabs
    let tabW = 80;
    let tabX0 = canvasW / 2 - (tabs.length * tabW) / 2;
    let tabY = 40;
    for (let i = 0; i < tabs.length; i++) {
        let tx = tabX0 + i * tabW;
        if (tabs[i] === activeTab) {
            fill('#006400');
        } else {
            fill(200);
        }
        noStroke();
        rect(tx, tabY, tabW - 4, 30, 6);
        fill(tabs[i] === activeTab ? 255 : 60);
        textSize(13);
        textAlign(CENTER, CENTER);
        text(tabs[i], tx + (tabW - 4) / 2, tabY + 15);
    }

    // Three-valued toggle
    let toggleX = canvasW / 2 - 80;
    let toggleY = tabY + 40;
    fill(threeValued ? '#006400' : '#ccc');
    noStroke();
    rect(toggleX, toggleY, 160, 28, 6);
    fill(threeValued ? 255 : 60);
    textSize(12);
    textAlign(CENTER, CENTER);
    text(threeValued ? 'Three-Valued (with Null) ON' : 'Three-Valued (with Null) OFF', toggleX + 80, toggleY + 14);

    // Determine values
    let vals = threeValued ? ['True', 'False', 'Null'] : ['True', 'False'];
    let n = vals.length;

    if (activeTab === 'NOT') {
        drawNotTable(vals, toggleY + 50);
    } else {
        drawBinaryTable(vals, toggleY + 50);
    }
}

function drawBinaryTable(vals, startY) {
    let n = vals.length;
    let cellSz = 60;
    let tableW = (n + 1) * cellSz;
    let x0 = canvasW / 2 - tableW / 2;
    let y0 = startY;

    // Header row
    fill(80);
    textSize(13);
    textAlign(CENTER, CENTER);
    text(activeTab, x0 + cellSz / 2, y0 + cellSz / 2);
    for (let c = 0; c < n; c++) {
        fill(c === highlightC ? color('#006400') : color(60));
        text(vals[c], x0 + (c + 1) * cellSz + cellSz / 2, y0 + cellSz / 2);
    }

    // Rows
    for (let r = 0; r < n; r++) {
        // Row label
        fill(r === highlightR ? color('#006400') : color(60));
        textSize(13);
        textAlign(CENTER, CENTER);
        text(vals[r], x0 + cellSz / 2, y0 + (r + 1) * cellSz + cellSz / 2);

        for (let c = 0; c < n; c++) {
            let cx = x0 + (c + 1) * cellSz;
            let cy = y0 + (r + 1) * cellSz;
            let result = evalOp(activeTab, vals[r], vals[c]);
            let bg = getCellColor(result);
            let isHL = (r === highlightR || c === highlightC);
            stroke(isHL ? '#006400' : '#999');
            strokeWeight(isHL ? 2 : 1);
            fill(bg);
            rect(cx, cy, cellSz, cellSz);
            noStroke();
            fill(result === 'Null' ? 60 : 255);
            textSize(12);
            textAlign(CENTER, CENTER);
            text(result, cx + cellSz / 2, cy + cellSz / 2);
        }
    }

    // Grid outlines
    stroke(150);
    strokeWeight(1);
    for (let i = 0; i <= n + 1; i++) {
        line(x0, y0 + i * cellSz, x0 + (n + 1) * cellSz, y0 + i * cellSz);
        line(x0 + i * cellSz, y0, x0 + i * cellSz, y0 + (n + 1) * cellSz);
    }
}

function drawNotTable(vals, startY) {
    let n = vals.length;
    let cellSz = 60;
    let tableW = 2 * cellSz;
    let x0 = canvasW / 2 - tableW / 2;
    let y0 = startY;

    // Headers
    fill(60);
    noStroke();
    textSize(13);
    textAlign(CENTER, CENTER);
    text('Input', x0 + cellSz / 2, y0 + cellSz / 2);
    text('NOT', x0 + cellSz + cellSz / 2, y0 + cellSz / 2);

    stroke(150);
    strokeWeight(1);
    for (let i = 0; i <= n + 1; i++) {
        line(x0, y0 + i * cellSz, x0 + 2 * cellSz, y0 + i * cellSz);
    }
    line(x0, y0, x0, y0 + (n + 1) * cellSz);
    line(x0 + cellSz, y0, x0 + cellSz, y0 + (n + 1) * cellSz);
    line(x0 + 2 * cellSz, y0, x0 + 2 * cellSz, y0 + (n + 1) * cellSz);

    for (let r = 0; r < n; r++) {
        let cy = y0 + (r + 1) * cellSz;
        let isHL = (r === highlightR);

        // Input cell
        stroke(isHL ? '#006400' : '#999');
        strokeWeight(isHL ? 2 : 1);
        fill(getCellColor(vals[r]));
        rect(x0, cy, cellSz, cellSz);
        noStroke();
        fill(vals[r] === 'Null' ? 60 : 255);
        textSize(12);
        textAlign(CENTER, CENTER);
        text(vals[r], x0 + cellSz / 2, cy + cellSz / 2);

        // Result cell
        let result = evalNot(vals[r]);
        stroke(isHL ? '#006400' : '#999');
        strokeWeight(isHL ? 2 : 1);
        fill(getCellColor(result));
        rect(x0 + cellSz, cy, cellSz, cellSz);
        noStroke();
        fill(result === 'Null' ? 60 : 255);
        textSize(12);
        textAlign(CENTER, CENTER);
        text(result, x0 + cellSz + cellSz / 2, cy + cellSz / 2);
    }
}

function mousePressed() {
    // Tab click
    let tabW = 80;
    let tabX0 = canvasW / 2 - (tabs.length * tabW) / 2;
    let tabY = 40;
    for (let i = 0; i < tabs.length; i++) {
        let tx = tabX0 + i * tabW;
        if (mouseX >= tx && mouseX <= tx + tabW - 4 && mouseY >= tabY && mouseY <= tabY + 30) {
            activeTab = tabs[i];
            highlightR = -1;
            highlightC = -1;
            return;
        }
    }

    // Toggle click
    let toggleX = canvasW / 2 - 80;
    let toggleY = tabY + 40;
    if (mouseX >= toggleX && mouseX <= toggleX + 160 && mouseY >= toggleY && mouseY <= toggleY + 28) {
        threeValued = !threeValued;
        highlightR = -1;
        highlightC = -1;
        return;
    }

    // Cell click for highlight
    let vals = threeValued ? ['True', 'False', 'Null'] : ['True', 'False'];
    let n = vals.length;
    let cellSz = 60;
    let startY = toggleY + 28 + 22;

    if (activeTab === 'NOT') {
        let tableW = 2 * cellSz;
        let x0 = canvasW / 2 - tableW / 2;
        let y0 = startY;
        for (let r = 0; r < n; r++) {
            let cy = y0 + (r + 1) * cellSz;
            if (mouseX >= x0 && mouseX <= x0 + 2 * cellSz && mouseY >= cy && mouseY <= cy + cellSz) {
                highlightR = (highlightR === r) ? -1 : r;
                return;
            }
        }
    } else {
        let tableW = (n + 1) * cellSz;
        let x0 = canvasW / 2 - tableW / 2;
        let y0 = startY;
        for (let r = 0; r < n; r++) {
            for (let c = 0; c < n; c++) {
                let cx = x0 + (c + 1) * cellSz;
                let cy = y0 + (r + 1) * cellSz;
                if (mouseX >= cx && mouseX <= cx + cellSz && mouseY >= cy && mouseY <= cy + cellSz) {
                    highlightR = r;
                    highlightC = c;
                    return;
                }
            }
        }
    }
    highlightR = -1;
    highlightC = -1;
}

function evalOp(op, a, b) {
    if (op === 'AND') {
        if (a === 'False' || b === 'False') return 'False';
        if (a === 'Null' || b === 'Null') return 'Null';
        return 'True';
    }
    if (op === 'OR') {
        if (a === 'True' || b === 'True') return 'True';
        if (a === 'Null' || b === 'Null') return 'Null';
        return 'False';
    }
    if (op === 'XOR') {
        if (a === 'Null' || b === 'Null') return 'Null';
        return (a !== b) ? 'True' : 'False';
    }
    return 'Null';
}

function evalNot(v) {
    if (v === 'True') return 'False';
    if (v === 'False') return 'True';
    return 'Null';
}

function getCellColor(v) {
    if (v === 'True') return color(34, 139, 34);
    if (v === 'False') return color(200, 50, 50);
    return color(180, 180, 180);
}
