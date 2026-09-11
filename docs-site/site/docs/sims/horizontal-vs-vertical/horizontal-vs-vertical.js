// Horizontal vs Vertical Operations
// CANVAS_HEIGHT: 450
let mode = 'vertical';
let canvasW, canvasH;
const gridData = [
    [10, 20, 30],
    [40, 50, 60],
    [70, 80, 90],
    [15, 25, 35]
];
const colNames = ['A', 'B', 'C'];
const cellW = 70;
const cellH = 45;
const gridX0 = 80;
const gridY0 = 80;

function setup() {
    const main = document.querySelector('main');
    canvasW = main.offsetWidth || 600;
    canvasH = 450;
    let cnv = createCanvas(canvasW, canvasH);
    cnv.parent(main);

    let btnDiv = createDiv('');
    btnDiv.parent(main);
    btnDiv.style('text-align', 'center');
    btnDiv.style('margin-top', '8px');

    let btn = createButton('Toggle: Vertical / Horizontal');
    btn.parent(btnDiv);
    btn.style('padding', '8px 18px');
    btn.style('font-size', '14px');
    btn.style('cursor', 'pointer');
    btn.style('background', '#006400');
    btn.style('color', '#fff');
    btn.style('border', 'none');
    btn.style('border-radius', '6px');
    btn.mousePressed(function() {
        mode = (mode === 'vertical') ? 'horizontal' : 'vertical';
    });
}

function draw() {
    background('#f0f8ff');

    // Title
    fill(0);
    noStroke();
    textSize(18);
    textAlign(CENTER, TOP);
    text('Horizontal vs Vertical Operations', canvasW / 2, 12);

    textSize(14);
    textAlign(CENTER, TOP);
    fill(80);
    text(mode === 'vertical' ? 'Vertical: sum() down a column -> 1 value' : 'Horizontal: greatest() across a row -> 1 value per row', canvasW / 2, 40);

    // Column headers
    textSize(13);
    textAlign(CENTER, CENTER);
    fill(60);
    for (let c = 0; c < 3; c++) {
        text(colNames[c], gridX0 + c * cellW + cellW / 2, gridY0 - 18);
    }

    // Row labels
    for (let r = 0; r < 4; r++) {
        textAlign(RIGHT, CENTER);
        fill(60);
        text('Row ' + r, gridX0 - 8, gridY0 + r * cellH + cellH / 2);
    }

    // Draw grid
    for (let r = 0; r < 4; r++) {
        for (let c = 0; c < 3; c++) {
            let x = gridX0 + c * cellW;
            let y = gridY0 + r * cellH;
            let highlighted = false;

            if (mode === 'vertical' && c === 1) {
                highlighted = true;
                fill(70, 130, 180, 80);
            } else if (mode === 'horizontal' && r === 1) {
                highlighted = true;
                fill(218, 165, 32, 80);
            } else {
                fill(255);
            }
            stroke(150);
            strokeWeight(1);
            rect(x, y, cellW, cellH);

            noStroke();
            fill(0);
            textAlign(CENTER, CENTER);
            textSize(14);
            text(gridData[r][c], x + cellW / 2, y + cellH / 2);
        }
    }

    // Arrow and result
    if (mode === 'vertical') {
        // Arrow down column B
        let ax = gridX0 + 1 * cellW + cellW / 2;
        let ay1 = gridY0;
        let ay2 = gridY0 + 4 * cellH + 10;
        stroke(70, 130, 180);
        strokeWeight(3);
        line(ax, ay1, ax, ay2);
        // Arrowhead
        fill(70, 130, 180);
        noStroke();
        triangle(ax - 8, ay2 - 4, ax + 8, ay2 - 4, ax, ay2 + 10);

        // Result box
        fill(70, 130, 180);
        noStroke();
        rectMode(CENTER);
        rect(ax, ay2 + 35, 100, 32, 6);
        rectMode(CORNER);
        fill(255);
        textSize(14);
        textAlign(CENTER, CENTER);
        let colSum = gridData[0][1] + gridData[1][1] + gridData[2][1] + gridData[3][1];
        text('sum() = ' + colSum, ax, ay2 + 35);

        // Label
        noStroke();
        fill(70, 130, 180);
        textSize(12);
        textAlign(LEFT, CENTER);
        text('sum() -> 1 value', ax + 15, (ay1 + ay2) / 2);
    } else {
        // Arrow across row 1
        let ay = gridY0 + 1 * cellH + cellH / 2;
        let ax1 = gridX0;
        let ax2 = gridX0 + 3 * cellW + 10;
        stroke(218, 165, 32);
        strokeWeight(3);
        line(ax1, ay, ax2, ay);
        // Arrowhead
        fill(218, 165, 32);
        noStroke();
        triangle(ax2 - 4, ay - 8, ax2 - 4, ay + 8, ax2 + 10, ay);

        // Result box
        fill(218, 165, 32);
        noStroke();
        rectMode(CENTER);
        rect(ax2 + 60, ay, 120, 32, 6);
        rectMode(CORNER);
        fill(255);
        textSize(14);
        textAlign(CENTER, CENTER);
        let rowMax = Math.max(gridData[1][0], gridData[1][1], gridData[1][2]);
        text('greatest() = ' + rowMax, ax2 + 60, ay);

        // Label
        noStroke();
        fill(218, 165, 32);
        textSize(12);
        textAlign(CENTER, TOP);
        text('greatest() -> 1 value per row', (ax1 + ax2) / 2, ay + cellH / 2 + 8);

        // Show results for all rows on right
        for (let r = 0; r < 4; r++) {
            let ry = gridY0 + r * cellH + cellH / 2;
            let rMax = Math.max(gridData[r][0], gridData[r][1], gridData[r][2]);
            fill(r === 1 ? color(218, 165, 32) : color(180));
            noStroke();
            textAlign(LEFT, CENTER);
            textSize(12);
            text('-> ' + rMax, gridX0 + 3 * cellW + 8, ry);
        }
    }
}
