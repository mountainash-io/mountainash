// DAG Container Structure
// CANVAS_HEIGHT: 500
document.addEventListener('DOMContentLoaded', function() {
    const main = document.querySelector('main');
    main.innerHTML = `
        <div style="position:relative;width:100%;height:500px;background:#f0f8ff;font-family:Arial,sans-serif;">
            <div id="network" style="width:100%;height:100%;"></div>
            <div style="position:absolute;top:10px;left:50%;transform:translateX(-50%);font-size:16px;font-weight:bold;background:rgba(240,248,255,0.9);padding:4px 12px;border-radius:4px;">DAG Container Structure</div>
            <div id="legend" style="position:absolute;top:10px;left:10px;background:rgba(255,255,255,0.95);padding:8px;border-radius:8px;font-size:11px;box-shadow:0 2px 4px rgba(0,0,0,0.1);">
                <div style="font-weight:bold;margin-bottom:4px;">Legend</div>
                <div><span style="color:#E67E22;">&#9679;</span> RelationDAG</div>
                <div><span style="color:#D35400;">&#9679;</span> Internal Structures</div>
                <div><span style="color:#F39C12;">&#9679;</span> Named Relations</div>
            </div>
            <div id="info" style="position:absolute;top:50px;right:10px;width:260px;background:rgba(255,255,255,0.95);padding:12px;border-radius:8px;font-size:12px;box-shadow:0 2px 4px rgba(0,0,0,0.1);display:none;"></div>
        </div>
    `;

    var cx = 400, cy = 240;

    function nc(bg, border) {
        return { background: bg, border: border,
            highlight: { background: lighten(bg, 25), border: border },
            hover: { background: lighten(bg, 25), border: border } };
    }

    var nodes = new vis.DataSet([
        // Central node
        { id: 'dag', label: 'RelationDAG', x: cx, y: cy, fixed: true,
          shape: 'box', color: nc('#E67E22', '#A04000'),
          font: { color: '#fff', size: 16, bold: true }, borderWidth: 3, size: 35,
          info: '<b>RelationDAG</b><br><br>The central container that holds all relations, assets, and edge sets. Provides methods for dependency resolution, topological ordering, and validation.<br><br><b>Key methods:</b> add_relation(), collect(), compile(), validate()' },

        // Internal structures (arranged around center)
        { id: 'relations', label: 'relations\ndict', x: cx - 180, y: cy - 100, fixed: true,
          shape: 'box', color: nc('#D35400', '#922B00'),
          font: { color: '#fff', size: 13, multi: true }, borderWidth: 2,
          info: '<b>relations: Dict[str, Relation]</b><br><br>Maps relation names to Relation objects. Each Relation describes a table\'s schema, source, and transformation logic.' },

        { id: 'assets', label: 'assets\ndict', x: cx + 180, y: cy - 100, fixed: true,
          shape: 'box', color: nc('#D35400', '#922B00'),
          font: { color: '#fff', size: 13, multi: true }, borderWidth: 2,
          info: '<b>assets: Dict[str, DataFrame]</b><br><br>Cache of materialized DataFrames. Populated during collect() as each relation is compiled and executed. Acts as a memoization layer.' },

        { id: 'dep-edges', label: 'dependency_edges\nset', x: cx - 180, y: cy + 120, fixed: true,
          shape: 'box', color: nc('#D35400', '#922B00'),
          font: { color: '#fff', size: 13, multi: true }, borderWidth: 2,
          info: '<b>dependency_edges: Set[Tuple[str, str]]</b><br><br>Directed edges representing data-flow dependencies. Edge (A, B) means B depends on A. Used for topological sorting during collect().' },

        { id: 'constraint-edges', label: 'constraint_edges\nset', x: cx + 180, y: cy + 120, fixed: true,
          shape: 'box', color: nc('#D35400', '#922B00'),
          font: { color: '#fff', size: 13, multi: true }, borderWidth: 2,
          info: '<b>constraint_edges: Set[Tuple[str, str, str]]</b><br><br>Foreign-key constraint edges. Each tuple is (child_table, parent_table, fk_field). Used for referential integrity validation after data is loaded.' },

        // Named relations
        { id: 'rel-customers', label: 'customers', x: cx - 280, y: cy - 10, fixed: true,
          shape: 'ellipse', color: nc('#F39C12', '#C77C02'),
          font: { color: '#fff', size: 12 }, borderWidth: 2,
          info: '<b>"customers"</b><br><br>A named relation representing the customers table. Stored as a key in relations dict. May have associated assets and edges.' },

        { id: 'rel-orders', label: 'orders', x: cx, y: cy - 140, fixed: true,
          shape: 'ellipse', color: nc('#F39C12', '#C77C02'),
          font: { color: '#fff', size: 12 }, borderWidth: 2,
          info: '<b>"orders"</b><br><br>A named relation representing the orders table. Depends on customers (FK). Stored in relations dict with corresponding edges in both edge sets.' },

        { id: 'rel-enriched', label: 'enriched', x: cx + 280, y: cy - 10, fixed: true,
          shape: 'ellipse', color: nc('#F39C12', '#C77C02'),
          font: { color: '#fff', size: 12 }, borderWidth: 2,
          info: '<b>"enriched"</b><br><br>A derived relation produced by joining customers and orders. Has dependency edges to both source tables. collect("enriched") triggers the full compilation chain.' }
    ]);

    var edges = new vis.DataSet([
        // DAG -> internal structures
        { from: 'dag', to: 'relations', arrows: 'to', color: { color: '#D35400' }, width: 2.5, label: 'contains', font: { size: 10, color: '#666' } },
        { from: 'dag', to: 'assets', arrows: 'to', color: { color: '#D35400' }, width: 2.5, label: 'contains', font: { size: 10, color: '#666' } },
        { from: 'dag', to: 'dep-edges', arrows: 'to', color: { color: '#D35400' }, width: 2.5, label: 'contains', font: { size: 10, color: '#666' } },
        { from: 'dag', to: 'constraint-edges', arrows: 'to', color: { color: '#D35400' }, width: 2.5, label: 'contains', font: { size: 10, color: '#666' } },

        // Named relations -> structures they belong to
        { from: 'rel-customers', to: 'relations', arrows: 'to', color: { color: '#F39C12' }, width: 1.5, dashes: [5, 5] },
        { from: 'rel-orders', to: 'relations', arrows: 'to', color: { color: '#F39C12' }, width: 1.5, dashes: [5, 5] },
        { from: 'rel-enriched', to: 'relations', arrows: 'to', color: { color: '#F39C12' }, width: 1.5, dashes: [5, 5] },

        { from: 'rel-enriched', to: 'assets', arrows: 'to', color: { color: '#F39C12' }, width: 1.5, dashes: [5, 5] },
        { from: 'rel-customers', to: 'dep-edges', arrows: 'to', color: { color: '#F39C12' }, width: 1.5, dashes: [5, 5] },
        { from: 'rel-orders', to: 'dep-edges', arrows: 'to', color: { color: '#F39C12' }, width: 1.5, dashes: [5, 5] },
        { from: 'rel-orders', to: 'constraint-edges', arrows: 'to', color: { color: '#F39C12' }, width: 1.5, dashes: [5, 5] }
    ]);

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

    function lighten(hex, amt) {
        var num = parseInt(hex.replace('#', ''), 16);
        var r = Math.min(255, (num >> 16) + amt);
        var g = Math.min(255, ((num >> 8) & 0xFF) + amt);
        var b = Math.min(255, (num & 0xFF) + amt);
        return '#' + (0x1000000 + r * 0x10000 + g * 0x100 + b).toString(16).slice(1);
    }
});
