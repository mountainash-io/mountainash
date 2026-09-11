// Expression System Composition — Class hierarchy with mixins
// CANVAS_HEIGHT: 500
document.addEventListener('DOMContentLoaded', function() {
    const main = document.querySelector('main');
    main.innerHTML = `
        <div style="position:relative;width:100%;height:500px;background:#f0f8ff;font-family:Arial,sans-serif;">
            <div id="network" style="width:100%;height:100%;"></div>
            <div style="position:absolute;top:10px;left:50%;transform:translateX(-50%);font-size:16px;font-weight:bold;background:rgba(240,248,255,0.9);padding:4px 12px;border-radius:4px;">Expression System Composition</div>
            <div id="legend" style="position:absolute;top:10px;left:10px;background:rgba(255,255,255,0.95);padding:8px;border-radius:8px;font-size:11px;box-shadow:0 2px 4px rgba(0,0,0,0.1);">
                <div style="font-weight:bold;margin-bottom:4px;">Legend</div>
                <div><span style="color:#32CD32;">&#9679;</span> Substrait Mixin</div>
                <div><span style="color:#FFD700;">&#9679;</span> Extension Mixin</div>
                <div><span style="color:#4682B4;">&#9679;</span> Expression System</div>
                <div style="margin-top:4px;font-size:10px;color:#666;">Click a system to<br/>highlight its parents</div>
            </div>
            <div id="info" style="position:absolute;top:50px;right:10px;width:250px;background:rgba(255,255,255,0.95);padding:12px;border-radius:8px;font-size:12px;box-shadow:0 2px 4px rgba(0,0,0,0.1);display:none;"></div>
        </div>
    `;

    // Mixin definitions: Substrait (green) vs Extension (gold)
    var mixins = [
        { id: 'arith',    label: 'Arithmetic\nMixin',   x: 80,  y: 120, type: 'substrait' },
        { id: 'compare',  label: 'Comparison\nMixin',   x: 200, y: 120, type: 'substrait' },
        { id: 'str',      label: 'String\nMixin',       x: 320, y: 120, type: 'substrait' },
        { id: 'datetime', label: 'DateTime\nMixin',     x: 440, y: 120, type: 'substrait' },
        { id: 'window',   label: 'Window\nMixin',       x: 560, y: 120, type: 'substrait' },
        { id: 'name',     label: 'Name\nMixin',         x: 680, y: 120, type: 'extension' },
        { id: 'null',     label: 'Null\nMixin',         x: 200, y: 220, type: 'extension' },
        { id: 'native',   label: 'Native\nMixin',       x: 560, y: 220, type: 'extension' }
    ];

    var systemDefs = [
        { id: 'polars', label: 'Polars\nExpressionSystem', x: 200, y: 380,
          parents: ['arith', 'compare', 'str', 'datetime', 'window', 'name', 'null', 'native'],
          info: '<b>PolarsExpressionSystem</b><br><br>Inherits all 8 mixins. Full Substrait coverage plus extension mixins for name aliasing, null handling, and Polars-native operations.' },
        { id: 'narwhals', label: 'Narwhals\nExpressionSystem', x: 420, y: 380,
          parents: ['arith', 'compare', 'str', 'datetime', 'name', 'null'],
          info: '<b>NarwhalsExpressionSystem</b><br><br>Inherits 6 mixins. Covers core Substrait operations and extension mixins. Window and Native mixins not yet supported via Narwhals.' },
        { id: 'ibis', label: 'Ibis\nExpressionSystem', x: 640, y: 380,
          parents: ['arith', 'compare', 'str', 'datetime', 'window', 'name', 'null'],
          info: '<b>IbisExpressionSystem</b><br><br>Inherits 7 mixins. Full Substrait coverage plus Name and Null extension mixins. Native mixin not applicable (SQL compilation).' }
    ];

    var substraitColor = { background: '#32CD32', border: '#228B22', highlight: { background: '#50E050', border: '#228B22' }, hover: { background: '#50E050', border: '#228B22' } };
    var extensionColor = { background: '#FFD700', border: '#DAA520', highlight: { background: '#FFE44D', border: '#DAA520' }, hover: { background: '#FFE44D', border: '#DAA520' } };
    var systemColor    = { background: '#4682B4', border: '#2C5F8A', highlight: { background: '#5A9BD4', border: '#2C5F8A' }, hover: { background: '#5A9BD4', border: '#2C5F8A' } };
    var dimColor       = { background: '#ddd', border: '#bbb' };

    var nodesList = [];
    mixins.forEach(function(m) {
        var c = m.type === 'substrait' ? substraitColor : extensionColor;
        nodesList.push({
            id: m.id, label: m.label, x: m.x, y: m.y, fixed: true,
            shape: 'box', borderWidth: 2,
            color: c,
            font: { color: '#000', size: 12, multi: true, align: 'center' },
            widthConstraint: { minimum: 100 },
            mixinType: m.type
        });
    });

    systemDefs.forEach(function(s) {
        nodesList.push({
            id: s.id, label: s.label, x: s.x, y: s.y, fixed: true,
            shape: 'box', borderWidth: 2, borderWidthSelected: 3,
            color: systemColor,
            font: { color: '#fff', size: 13, multi: true, bold: true },
            widthConstraint: { minimum: 140 },
            info: s.info, parents: s.parents
        });
    });

    var nodes = new vis.DataSet(nodesList);

    var edgesList = [];
    systemDefs.forEach(function(s) {
        s.parents.forEach(function(pid) {
            edgesList.push({
                from: s.id, to: pid, id: s.id + '-' + pid,
                color: { color: '#aaa', highlight: '#4682B4' },
                width: 1.5,
                arrows: { to: { enabled: true, scaleFactor: 0.6, type: 'triangle' } },
                smooth: { type: 'cubicBezier', forceDirection: 'vertical', roundness: 0.3 }
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
            if (node.parents) {
                if (selectedSystem === nodeId) {
                    selectedSystem = null;
                    infoPanel.style.display = 'none';
                    resetHighlights();
                } else {
                    selectedSystem = nodeId;
                    infoPanel.innerHTML = node.info;
                    infoPanel.style.display = 'block';
                    highlightParents(nodeId, node.parents);
                }
            }
        } else {
            selectedSystem = null;
            infoPanel.style.display = 'none';
            resetHighlights();
        }
    });

    function highlightParents(systemId, parentIds) {
        var edgeUpdates = [];
        edgesList.forEach(function(e) {
            if (e.from === systemId) {
                edgeUpdates.push({ id: e.id, color: { color: '#4682B4' }, width: 3 });
            } else {
                edgeUpdates.push({ id: e.id, color: { color: '#e0e0e0' }, width: 1 });
            }
        });
        edges.update(edgeUpdates);

        var nodeUpdates = [];
        mixins.forEach(function(m) {
            if (parentIds.indexOf(m.id) >= 0) {
                var c = m.type === 'substrait' ? substraitColor : extensionColor;
                nodeUpdates.push({ id: m.id, color: c, font: { color: '#000', size: 12, multi: true, align: 'center' } });
            } else {
                nodeUpdates.push({ id: m.id, color: dimColor, font: { color: '#999', size: 12, multi: true, align: 'center' } });
            }
        });
        systemDefs.forEach(function(s) {
            if (s.id === systemId) {
                nodeUpdates.push({ id: s.id, color: { background: '#3A70A0', border: '#1E3F60' }, font: { color: '#fff', size: 13, multi: true, bold: true } });
            } else {
                nodeUpdates.push({ id: s.id, color: { background: '#B0C4DE', border: '#8899AA' }, font: { color: '#666', size: 13, multi: true, bold: true } });
            }
        });
        nodes.update(nodeUpdates);
    }

    function resetHighlights() {
        var edgeUpdates = [];
        edgesList.forEach(function(e) {
            edgeUpdates.push({ id: e.id, color: { color: '#aaa', highlight: '#4682B4' }, width: 1.5 });
        });
        edges.update(edgeUpdates);

        var nodeUpdates = [];
        mixins.forEach(function(m) {
            var c = m.type === 'substrait' ? substraitColor : extensionColor;
            nodeUpdates.push({ id: m.id, color: c, font: { color: '#000', size: 12, multi: true, align: 'center' } });
        });
        systemDefs.forEach(function(s) {
            nodeUpdates.push({ id: s.id, color: systemColor, font: { color: '#fff', size: 13, multi: true, bold: true } });
        });
        nodes.update(nodeUpdates);
    }
});
