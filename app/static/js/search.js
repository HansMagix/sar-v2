// SAR v2 Search Logic (Master Overhaul)
document.addEventListener("DOMContentLoaded", function () {

    // --- Common Render Logic ---
    const renderOption = function (data, escape) {
        return '<div class="px-2 py-1 text-slate-300 hover:bg-blue-600 hover:text-white transition">' + escape(data.text) + '</div>';
    };

    // --- Tom Select Config ---
    const singleOptions = {
        create: false,
        sortField: { field: "text", direction: "asc" },
        plugins: ['dropdown_input'],
        maxOptions: 200,
        render: { option: renderOption },
        valueField: 'value',
        labelField: 'text',
        searchField: 'text'
    };

    const multiOptions = {
        create: false,
        sortField: { field: "text", direction: "asc" },
        plugins: ['dropdown_input', 'remove_button'],
        maxItems: null,
        render: {
            option: renderOption,
            item: function (data, escape) {
                return '<div class="item px-2 py-0.5 bg-blue-900/40 border border-blue-500/30 text-blue-200 rounded-md mr-1 mb-1 flex items-center gap-1">'
                    + escape(data.text) +
                    '</div>';
            }
        },
        valueField: 'value',
        labelField: 'text',
        searchField: 'text'
    };

    let tsCourse, tsUni, tsCluster; // Instances

    // --- 1. Fetch Options Async ---
    fetch('/api/filters')
        .then(response => response.json())
        .then(data => {
            // Transform data for Tom Select (expecting array of objects {value: 'x', text: 'x'})
            const courses = data.courses.map(x => ({ value: x, text: x }));
            const universities = data.universities.map(x => ({ value: x, text: x }));
            const clusters = data.clusters.map(x => ({ value: x, text: x }));

            // --- 2. Initialize Tom Select ---
            if (document.getElementById('select-course')) {
                // clear loading option
                document.getElementById('select-course').innerHTML = '';
                tsCourse = new TomSelect("#select-course", {
                    ...singleOptions,
                    options: courses,
                    placeholder: "All Courses..."
                });
            }

            if (document.getElementById('select-uni')) {
                document.getElementById('select-uni').innerHTML = '';
                tsUni = new TomSelect("#select-uni", {
                    ...multiOptions,
                    options: universities,
                    placeholder: "All Universities..."
                });
            }

            if (document.getElementById('select-cluster')) {
                document.getElementById('select-cluster').innerHTML = '';
                tsCluster = new TomSelect("#select-cluster", {
                    ...multiOptions,
                    sortField: { field: "$order" },
                    options: clusters,
                    placeholder: "All Clusters..."
                });
            }

            // Re-attach listeners after init
            attachListeners();

            // Restore State from Deep Link
            restoreFromURL();
        })
        .catch(err => console.error("Failed to load filters:", err));


    // --- 3. Auto-Search Logic ---
    const inputPoints = document.getElementById('input-points');
    const dynamicContainer = document.getElementById('dynamic-points-container');
    const resultsGrid = document.getElementById('results-grid');

    function updatePointsUI() {
        if (!tsCluster || !dynamicContainer || !inputPoints) return;

        const clusters = tsCluster.getValue(); // Returns array of strings or string
        const clusterArray = Array.isArray(clusters) ? clusters : (clusters ? [clusters] : []);

        if (clusterArray.length > 1) {
            // Multi-Cluster Mode
            inputPoints.classList.add('hidden');
            dynamicContainer.classList.remove('hidden');

            // Diff Check: Only rebuild if clusters changed significantly to avoid losing focus/values
            // Ideally we just want to ADD/REMOVE fields, but full rebuild is easier for now. 
            // To preserve values, we can read current ones.
            const currentValues = {};
            dynamicContainer.querySelectorAll('.dynamic-point-input').forEach(inp => {
                currentValues[inp.dataset.cluster] = inp.value;
            });

            // Rebuild
            dynamicContainer.innerHTML = '';
            clusterArray.forEach(c => {
                const safeValue = currentValues[c] || inputPoints.value || ''; // Fallback to main input

                const div = document.createElement('div');
                div.innerHTML = `
                    <label class="block text-[10px] uppercase font-bold text-slate-500 mb-1">${c}</label>
                    <input type="number" step="0.001" min="0" max="48" 
                        class="dynamic-point-input w-full bg-slate-900 border border-slate-700 rounded px-3 py-2 text-sm text-white focus:ring-2 focus:ring-emerald-500/50 outline-none transition" 
                        data-cluster="${c}" value="${safeValue}" placeholder="Points for ${c}">
                `;
                dynamicContainer.appendChild(div);

                // Attach listener to new input
                const inp = div.querySelector('input');
                let timer;
                inp.addEventListener('input', () => {
                    clearTimeout(timer);
                    timer = setTimeout(performSearch, 500);
                });
            });

        } else {
            // Single/No Cluster Mode
            inputPoints.classList.remove('hidden');
            dynamicContainer.classList.add('hidden');
        }
    }

    function performSearch() {
        const course = tsCourse ? tsCourse.getValue() : '';
        const uni = tsUni ? tsUni.getValue() : [];
        const cluster = tsCluster ? tsCluster.getValue() : [];
        const reach = (document.getElementById('check-reach') && document.getElementById('check-reach').checked) ? 'true' : '';

        // Points Logic
        let points = inputPoints ? inputPoints.value : '';
        let clusterMap = {};

        // Gather Dynamic Points if visible
        if (dynamicContainer && !dynamicContainer.classList.contains('hidden')) {
            dynamicContainer.querySelectorAll('.dynamic-point-input').forEach(inp => {
                if (inp.value) clusterMap[inp.dataset.cluster] = inp.value;
            });
            // Also update main 'points' var to be non-empty so "Gatekeeper" doesn't block request
            // We use the first found value or a dummy just to pass the "has_points" check if user entered ANY cluster point
            if (Object.keys(clusterMap).length > 0) {
                points = Object.values(clusterMap)[0];
            }
        }

        // Build Query String
        const params = new URLSearchParams();

        if (course) params.append('course', course);
        if (points) params.append('points', points); // Still send main points as fallback/signal
        if (reach) params.append('reach', reach);

        if (Object.keys(clusterMap).length > 0) {
            params.append('cluster_map', JSON.stringify(clusterMap));
        }

        if (Array.isArray(uni) && uni.length > 0) {
            uni.forEach(v => params.append('uni', v));
        } else if (typeof uni === 'string' && uni) {
            params.append('uni', uni);
        }

        if (Array.isArray(cluster) && cluster.length > 0) {
            cluster.forEach(v => params.append('cluster', v));
        } else if (typeof cluster === 'string' && cluster) {
            params.append('cluster', cluster);
        }

        // AJAX Fetch
        resultsGrid.style.opacity = '0.5';

        // 1. Sync URL (Deep Linking)
        const newUrl = `${window.location.pathname}?${params.toString()}`;
        window.history.replaceState(null, '', newUrl);

        fetch(`/search?${params.toString()}`, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
            .then(response => response.text())
            .then(html => {
                resultsGrid.innerHTML = html;
                resultsGrid.style.opacity = '1';

                // Restore Selections (Persistence)
                setTimeout(restoreSelections, 50);
            })
            .catch(err => {
                console.error('Search failed', err);
                resultsGrid.style.opacity = '1';
            });
    }

    function attachListeners() {
        if (tsCourse) tsCourse.on('change', performSearch);
        if (tsUni) tsUni.on('change', performSearch);
        if (tsCluster) tsCluster.on('change', () => {
            updatePointsUI();
            performSearch();
        });
    }

    function restoreFromURL() {
        const params = new URLSearchParams(window.location.search);

        let needsSearch = false;

        // Restore Course
        const course = params.get('course');
        if (course && tsCourse) {
            tsCourse.setValue(course, true); // true = silent (no event)
            needsSearch = true;
        }

        // Restore Unis
        const unis = params.getAll('uni');
        if (unis.length > 0 && tsUni) {
            unis.forEach(u => tsUni.addItem(u, true));
            needsSearch = true;
        }

        // Restore Clusters
        const clusters = params.getAll('cluster');
        if (clusters.length > 0 && tsCluster) {
            clusters.forEach(c => tsCluster.addItem(c, true));
            updatePointsUI(); // Important to show dynamic inputs
            needsSearch = true;
        }

        // Restore Points
        const points = params.get('points');
        if (points && inputPoints) {
            inputPoints.value = points;
            needsSearch = true;
        }

        // Restore Reach
        const reach = params.get('reach');
        const checkReach = document.getElementById('check-reach');
        if (reach === 'true' && checkReach) {
            checkReach.checked = true;
            needsSearch = true;
        }

        // Restore Dynamic Map
        // The URL might have cluster_map parameter if we implemented that in performSearch URL building? based on implementation...
        // The previous implementation of performSearch appends cluster_map param. 
        // We should handle that.
        const clusterMapJson = params.get('cluster_map');
        if (clusterMapJson) {
            try {
                const map = JSON.parse(clusterMapJson);
                const dynamicContainer = document.getElementById('dynamic-points-container');
                if (dynamicContainer) {
                    // Populate values - updatePointsUI should have created inputs if clusters were set
                    Object.keys(map).forEach(key => {
                        const inp = dynamicContainer.querySelector(`input[data-cluster="${key}"]`);
                        if (inp) inp.value = map[key];
                    });
                    needsSearch = true;
                }
            } catch (e) { console.error("Error parsing cluster_map", e); }
        }

        if (needsSearch) {
            performSearch();
        }
    }

    // Reach listener
    const checkReach = document.getElementById('check-reach');
    if (checkReach) {
        checkReach.addEventListener('change', function (e) {
            if (this.checked) {
                // Free for all
            }
            performSearch();
        });
    }

    // Points listener is independent of Tom Select init
    if (inputPoints) {
        let debounceTimer;
        inputPoints.addEventListener('input', () => {
            // Strict Clamping 0-48
            let val = parseFloat(inputPoints.value);
            if (val < 0) inputPoints.value = 0;
            if (val > 48) inputPoints.value = 48;

            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(performSearch, 500);
        });
    }

    // --- 5. Export Button Logic ---
    const btnExport = document.getElementById('btn-export');
    if (btnExport) {
        btnExport.addEventListener('click', function () {
            // 1. Check Tier
            // 1. Check Tier - Removed (Free)

            // 2. Gather Filters (Reuse performSearch logic basically)
            const course = tsCourse ? tsCourse.getValue() : '';
            const uni = tsUni ? tsUni.getValue() : [];
            const cluster = tsCluster ? tsCluster.getValue() : [];
            const points = inputPoints ? inputPoints.value : '';

            // 3. Build URL
            const params = new URLSearchParams();
            if (course) params.append('course', course);
            if (points) params.append('points', points);

            if (Array.isArray(uni) && uni.length > 0) uni.forEach(v => params.append('uni', v));
            else if (typeof uni === 'string' && uni) params.append('uni', uni);

            if (Array.isArray(cluster) && cluster.length > 0) cluster.forEach(v => params.append('cluster', v));
            else if (typeof cluster === 'string' && cluster) params.append('cluster', cluster);

            // 4. Trigger Download
            window.location.href = `/export?${params.toString()}`;
        });
    }
});

// --- 6. Compare Logic (Global Scope) ---
let selectedCourses = [];

function handleCompare(checkbox) {
    // 0. Premium Check
    // 0. Premium Check - Removed (Free)

    // Parse Course Data
    let course;
    if (typeof checkbox.dataset.course === 'string') {
        course = JSON.parse(checkbox.dataset.course);
    } else {
        course = checkbox.dataset.course;
    }

    if (checkbox.checked) {
        // Add to Selection
        if (selectedCourses.length >= 4) {
            alert("Compare Limit: You can compare up to 4 courses at a time.");
            checkbox.checked = false;
            return;
        }
        selectedCourses.push(course);
        addToTray(course); // Add visual item to tray
    } else {
        // Remove from Selection
        selectedCourses = selectedCourses.filter(c => c.code !== course.code);
        removeFromTray(course.code); // Remove visual item from tray
    }

    updateTrayUI();
}

// Visual Tray Logic
function addToTray(course) {
    const trayItems = document.getElementById('tray-items');

    const div = document.createElement('div');
    div.id = `tray-item-${course.code}`;
    div.className = "bg-slate-700 p-3 rounded border border-slate-600 flex justify-between items-center group";
    div.innerHTML = `
        <div>
            <div class="text-white font-bold text-sm truncate w-[200px]">${course.name}</div>
            <div class="text-slate-400 text-xs">${course.institution}</div>
        </div>
        <button onclick="removeComparable('${course.code}')" class="text-slate-500 hover:text-red-400 p-1">
            <i class="fa-solid fa-xmark"></i>
        </button>
    `;
    trayItems.appendChild(div);
}

function removeFromTray(code) {
    const item = document.getElementById(`tray-item-${code}`);
    if (item) item.remove();
}

// Triggered by 'X' button in Tray
function removeComparable(code) {
    // 1. Remove from data
    selectedCourses = selectedCourses.filter(c => c.code !== code);

    // 2. Remove visual from tray
    removeFromTray(code);

    // 3. Uncheck if present in current grid
    const checkbox = document.querySelector(`input[type="checkbox"][data-code="${code}"]`);
    if (checkbox) checkbox.checked = false;

    updateTrayUI();
}

function updateTrayUI() {
    const tray = document.getElementById('comparison-tray');
    const countSpan = document.getElementById('tray-count');

    if (countSpan) countSpan.innerText = selectedCourses.length;

    if (selectedCourses.length > 0) {
        tray.classList.remove('hidden');
    } else {
        tray.classList.add('hidden');
    }
}

function openCompareModal() {
    const modal = document.getElementById('modal-compare');
    const container = document.getElementById('compare-container');

    modal.classList.remove('hidden');
    container.innerHTML = ''; // Clear previous

    if (selectedCourses.length === 0) {
        container.innerHTML = '<div class="p-10 text-slate-500 w-full text-center">No courses selected</div>';
        return;
    }

    // Helper to render a column
    const renderColumn = (c) => {
        let gapHtml = '';
        if (c.diff !== undefined) {
            const color = c.diff >= 0 ? 'text-emerald-400' : 'text-amber-400';
            const icon = c.diff >= 0 ? '<i class="fa-solid fa-arrow-up"></i>' : '<i class="fa-solid fa-arrow-down"></i>';
            const sign = c.diff >= 0 ? '+' : '';
            gapHtml = `<span class="${color} font-mono font-bold text-sm bg-slate-800 px-2 py-1 rounded border border-slate-700">${icon} ${sign}${c.diff.toFixed(2)}</span>`;
        } else {
            gapHtml = '<span class="text-slate-500 text-xs">Points not set</span>';
        }

        let clusterName = c.cluster || '-';
        const match = clusterName.match(/^(Cluster\s+\d+)/i);
        if (match) {
            clusterName = match[1];
        }

        const div = document.createElement('div');
        // Fixed Width Column
        div.className = "w-40 md:w-48 flex-shrink-0 border-r border-slate-700/50 hover:bg-slate-800/50 transition space-y-4 py-4";
        div.innerHTML = `
            <div class="h-14 flex items-center justify-center font-bold text-white text-xs md:text-sm leading-tight px-2 text-center break-words overflow-hidden">${c.name}</div>
            <div class="h-12 flex items-center justify-center text-slate-300 text-[10px] md:text-xs px-2 text-center leading-tight">${c.institution}</div>
            <div class="h-12 flex items-center justify-center font-mono text-white font-bold text-base md:text-lg border-t border-slate-700/50 bg-slate-900/20">${c.cutoff || 'N/A'}</div>
            <div class="h-12 flex items-center justify-center border-t border-slate-700/50">${gapHtml}</div>
            <div class="h-12 flex items-center justify-center text-slate-400 text-[10px] font-bold uppercase tracking-wider border-t border-slate-700/50">${clusterName}</div>
        `;
        return div;
    };

    selectedCourses.forEach(c => {
        container.appendChild(renderColumn(c));
    });
}

function closeCompareModal() {
    document.getElementById('modal-compare').classList.add('hidden');
}

function restoreSelections() {
    // Sync checkboxes in the new grid with selectedCourses state
    selectedCourses.forEach(course => {
        // Robust Selection via data-code
        const checkbox = document.querySelector(`input[type="checkbox"][data-code="${course.code}"]`);

        if (checkbox) {
            checkbox.checked = true;

            // Optional: Highlight the card
            const card = checkbox.closest('.bg-slate-800');
            if (card) {
                card.classList.remove('border-slate-700');
                card.classList.add('ring-1', 'ring-blue-500/50', 'border-blue-500/30');
            }
        }
    });
}

