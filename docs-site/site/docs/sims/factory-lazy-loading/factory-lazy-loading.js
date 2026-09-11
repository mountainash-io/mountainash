// Factory Lazy Loading Workflow
// CANVAS_HEIGHT: 500
document.addEventListener('DOMContentLoaded', function() {
    const main = document.querySelector('main');
    main.innerHTML = `
        <div style="position:relative;width:100%;height:500px;background:#f0f8ff;font-family:Arial,sans-serif;">
            <div id="network" style="width:100%;height:100%;"></div>
            <div style="position:absolute;top:10px;left:50%;transform:translateX(-50%);font-size:16px;font-weight:bold;background:rgba(240,248,255,0.9);padding:4px 12px;border-radius:4px;">Factory Lazy Loading</div>
            <div id="legend" style="position:absolute;top:10px;left:10px;background:rgba(255,255,255,0.95);padding:8px;border-radius:8px;font-size:11px;box-shadow:0 2px 4px rgba(0,0,0,0.1);">
                <div style="font-weight:bold;margin-bottom:4px;">Legend</div>
                <div><span style="color:#483D8B;">&#9679;</span> Process Step</div>
                <div><span style="color:#DAA520;">&#9670;</span> Decision</div>
                <div><span style="color:#228B22;">&#9679;</span> Success</div>
                <div><span style="color:#B22222;">&#9679;</span> Error</div>
                <div style="margin-top:4px;color:#888;">Click to expand details</div>
            </div>
            <div id="info" style="position:absolute;top:50px;right:10px;width:260px;background:rgba(255,255,255,0.95);padding:12px;border-radius:8px;font-size:12px;box-shadow:0 2px 4px rgba(0,0,0,0.1);display:none;"></div>
        </div>
    `;

    var centerX = 350;
    var stepColor = { background: '#483D8B', border: '#362D6B', highlight: { background: '#5A4DA0', border: '#362D6B' }, hover: { background: '#5A4DA0', border: '#362D6B' } };
    var decisionColor = { background: '#DAA520', border: '#B8860B', highlight: { background: '#F0C040', border: '#B8860B' }, hover: { background: '#F0C040', border: '#B8860B' } };
    var successColor = { background: '#228B22', border: '#196619', highlight: { background: '#2EAE2E', border: '#196619' }, hover: { background: '#2EAE2E', border: '#196619' } };
    var errorColor = { background: '#B22222', border: '#8B1A1A', highlight: { background: '#D43333', border: '#8B1A1A' }, hover: { background: '#D43333', border: '#8B1A1A' } };

    var nodes = new vis.DataSet([
        { id: 'detect', label: 'Detect Backend', x: centerX, y: 60, fixed: true, shape: 'box', color: stepColor, font: { color: '#fff', size: 13 }, borderWidth: 2,
          info: '<b>Detect Backend</b><br><br>Inspects the input object type to determine which backend to use. Checks isinstance() against known DataFrame types (polars.DataFrame, pandas.DataFrame, etc.).' },

        { id: 'cache', label: 'Cache\nLookup', x: centerX, y: 160, fixed: true, shape: 'diamond', color: decisionColor, font: { color: '#fff', size: 11 }, borderWidth: 2, size: 25,
          info: '<b>Cache Lookup</b><br><br>Checks whether the backend module has already been imported and cached. Uses a module-level dictionary keyed by CONST_BACKEND enum value. Cache hit avoids expensive import.' },

        { id: 'cache-hit', label: 'Return\nCached Module', x: centerX + 180, y: 160, fixed: true, shape: 'box', color: successColor, font: { color: '#fff', size: 11 }, borderWidth: 2,
          info: '<b>Cache Hit</b><br><br>Backend module was previously imported. Returns the cached module reference immediately. No import cost on subsequent calls.' },

        { id: 'lazy-import', label: 'Lazy Import', x: centerX, y: 270, fixed: true, shape: 'box', color: stepColor, font: { color: '#fff', size: 13 }, borderWidth: 2,
          info: '<b>Lazy Import</b><br><br>Performs importlib.import_module() for the backend. Only triggers on first use, keeping startup fast. The module path is resolved from a registry mapping CONST_BACKEND to module paths.' },

        { id: 'validate', label: 'Validate\nBackend', x: centerX, y: 370, fixed: true, shape: 'box', color: stepColor, font: { color: '#fff', size: 13 }, borderWidth: 2,
          info: '<b>Validate Backend</b><br><br>Confirms the imported module exposes the required interface (compile, execute methods). Raises BackendValidationError if the contract is not satisfied.' },

        { id: 'store', label: 'Store in Cache\n& Return', x: centerX, y: 460, fixed: true, shape: 'box', color: successColor, font: { color: '#fff', size: 12 }, borderWidth: 2,
          info: '<b>Store & Return</b><br><br>Caches the validated module for future lookups and returns it to the caller. Subsequent requests for the same backend skip import entirely.' },

        { id: 'import-err', label: 'ImportError', x: centerX - 200, y: 270, fixed: true, shape: 'box', color: errorColor, font: { color: '#fff', size: 11 }, borderWidth: 2,
          info: '<b>ImportError</b><br><br>The backend library is not installed. Raises a descriptive error: "Backend \'polars\' requires: pip install polars". Guides the user to install the missing dependency.' },

        { id: 'valid-err', label: 'ValidationError', x: centerX - 200, y: 370, fixed: true, shape: 'box', color: errorColor, font: { color: '#fff', size: 11 }, borderWidth: 2,
          info: '<b>BackendValidationError</b><br><br>The module exists but does not satisfy the backend contract. This typically indicates a version mismatch or corrupted installation.' }
    ]);

    var edges = new vis.DataSet([
        { from: 'detect', to: 'cache', color: { color: '#483D8B' }, width: 2, arrows: { to: { enabled: true, scaleFactor: 0.8 } } },
        { from: 'cache', to: 'cache-hit', label: 'hit', font: { size: 10, color: '#228B22' }, color: { color: '#228B22' }, width: 2, arrows: { to: { enabled: true, scaleFactor: 0.8 } }, smooth: { type: 'curvedCW', roundness: 0.2 } },
        { from: 'cache', to: 'lazy-import', label: 'miss', font: { size: 10, color: '#483D8B' }, color: { color: '#483D8B' }, width: 2, arrows: { to: { enabled: true, scaleFactor: 0.8 } } },
        { from: 'lazy-import', to: 'validate', color: { color: '#483D8B' }, width: 2, arrows: { to: { enabled: true, scaleFactor: 0.8 } } },
        { from: 'validate', to: 'store', color: { color: '#228B22' }, width: 2, arrows: { to: { enabled: true, scaleFactor: 0.8 } } },
        { from: 'lazy-import', to: 'import-err', label: 'fail', font: { size: 10, color: '#B22222' }, color: { color: '#B22222' }, width: 1.5, dashes: true, arrows: { to: { enabled: true, scaleFactor: 0.7 } }, smooth: { type: 'curvedCCW', roundness: 0.3 } },
        { from: 'validate', to: 'valid-err', label: 'fail', font: { size: 10, color: '#B22222' }, color: { color: '#B22222' }, width: 1.5, dashes: true, arrows: { to: { enabled: true, scaleFactor: 0.7 } }, smooth: { type: 'curvedCCW', roundness: 0.3 } }
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
