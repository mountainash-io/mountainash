// Relation Node Type Hierarchy
// CANVAS_HEIGHT: 500
document.addEventListener('DOMContentLoaded', function() {
    const main = document.querySelector('main');
    main.innerHTML = `
        <div style="position:relative;width:100%;height:500px;background:#f0f8ff;font-family:Arial,sans-serif;">
            <div id="network" style="width:100%;height:100%;"></div>
            <div style="position:absolute;top:10px;left:50%;transform:translateX(-50%);font-size:16px;font-weight:bold;background:rgba(240,248,255,0.9);padding:4px 12px;border-radius:4px;">Relation Node Type Hierarchy</div>
            <div id="legend" style="position:absolute;top:10px;left:10px;background:rgba(255,255,255,0.95);padding:8px;border-radius:8px;font-size:11px;box-shadow:0 2px 4px rgba(0,0,0,0.1);">
                <div style="font-weight:bold;margin-bottom:4px;">Legend</div>
                <div><span style="color:#1E90FF;">&#9679;</span> Substrait-Aligned</div>
                <div><span style="color:#FF8C00;">&#9679;</span> Extensions</div>
                <div><span style="color:#4682B4;">&#9679;</span> Base Class</div>
            </div>
            <div id="info" style="position:absolute;bottom:10px;left:50%;transform:translateX(-50%);max-width:500px;background:rgba(255,255,255,0.95);padding:12px;border-radius:8px;font-size:12px;box-shadow:0 2px 4px rgba(0,0,0,0.1);display:none;text-align:center;"></div>
        </div>
    `;

    var descriptions = {
        'root': '<b>RelationNode</b><br>Abstract base class for all relation algebra nodes. Provides tree structure, visitor pattern, and schema propagation.',
        'substrait': '<b>Substrait-Aligned</b><br>Nodes that map directly to Substrait relation types for cross-engine compatibility.',
        'extensions': '<b>Extensions</b><br>mountainash-specific nodes that extend beyond the Substrait specification.',
        'read': '<b>ReadRelNode</b><br>Reads data from a source (DataFrame, table, file). The leaf node of most query trees.',
        'project': '<b>ProjectRelNode</b><br>Selects and transforms columns. Equivalent to SQL SELECT with expressions.',
        'filter': '<b>FilterRelNode</b><br>Filters rows based on a boolean predicate. Equivalent to SQL WHERE.',
        'aggregate': '<b>AggregateRelNode</b><br>Groups rows and computes aggregate functions. Equivalent to SQL GROUP BY.',
        'join': '<b>JoinRelNode</b><br>Combines two relations on a join condition. Supports inner, left, right, outer, cross joins.',
        'fetch': '<b>FetchRelNode</b><br>Limits the number of rows returned. Equivalent to SQL LIMIT/OFFSET.',
        'sort': '<b>SortRelNode</b><br>Orders rows by one or more sort keys. Equivalent to SQL ORDER BY.',
        'set': '<b>SetRelNode</b><br>Set operations: union, intersection, difference between two relations.',
        'extension': '<b>ExtensionRelNode</b><br>Generic extension point for custom relation operations not in Substrait.',
        'source': '<b>SourceRelNode</b><br>Represents a named data source for deferred resolution.',
        'ref': '<b>RefRelNode</b><br>Reference to another relation node, enabling DAG (not just tree) structures.',
        'resource': '<b>ResourceReadRelNode</b><br>Reads from a mountainash DataResource with schema and format metadata.',
        'conform': '<b>ConformRelNode</b><br>Ensures schema conformance by casting, renaming, or reordering columns.',
        'params': '<b>ParamsRelNode</b><br>Injects runtime parameters into the relation tree for parameterized queries.',
        'pipeline': '<b>PipelineStepRelNode</b><br>Wraps a relation as a named pipeline step for orchestration and lineage.'
    };

    var cx = 400, rootY = 40, catY = 130, leafY = 230;
    var substraitColor = '#1E90FF';
    var extensionColor = '#FF8C00';
    var baseColor = '#4682B4';

    function makeNode(id, label, x, y, bg) {
        return {
            id: id, label: label, x: x, y: y, fixed: true, shape: 'box',
            color: { background: bg, border: shadeColor(bg, -30), highlight: { background: lightenColor(bg, 20), border: shadeColor(bg, -30) }, hover: { background: lightenColor(bg, 20), border: shadeColor(bg, -30) } },
            font: { color: '#fff', size: 12 }, borderWidth: 2
        };
    }

    var substraitNodes = ['Read', 'Project', 'Filter', 'Aggregate', 'Join', 'Fetch', 'Sort', 'Set'];
    var substraitIds   = ['read', 'project', 'filter', 'aggregate', 'join', 'fetch', 'sort', 'set'];
    var extensionNodes = ['Extension', 'Source', 'Ref', 'ResourceRead', 'Conform', 'ParamsRelNode', 'PipelineStep'];
    var extensionIds   = ['extension', 'source', 'ref', 'resource', 'conform', 'params', 'pipeline'];

    var nodeList = [
        makeNode('root', 'RelationNode', cx, rootY, baseColor),
        makeNode('substrait', 'Substrait-Aligned', cx - 200, catY, substraitColor),
        makeNode('extensions', 'Extensions', cx + 200, catY, extensionColor)
    ];

    var edgeList = [
        { from: 'root', to: 'substrait', color: { color: '#999' }, width: 2, arrows: { to: { enabled: true, scaleFactor: 0.7 } } },
        { from: 'root', to: 'extensions', color: { color: '#999' }, width: 2, arrows: { to: { enabled: true, scaleFactor: 0.7 } } }
    ];

    var subStartX = cx - 200 - (substraitNodes.length - 1) * 50;
    substraitNodes.forEach(function(name, i) {
        var x = subStartX + i * 100;
        var row = i < 4 ? 0 : 1;
        var colInRow = i < 4 ? i : i - 4;
        var rx = (cx - 200) - 150 + colInRow * 100;
        var ry = leafY + row * 70;
        nodeList.push(makeNode(substraitIds[i], name + '\nRelNode', rx, ry, substraitColor));
        edgeList.push({ from: 'substrait', to: substraitIds[i], color: { color: substraitColor, opacity: 0.5 }, width: 1.5, arrows: { to: { enabled: true, scaleFactor: 0.5 } } });
    });

    extensionNodes.forEach(function(name, i) {
        var row = i < 4 ? 0 : 1;
        var colInRow = i < 4 ? i : i - 4;
        var rx = (cx + 200) - 150 + colInRow * 100;
        var ry = leafY + row * 70;
        nodeList.push(makeNode(extensionIds[i], name + '\nRelNode', rx, ry, extensionColor));
        edgeList.push({ from: 'extensions', to: extensionIds[i], color: { color: extensionColor, opacity: 0.5 }, width: 1.5, arrows: { to: { enabled: true, scaleFactor: 0.5 } } });
    });

    var nodes = new vis.DataSet(nodeList);
    var edges = new vis.DataSet(edgeList);

    var container = document.getElementById('network');
    var network = new vis.Network(container, { nodes: nodes, edges: edges }, {
        interaction: { zoomView: false, dragView: false, dragNodes: false, hover: true },
        physics: { enabled: false },
        layout: { improvedLayout: false }
    });

    var infoPanel = document.getElementById('info');

    network.on('click', function(params) {
        if (params.nodes.length > 0) {
            var nodeId = params.nodes[0];
            if (descriptions[nodeId]) {
                infoPanel.innerHTML = descriptions[nodeId];
                infoPanel.style.display = 'block';
            }
        } else {
            infoPanel.style.display = 'none';
        }
    });

    function shadeColor(hex, percent) {
        var num = parseInt(hex.replace('#', ''), 16);
        var r = Math.max(0, Math.min(255, (num >> 16) + percent));
        var g = Math.max(0, Math.min(255, ((num >> 8) & 0x00FF) + percent));
        var b = Math.max(0, Math.min(255, (num & 0x0000FF) + percent));
        return '#' + (0x1000000 + r * 0x10000 + g * 0x100 + b).toString(16).slice(1);
    }
    function lightenColor(hex, percent) { return shadeColor(hex, percent); }
});
