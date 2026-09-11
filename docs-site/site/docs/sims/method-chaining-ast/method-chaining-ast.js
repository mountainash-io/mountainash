// Method Chaining to AST Mapping
// CANVAS_HEIGHT: 500
document.addEventListener('DOMContentLoaded', function() {
    const main = document.querySelector('main');
    main.innerHTML = `
        <div style="position:relative;width:100%;height:500px;background:#f0f8ff;font-family:Arial,sans-serif;">
            <div id="network" style="width:100%;height:100%;"></div>
            <div style="position:absolute;top:10px;left:50%;transform:translateX(-50%);font-size:16px;font-weight:bold;background:rgba(240,248,255,0.9);padding:4px 12px;border-radius:4px;">Method Chaining &rarr; AST Nodes</div>
            <div id="legend" style="position:absolute;top:10px;left:10px;background:rgba(255,255,255,0.95);padding:8px;border-radius:8px;font-size:11px;box-shadow:0 2px 4px rgba(0,0,0,0.1);">
                <div style="font-weight:bold;margin-bottom:4px;">Legend</div>
                <div><span style="color:#5F9EA0;">&#9679;</span> Python Code</div>
                <div><span style="color:#008080;">&#9679;</span> AST Node</div>
                <div style="margin-top:4px;color:#888;">Click a node for details</div>
            </div>
            <div id="info" style="position:absolute;top:50px;right:10px;width:260px;background:rgba(255,255,255,0.95);padding:12px;border-radius:8px;font-size:12px;box-shadow:0 2px 4px rgba(0,0,0,0.1);display:none;"></div>
        </div>
    `;

    var codeLines = [
        { id: 'c1', label: 'df.read("t.csv")', y: 60,
          info: '<b>.read("t.csv")</b><br><br>Reads a CSV file into a DataFrame. This is the data source entry point of the pipeline.' },
        { id: 'c2', label: '.filter(col("x") > 10)', y: 150,
          info: '<b>.filter(col("x") > 10)</b><br><br>Applies a predicate filter, keeping only rows where column "x" exceeds 10.' },
        { id: 'c3', label: '.select("x", "y")', y: 240,
          info: '<b>.select("x", "y")</b><br><br>Projects the result to only columns "x" and "y", discarding all others.' },
        { id: 'c4', label: '.sort("x")', y: 330,
          info: '<b>.sort("x")</b><br><br>Orders the result set by column "x" in ascending order.' },
        { id: 'c5', label: '.head(100)', y: 420,
          info: '<b>.head(100)</b><br><br>Limits the output to the first 100 rows. This is a terminal operation.' }
    ];

    var astNodes = [
        { id: 'a1', label: 'ReadRelNode', y: 60,
          info: '<b>ReadRelNode</b><br><br>Leaf node in the AST. Represents a data source scan operation. Properties: path="t.csv", format=CSV.' },
        { id: 'a2', label: 'FilterRelNode', y: 150,
          info: '<b>FilterRelNode</b><br><br>Applies a boolean predicate to filter rows. Child: ReadRelNode. Predicate: col("x") > 10.' },
        { id: 'a3', label: 'ProjectRelNode', y: 240,
          info: '<b>ProjectRelNode</b><br><br>Selects a subset of columns from the relation. Child: FilterRelNode. Columns: ["x", "y"].' },
        { id: 'a4', label: 'SortRelNode', y: 330,
          info: '<b>SortRelNode</b><br><br>Orders tuples by one or more sort keys. Child: ProjectRelNode. Keys: [("x", ASC)].' },
        { id: 'a5', label: 'FetchRelNode', y: 420,
          info: '<b>FetchRelNode</b><br><br>Limits the number of returned rows. Child: SortRelNode. Limit: 100, Offset: 0.' }
    ];

    var codeX = 180;
    var astX = 580;

    var nodes = new vis.DataSet();
    var edges = new vis.DataSet();

    codeLines.forEach(function(c) {
        nodes.add({
            id: c.id, label: c.label, x: codeX, y: c.y, fixed: true,
            shape: 'box',
            color: { background: '#5F9EA0', border: '#4A7C7E', highlight: { background: '#7AB8BA', border: '#4A7C7E' }, hover: { background: '#7AB8BA', border: '#4A7C7E' } },
            font: { color: '#fff', size: 12, face: 'monospace' }, borderWidth: 2,
            info: c.info
        });
    });

    astNodes.forEach(function(a) {
        nodes.add({
            id: a.id, label: a.label, x: astX, y: a.y, fixed: true,
            shape: 'box',
            color: { background: '#008080', border: '#006060', highlight: { background: '#20A0A0', border: '#006060' }, hover: { background: '#20A0A0', border: '#006060' } },
            font: { color: '#fff', size: 13, face: 'monospace' }, borderWidth: 2,
            info: a.info
        });
    });

    // Code-to-AST mapping edges
    for (var i = 0; i < 5; i++) {
        edges.add({
            from: codeLines[i].id, to: astNodes[i].id,
            color: { color: '#999', highlight: '#008080', hover: '#008080' },
            width: 1.5, dashes: true,
            arrows: { to: { enabled: true, scaleFactor: 0.7 } },
            smooth: { type: 'straightCross' }
        });
    }

    // AST tree edges (parent-child chain)
    for (var j = 0; j < 4; j++) {
        edges.add({
            from: astNodes[j].id, to: astNodes[j + 1].id,
            color: { color: '#008080', highlight: '#006060', hover: '#006060' },
            width: 2,
            arrows: { to: { enabled: true, scaleFactor: 0.8 } },
            smooth: false
        });
    }

    var container = document.getElementById('network');
    var network = new vis.Network(container, { nodes: nodes, edges: edges }, {
        interaction: { zoomView: false, dragView: false, dragNodes: false, navigationButtons: false, hover: true },
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
});
