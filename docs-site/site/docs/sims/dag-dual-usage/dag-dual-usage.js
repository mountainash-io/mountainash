// DAG Dual Usage — Relational AST vs RelationDAG
// CANVAS_HEIGHT: 500
document.addEventListener('DOMContentLoaded', function() {
    const main = document.querySelector('main');
    main.innerHTML = `
        <div style="position:relative;width:100%;height:500px;background:#f0f8ff;font-family:Arial,sans-serif;">
            <div id="network" style="width:100%;height:100%;"></div>
            <div style="position:absolute;top:10px;left:50%;transform:translateX(-50%);font-size:16px;font-weight:bold;background:rgba(240,248,255,0.9);padding:4px 12px;border-radius:4px;">DAG Dual Usage</div>
            <div id="legend" style="position:absolute;top:10px;left:10px;background:rgba(255,255,255,0.95);padding:8px;border-radius:8px;font-size:11px;box-shadow:0 2px 4px rgba(0,0,0,0.1);">
                <div style="font-weight:bold;margin-bottom:4px;">Legend</div>
                <div><span style="color:#1E90FF;">&#9679;</span> Relational AST</div>
                <div><span style="color:#FF8C00;">&#9679;</span> RelationDAG</div>
                <div style="margin-top:4px;color:#888;">Click to highlight deps</div>
            </div>
            <div id="info" style="position:absolute;top:50px;right:10px;width:260px;background:rgba(255,255,255,0.95);padding:12px;border-radius:8px;font-size:12px;box-shadow:0 2px 4px rgba(0,0,0,0.1);display:none;"></div>
        </div>
    `;

    // --- Relational AST (left group) ---
    var astColor = '#1E90FF';
    var astBorder = '#1565C0';
    var astHover = '#42A5F5';

    // --- RelationDAG (right group) ---
    var dagColor = '#FF8C00';
    var dagBorder = '#CC7000';
    var dagHover = '#FFB347';

    function makeColor(bg, border, hover) {
        return { background: bg, border: border, highlight: { background: hover, border: border }, hover: { background: hover, border: border } };
    }

    var leftX = 180;
    var rightX = 580;

    var nodes = new vis.DataSet([
        // AST nodes
        { id: 'read-cust', label: 'ReadRelNode\n(customers)', x: leftX - 80, y: 400, fixed: true, shape: 'box', color: makeColor(astColor, astBorder, astHover), font: { color: '#fff', size: 11 }, borderWidth: 2, group: 'ast',
          info: '<b>ReadRelNode (customers)</b><br><br>Leaf node. Scans the customers table from storage.' },
        { id: 'read-ord', label: 'ReadRelNode\n(orders)', x: leftX + 80, y: 400, fixed: true, shape: 'box', color: makeColor(astColor, astBorder, astHover), font: { color: '#fff', size: 11 }, borderWidth: 2, group: 'ast',
          info: '<b>ReadRelNode (orders)</b><br><br>Leaf node. Scans the orders table from storage.' },
        { id: 'filter', label: 'FilterRelNode', x: leftX - 80, y: 300, fixed: true, shape: 'box', color: makeColor(astColor, astBorder, astHover), font: { color: '#fff', size: 12 }, borderWidth: 2, group: 'ast',
          info: '<b>FilterRelNode</b><br><br>Filters customers by a predicate (e.g., active=true). Child: ReadRelNode(customers).' },
        { id: 'project', label: 'ProjectRelNode', x: leftX + 80, y: 300, fixed: true, shape: 'box', color: makeColor(astColor, astBorder, astHover), font: { color: '#fff', size: 12 }, borderWidth: 2, group: 'ast',
          info: '<b>ProjectRelNode</b><br><br>Selects columns from orders (order_id, customer_id, total). Child: ReadRelNode(orders).' },
        { id: 'join', label: 'JoinRelNode', x: leftX, y: 180, fixed: true, shape: 'box', color: makeColor(astColor, astBorder, astHover), font: { color: '#fff', size: 13, bold: true }, borderWidth: 3, group: 'ast',
          info: '<b>JoinRelNode</b><br><br>Inner join on customer_id. Left child: FilterRelNode, Right child: ProjectRelNode.' },
        { id: 'ast-label', label: 'Relational AST', x: leftX, y: 80, fixed: true, shape: 'text', font: { color: '#1565C0', size: 14, bold: true } },

        // RelationDAG nodes
        { id: 'r-customers', label: 'customers', x: rightX - 80, y: 400, fixed: true, shape: 'box', color: makeColor(dagColor, dagBorder, dagHover), font: { color: '#fff', size: 13 }, borderWidth: 2, group: 'dag',
          info: '<b>customers</b><br><br>Named relation registered in the DAG. Source table with columns: id, name, active, region.' },
        { id: 'r-orders', label: 'orders', x: rightX + 80, y: 400, fixed: true, shape: 'box', color: makeColor(dagColor, dagBorder, dagHover), font: { color: '#fff', size: 13 }, borderWidth: 2, group: 'dag',
          info: '<b>orders</b><br><br>Named relation. Contains order_id, customer_id, total, date columns.' },
        { id: 'r-summary', label: 'summary', x: rightX, y: 250, fixed: true, shape: 'box', color: makeColor(dagColor, dagBorder, dagHover), font: { color: '#fff', size: 13, bold: true }, borderWidth: 3, group: 'dag',
          info: '<b>summary</b><br><br>Derived relation that depends on both customers and orders. Represents the joined and aggregated result.' },
        { id: 'dag-label', label: 'RelationDAG', x: rightX, y: 80, fixed: true, shape: 'text', font: { color: '#CC7000', size: 14, bold: true } }
    ]);

    var edges = new vis.DataSet([
        // AST edges (child -> parent)
        { from: 'read-cust', to: 'filter', color: { color: astColor, highlight: astColor, hover: astColor }, width: 2, arrows: { to: { enabled: true, scaleFactor: 0.7 } } },
        { from: 'read-ord', to: 'project', color: { color: astColor, highlight: astColor, hover: astColor }, width: 2, arrows: { to: { enabled: true, scaleFactor: 0.7 } } },
        { from: 'filter', to: 'join', color: { color: astColor, highlight: astColor, hover: astColor }, width: 2, arrows: { to: { enabled: true, scaleFactor: 0.7 } } },
        { from: 'project', to: 'join', color: { color: astColor, highlight: astColor, hover: astColor }, width: 2, arrows: { to: { enabled: true, scaleFactor: 0.7 } } },

        // DAG edges (dependency)
        { from: 'r-customers', to: 'r-summary', color: { color: dagColor, highlight: dagColor, hover: dagColor }, width: 2, arrows: { to: { enabled: true, scaleFactor: 0.7 } } },
        { from: 'r-orders', to: 'r-summary', color: { color: dagColor, highlight: dagColor, hover: dagColor }, width: 2, arrows: { to: { enabled: true, scaleFactor: 0.7 } } }
    ]);

    var container = document.getElementById('network');
    var network = new vis.Network(container, { nodes: nodes, edges: edges }, {
        interaction: { zoomView: false, dragView: false, dragNodes: false, navigationButtons: false, hover: true },
        physics: { enabled: false },
        layout: { improvedLayout: false }
    });

    var infoPanel = document.getElementById('info');
    var selectedGroup = null;

    network.on('click', function(params) {
        if (params.nodes.length > 0) {
            var nodeId = params.nodes[0];
            var node = nodes.get(nodeId);
            if (node && node.info) {
                infoPanel.innerHTML = node.info;
                infoPanel.style.display = 'block';
            }

            // Highlight dependencies in the same group
            var group = node.group;
            if (group) {
                var connectedIds = [nodeId];
                var connected = network.getConnectedNodes(nodeId);
                connected.forEach(function(cid) {
                    var cn = nodes.get(cid);
                    if (cn && cn.group === group) connectedIds.push(cid);
                });

                // Dim non-connected nodes in the same group
                nodes.forEach(function(n) {
                    if (n.group === group && connectedIds.indexOf(n.id) === -1) {
                        nodes.update({ id: n.id, opacity: 0.3 });
                    } else {
                        nodes.update({ id: n.id, opacity: 1.0 });
                    }
                });
                selectedGroup = group;
            }
        } else {
            infoPanel.style.display = 'none';
            // Reset opacity
            nodes.forEach(function(n) {
                nodes.update({ id: n.id, opacity: 1.0 });
            });
            selectedGroup = null;
        }
    });
});
