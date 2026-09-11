// Window Function Anatomy
// CANVAS_HEIGHT: 550
let currentRow = 3;
let selectedFunc = 'SUM';
let canvasW, canvasH;
let funcSelect;
let rowSlider;

const partitions = [
    { group: 'A', values: [10, 20, 30, 15] },
    { group: 'B', values: [50, 40, 60] },
    { group: 'C', values: [25, 35, 45] }
];

// Flatten rows
let rows = [];
partitions.forEach(function(p) {
    p.values.forEach(function(v) {
        rows.push({ group: p.group, value: v });
    });
});

const groupColors = {
    'A': [173, 216, 230, 60],
    'B': [255, 228, 196, 60],
    'C': [216, 191, 216, 60]
};

const groupBorders = {
    'A': [70, 130, 180],
    'B': [210, 140, 70],
    'C': [140, 100, 160]
};

function setup() {
    const main = document.querySelector('main');
    canvasW = main.offsetWidth || 600;
    canvasH = 550;
    let cnv = createCanvas(canvasW, canvasH);
    cnv.parent(main);

    let controls = createDiv('');
    controls.parent(main);
    controls.style('display', 'flex');
    controls.style('align-items', 'center');
    controls.style('justify-content', 'center');
    controls.style('gap', '16px');
    controls.style('margin-top', '8px');
    controls.style('font-family', 'Arial, sans-serif');

    let sliderLabel = createSpan('Current Row: ');
    sliderLabel.parent(controls);
    sliderLabel.style('font-size', '13px');

    rowSlider = createSlider(0, rows.length - 1, currentRow, 1);
    rowSlider.parent(controls);
    rowSlider.style('width', '180px');
    rowSlider.input(function() { currentRow = rowSlider.value(); });

    let selLabel = createSpan('Function: ');
    selLabel.parent(controls);
    selLabel.style('font-size', '13px');

    funcSelect = createSelect();
    funcSelect.parent(controls);
    funcSelect.option('SUM');
    funcSelect.option('RANK');
    funcSelect.option('LAG');
    funcSelect.selected(selectedFunc);
    funcSelect.style('padding', '4px 8px');
    funcSelect.style('font-size', '13px');
    funcSelect.changed(function() { selectedFunc = funcSelect.value(); });
}

function draw() {
    background('#f0f8ff');
    currentRow = rowSlider.value();

    // Title
    fill(0);
    noStroke();
    textSize(18);
    textAlign(CENTER, TOP);
    text('Window Function Anatomy', canvasW / 2, 10);

    let tableX = 60;
    let tableY = 50;
    let rowH = 40;
    let colW_group = 80;
    let colW_val = 80;
    let colW_result = 100;
    let totalW = colW_group + colW_val + colW_result;

    // Header
    fill(100, 60, 150);
    noStroke();
    rect(tableX, tableY, totalW, rowH);
    fill(255);
    textSize(13);
    textAlign(CENTER, CENTER);
    text('Group', tableX + colW_group / 2, tableY + rowH / 2);
    text('Value', tableX + colW_group + colW_val / 2, tableY + rowH / 2);
    text(selectedFunc + '()', tableX + colW_group + colW_val + colW_result / 2, tableY + rowH / 2);

    // Current row's partition
    let curGroup = rows[currentRow].group;
    let partitionIndices = [];
    for (let i = 0; i < rows.length; i++) {
        if (rows[i].group === curGroup) partitionIndices.push(i);
    }

    // Window frame: for SUM, full partition; for LAG, previous row; for RANK, full partition
    let frameStart, frameEnd;
    if (selectedFunc === 'LAG') {
        let posInPartition = partitionIndices.indexOf(currentRow);
        frameStart = posInPartition > 0 ? partitionIndices[posInPartition - 1] : -1;
        frameEnd = frameStart;
    } else {
        frameStart = partitionIndices[0];
        frameEnd = partitionIndices[partitionIndices.length - 1];
    }

    // Compute result
    let resultVal = computeResult(currentRow, curGroup, partitionIndices);

    // Draw rows
    for (let i = 0; i < rows.length; i++) {
        let ry = tableY + (i + 1) * rowH;
        let r = rows[i];
        let gc = groupColors[r.group] || [220, 220, 220, 60];
        let isInFrame = (i >= frameStart && i <= frameEnd && frameStart >= 0);
        let isCurrent = (i === currentRow);

        // Background
        if (isCurrent) {
            fill(147, 112, 219, 120);
        } else if (isInFrame) {
            fill(147, 112, 219, 50);
        } else {
            fill(gc[0], gc[1], gc[2], gc[3]);
        }
        stroke(isCurrent ? color(100, 60, 150) : color(180));
        strokeWeight(isCurrent ? 2 : 1);
        rect(tableX, ry, totalW, rowH);

        // Cell text
        noStroke();
        fill(0);
        textSize(13);
        textAlign(CENTER, CENTER);
        text(r.group, tableX + colW_group / 2, ry + rowH / 2);
        text(r.value, tableX + colW_group + colW_val / 2, ry + rowH / 2);

        // Result column for current row
        if (isCurrent) {
            fill(100, 60, 150);
            textStyle(BOLD);
            text(resultVal, tableX + colW_group + colW_val + colW_result / 2, ry + rowH / 2);
            textStyle(NORMAL);
        }
    }

    // Column dividers
    stroke(180);
    strokeWeight(1);
    line(tableX + colW_group, tableY, tableX + colW_group, tableY + (rows.length + 1) * rowH);
    line(tableX + colW_group + colW_val, tableY, tableX + colW_group + colW_val, tableY + (rows.length + 1) * rowH);

    // Window frame bracket
    if (frameStart >= 0) {
        let bracketX = tableX + totalW + 15;
        let fy1 = tableY + (frameStart + 1) * rowH;
        let fy2 = tableY + (frameEnd + 2) * rowH;
        stroke(147, 112, 219);
        strokeWeight(3);
        noFill();
        line(bracketX, fy1, bracketX + 12, fy1);
        line(bracketX + 12, fy1, bracketX + 12, fy2);
        line(bracketX, fy2, bracketX + 12, fy2);

        noStroke();
        fill(100, 60, 150);
        textSize(11);
        textAlign(LEFT, CENTER);
        text('frame', bracketX + 18, (fy1 + fy2) / 2);
    }

    // Partition label
    let pStart = tableY + (partitionIndices[0] + 1) * rowH;
    let pEnd = tableY + (partitionIndices[partitionIndices.length - 1] + 2) * rowH;
    let labelX = tableX - 10;
    stroke(groupBorders[curGroup][0], groupBorders[curGroup][1], groupBorders[curGroup][2]);
    strokeWeight(2);
    noFill();
    line(labelX, pStart, labelX - 8, pStart);
    line(labelX - 8, pStart, labelX - 8, pEnd);
    line(labelX, pEnd, labelX - 8, pEnd);
    noStroke();
    fill(80);
    textSize(11);
    textAlign(RIGHT, CENTER);
    push();
    translate(labelX - 14, (pStart + pEnd) / 2);
    rotate(-HALF_PI);
    textAlign(CENTER, CENTER);
    text('partition ' + curGroup, 0, 0);
    pop();

    // Info text
    noStroke();
    fill(80);
    textSize(12);
    textAlign(LEFT, TOP);
    let infoY = tableY + (rows.length + 1) * rowH + 15;
    text('Row ' + currentRow + '  |  Group: ' + curGroup + '  |  ' + selectedFunc + '() = ' + resultVal, tableX, infoY);
    textSize(11);
    fill(120);
    if (selectedFunc === 'SUM') {
        text('SUM over partition ' + curGroup + ': adds all values in the partition', tableX, infoY + 20);
    } else if (selectedFunc === 'RANK') {
        text('RANK within partition ' + curGroup + ': position when sorted by value (ascending)', tableX, infoY + 20);
    } else if (selectedFunc === 'LAG') {
        text('LAG(1) within partition ' + curGroup + ': previous row\'s value (null if first)', tableX, infoY + 20);
    }
}

function computeResult(rowIdx, group, partIndices) {
    if (selectedFunc === 'SUM') {
        let s = 0;
        partIndices.forEach(function(pi) { s += rows[pi].value; });
        return s;
    }
    if (selectedFunc === 'RANK') {
        let partVals = partIndices.map(function(pi) { return { idx: pi, val: rows[pi].value }; });
        partVals.sort(function(a, b) { return a.val - b.val; });
        for (let r = 0; r < partVals.length; r++) {
            if (partVals[r].idx === rowIdx) return r + 1;
        }
        return '?';
    }
    if (selectedFunc === 'LAG') {
        let posInPart = partIndices.indexOf(rowIdx);
        if (posInPart <= 0) return 'null';
        return rows[partIndices[posInPart - 1]].value;
    }
    return '?';
}
