// Function Key Taxonomy — Hierarchical Tree
// CANVAS_HEIGHT: 500
document.addEventListener('DOMContentLoaded', function() {
    const main = document.querySelector('main');
    main.innerHTML = `
        <div style="position:relative;width:100%;height:500px;background:#f0f8ff;font-family:Arial,sans-serif;">
            <div id="network" style="width:100%;height:100%;"></div>
            <div style="position:absolute;top:8px;left:50%;transform:translateX(-50%);font-size:16px;font-weight:bold;background:rgba(240,248,255,0.9);padding:4px 12px;border-radius:4px;">Function Key Taxonomy</div>
            <div id="detail" style="position:absolute;bottom:10px;right:10px;width:260px;background:rgba(255,255,255,0.97);padding:12px;border-radius:8px;font-size:12px;box-shadow:0 2px 8px rgba(0,0,0,0.15);display:none;"></div>
        </div>
    `;

    var limeGreen = '#32CD32';
    var darkLime = '#228B22';
    var lightLime = '#90EE90';

    var substraitCats = [
        { id: 'sub_arith', label: 'Arithmetic\n(14)', detail: 'add, subtract, multiply, divide, modulus, power, abs, sign, negate, ceil, floor, round, sqrt, exp' },
        { id: 'sub_comp', label: 'Comparison\n(8)', detail: 'equal, not_equal, lt, lte, gt, gte, between, is_null' },
        { id: 'sub_bool', label: 'Boolean\n(4)', detail: 'and, or, not, xor' },
        { id: 'sub_str', label: 'String\n(12)', detail: 'concat, like, substring, upper, lower, trim, ltrim, rtrim, replace, char_length, starts_with, ends_with' },
        { id: 'sub_agg', label: 'Aggregate\n(8)', detail: 'sum, min, max, count, avg, any, every, count_distinct' },
        { id: 'sub_dt', label: 'Datetime\n(6)', detail: 'extract, add_intervals, current_date, current_timestamp, local_timestamp, date_trunc' },
        { id: 'sub_cast', label: 'Casting\n(3)', detail: 'cast, try_cast, safe_cast' }
    ];

    var extCats = [
        { id: 'ext_pat', label: 'Pattern\n(4)', detail: 'regex_match, regex_replace, glob, ilike' },
        { id: 'ext_temp', label: 'Temporal\n(18)', detail: 'year, month, day, hour, minute, second, weekday, week, quarter, epoch, ordinal_day, truncate, round, offset_by, combine, duration, total_days, timestamp' },
        { id: 'ext_list', label: 'List\n(8)', detail: 'explode, list_get, list_len, list_contains, list_sum, list_mean, list_min, list_max' },
        { id: 'ext_struct', label: 'Struct\n(4)', detail: 'field, rename_fields, unnest, to_struct' },
        { id: 'ext_win', label: 'Window\n(6)', detail: 'rank, dense_rank, row_number, lag, lead, nth_value' },
        { id: 'ext_null', label: 'Null\n(5)', detail: 'is_null, is_not_null, fill_null, coalesce, drop_nulls' },
        { id: 'ext_cond', label: 'Conditional\n(3)', detail: 'when/then/otherwise, if_else, coalesce' }
    ];

    var cx = 400;
    var rootY = 40;
    var branchY = 130;
    var leafY_start = 230;
    var leafSpacing = 40;

    var nodes = new vis.DataSet();
    var edges = new vis.DataSet();

    // Root
    nodes.add({
        id: 'root', label: 'Function Keys', x: cx, y: rootY, fixed: true,
        shape: 'box', widthConstraint: { minimum: 140 },
        color: { background: darkLime, border: '#145214', hover: { background: limeGreen, border: '#145214' } },
        font: { color: '#fff', size: 15, bold: true }, borderWidth: 2
    });

    // Substrait branch
    var subX = cx - 220;
    nodes.add({
        id: 'substrait', label: 'Substrait\nStandard', x: subX, y: branchY, fixed: true,
        shape: 'box', widthConstraint: { minimum: 120 },
        color: { background: limeGreen, border: darkLime, hover: { background: lightLime, border: darkLime } },
        font: { color: '#000', size: 13, multi: true }, borderWidth: 2
    });
    edges.add({ from: 'root', to: 'substrait', color: { color: darkLime }, width: 2, arrows: { to: { enabled: true, scaleFactor: 0.6 } }, smooth: false });

    // Extensions branch
    var extX = cx + 220;
    nodes.add({
        id: 'extensions', label: 'Mountainash\nExtensions', x: extX, y: branchY, fixed: true,
        shape: 'box', widthConstraint: { minimum: 120 },
        color: { background: limeGreen, border: darkLime, hover: { background: lightLime, border: darkLime } },
        font: { color: '#000', size: 13, multi: true }, borderWidth: 2
    });
    edges.add({ from: 'root', to: 'extensions', color: { color: darkLime }, width: 2, arrows: { to: { enabled: true, scaleFactor: 0.6 } }, smooth: false });

    // Substrait leaves
    var subLeafX0 = subX - (substraitCats.length - 1) * leafSpacing / 2;
    substraitCats.forEach(function(cat, i) {
        var lx = subLeafX0 + i * leafSpacing;
        nodes.add({
            id: cat.id, label: cat.label, x: lx, y: leafY_start + (i % 2) * 50, fixed: true,
            shape: 'box', widthConstraint: { minimum: 80 },
            color: { background: lightLime, border: limeGreen, hover: { background: '#c8ffc8', border: limeGreen } },
            font: { color: '#000', size: 11, multi: true }, borderWidth: 1,
            detail: cat.detail
        });
        edges.add({ from: 'substrait', to: cat.id, color: { color: limeGreen }, width: 1.5, smooth: { type: 'cubicBezier', roundness: 0.3 } });
    });

    // Extension leaves
    var extLeafX0 = extX - (extCats.length - 1) * leafSpacing / 2;
    extCats.forEach(function(cat, i) {
        var lx = extLeafX0 + i * leafSpacing;
        nodes.add({
            id: cat.id, label: cat.label, x: lx, y: leafY_start + (i % 2) * 50, fixed: true,
            shape: 'box', widthConstraint: { minimum: 80 },
            color: { background: lightLime, border: limeGreen, hover: { background: '#c8ffc8', border: limeGreen } },
            font: { color: '#000', size: 11, multi: true }, borderWidth: 1,
            detail: cat.detail
        });
        edges.add({ from: 'extensions', to: cat.id, color: { color: limeGreen }, width: 1.5, smooth: { type: 'cubicBezier', roundness: 0.3 } });
    });

    var container = document.getElementById('network');
    var network = new vis.Network(container, { nodes: nodes, edges: edges }, {
        interaction: { zoomView: false, dragView: false, dragNodes: false, hover: true },
        physics: { enabled: false },
        layout: { improvedLayout: false }
    });

    var detailPanel = document.getElementById('detail');

    network.on('click', function(params) {
        if (params.nodes.length > 0) {
            var node = nodes.get(params.nodes[0]);
            if (node && node.detail) {
                var ops = node.detail.split(', ');
                detailPanel.innerHTML = '<b>' + node.label.replace(/\n/g, ' ') + '</b><br><br>' +
                    ops.map(function(o) { return '<span style="display:inline-block;margin:2px;padding:2px 6px;background:#e8f5e9;border-radius:4px;font-family:monospace;font-size:11px;">' + o + '</span>'; }).join('');
                detailPanel.style.display = 'block';
            } else {
                detailPanel.style.display = 'none';
            }
        } else {
            detailPanel.style.display = 'none';
        }
    });
});
