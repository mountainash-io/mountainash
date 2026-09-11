// DAG Validation Phases
// CANVAS_HEIGHT: 500
document.addEventListener('DOMContentLoaded', function() {
    const main = document.querySelector('main');
    main.innerHTML = `
        <div style="position:relative;width:100%;height:500px;background:#f0f8ff;font-family:Arial,sans-serif;">
            <div id="network" style="width:100%;height:100%;"></div>
            <div style="position:absolute;top:10px;left:50%;transform:translateX(-50%);font-size:16px;font-weight:bold;background:rgba(240,248,255,0.9);padding:4px 12px;border-radius:4px;">DAG Validation Phases</div>
            <div id="controls" style="position:absolute;top:10px;left:10px;background:rgba(255,255,255,0.95);padding:10px;border-radius:8px;font-size:13px;box-shadow:0 2px 4px rgba(0,0,0,0.1);">
                <div style="font-weight:bold;margin-bottom:6px;">Validation Mode</div>
                <label style="display:block;margin-bottom:4px;cursor:pointer;">
                    <input type="radio" name="mode" value="full" checked> Full (Phase 1 + 2)
                </label>
                <label style="display:block;cursor:pointer;">
                    <input type="radio" name="mode" value="quick"> Quick (Phase 1 only)
                </label>
            </div>
            <div id="info" style="position:absolute;top:50px;right:10px;width:240px;background:rgba(255,255,255,0.95);padding:12px;border-radius:8px;font-size:12px;box-shadow:0 2px 4px rgba(0,0,0,0.1);display:none;"></div>
        </div>
    `;

    // Two-column layout
    var col1X = 200; // Phase 1 center
    var col2X = 600; // Phase 2 center
    var startY = 100;

    function nc(bg, border) {
        return { background: bg, border: border,
            highlight: { background: lighten(bg, 20), border: border },
            hover: { background: lighten(bg, 20), border: border } };
    }

    var phase1Color = nc('#E67E22', '#A04000');
    var phase2Color = nc('#D35400', '#922B00');
    var cacheColor = nc('#27AE60', '#1E8449');
    var disabledColor = nc('#BDC3C7', '#95A5A6');

    var allNodes = [
        // Phase 1 header
        { id: 'p1-header', label: 'Phase 1\nTable Validation', x: col1X, y: startY, fixed: true,
          shape: 'box', color: nc('#A04000', '#7A2E00'),
          font: { color: '#fff', size: 14, bold: true, multi: true }, borderWidth: 3,
          info: '<b>Phase 1: Per-Table Validation</b><br><br>Validates each resource independently: schema conformance, type checking, null constraints, unique constraints, and format validation. Always runs.' },

        // Per-resource validation nodes
        { id: 'val-customers', label: 'validate\ncustomers', x: col1X - 90, y: startY + 90, fixed: true,
          shape: 'box', color: phase1Color,
          font: { color: '#fff', size: 12, multi: true }, borderWidth: 2,
          info: '<b>Validate "customers"</b><br><br>Checks schema: id (integer, unique), name (string, required), email (string, format:email). Reports row-level errors.' },

        { id: 'val-orders', label: 'validate\norders', x: col1X + 90, y: startY + 90, fixed: true,
          shape: 'box', color: phase1Color,
          font: { color: '#fff', size: 12, multi: true }, borderWidth: 2,
          info: '<b>Validate "orders"</b><br><br>Checks schema: id (integer, unique), customer_id (integer, required), total (number, >=0). Reports row-level errors.' },

        { id: 'val-items', label: 'validate\norder_items', x: col1X, y: startY + 180, fixed: true,
          shape: 'box', color: phase1Color,
          font: { color: '#fff', size: 12, multi: true }, borderWidth: 2,
          info: '<b>Validate "order_items"</b><br><br>Checks schema: id (integer, unique), order_id (integer, required), product (string), qty (integer, >0). Reports row-level errors.' },

        // Cached DataFrames (middle)
        { id: 'cache', label: 'Cached\nDataFrames', x: (col1X + col2X) / 2, y: startY + 130, fixed: true,
          shape: 'box', color: cacheColor,
          font: { color: '#fff', size: 13, multi: true }, borderWidth: 2,
          info: '<b>Cached DataFrames</b><br><br>After Phase 1 passes, validated DataFrames are cached. Phase 2 reads from cache for cross-table FK integrity checks.' },

        // Phase 2 header
        { id: 'p2-header', label: 'Phase 2\nFK Integrity', x: col2X, y: startY, fixed: true,
          shape: 'box', color: nc('#922B00', '#6B1E00'), phase: 2,
          font: { color: '#fff', size: 14, bold: true, multi: true }, borderWidth: 3,
          info: '<b>Phase 2: Foreign Key Integrity</b><br><br>Cross-table validation: checks that every FK value in a child table references an existing PK in the parent table. Only runs in Full mode.' },

        // FK check nodes
        { id: 'fk-orders-customers', label: 'FK check\norders.customer_id\n-> customers.id', x: col2X - 70, y: startY + 110, fixed: true,
          shape: 'box', color: phase2Color, phase: 2,
          font: { color: '#fff', size: 11, multi: true }, borderWidth: 2,
          info: '<b>FK: orders.customer_id -> customers.id</b><br><br>Verifies every customer_id in orders exists in customers.id. Reports orphaned rows with their row numbers and values.' },

        { id: 'fk-items-orders', label: 'FK check\norder_items.order_id\n-> orders.id', x: col2X + 70, y: startY + 110, fixed: true,
          shape: 'box', color: phase2Color, phase: 2,
          font: { color: '#fff', size: 11, multi: true }, borderWidth: 2,
          info: '<b>FK: order_items.order_id -> orders.id</b><br><br>Verifies every order_id in order_items exists in orders.id. Reports orphaned rows with their row numbers and values.' },

        // Result nodes
        { id: 'result-p1', label: 'Phase 1\nResult', x: col1X, y: startY + 300, fixed: true,
          shape: 'ellipse', color: cacheColor,
          font: { color: '#fff', size: 12, multi: true }, borderWidth: 2,
          info: '<b>Phase 1 Result</b><br><br>Summary of per-table validation: pass/fail per resource, total error count, error details by table and row.' },

        { id: 'result-p2', label: 'Phase 2\nResult', x: col2X, y: startY + 300, fixed: true,
          shape: 'ellipse', color: cacheColor, phase: 2,
          font: { color: '#fff', size: 12, multi: true }, borderWidth: 2,
          info: '<b>Phase 2 Result</b><br><br>Summary of FK integrity: pass/fail per constraint edge, list of orphaned values per FK relationship.' },

        { id: 'final', label: 'ValidationReport', x: (col1X + col2X) / 2, y: startY + 380, fixed: true,
          shape: 'box', color: nc('#A04000', '#7A2E00'),
          font: { color: '#fff', size: 14, bold: true }, borderWidth: 3,
          info: '<b>ValidationReport</b><br><br>Combined report from both phases. In Quick mode, Phase 2 results are empty. Overall pass requires all phases to pass.' }
    ];

    var allEdges = [
        // Phase 1 flow
        { id: 'e-p1-cust', from: 'p1-header', to: 'val-customers', arrows: 'to', color: { color: '#E67E22' }, width: 2 },
        { id: 'e-p1-ord', from: 'p1-header', to: 'val-orders', arrows: 'to', color: { color: '#E67E22' }, width: 2 },
        { id: 'e-p1-items', from: 'p1-header', to: 'val-items', arrows: 'to', color: { color: '#E67E22' }, width: 2 },

        // To cache
        { id: 'e-cust-cache', from: 'val-customers', to: 'cache', arrows: 'to', color: { color: '#27AE60' }, width: 1.5 },
        { id: 'e-ord-cache', from: 'val-orders', to: 'cache', arrows: 'to', color: { color: '#27AE60' }, width: 1.5 },
        { id: 'e-items-cache', from: 'val-items', to: 'cache', arrows: 'to', color: { color: '#27AE60' }, width: 1.5 },

        // Cache to Phase 2
        { id: 'e-cache-fk1', from: 'cache', to: 'fk-orders-customers', arrows: 'to', color: { color: '#D35400' }, width: 2, phase: 2 },
        { id: 'e-cache-fk2', from: 'cache', to: 'fk-items-orders', arrows: 'to', color: { color: '#D35400' }, width: 2, phase: 2 },

        // Phase 2 header
        { id: 'e-p2-fk1', from: 'p2-header', to: 'fk-orders-customers', arrows: 'to', color: { color: '#D35400' }, width: 2, phase: 2 },
        { id: 'e-p2-fk2', from: 'p2-header', to: 'fk-items-orders', arrows: 'to', color: { color: '#D35400' }, width: 2, phase: 2 },

        // To results
        { id: 'e-val-r1', from: 'val-customers', to: 'result-p1', arrows: 'to', color: { color: '#27AE60' }, width: 1.5 },
        { id: 'e-val-r1b', from: 'val-orders', to: 'result-p1', arrows: 'to', color: { color: '#27AE60' }, width: 1.5 },
        { id: 'e-val-r1c', from: 'val-items', to: 'result-p1', arrows: 'to', color: { color: '#27AE60' }, width: 1.5 },

        { id: 'e-fk-r2a', from: 'fk-orders-customers', to: 'result-p2', arrows: 'to', color: { color: '#27AE60' }, width: 1.5, phase: 2 },
        { id: 'e-fk-r2b', from: 'fk-items-orders', to: 'result-p2', arrows: 'to', color: { color: '#27AE60' }, width: 1.5, phase: 2 },

        // Results to final
        { id: 'e-r1-final', from: 'result-p1', to: 'final', arrows: 'to', color: { color: '#A04000' }, width: 2.5 },
        { id: 'e-r2-final', from: 'result-p2', to: 'final', arrows: 'to', color: { color: '#A04000' }, width: 2.5, phase: 2 }
    ];

    var nodes = new vis.DataSet(allNodes);
    var edges = new vis.DataSet(allEdges);

    var container = document.getElementById('network');
    var network = new vis.Network(container, { nodes: nodes, edges: edges }, {
        interaction: { zoomView: false, dragView: false, dragNodes: false, hover: true },
        physics: { enabled: false },
        layout: { improvedLayout: false }
    });

    var infoPanel = document.getElementById('info');

    network.on('hoverNode', function(params) {
        var node = nodes.get(params.node);
        if (node && node.info) {
            infoPanel.innerHTML = node.info;
            infoPanel.style.display = 'block';
        }
    });

    network.on('blurNode', function() {
        infoPanel.style.display = 'none';
    });

    // Mode toggle
    var radios = document.querySelectorAll('input[name="mode"]');
    radios.forEach(function(radio) {
        radio.addEventListener('change', function() {
            var isQuick = this.value === 'quick';
            // Update Phase 2 nodes
            allNodes.forEach(function(n) {
                if (n.phase === 2) {
                    nodes.update({ id: n.id,
                        color: isQuick ? disabledColor : (n.id === 'p2-header' ? nc('#922B00', '#6B1E00') : (n.id === 'result-p2' ? cacheColor : phase2Color)),
                        font: { color: isQuick ? '#999' : '#fff', size: n.font.size, bold: n.font.bold, multi: n.font.multi }
                    });
                }
            });
            // Update Phase 2 edges
            allEdges.forEach(function(e) {
                if (e.phase === 2) {
                    edges.update({ id: e.id,
                        color: { color: isQuick ? '#BDC3C7' : e.color.color },
                        dashes: isQuick ? [4, 4] : false
                    });
                }
            });
        });
    });

    function lighten(hex, amt) {
        var num = parseInt(hex.replace('#', ''), 16);
        var r = Math.min(255, (num >> 16) + amt);
        var g = Math.min(255, ((num >> 8) & 0xFF) + amt);
        var b = Math.min(255, (num & 0xFF) + amt);
        return '#' + (0x1000000 + r * 0x10000 + g * 0x100 + b).toString(16).slice(1);
    }
});
