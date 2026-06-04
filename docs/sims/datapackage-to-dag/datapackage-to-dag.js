// DataPackage to DAG Conversion Flow
// CANVAS_HEIGHT: 500
document.addEventListener('DOMContentLoaded', function() {
    const main = document.querySelector('main');
    main.innerHTML = `
        <div style="position:relative;width:100%;height:500px;background:#f0f8ff;font-family:Arial,sans-serif;">
            <div id="network" style="width:100%;height:100%;"></div>
            <div style="position:absolute;top:10px;left:50%;transform:translateX(-50%);font-size:16px;font-weight:bold;background:rgba(240,248,255,0.9);padding:4px 12px;border-radius:4px;">DataPackage to RelationDAG</div>
            <div id="legend" style="position:absolute;top:10px;left:10px;background:rgba(255,255,255,0.95);padding:8px;border-radius:8px;font-size:11px;box-shadow:0 2px 4px rgba(0,0,0,0.1);">
                <div style="font-weight:bold;margin-bottom:4px;">Legend</div>
                <div><span style="color:#E67E22;">&#9679;</span> Primary path</div>
                <div><span style="color:#8E44AD;">&#9679;</span> Override path</div>
                <div>&#8594; Solid = main flow</div>
                <div>- - &#8594; Dashed = override</div>
            </div>
            <div id="info" style="position:absolute;top:50px;right:10px;width:260px;background:rgba(255,255,255,0.95);padding:12px;border-radius:8px;font-size:12px;box-shadow:0 2px 4px rgba(0,0,0,0.1);display:none;"></div>
        </div>
    `;

    // Left-to-right layout
    var y1 = 200; // main flow
    var y2 = 370; // override path
    var xs = [80, 240, 420, 620, 780];

    function nc(bg, border) {
        return { background: bg, border: border,
            highlight: { background: lighten(bg, 20), border: border },
            hover: { background: lighten(bg, 20), border: border } };
    }

    var nodes = new vis.DataSet([
        // Main flow
        { id: 'json', label: 'DataPackage\nJSON', x: xs[0], y: y1, fixed: true,
          shape: 'box', color: nc('#E67E22', '#A04000'),
          font: { color: '#fff', size: 13, multi: true }, borderWidth: 2,
          info: '<b>DataPackage JSON</b><br><br>A Frictionless Data descriptor file (datapackage.json). Contains resource definitions, schemas, foreign keys, and data paths.<br><br><b>Structure:</b><pre>{\n  "resources": [...],\n  "foreignKeys": [...]\n}</pre>' },

        { id: 'from-desc', label: 'from_\ndescriptor()', x: xs[1], y: y1, fixed: true,
          shape: 'box', color: nc('#D35400', '#922B00'),
          font: { color: '#fff', size: 13, multi: true }, borderWidth: 2,
          info: '<b>from_descriptor()</b><br><br>Class method that parses a DataPackage JSON descriptor into a DataPackage object. Validates the schema and resolves resource paths.<br><br>Returns: DataPackage' },

        { id: 'dp-obj', label: 'DataPackage\nObject', x: xs[2], y: y1, fixed: true,
          shape: 'box', color: nc('#E67E22', '#A04000'),
          font: { color: '#fff', size: 13, multi: true }, borderWidth: 2,
          info: '<b>DataPackage Object</b><br><br>Python object containing parsed resources, schemas, and foreign key relationships. Provides to_relation_dag() for conversion.<br><br><b>Attributes:</b> resources, foreign_keys, name, description' },

        { id: 'to-dag', label: 'to_relation_\ndag()', x: xs[3], y: y1, fixed: true,
          shape: 'box', color: nc('#D35400', '#922B00'),
          font: { color: '#fff', size: 13, multi: true }, borderWidth: 2,
          info: '<b>to_relation_dag()</b><br><br>Converts the DataPackage into a RelationDAG. Creates a Relation for each resource, adds dependency_edges from FK references, and adds constraint_edges for FK validation.' },

        { id: 'dag', label: 'RelationDAG', x: xs[4], y: y1, fixed: true,
          shape: 'box', color: nc('#E67E22', '#A04000'),
          font: { color: '#fff', size: 14, bold: true, multi: true }, borderWidth: 3,
          info: '<b>RelationDAG</b><br><br>The resulting DAG containing:<br><br>&#8226; <b>relations:</b> one per resource<br>&#8226; <b>assets:</b> empty (not yet collected)<br>&#8226; <b>dependency_edges:</b> from FK analysis<br>&#8226; <b>constraint_edges:</b> for FK validation' },

        // DAG contents (below main DAG node)
        { id: 'dag-rels', label: 'relations', x: xs[4] - 60, y: y1 + 70, fixed: true,
          shape: 'ellipse', color: nc('#F39C12', '#C77C02'),
          font: { color: '#fff', size: 11 }, borderWidth: 1 },
        { id: 'dag-assets', label: 'assets', x: xs[4], y: y1 + 70, fixed: true,
          shape: 'ellipse', color: nc('#BDC3C7', '#95A5A6'),
          font: { color: '#fff', size: 11 }, borderWidth: 1,
          info: '<b>assets</b><br><br>Empty dict — no data has been loaded yet. Populated when collect() is called.' },
        { id: 'dag-edges', label: 'constraint\nedges', x: xs[4] + 70, y: y1 + 70, fixed: true,
          shape: 'ellipse', color: nc('#F39C12', '#C77C02'),
          font: { color: '#fff', size: 10, multi: true }, borderWidth: 1 },

        // Override path
        { id: 'override', label: 'Override\nDict', x: xs[1], y: y2, fixed: true,
          shape: 'box', color: nc('#8E44AD', '#6C3483'),
          font: { color: '#fff', size: 13, multi: true }, borderWidth: 2,
          info: '<b>Override Dict</b><br><br>Optional dictionary mapping resource names to custom Relation factories or pre-built DataFrames. Allows replacing the default from-file loading with custom logic.<br><br><b>Example:</b><pre>{"customers": my_custom_loader}</pre>' },

        { id: 'merge', label: 'merge\noverrides', x: xs[2], y: y2, fixed: true,
          shape: 'box', color: nc('#8E44AD', '#6C3483'),
          font: { color: '#fff', size: 12, multi: true }, borderWidth: 2,
          info: '<b>Merge Overrides</b><br><br>When overrides are provided, the to_relation_dag() method replaces default Relation definitions with the overridden versions before building the DAG.' }
    ]);

    var edges = new vis.DataSet([
        // Main flow
        { from: 'json', to: 'from-desc', arrows: 'to', color: { color: '#D35400' }, width: 3 },
        { from: 'from-desc', to: 'dp-obj', arrows: 'to', color: { color: '#D35400' }, width: 3 },
        { from: 'dp-obj', to: 'to-dag', arrows: 'to', color: { color: '#D35400' }, width: 3 },
        { from: 'to-dag', to: 'dag', arrows: 'to', color: { color: '#D35400' }, width: 3 },

        // DAG sub-elements
        { from: 'dag', to: 'dag-rels', arrows: 'to', color: { color: '#F39C12' }, width: 1.5 },
        { from: 'dag', to: 'dag-assets', arrows: 'to', color: { color: '#BDC3C7' }, width: 1.5 },
        { from: 'dag', to: 'dag-edges', arrows: 'to', color: { color: '#F39C12' }, width: 1.5 },

        // Override path
        { from: 'override', to: 'merge', arrows: 'to', color: { color: '#8E44AD' }, width: 2, dashes: [8, 4] },
        { from: 'merge', to: 'to-dag', arrows: 'to', color: { color: '#8E44AD' }, width: 2, dashes: [8, 4],
          smooth: { type: 'curvedCW', roundness: 0.3 } }
    ]);

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
            if (node && node.info) {
                infoPanel.innerHTML = node.info;
                infoPanel.style.display = 'block';
            }
        } else {
            infoPanel.style.display = 'none';
        }
    });

    network.on('hoverNode', function(params) {
        var node = nodes.get(params.node);
        if (node && node.info) { container.style.cursor = 'pointer'; }
    });

    network.on('blurNode', function() { container.style.cursor = 'default'; });

    function lighten(hex, amt) {
        var num = parseInt(hex.replace('#', ''), 16);
        var r = Math.min(255, (num >> 16) + amt);
        var g = Math.min(255, ((num >> 8) & 0xFF) + amt);
        var b = Math.min(255, (num & 0xFF) + amt);
        return '#' + (0x1000000 + r * 0x10000 + g * 0x100 + b).toString(16).slice(1);
    }
});
