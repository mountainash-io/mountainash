// Protocol-System Composition — UML-style class diagram
// CANVAS_HEIGHT: 500
document.addEventListener('DOMContentLoaded', function() {
    const main = document.querySelector('main');
    main.innerHTML = `
        <div style="position:relative;width:100%;height:500px;background:#f0f8ff;font-family:Arial,sans-serif;">
            <div id="network" style="width:100%;height:100%;"></div>
            <div style="position:absolute;top:10px;left:50%;transform:translateX(-50%);font-size:16px;font-weight:bold;background:rgba(240,248,255,0.9);padding:4px 12px;border-radius:4px;">Protocol–System Composition</div>
            <div id="legend" style="position:absolute;top:10px;left:10px;background:rgba(255,255,255,0.95);padding:8px;border-radius:8px;font-size:11px;box-shadow:0 2px 4px rgba(0,0,0,0.1);">
                <div style="font-weight:bold;margin-bottom:4px;">Legend</div>
                <div><span style="color:#32CD32;">&#9679;</span> Protocol</div>
                <div><span style="color:#FFD700;">&#9679;</span> Expression System</div>
                <div style="margin-top:4px;font-size:10px;color:#666;">Click a system to see<br/>which protocols it satisfies</div>
            </div>
            <div id="info" style="position:absolute;top:50px;right:10px;width:260px;background:rgba(255,255,255,0.95);padding:12px;border-radius:8px;font-size:12px;box-shadow:0 2px 4px rgba(0,0,0,0.1);display:none;"></div>
        </div>
    `;

    var W = 800;
    var protocolY = 100;
    var systemY = 360;

    var protocols = [
        { id: 'scalar-arith', label: '<<protocol>>\nScalarArithmetic\nProtocol', x: 100 },
        { id: 'scalar-cmp',   label: '<<protocol>>\nScalarComparison\nProtocol', x: 300 },
        { id: 'scalar-str',   label: '<<protocol>>\nScalarString\nProtocol',     x: 500 },
        { id: 'window',       label: '<<protocol>>\nWindow\nProtocol',           x: 700 }
    ];

    var systems = [
        { id: 'polars', label: 'PolarsExpression\nSystem', x: 200,
          satisfies: ['scalar-arith', 'scalar-cmp', 'scalar-str', 'window'],
          info: '<b>PolarsExpressionSystem</b><br><br>Satisfies all four protocols. Maps each protocol method to native Polars Expr operations for maximum performance.' },
        { id: 'narwhals', label: 'NarwhalsExpression\nSystem', x: 400,
          satisfies: ['scalar-arith', 'scalar-cmp', 'scalar-str'],
          info: '<b>NarwhalsExpressionSystem</b><br><br>Satisfies Arithmetic, Comparison, and String protocols via Narwhals\' cross-backend API. Window protocol not yet supported.' },
        { id: 'ibis', label: 'IbisExpression\nSystem', x: 600,
          satisfies: ['scalar-arith', 'scalar-cmp', 'window'],
          info: '<b>IbisExpressionSystem</b><br><br>Satisfies Arithmetic, Comparison, and Window protocols. Compiles to SQL backends. String protocol support planned.' }
    ];

    var nodesList = [];

    protocols.forEach(function(p) {
        nodesList.push({
            id: p.id, label: p.label, x: p.x, y: protocolY, fixed: true,
            shape: 'box', borderWidth: 2, borderWidthSelected: 3,
            color: { background: '#32CD32', border: '#228B22',
                     highlight: { background: '#50E050', border: '#228B22' },
                     hover: { background: '#50E050', border: '#228B22' } },
            font: { color: '#000', size: 12, multi: true, align: 'center' },
            widthConstraint: { minimum: 140 }
        });
    });

    systems.forEach(function(s) {
        nodesList.push({
            id: s.id, label: s.label, x: s.x, y: systemY, fixed: true,
            shape: 'box', borderWidth: 2, borderWidthSelected: 3,
            color: { background: '#FFD700', border: '#DAA520',
                     highlight: { background: '#FFE44D', border: '#DAA520' },
                     hover: { background: '#FFE44D', border: '#DAA520' } },
            font: { color: '#000', size: 13, multi: true, bold: true },
            widthConstraint: { minimum: 140 },
            info: s.info, satisfies: s.satisfies
        });
    });

    var nodes = new vis.DataSet(nodesList);

    var edgesList = [];
    systems.forEach(function(s) {
        s.satisfies.forEach(function(pid) {
            edgesList.push({
                from: s.id, to: pid, id: s.id + '-' + pid,
                dashes: [8, 4],
                color: { color: '#999', highlight: '#32CD32', hover: '#999' },
                width: 1.5,
                arrows: { to: { enabled: true, scaleFactor: 0.7, type: 'vee' } },
                smooth: { type: 'cubicBezier', forceDirection: 'vertical', roundness: 0.4 }
            });
        });
    });
    var edges = new vis.DataSet(edgesList);

    var container = document.getElementById('network');
    var network = new vis.Network(container, { nodes: nodes, edges: edges }, {
        interaction: { zoomView: false, dragView: false, dragNodes: false, hover: true },
        physics: { enabled: false },
        layout: { improvedLayout: false }
    });

    var infoPanel = document.getElementById('info');
    var selectedSystem = null;

    network.on('click', function(params) {
        if (params.nodes.length > 0) {
            var nodeId = params.nodes[0];
            var node = nodes.get(nodeId);
            if (node.satisfies) {
                // It's a system node
                if (selectedSystem === nodeId) {
                    // Deselect
                    selectedSystem = null;
                    infoPanel.style.display = 'none';
                    resetEdgeColors();
                } else {
                    selectedSystem = nodeId;
                    infoPanel.innerHTML = node.info;
                    infoPanel.style.display = 'block';
                    highlightEdges(nodeId, node.satisfies);
                }
            }
        } else {
            selectedSystem = null;
            infoPanel.style.display = 'none';
            resetEdgeColors();
        }
    });

    function highlightEdges(systemId, satisfiedProtocols) {
        var updates = [];
        edgesList.forEach(function(e) {
            if (e.from === systemId) {
                updates.push({ id: e.id, color: { color: '#32CD32', highlight: '#32CD32' }, width: 3, dashes: false });
            } else {
                updates.push({ id: e.id, color: { color: '#ddd', highlight: '#ddd' }, width: 1, dashes: [8, 4] });
            }
        });
        edges.update(updates);

        // Dim non-related protocols
        var nodeUpdates = [];
        protocols.forEach(function(p) {
            if (satisfiedProtocols.indexOf(p.id) >= 0) {
                nodeUpdates.push({ id: p.id, color: { background: '#32CD32', border: '#228B22' }, font: { color: '#000', size: 12, multi: true, align: 'center' } });
            } else {
                nodeUpdates.push({ id: p.id, color: { background: '#ccc', border: '#999' }, font: { color: '#666', size: 12, multi: true, align: 'center' } });
            }
        });
        nodes.update(nodeUpdates);
    }

    function resetEdgeColors() {
        var updates = [];
        edgesList.forEach(function(e) {
            updates.push({ id: e.id, color: { color: '#999', highlight: '#32CD32' }, width: 1.5, dashes: [8, 4] });
        });
        edges.update(updates);

        var nodeUpdates = [];
        protocols.forEach(function(p) {
            nodeUpdates.push({ id: p.id, color: { background: '#32CD32', border: '#228B22' }, font: { color: '#000', size: 12, multi: true, align: 'center' } });
        });
        nodes.update(nodeUpdates);
    }
});
