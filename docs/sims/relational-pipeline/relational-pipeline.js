// Relational Operations Pipeline — Interactive stage toggles
// CANVAS_HEIGHT: 500
new p5(function(p) {
    var canvasWidth = 800;
    var canvasHeight = 500;

    var teal       = '#20B2AA';
    var tealDark   = '#178F89';
    var tealLight  = '#7EDCD6';
    var tealBg     = '#E0F7F5';

    // Sample data
    var allRows = [
        { id: 1, name: 'Alice',   dept: 'Eng',    salary: 95000,  active: true },
        { id: 2, name: 'Bob',     dept: 'Sales',   salary: 72000,  active: true },
        { id: 3, name: 'Carol',   dept: 'Eng',     salary: 105000, active: false },
        { id: 4, name: 'Dave',    dept: 'Eng',     salary: 88000,  active: true },
        { id: 5, name: 'Eve',     dept: 'HR',      salary: 67000,  active: true },
        { id: 6, name: 'Frank',   dept: 'Sales',   salary: 81000,  active: true },
        { id: 7, name: 'Grace',   dept: 'Eng',     salary: 112000, active: true },
        { id: 8, name: 'Hank',    dept: 'HR',      salary: 59000,  active: false }
    ];

    var columns = ['id', 'name', 'dept', 'salary', 'active'];

    var stages = [
        { name: 'Filter',  desc: 'active == true', enabled: true },
        { name: 'Sort',    desc: 'salary DESC',    enabled: true },
        { name: 'Select',  desc: 'name, dept, salary', enabled: true },
        { name: 'Head',    desc: 'limit 3',        enabled: true }
    ];

    var stageX = [100, 280, 460, 640];
    var stageY = 50;
    var stageW = 130;
    var stageH = 50;
    var toggleSize = 18;
    var tableTop = 140;
    var rowH = 22;
    var colW = 70;

    function computePipeline() {
        var rows = allRows.slice();
        var cols = columns.slice();
        var results = [{ rows: rows, cols: cols, count: rows.length }];

        // Filter
        if (stages[0].enabled) {
            rows = rows.filter(function(r) { return r.active; });
        }
        results.push({ rows: rows.slice(), cols: cols.slice(), count: rows.length });

        // Sort
        if (stages[1].enabled) {
            rows.sort(function(a, b) { return b.salary - a.salary; });
        }
        results.push({ rows: rows.slice(), cols: cols.slice(), count: rows.length });

        // Select
        if (stages[2].enabled) {
            cols = ['name', 'dept', 'salary'];
        }
        results.push({ rows: rows.slice(), cols: cols.slice(), count: rows.length });

        // Head
        if (stages[3].enabled) {
            rows = rows.slice(0, 3);
        }
        results.push({ rows: rows.slice(), cols: cols.slice(), count: rows.length });

        return results;
    }

    p.setup = function() {
        var mainEl = document.querySelector('main');
        var canvas = p.createCanvas(canvasWidth, canvasHeight);
        canvas.parent(mainEl);
        p.textFont('Arial');
    };

    p.draw = function() {
        p.background(240, 248, 255);

        // Title
        p.fill(30);
        p.noStroke();
        p.textSize(18);
        p.textAlign(p.CENTER, p.TOP);
        p.text('Relational Operations Pipeline', canvasWidth / 2, 8);

        var pipeline = computePipeline();

        // Draw stages with arrows and toggles
        for (var i = 0; i < stages.length; i++) {
            var sx = stageX[i];
            var enabled = stages[i].enabled;

            // Stage box
            if (enabled) {
                p.fill(teal);
            } else {
                p.fill(180);
            }
            p.stroke(enabled ? tealDark : '#aaa');
            p.strokeWeight(2);
            p.rect(sx, stageY, stageW, stageH, 8);

            p.fill(255);
            p.noStroke();
            p.textSize(14);
            p.textAlign(p.CENTER, p.CENTER);
            p.text(stages[i].name, sx + stageW / 2, stageY + 18);

            p.textSize(9);
            p.fill(enabled ? 230 : 200);
            p.text(stages[i].desc, sx + stageW / 2, stageY + 36);

            // Toggle button
            var tx = sx + stageW / 2 - toggleSize / 2;
            var ty = stageY + stageH + 6;
            p.fill(enabled ? '#2ECC71' : '#E74C3C');
            p.noStroke();
            p.rect(tx, ty, toggleSize, toggleSize, 4);
            p.fill(255);
            p.textSize(11);
            p.textAlign(p.CENTER, p.CENTER);
            p.text(enabled ? 'ON' : 'OFF', tx + toggleSize / 2, ty + toggleSize / 2);

            // Arrow between stages
            if (i < stages.length - 1) {
                var ax1 = sx + stageW + 4;
                var ax2 = stageX[i + 1] - 4;
                var ay = stageY + stageH / 2;
                p.stroke(150);
                p.strokeWeight(2);
                p.line(ax1, ay, ax2, ay);
                // Arrowhead
                p.fill(150);
                p.noStroke();
                p.triangle(ax2, ay, ax2 - 8, ay - 5, ax2 - 8, ay + 5);
            }

            // Row count between stages
            var resultIdx = i + 1;
            if (resultIdx < pipeline.length) {
                var countY = stageY + stageH + 32;
                p.fill(80);
                p.noStroke();
                p.textSize(10);
                p.textAlign(p.CENTER, p.TOP);
                p.text(pipeline[resultIdx].count + ' rows', sx + stageW / 2, countY);
            }
        }

        // Input label
        p.fill(80);
        p.textSize(10);
        p.textAlign(p.CENTER, p.TOP);
        p.text('Input: ' + pipeline[0].count + ' rows', stageX[0] - 60, stageY + stageH / 2 - 5);

        // Draw mini data tables: input + final output
        drawMiniTable(20, tableTop + 80, pipeline[0].cols, pipeline[0].rows, 'Input Data');
        var final = pipeline[pipeline.length - 1];
        drawMiniTable(canvasWidth / 2 + 20, tableTop + 80, final.cols, final.rows, 'Output Data');
    };

    function drawMiniTable(x, y, cols, rows, title) {
        var cw = 70;
        var rh = 20;
        var maxRows = Math.min(rows.length, 8);
        var tableW = cols.length * cw;
        var tableH = (maxRows + 1) * rh + 26;

        // Background
        p.fill(255, 255, 255, 220);
        p.stroke(180);
        p.strokeWeight(1);
        p.rect(x, y, tableW + 16, tableH, 6);

        // Title
        p.fill(50);
        p.noStroke();
        p.textSize(12);
        p.textAlign(p.LEFT, p.TOP);
        p.text(title, x + 8, y + 4);

        var startY = y + 24;

        // Header
        p.fill(tealBg);
        p.noStroke();
        p.rect(x + 8, startY, tableW, rh);
        p.fill(tealDark);
        p.textSize(10);
        p.textAlign(p.CENTER, p.CENTER);
        cols.forEach(function(c, ci) {
            p.text(c, x + 8 + ci * cw + cw / 2, startY + rh / 2);
        });

        // Rows
        for (var ri = 0; ri < maxRows; ri++) {
            var ry = startY + (ri + 1) * rh;
            p.fill(ri % 2 === 0 ? 255 : 248);
            p.noStroke();
            p.rect(x + 8, ry, tableW, rh);

            p.fill(60);
            p.textSize(9);
            cols.forEach(function(c, ci) {
                var val = rows[ri][c];
                if (typeof val === 'boolean') val = val ? 'T' : 'F';
                p.text(String(val), x + 8 + ci * cw + cw / 2, ry + rh / 2);
            });
        }

        // Border
        p.noFill();
        p.stroke(180);
        p.strokeWeight(1);
        p.rect(x + 8, startY, tableW, (maxRows + 1) * rh);
    }

    p.mousePressed = function() {
        // Check toggle clicks
        for (var i = 0; i < stages.length; i++) {
            var tx = stageX[i] + stageW / 2 - toggleSize / 2;
            var ty = stageY + stageH + 6;
            if (p.mouseX >= tx && p.mouseX <= tx + toggleSize &&
                p.mouseY >= ty && p.mouseY <= ty + toggleSize) {
                stages[i].enabled = !stages[i].enabled;
            }
        }
    };
}, document.querySelector('main'));
