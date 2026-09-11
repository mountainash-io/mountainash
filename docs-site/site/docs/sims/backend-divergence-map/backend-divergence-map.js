// Backend Divergence Map
// CANVAS_HEIGHT: 500
document.addEventListener('DOMContentLoaded', function() {
    const main = document.querySelector('main');

    var operations = ['filter', 'join', 'aggregate', 'sort', 'null_handling', 'group_by', 'window', 'cast'];
    var opLabels = ['Filter', 'Join', 'Aggregate', 'Sort', 'Null Handling', 'Group By', 'Window Fns', 'Type Cast'];
    var backends = ['Polars', 'Narwhals', 'Ibis'];

    // 0=green(identical), 1=yellow(minor), 2=red(incompatible)
    var matrix = [
        [0, 0, 0],  // filter
        [0, 1, 1],  // join
        [0, 1, 0],  // aggregate
        [0, 0, 0],  // sort
        [0, 2, 1],  // null_handling
        [0, 0, 0],  // group_by
        [0, 2, 1],  // window
        [0, 1, 1]   // cast
    ];

    var details = [
        ['Identical predicate syntax', 'Identical via nw.col() wrapper', 'Identical via ibis expressions'],
        ['Full join type support', 'Cross join unsupported; workaround via merge', 'Anti-join syntax differs; uses .anti_join()'],
        ['All agg functions aligned', 'median() not in all pandas backends', 'Identical SQL aggregation semantics'],
        ['Stable sort with nulls_last', 'Identical via sort_values()', 'Identical via order_by()'],
        ['Native null propagation', 'NaN/None confusion in pandas; requires careful coercion', 'SQL NULL semantics; three-valued logic differences'],
        ['Identical groupby semantics', 'Identical via nw.group_by()', 'Identical GROUP BY compilation'],
        ['Full window function support', 'Not supported in all pandas versions; partial workarounds', 'SQL window functions; minor syntax mapping'],
        ['Strict type casting', 'pandas dtype coercion may be lossy', 'SQL CAST semantics vary by backend engine']
    ];

    var severityColors = ['#27AE60', '#F1C40F', '#E74C3C'];
    var severityLabels = ['Identical', 'Minor Divergence', 'Known Incompatibility'];
    var severityFilter = -1; // -1 = show all

    function render() {
        var cellW = 130, cellH = 42, headerH = 40, labelW = 110, padL = 20, padT = 60;

        var html = '<div style="position:relative;width:100%;height:500px;background:#f0f8ff;font-family:Arial,sans-serif;overflow:hidden;">';
        html += '<div style="position:absolute;top:10px;left:50%;transform:translateX(-50%);font-size:16px;font-weight:bold;">Backend Divergence Map</div>';

        // Legend and filter
        html += '<div style="position:absolute;top:10px;left:10px;background:rgba(255,255,255,0.95);padding:8px;border-radius:8px;font-size:11px;box-shadow:0 2px 4px rgba(0,0,0,0.1);">';
        html += '<div style="font-weight:bold;margin-bottom:4px;">Filter by severity</div>';
        html += '<div style="cursor:pointer;margin:2px 0;" data-sev="-1"><span style="color:#666;">&#9679;</span> Show All</div>';
        severityLabels.forEach(function(label, i) {
            html += '<div style="cursor:pointer;margin:2px 0;" data-sev="' + i + '"><span style="color:' + severityColors[i] + ';">&#9679;</span> ' + label + '</div>';
        });
        html += '</div>';

        // Column headers
        backends.forEach(function(b, ci) {
            var x = padL + labelW + ci * cellW;
            html += '<div style="position:absolute;left:' + x + 'px;top:' + padT + 'px;width:' + cellW + 'px;height:' + headerH + 'px;display:flex;align-items:center;justify-content:center;font-weight:bold;font-size:13px;color:#333;">' + b + '</div>';
        });

        // Rows
        operations.forEach(function(op, ri) {
            var y = padT + headerH + ri * cellH;
            // Row label
            html += '<div style="position:absolute;left:' + padL + 'px;top:' + y + 'px;width:' + labelW + 'px;height:' + cellH + 'px;display:flex;align-items:center;font-size:12px;font-weight:bold;color:#444;">' + opLabels[ri] + '</div>';
            // Cells
            backends.forEach(function(b, ci) {
                var sev = matrix[ri][ci];
                var show = severityFilter === -1 || severityFilter === sev;
                var bg = show ? severityColors[sev] : '#E8E8E8';
                var textColor = show ? '#fff' : '#ccc';
                var x = padL + labelW + ci * cellW;
                html += '<div class="cell" data-row="' + ri + '" data-col="' + ci + '" style="position:absolute;left:' + x + 'px;top:' + y + 'px;width:' + (cellW - 4) + 'px;height:' + (cellH - 4) + 'px;margin:2px;background:' + bg + ';border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:10px;color:' + textColor + ';cursor:pointer;transition:all 0.2s;">' + (show ? severityLabels[sev] : '') + '</div>';
            });
        });

        // Detail panel
        html += '<div id="detail" style="position:absolute;bottom:10px;left:50%;transform:translateX(-50%);max-width:500px;background:rgba(255,255,255,0.95);padding:10px 14px;border-radius:8px;font-size:12px;box-shadow:0 2px 4px rgba(0,0,0,0.1);display:none;text-align:center;"></div>';
        html += '</div>';

        main.innerHTML = html;

        // Click handlers for cells
        document.querySelectorAll('.cell').forEach(function(cell) {
            cell.addEventListener('click', function() {
                var ri = parseInt(this.getAttribute('data-row'));
                var ci = parseInt(this.getAttribute('data-col'));
                var detail = document.getElementById('detail');
                detail.innerHTML = '<b>' + opLabels[ri] + ' / ' + backends[ci] + '</b><br>' + details[ri][ci];
                detail.style.display = 'block';
            });
        });

        // Filter handlers
        document.querySelectorAll('[data-sev]').forEach(function(el) {
            el.addEventListener('click', function() {
                severityFilter = parseInt(this.getAttribute('data-sev'));
                render();
            });
        });
    }

    render();
});
