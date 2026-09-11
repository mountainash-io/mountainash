// Namespace Descriptor Mechanism — Sequence Diagram
// CANVAS_HEIGHT: 500
document.addEventListener('DOMContentLoaded', function() {
    const main = document.querySelector('main');
    main.innerHTML = `
        <div style="position:relative;width:100%;height:500px;background:#f0f8ff;font-family:Arial,sans-serif;">
            <div id="network" style="width:100%;height:100%;"></div>
            <div style="position:absolute;top:8px;left:50%;transform:translateX(-50%);font-size:16px;font-weight:bold;background:rgba(240,248,255,0.9);padding:4px 12px;border-radius:4px;">Namespace Descriptor Mechanism</div>
            <div id="info" style="position:absolute;bottom:10px;right:10px;width:280px;background:rgba(255,255,255,0.95);padding:12px;border-radius:8px;font-size:12px;box-shadow:0 2px 4px rgba(0,0,0,0.1);display:none;"></div>
        </div>
    `;

    var cx = 400;
    var startY = 60;
    var stepH = 90;
    var darkGreen = '#006400';
    var lightGreen = '#228B22';

    var steps = [
        { id: 's1', label: 'User: .str', y: startY,
          code: 'df.select(col("name").str.upper())' },
        { id: 's2', label: 'Descriptor.__get__', y: startY + stepH,
          code: 'class NamespaceDescriptor:\n  def __get__(self, obj, objtype):\n    return self.ns_class(obj)' },
        { id: 's3', label: 'Instantiate\nStringNamespace', y: startY + stepH * 2,
          code: 'StringNamespace(expr)\n# Binds the parent Expr to the namespace' },
        { id: 's4', label: 'User: .upper()', y: startY + stepH * 3,
          code: 'StringNamespace.upper()\n# Delegates to function registry' },
        { id: 's5', label: 'Build\nScalarFunctionNode', y: startY + stepH * 4,
          code: 'ScalarFunctionNode(\n  key=FunctionKey("upper", "string"),\n  args=[parent_expr]\n)' }
    ];

    var nodes = new vis.DataSet();
    var edges = new vis.DataSet();

    steps.forEach(function(s, i) {
        nodes.add({
            id: s.id, label: s.label,
            x: cx, y: s.y, fixed: true,
            shape: 'box',
            widthConstraint: { minimum: 200, maximum: 200 },
            color: {
                background: darkGreen, border: '#004000',
                highlight: { background: lightGreen, border: '#004000' },
                hover: { background: lightGreen, border: '#004000' }
            },
            font: { color: '#fff', size: 14, multi: true },
            borderWidth: 2,
            code: s.code
        });
        if (i > 0) {
            edges.add({
                from: steps[i - 1].id, to: s.id,
                label: 'Step ' + (i + 1),
                font: { size: 11, color: '#333', strokeWidth: 2, strokeColor: '#f0f8ff' },
                color: { color: darkGreen, highlight: lightGreen, hover: lightGreen },
                width: 2,
                arrows: { to: { enabled: true, scaleFactor: 0.8 } },
                smooth: false
            });
        }
    });

    // Step 1 label on first edge position (above first node)
    edges.add({
        from: 's1', to: 's1',
        hidden: true
    });

    var container = document.getElementById('network');
    var network = new vis.Network(container, { nodes: nodes, edges: edges }, {
        interaction: { zoomView: false, dragView: false, dragNodes: false, hover: true },
        physics: { enabled: false },
        layout: { improvedLayout: false }
    });

    var infoPanel = document.getElementById('info');

    network.on('hoverNode', function(params) {
        var node = nodes.get(params.node);
        if (node && node.code) {
            infoPanel.innerHTML = '<b>' + node.label.replace(/\n/g, ' ') + '</b><br><pre style="margin:6px 0;padding:6px;background:#1e1e1e;color:#d4d4d4;border-radius:4px;font-size:11px;overflow-x:auto;white-space:pre-wrap;">' + node.code + '</pre>';
            infoPanel.style.display = 'block';
        }
    });

    network.on('blurNode', function() {
        infoPanel.style.display = 'none';
    });
});
