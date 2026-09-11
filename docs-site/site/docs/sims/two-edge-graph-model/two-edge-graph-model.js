// Two-Edge Graph Model
// CANVAS_HEIGHT: 500
document.addEventListener('DOMContentLoaded', function() {
    const main = document.querySelector('main');
    main.innerHTML = `
        <div style="position:relative;width:100%;height:500px;background:#f0f8ff;font-family:Arial,sans-serif;">
            <div id="network" style="width:100%;height:100%;"></div>
            <div style="position:absolute;top:10px;left:50%;transform:translateX(-50%);font-size:16px;font-weight:bold;background:rgba(240,248,255,0.9);padding:4px 12px;border-radius:4px;">Two-Edge Graph Model</div>
            <div id="controls" style="position:absolute;top:10px;left:10px;background:rgba(255,255,255,0.95);padding:10px;border-radius:8px;font-size:13px;box-shadow:0 2px 4px rgba(0,0,0,0.1);">
                <div style="font-weight:bold;margin-bottom:6px;">Edge Types</div>
                <label style="display:block;margin-bottom:4px;cursor:pointer;">
                    <input type="checkbox" id="toggle-dep" checked> <span style="color:#2980B9;">&#9644;&#9644;</span> Dependency (data-flow)
                </label>
                <label style="display:block;cursor:pointer;">
                    <input type="checkbox" id="toggle-fk" checked> <span style="color:#E67E22;">- - -</span> Constraint (FK)
                </label>
            </div>
            <div id="info" style="position:absolute;bottom:10px;left:50%;transform:translateX(-50%);background:rgba(255,255,255,0.95);padding:8px 16px;border-radius:8px;font-size:12px;box-shadow:0 2px 4px rgba(0,0,0,0.1);text-align:center;"></div>
        </div>
    `;

    var cx = 400, topY = 140, botLeftX = 250, botRightX = 550, botY = 360;

    function nc(bg, border) {
        return { background: bg, border: border,
            highlight: { background: lighten(bg, 20), border: border },
            hover: { background: lighten(bg, 20), border: border } };
    }

    var nodes = new vis.DataSet([
        { id: 'customers', label: 'customers\n(id, name, email)', x: cx, y: topY, fixed: true,
          shape: 'box', color: nc('#2C3E50', '#1A252F'),
          font: { color: '#fff', size: 14, multi: true }, borderWidth: 2 },

        { id: 'orders', label: 'orders\n(id, customer_id, total)', x: botLeftX, y: botY, fixed: true,
          shape: 'box', color: nc('#2C3E50', '#1A252F'),
          font: { color: '#fff', size: 14, multi: true }, borderWidth: 2 },

        { id: 'order_items', label: 'order_items\n(id, order_id, product, qty)', x: botRightX, y: botY, fixed: true,
          shape: 'box', color: nc('#2C3E50', '#1A252F'),
          font: { color: '#fff', size: 14, multi: true }, borderWidth: 2 }
    ]);

    // Dependency edges (solid blue): data-flow direction
    var depEdges = [
        { id: 'dep-oc', from: 'customers', to: 'orders', arrows: 'to',
          color: { color: '#2980B9', highlight: '#2980B9', hover: '#2980B9' },
          width: 3, label: 'dependency', font: { size: 10, color: '#2980B9' },
          smooth: { type: 'curvedCW', roundness: 0.15 } },
        { id: 'dep-oi', from: 'orders', to: 'order_items', arrows: 'to',
          color: { color: '#2980B9', highlight: '#2980B9', hover: '#2980B9' },
          width: 3, label: 'dependency', font: { size: 10, color: '#2980B9' },
          smooth: { type: 'curvedCW', roundness: 0.15 } }
    ];

    // Constraint edges (dashed orange): FK references
    var fkEdges = [
        { id: 'fk-oc', from: 'orders', to: 'customers', arrows: 'to',
          color: { color: '#E67E22', highlight: '#E67E22', hover: '#E67E22' },
          width: 2.5, dashes: [8, 4], label: 'FK: customer_id', font: { size: 10, color: '#E67E22' },
          smooth: { type: 'curvedCCW', roundness: 0.15 } },
        { id: 'fk-oio', from: 'order_items', to: 'orders', arrows: 'to',
          color: { color: '#E67E22', highlight: '#E67E22', hover: '#E67E22' },
          width: 2.5, dashes: [8, 4], label: 'FK: order_id', font: { size: 10, color: '#E67E22' },
          smooth: { type: 'curvedCCW', roundness: 0.15 } }
    ];

    var edges = new vis.DataSet([...depEdges, ...fkEdges]);

    var container = document.getElementById('network');
    var network = new vis.Network(container, { nodes: nodes, edges: edges }, {
        interaction: { zoomView: false, dragView: false, dragNodes: false, hover: true },
        physics: { enabled: false },
        layout: { improvedLayout: false }
    });

    var infoEl = document.getElementById('info');
    infoEl.innerHTML = 'Toggle checkboxes to show/hide edge types independently. <b>Solid blue</b> = dependency (data-flow). <b>Dashed orange</b> = constraint (FK).';

    // Toggle handlers
    document.getElementById('toggle-dep').addEventListener('change', function() {
        var show = this.checked;
        depEdges.forEach(function(e) {
            if (show) {
                try { edges.add(e); } catch(ex) { /* already exists */ }
            } else {
                edges.remove(e.id);
            }
        });
    });

    document.getElementById('toggle-fk').addEventListener('change', function() {
        var show = this.checked;
        fkEdges.forEach(function(e) {
            if (show) {
                try { edges.add(e); } catch(ex) { /* already exists */ }
            } else {
                edges.remove(e.id);
            }
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
