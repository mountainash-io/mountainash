// Relation System Composition
// CANVAS_HEIGHT: 500
document.addEventListener('DOMContentLoaded', function() {
    const main = document.querySelector('main');
    main.innerHTML = `
        <div style="position:relative;width:100%;height:500px;background:#f0f8ff;font-family:Arial,sans-serif;">
            <div id="network" style="width:100%;height:100%;"></div>
            <div style="position:absolute;top:10px;left:50%;transform:translateX(-50%);font-size:16px;font-weight:bold;background:rgba(240,248,255,0.9);padding:4px 12px;border-radius:4px;">Relation System Composition</div>
            <div id="legend" style="position:absolute;top:10px;left:10px;background:rgba(255,255,255,0.95);padding:8px;border-radius:8px;font-size:11px;box-shadow:0 2px 4px rgba(0,0,0,0.1);">
                <div style="font-weight:bold;margin-bottom:4px;">Legend</div>
                <div><span style="color:#008080;">&#9679;</span> Base / Protocol</div>
                <div><span style="color:#DAA520;">&#9679;</span> Concrete System</div>
                <div><span style="color:#6A5ACD;">&#9679;</span> Registry</div>
            </div>
            <div id="info" style="position:absolute;top:10px;right:10px;width:250px;background:rgba(255,255,255,0.95);padding:12px;border-radius:8px;font-size:12px;box-shadow:0 2px 4px rgba(0,0,0,0.1);display:none;"></div>
        </div>
    `;

    var teal = '#008080';
    var gold = '#DAA520';
    var purple = '#6A5ACD';
    var cx = 370;

    var protocols = [
        { id: 'read-p', label: 'ReadProtocol' },
        { id: 'filter-p', label: 'FilterProtocol' },
        { id: 'project-p', label: 'ProjectProtocol' },
        { id: 'aggregate-p', label: 'AggregateProtocol' },
        { id: 'join-p', label: 'JoinProtocol' },
        { id: 'sort-p', label: 'SortProtocol' },
        { id: 'fetch-p', label: 'FetchProtocol' },
        { id: 'set-p', label: 'SetProtocol' },
        { id: 'conform-p', label: 'ConformProtocol' }
    ];

    var systems = [
        { id: 'polars', label: 'PolarsRelation\nSystem', info: '<b>PolarsRelationSystem</b><br><br>Implements all protocols using Polars LazyFrame API. Preferred backend for local data processing with automatic query optimization.' },
        { id: 'narwhals', label: 'NarwhalsRelation\nSystem', info: '<b>NarwhalsRelationSystem</b><br><br>Implements protocols via Narwhals compatibility layer. Supports pandas, cuDF, and other eager backends through a unified API.' },
        { id: 'ibis', label: 'IbisRelation\nSystem', info: '<b>IbisRelationSystem</b><br><br>Compiles relation operations to SQL via Ibis expressions. Targets DuckDB, BigQuery, Spark, and other SQL backends.' }
    ];

    var nodeData = [];
    var edgeData = [];

    // Base class
    nodeData.push({
        id: 'base', label: 'RelationSystem\n(base class)', x: cx, y: 50, fixed: true, shape: 'box',
        color: { background: teal, border: '#006060' }, font: { color: '#fff', size: 14, multi: true }, borderWidth: 2,
        info: '<b>RelationSystem</b><br><br>Abstract base class that defines the interface all relation backends must implement. Uses protocol mixins for each operation type.'
    });

    // Protocol mixins in two rows
    protocols.forEach(function(p, i) {
        var row = i < 5 ? 0 : 1;
        var col = i < 5 ? i : i - 5;
        var count = i < 5 ? 5 : 4;
        var startX = cx - (count - 1) * 75 / 2;
        nodeData.push({
            id: p.id, label: p.label, x: startX + col * 75, y: 140 + row * 60, fixed: true, shape: 'box',
            color: { background: teal, border: '#006060', highlight: { background: '#20B2AA', border: '#006060' }, hover: { background: '#20B2AA', border: '#006060' } },
            font: { color: '#fff', size: 10 }, borderWidth: 1,
            info: '<b>' + p.label + '</b><br><br>Protocol mixin defining the ' + p.label.replace('Protocol', '').toLowerCase() + ' operation interface.'
        });
        edgeData.push({ from: 'base', to: p.id, color: { color: '#999' }, width: 1, arrows: { to: { enabled: true, scaleFactor: 0.5 } } });
    });

    // Concrete systems
    systems.forEach(function(s, i) {
        var startX = cx - (systems.length - 1) * 140 / 2;
        nodeData.push({
            id: s.id, label: s.label, x: startX + i * 140, y: 330, fixed: true, shape: 'box',
            color: { background: gold, border: '#B8860B', highlight: { background: '#FFD700', border: '#B8860B' }, hover: { background: '#FFD700', border: '#B8860B' } },
            font: { color: '#fff', size: 12, multi: true }, borderWidth: 2,
            info: s.info
        });
        // Inheritance edges from all protocols
        edgeData.push({ from: 'base', to: s.id, color: { color: gold, opacity: 0.6 }, width: 2, dashes: [8, 4], arrows: { to: { enabled: true, scaleFactor: 0.7 } }, smooth: { type: 'curvedCW', roundness: 0.15 * (i - 1) } });
    });

    // Registry nodes
    nodeData.push({
        id: 'decorator', label: '@register_relation_system', x: 680, y: 280, fixed: true, shape: 'box',
        color: { background: purple, border: '#483D8B', highlight: { background: '#7B68EE', border: '#483D8B' }, hover: { background: '#7B68EE', border: '#483D8B' } },
        font: { color: '#fff', size: 11 }, borderWidth: 2,
        info: '<b>@register_relation_system</b><br><br>Decorator that registers a RelationSystem subclass in the global registry with a unique backend key.'
    });
    nodeData.push({
        id: 'lookup', label: 'get_relation_system()', x: 680, y: 360, fixed: true, shape: 'box',
        color: { background: purple, border: '#483D8B', highlight: { background: '#7B68EE', border: '#483D8B' }, hover: { background: '#7B68EE', border: '#483D8B' } },
        font: { color: '#fff', size: 11 }, borderWidth: 2,
        info: '<b>get_relation_system()</b><br><br>Looks up a registered RelationSystem by backend key. Used by auto-detection and explicit backend selection.'
    });
    edgeData.push({ from: 'decorator', to: 'lookup', color: { color: purple }, width: 1.5, arrows: { to: { enabled: true, scaleFactor: 0.5 } }, label: 'populates', font: { size: 9, color: '#666' } });
    systems.forEach(function(s) {
        edgeData.push({ from: s.id, to: 'decorator', color: { color: purple, opacity: 0.4 }, width: 1, dashes: [4, 4], arrows: { to: { enabled: true, scaleFactor: 0.4 } } });
    });

    var nodes = new vis.DataSet(nodeData);
    var edges = new vis.DataSet(edgeData);

    var container = document.getElementById('network');
    var network = new vis.Network(container, { nodes: nodes, edges: edges }, {
        interaction: { zoomView: false, dragView: false, dragNodes: false, hover: true },
        physics: { enabled: false },
        layout: { improvedLayout: false }
    });

    var infoPanel = document.getElementById('info');
    network.on('click', function(params) {
        if (params.nodes.length > 0) {
            var node = nodes.get(params.nodes[0]);
            if (node && node.info) { infoPanel.innerHTML = node.info; infoPanel.style.display = 'block'; }
        } else { infoPanel.style.display = 'none'; }
    });
});
