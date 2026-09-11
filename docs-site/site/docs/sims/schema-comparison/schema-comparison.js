// Schema Comparison Workflow — Two-panel field comparison
// CANVAS_HEIGHT: 500
new p5(function(p) {
    var canvasWidth = 800;
    var canvasHeight = 500;
    var hoveredField = null;

    var sourceFields = [
        { name: 'id',          type: 'Int64' },
        { name: 'name',        type: 'Utf8' },
        { name: 'email',       type: 'Utf8' },
        { name: 'age',         type: 'Int32' },
        { name: 'score',       type: 'Float64' },
        { name: 'created_at',  type: 'Date' },
        { name: 'is_active',   type: 'Boolean' }
    ];

    var targetFields = [
        { name: 'id',          type: 'Int64' },
        { name: 'full_name',   type: 'Utf8' },
        { name: 'age',         type: 'Int64' },
        { name: 'score',       type: 'Float64' },
        { name: 'created_at',  type: 'Datetime' },
        { name: 'is_active',   type: 'Boolean' },
        { name: 'department',  type: 'Utf8' }
    ];

    // Mappings: source index -> target index, with status
    var mappings = [
        { si: 0, ti: 0, status: 'match' },       // id -> id (same type)
        { si: 1, ti: 1, status: 'renamed' },      // name -> full_name (renamed, display as match-ish)
        { si: 3, ti: 2, status: 'typechange' },   // age Int32 -> Int64
        { si: 4, ti: 3, status: 'match' },        // score -> score
        { si: 5, ti: 4, status: 'typechange' },   // created_at Date -> Datetime
        { si: 6, ti: 5, status: 'match' }         // is_active -> is_active
    ];

    // Missing from target: email (source index 2)
    var missingFromTarget = [2];
    // Added in target: department (target index 6)
    var addedInTarget = [6];

    var statusColors = {
        match:      '#2ECC71',
        renamed:    '#2ECC71',
        typechange: '#F1C40F',
        missing:    '#E74C3C',
        added:      '#3498DB'
    };

    var panelLeft = 40;
    var panelRight = canvasWidth - 40;
    var panelWidth = 260;
    var panelTop = 80;
    var fieldHeight = 40;
    var fieldGap = 6;

    function fieldY(index) {
        return panelTop + 40 + index * (fieldHeight + fieldGap);
    }

    p.setup = function() {
        var mainEl = document.querySelector('main');
        var canvas = p.createCanvas(canvasWidth, canvasHeight);
        canvas.parent(mainEl);
        p.textFont('Arial');
        p.noLoop();
    };

    p.draw = function() {
        p.background(240, 248, 255);

        // Title
        p.fill(30);
        p.noStroke();
        p.textSize(18);
        p.textAlign(p.CENTER, p.TOP);
        p.text('Schema Comparison', canvasWidth / 2, 12);

        // Legend
        p.textSize(11);
        p.textAlign(p.LEFT, p.CENTER);
        var legendX = canvasWidth / 2 - 140;
        var legendY = 44;
        var legendItems = [
            { label: 'Match', color: statusColors.match },
            { label: 'Type change', color: statusColors.typechange },
            { label: 'Missing', color: statusColors.missing },
            { label: 'Added', color: statusColors.added }
        ];
        legendItems.forEach(function(item, i) {
            var lx = legendX + i * 80;
            p.fill(item.color);
            p.noStroke();
            p.ellipse(lx, legendY, 10, 10);
            p.fill(60);
            p.text(item.label, lx + 8, legendY);
        });

        // Source panel
        drawPanel(panelLeft, panelTop, panelWidth, 'Source TypeSpec', sourceFields, missingFromTarget, 'missing');

        // Target panel
        drawPanel(panelRight - panelWidth, panelTop, panelWidth, 'Target TypeSpec', targetFields, addedInTarget, 'added');

        // Connection lines
        var srcCenterX = panelLeft + panelWidth;
        var tgtCenterX = panelRight - panelWidth;

        mappings.forEach(function(m) {
            var sy = fieldY(m.si) + fieldHeight / 2;
            var ty = fieldY(m.ti) + fieldHeight / 2;
            var col = p.color(statusColors[m.status]);
            p.stroke(col);
            p.strokeWeight(2.5);
            p.noFill();
            // Bezier curve between panels
            var cp = (tgtCenterX - srcCenterX) * 0.4;
            p.bezier(srcCenterX, sy, srcCenterX + cp, sy, tgtCenterX - cp, ty, tgtCenterX, ty);
        });

        // Missing field markers (red X on source side)
        missingFromTarget.forEach(function(si) {
            var sy = fieldY(si) + fieldHeight / 2;
            p.stroke(statusColors.missing);
            p.strokeWeight(3);
            var mx = srcCenterX + 20;
            p.line(mx - 6, sy - 6, mx + 6, sy + 6);
            p.line(mx - 6, sy + 6, mx + 6, sy - 6);
        });

        // Added field markers (blue + on target side)
        addedInTarget.forEach(function(ti) {
            var ty = fieldY(ti) + fieldHeight / 2;
            p.stroke(statusColors.added);
            p.strokeWeight(3);
            var mx = tgtCenterX - 20;
            p.line(mx - 6, ty, mx + 6, ty);
            p.line(mx, ty - 6, mx, ty + 6);
        });
    };

    function drawPanel(x, y, w, title, fields, markedIndices, markType) {
        // Panel background
        p.fill(255, 255, 255, 230);
        p.stroke(180);
        p.strokeWeight(1);
        p.rect(x, y, w, 40 + fields.length * (fieldHeight + fieldGap) + 10, 8);

        // Panel title
        p.fill(50);
        p.noStroke();
        p.textSize(14);
        p.textAlign(p.CENTER, p.CENTER);
        p.text(title, x + w / 2, y + 20);

        // Fields
        fields.forEach(function(f, i) {
            var fy = fieldY(i);
            var isMarked = markedIndices.indexOf(i) >= 0;
            var bg;
            if (isMarked) {
                bg = markType === 'missing' ? p.color(255, 200, 200) : p.color(200, 220, 255);
            } else {
                bg = p.color(245, 248, 252);
            }

            p.fill(bg);
            p.stroke(200);
            p.strokeWeight(1);
            p.rect(x + 10, fy, w - 20, fieldHeight, 4);

            p.fill(30);
            p.noStroke();
            p.textSize(12);
            p.textAlign(p.LEFT, p.CENTER);
            p.text(f.name, x + 18, fy + fieldHeight / 2);

            p.fill(100);
            p.textSize(10);
            p.textAlign(p.RIGHT, p.CENTER);
            p.text(f.type, x + w - 18, fy + fieldHeight / 2);
        });
    }
}, document.querySelector('main'));
