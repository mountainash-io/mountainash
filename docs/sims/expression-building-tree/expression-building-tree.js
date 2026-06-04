// Expression Building Tree
// CANVAS_HEIGHT: 500
document.addEventListener('DOMContentLoaded', function() {
    const main = document.querySelector('main');
    main.innerHTML = `
        <div style="position:relative;width:100%;height:500px;background:#f0f8ff;font-family:Arial,sans-serif;">
            <div id="network" style="width:100%;height:100%;"></div>
            <div style="position:absolute;top:10px;left:50%;transform:translateX(-50%);font-size:16px;font-weight:bold;background:rgba(240,248,255,0.9);padding:4px 12px;border-radius:4px;">Expression Building Tree</div>
            <div id="legend" style="position:absolute;top:10px;left:10px;background:rgba(255,255,255,0.95);padding:8px;border-radius:8px;font-size:11px;box-shadow:0 2px 4px rgba(0,0,0,0.1);">
                <div style="font-weight:bold;margin-bottom:4px;">Legend</div>
                <div><span style="color:#006400;">&#9679;</span> Function Node</div>
                <div><span style="color:#32CD32;">&#9679;</span> Field Reference</div>
                <div style="margin-top:6px;font-size:10px;color:#666;">Expression:<br><code>price * quantity + tax</code></div>
                <div style="margin-top:4px;color:#888;">Click for properties</div>
            </div>
            <div id="info" style="position:absolute;top:50px;right:10px;width:260px;background:rgba(255,255,255,0.95);padding:12px;border-radius:8px;font-size:12px;box-shadow:0 2px 4px rgba(0,0,0,0.1);display:none;"></div>
        </div>
    `;

    var funcColor = { background: '#006400', border: '#004D00', highlight: { background: '#008000', border: '#004D00' }, hover: { background: '#008000', border: '#004D00' } };
    var fieldColor = { background: '#32CD32', border: '#228B22', highlight: { background: '#50E050', border: '#228B22' }, hover: { background: '#50E050', border: '#228B22' } };

    var centerX = 400;

    var nodes = new vis.DataSet([
        // Root: ADD
        { id: 'add', label: 'ScalarFunctionNode\n(ADD)', x: centerX, y: 80, fixed: true,
          shape: 'box', color: funcColor, font: { color: '#fff', size: 13, bold: true }, borderWidth: 3,
          info: '<b>ScalarFunctionNode (ADD)</b><br><br><b>Type:</b> ScalarFunctionNode<br><b>Function:</b> ADD<br><b>Return type:</b> Float64<br><b>Children:</b> 2<br><br>Root of the expression tree. Adds the result of MULTIPLY (left) with the tax field reference (right).<br><br><code>price * quantity + tax</code>' },

        // Left child: MULTIPLY
        { id: 'mul', label: 'ScalarFunctionNode\n(MULTIPLY)', x: centerX - 160, y: 220, fixed: true,
          shape: 'box', color: funcColor, font: { color: '#fff', size: 12 }, borderWidth: 2,
          info: '<b>ScalarFunctionNode (MULTIPLY)</b><br><br><b>Type:</b> ScalarFunctionNode<br><b>Function:</b> MULTIPLY<br><b>Return type:</b> Float64<br><b>Children:</b> 2<br><br>Multiplies the price and quantity fields.<br><br><code>price * quantity</code>' },

        // Right child: tax field
        { id: 'tax', label: 'FieldReferenceNode\n("tax")', x: centerX + 160, y: 220, fixed: true,
          shape: 'box', color: fieldColor, font: { color: '#fff', size: 12 }, borderWidth: 2,
          info: '<b>FieldReferenceNode ("tax")</b><br><br><b>Type:</b> FieldReferenceNode<br><b>Field name:</b> tax<br><b>Data type:</b> Float64<br><b>Nullable:</b> true<br><br>Leaf node. References the "tax" column in the input relation.' },

        // MULTIPLY children
        { id: 'price', label: 'FieldReferenceNode\n("price")', x: centerX - 260, y: 380, fixed: true,
          shape: 'box', color: fieldColor, font: { color: '#fff', size: 12 }, borderWidth: 2,
          info: '<b>FieldReferenceNode ("price")</b><br><br><b>Type:</b> FieldReferenceNode<br><b>Field name:</b> price<br><b>Data type:</b> Float64<br><b>Nullable:</b> false<br><br>Leaf node. References the "price" column in the input relation.' },

        { id: 'qty', label: 'FieldReferenceNode\n("quantity")', x: centerX - 60, y: 380, fixed: true,
          shape: 'box', color: fieldColor, font: { color: '#fff', size: 12 }, borderWidth: 2,
          info: '<b>FieldReferenceNode ("quantity")</b><br><br><b>Type:</b> FieldReferenceNode<br><b>Field name:</b> quantity<br><b>Data type:</b> Int64<br><b>Nullable:</b> false<br><br>Leaf node. References the "quantity" column in the input relation.' }
    ]);

    var edges = new vis.DataSet([
        { from: 'add', to: 'mul', label: 'left', font: { size: 10, color: '#006400' }, color: { color: '#006400', highlight: '#008000', hover: '#008000' }, width: 2.5, arrows: { to: { enabled: true, scaleFactor: 0.8 } } },
        { from: 'add', to: 'tax', label: 'right', font: { size: 10, color: '#006400' }, color: { color: '#006400', highlight: '#008000', hover: '#008000' }, width: 2.5, arrows: { to: { enabled: true, scaleFactor: 0.8 } } },
        { from: 'mul', to: 'price', label: 'left', font: { size: 10, color: '#006400' }, color: { color: '#006400', highlight: '#008000', hover: '#008000' }, width: 2, arrows: { to: { enabled: true, scaleFactor: 0.8 } } },
        { from: 'mul', to: 'qty', label: 'right', font: { size: 10, color: '#006400' }, color: { color: '#006400', highlight: '#008000', hover: '#008000' }, width: 2, arrows: { to: { enabled: true, scaleFactor: 0.8 } } }
    ]);

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
