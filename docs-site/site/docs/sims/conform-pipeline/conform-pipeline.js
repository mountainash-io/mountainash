// Conform Transformation Pipeline — Horizontal workflow
// CANVAS_HEIGHT: 500
document.addEventListener('DOMContentLoaded', function() {
    const main = document.querySelector('main');
    main.innerHTML = `
        <div style="position:relative;width:100%;height:500px;background:#f0f8ff;font-family:Arial,sans-serif;">
            <div id="network" style="width:100%;height:100%;"></div>
            <div style="position:absolute;top:10px;left:50%;transform:translateX(-50%);font-size:16px;font-weight:bold;background:rgba(240,248,255,0.9);padding:4px 12px;border-radius:4px;">Conform: plan from original sources, then execute</div>
            <div id="legend" style="position:absolute;top:10px;left:10px;background:rgba(255,255,255,0.95);padding:8px;border-radius:8px;font-size:11px;box-shadow:0 2px 4px rgba(0,0,0,0.1);">
                <div style="font-weight:bold;margin-bottom:4px;">Legend</div>
                <div><span style="color:#9370DB;">&#9679;</span> Type operation (FieldDefinition)</div>
                <div><span style="color:#20B2AA;">&#9679;</span> Relation operation</div>
                <div><span style="color:#4682B4;">&#9679;</span> Data (input/output)</div>
                <div style="margin-top:4px;font-size:10px;color:#666;">Click a step for its owner.<br/>Intermediate boxes are plans,<br/>not mutated input frames.</div>
            </div>
            <div id="info" style="position:absolute;bottom:10px;left:50%;transform:translateX(-50%);max-width:550px;background:rgba(255,255,255,0.95);padding:12px;border-radius:8px;font-size:12px;box-shadow:0 2px 4px rgba(0,0,0,0.1);display:none;"></div>
        </div>
    `;

    var stepY = 180;
    var colStateY = 300;
    var startX = 50;
    var stepSpacing = 115;

    var steps = [
        { id: 'input', label: 'Input\nColumns', x: startX, type: 'data',
          columns: 'user_name, email_addr,\nage (str), score, dept,\nold_flag',
          info: null },
        { id: 'detect', label: 'Resolve\nSources', x: startX + stepSpacing, type: 'type',
          columns: 'name←user_name,\nemail←email_addr,\nage←age, score←score',
          info: '<b>Resolve Sources</b><br><br><code>FieldDefinition.rename_from</code> selects an original source. The key in <code>TableSchema.fields</code> supplies the target name; definitions have no name, target_name or aliases property.' },
        { id: 'rename', label: 'Bind\nOutputs', x: startX + stepSpacing * 2, type: 'relation',
          columns: 'name←user_name,\nemail←email_addr,\nage←age, score←score',
          info: '<b>Bind Outputs</b><br><br>Build expressions against unchanged input columns, then alias each output. Swaps and fan-out do not read an earlier target result. These are planned expressions, not sequentially renamed frames.' },
        { id: 'cast', label: 'Cast\nTypes', x: startX + stepSpacing * 3, type: 'type',
          columns: 'name (str), email (str),\nage (int), score (float),\ndept (str), old_flag (bool)',
          info: '<b>Cast Types</b><br><br><code>type</code>, precise <code>dtype</code> and <code>format</code> contribute to shared resolution. Native adapters own representations; existing expression systems own casts. <code>ConformContract</code> owns failure policy, not a FieldDefinition.strict flag.' },
        { id: 'fill', label: 'Fill\nNulls', x: startX + stepSpacing * 4, type: 'type',
          columns: 'name (str), email (str),\nage (int, filled),\nscore (float), dept (str),\nold_flag (bool)',
          info: '<b>Fill Nulls</b><br><br><code>null_fill</code> substitutes original missing values, including configured <code>missing_values</code>. A failed cast is not an original null. Required/nullable checks belong to validation, not this conversion step.' },
        { id: 'filter', label: 'Execute\nProjection', x: startX + stepSpacing * 5, type: 'relation',
          columns: 'name (str),\nemail (str),\nage (int),\nscore (float)',
          info: '<b>Execute Projection</b><br><br><code>TableSchema.fields_match</code> and the conform contract govern columns and drift. This example uses partial mode, dropping dept and old_flag. Terminal execution compiles the deferred ConformRelNode through the existing relation system; no separate schema execution engine is used.' },
        { id: 'output', label: 'Output\nColumns', x: startX + stepSpacing * 6, type: 'data',
          columns: 'name (str),\nemail (str),\nage (int),\nscore (float)',
          info: null }
    ];

    var typeColor    = { background: '#9370DB', border: '#7B60CB', highlight: { background: '#A88DE0', border: '#7B60CB' }, hover: { background: '#A88DE0', border: '#7B60CB' } };
    var relationColor = { background: '#20B2AA', border: '#178F89', highlight: { background: '#40D0C8', border: '#178F89' }, hover: { background: '#40D0C8', border: '#178F89' } };
    var dataColor    = { background: '#4682B4', border: '#2C5F8A', highlight: { background: '#5A9BD4', border: '#2C5F8A' }, hover: { background: '#5A9BD4', border: '#2C5F8A' } };

    function colorFor(type) {
        if (type === 'type') return typeColor;
        if (type === 'relation') return relationColor;
        return dataColor;
    }

    var nodesList = [];
    steps.forEach(function(s) {
        // Main step node
        nodesList.push({
            id: s.id, label: s.label, x: s.x, y: stepY, fixed: true,
            shape: 'box', borderWidth: 2, borderWidthSelected: 3,
            color: colorFor(s.type),
            font: { color: '#fff', size: 12, multi: true, bold: true },
            widthConstraint: { minimum: 90 },
            info: s.info
        });
        // Column state node below
        nodesList.push({
            id: s.id + '-cols', label: s.columns, x: s.x, y: colStateY, fixed: true,
            shape: 'box', borderWidth: 1,
            color: { background: '#fff', border: '#ccc',
                     highlight: { background: '#f0f0ff', border: '#aaa' },
                     hover: { background: '#f0f0ff', border: '#aaa' } },
            font: { color: '#333', size: 9, multi: true, align: 'left', face: 'monospace' },
            widthConstraint: { minimum: 100 }
        });
    });

    var nodes = new vis.DataSet(nodesList);

    var edgesList = [];
    // Horizontal arrows between steps
    for (var i = 0; i < steps.length - 1; i++) {
        edgesList.push({
            from: steps[i].id, to: steps[i + 1].id, id: 'flow-' + i,
            color: { color: '#999' }, width: 2,
            arrows: { to: { enabled: true, scaleFactor: 0.7 } },
            smooth: false
        });
    }
    // Vertical dashed lines from step to column state
    steps.forEach(function(s) {
        edgesList.push({
            from: s.id, to: s.id + '-cols', id: 'state-' + s.id,
            color: { color: '#ccc' }, width: 1, dashes: [4, 4],
            arrows: { to: { enabled: false } },
            smooth: false
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
    var selectedStep = null;

    network.on('click', function(params) {
        if (params.nodes.length > 0) {
            var nodeId = params.nodes[0];
            var node = nodes.get(nodeId);
            if (node && node.info) {
                if (selectedStep === nodeId) {
                    selectedStep = null;
                    infoPanel.style.display = 'none';
                    resetHighlights();
                } else {
                    selectedStep = nodeId;
                    infoPanel.innerHTML = node.info;
                    infoPanel.style.display = 'block';
                    highlightStep(nodeId);
                }
            }
        } else {
            selectedStep = null;
            infoPanel.style.display = 'none';
            resetHighlights();
        }
    });

    function highlightStep(stepId) {
        var nodeUpdates = [];
        steps.forEach(function(s) {
            if (s.id === stepId) {
                var c = colorFor(s.type);
                nodeUpdates.push({ id: s.id, borderWidth: 3 });
                nodeUpdates.push({ id: s.id + '-cols', color: { background: '#FFFDE0', border: '#DAA520' } });
            } else {
                nodeUpdates.push({ id: s.id, borderWidth: 2, opacity: 0.5 });
                nodeUpdates.push({ id: s.id + '-cols', color: { background: '#f5f5f5', border: '#ddd' } });
            }
        });
        nodes.update(nodeUpdates);
    }

    function resetHighlights() {
        var nodeUpdates = [];
        steps.forEach(function(s) {
            nodeUpdates.push({ id: s.id, borderWidth: 2, opacity: 1.0 });
            nodeUpdates.push({ id: s.id + '-cols', color: { background: '#fff', border: '#ccc' } });
        });
        nodes.update(nodeUpdates);
    }
});
